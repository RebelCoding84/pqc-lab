from __future__ import annotations

"""Capacity harness with per-handshake latency and throughput reporting.

Examples:
    python -m src.capacity.harness \
      --profile profiles/real_mlkem.yaml \
      --concurrency 1 \
      --duration 30 \
      --warmup 5 \
      --out reports/mlkem768_c1.json

    for c in 1 2 4 8 16; do
      python -m src.capacity.harness \
        --profile profiles/real_mlkem.yaml \
        --concurrency "$c" \
        --duration 30 \
        --warmup 5 \
        --out "reports/mlkem768_c${c}.json";
    done
"""

import argparse
import copy
import hashlib
import json
import os
import platform
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from src.crypto_agility.runner import run_profile
from src.crypto_agility.schema import Profile, _parse_profile

MAX_LATENCY_SAMPLES = 2_000_000
CPU_SAMPLE_INTERVAL_S = 0.5


@dataclass
class Metrics:
    success_count: int = 0
    failure_count: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    latency_truncated: bool = False
    errors: Counter[tuple[str, str]] = field(default_factory=Counter)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit-ready key-exchange capacity harness."
    )
    parser.add_argument("--profile", required=True, help="Path to YAML profile.")
    parser.add_argument(
        "--concurrency",
        required=True,
        type=_positive_int,
        help="Worker thread count.",
    )
    parser.add_argument(
        "--duration",
        required=True,
        type=_positive_int,
        help="Measurement duration in seconds.",
    )
    parser.add_argument(
        "--warmup",
        required=True,
        type=_non_negative_int,
        help="Warmup duration in seconds.",
    )
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args(argv)

    profile_path = Path(args.profile)
    try:
        profile_dict, profile_obj = _load_profile_once(profile_path)
    except (OSError, yaml.YAMLError, ValueError, TypeError) as exc:
        print(f"fatal: could not load profile: {exc}", file=sys.stderr)
        return 1

    try:
        report = _run_harness(
            profile_path=profile_path,
            profile_dict=profile_dict,
            profile_obj=profile_obj,
            concurrency=args.concurrency,
            duration_s=args.duration,
            warmup_s=args.warmup,
        )
    except Exception as exc:  # Non-fatal benchmark errors are reported in JSON.
        report = _build_internal_error_report(
            profile_path=profile_path,
            profile_dict=profile_dict,
            profile_obj=profile_obj,
            concurrency=args.concurrency,
            duration_s=args.duration,
            warmup_s=args.warmup,
            exc=exc,
        )

    payload = json.dumps(report, indent=2, sort_keys=True)
    out_path = Path(args.out)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"fatal: could not write output: {exc}", file=sys.stderr)
        return 1

    print(payload)
    return 0


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def _load_profile_once(path: Path) -> tuple[dict[str, Any], Profile]:
    raw_text = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(raw_text)
    if not isinstance(loaded, Mapping):
        raise ValueError("profile YAML must be a mapping at top level")
    profile_dict = _to_plain_object(loaded)
    if not isinstance(profile_dict, dict):
        raise ValueError("profile YAML root must be a dict")
    profile_obj = _parse_profile(profile_dict)
    return profile_dict, profile_obj


def _to_plain_object(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain_object(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain_object(item) for item in value]
    return value


def _run_harness(
    profile_path: Path,
    profile_dict: dict[str, Any],
    profile_obj: Profile,
    concurrency: int,
    duration_s: int,
    warmup_s: int,
) -> dict[str, Any]:
    mode = _detect_mode(profile_dict)
    provider = profile_obj.provider or "mock"
    notes: list[str] = []

    if warmup_s > 0:
        warmup_deadline = time.perf_counter() + float(warmup_s)
        _run_phase(
            concurrency=concurrency,
            deadline=warmup_deadline,
            profile_template=profile_dict,
            metrics=None,
        )
        notes.append("Warmup completed; warmup metrics discarded and counters reset.")

    metrics = Metrics()

    cpu_samples: list[float] = []
    cpu_stop = threading.Event()
    cpu_thread, cpu_note = _start_cpu_sampler(cpu_samples, cpu_stop)
    if cpu_note is not None:
        notes.append(cpu_note)

    measurement_deadline = time.perf_counter() + float(duration_s)
    try:
        _run_phase(
            concurrency=concurrency,
            deadline=measurement_deadline,
            profile_template=profile_dict,
            metrics=metrics,
        )
    finally:
        cpu_stop.set()
        if cpu_thread is not None:
            cpu_thread.join(timeout=2.0)

    if metrics.latency_truncated:
        notes.append("Latency list hit 2,000,000 samples; additional latencies were dropped.")

    total_handshakes = metrics.success_count + metrics.failure_count
    throughput_hs_per_sec = total_handshakes / float(duration_s)
    latency_summary = _summarize_latencies(metrics.latencies_ms)
    cpu_summary = _summarize_cpu(cpu_samples)
    errors = _format_errors(metrics.errors)

    return {
        "profile_path": str(profile_path),
        "profile_name": profile_obj.name,
        "provider": provider,
        "mode": mode,
        "concurrency": concurrency,
        "warmup_s": warmup_s,
        "duration_s": duration_s,
        "timestamp_utc": _utc_now_iso(),
        "environment": {
            "type": "bare_metal_container",
            "image": "pqc-lab:pqc",
            "python": platform.python_version(),
            "cpu_count": int(os.cpu_count() or 0),
            "platform": platform.platform(),
            "processor": platform.processor() or "",
            "git_commit": os.environ.get("GIT_COMMIT", ""),
        },
        "workload": {
            "handshake_model": "burst",
            "iterations_per_handshake": 1,
        },
        "results": {
            "success_count": metrics.success_count,
            "failure_count": metrics.failure_count,
            "throughput_hs_per_sec": throughput_hs_per_sec,
        },
        "latency_ms": latency_summary,
        "latency_truncated": metrics.latency_truncated,
        "cpu": cpu_summary,
        "errors": errors,
        "notes": notes,
    }


def _run_phase(
    concurrency: int,
    deadline: float,
    profile_template: dict[str, Any],
    metrics: Metrics | None,
) -> None:
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                _worker_loop,
                deadline,
                profile_template,
                metrics,
            )
            for _ in range(concurrency)
        ]
        for future in futures:
            future.result()


def _worker_loop(
    deadline: float,
    profile_template: dict[str, Any],
    metrics: Metrics | None,
) -> None:
    while time.perf_counter() < deadline:
        try:
            # Per-handshake deep copy for auditability while keeping seed fields unchanged.
            profile_copy = copy.deepcopy(profile_template)
            key_exchange = profile_copy.get("key_exchange")
            if not isinstance(key_exchange, dict):
                raise ValueError("profile_copy.key_exchange must be a dict")
            key_exchange["iterations"] = 1
            iterations = int(key_exchange.get("iterations", 0))
            if iterations != 1:
                raise ValueError("failed to force key_exchange.iterations=1")
            handshake_profile = _parse_profile(profile_copy)

            started = time.perf_counter()
            try:
                result = run_profile(handshake_profile)
                call_exc: Exception | None = None
            except Exception as exc:  # noqa: PERF203
                result = None
                call_exc = exc
            latency_ms = (time.perf_counter() - started) * 1000.0
        except Exception as exc:  # Includes deepcopy/mutation failures.
            if metrics is None:
                continue
            err_key = (exc.__class__.__name__, _hash_message(exc))
            with metrics.lock:
                metrics.failure_count += 1
                metrics.errors[err_key] += 1
            continue

        if metrics is None:
            continue

        with metrics.lock:
            if len(metrics.latencies_ms) < MAX_LATENCY_SAMPLES:
                metrics.latencies_ms.append(latency_ms)
            else:
                metrics.latency_truncated = True

            if call_exc is not None:
                metrics.failure_count += 1
                metrics.errors[(call_exc.__class__.__name__, _hash_message(call_exc))] += 1
                continue

            if _is_success_result(result):
                metrics.success_count += 1
            else:
                metrics.failure_count += 1


def _is_success_result(result: Any) -> bool:
    if not isinstance(result, Mapping):
        return False

    if "failure_count" in result:
        try:
            if result["failure_count"] > 0:
                return False
        except TypeError:
            return False

    if "success_count" in result:
        try:
            return result["success_count"] > 0
        except TypeError:
            return False

    return False


def _hash_message(exc: Exception) -> str:
    return hashlib.sha256(str(exc).encode("utf-8")).hexdigest()[:12]


def _detect_mode(profile_dict: Mapping[str, Any]) -> str:
    key_exchange = profile_dict.get("key_exchange")
    if isinstance(key_exchange, Mapping) and key_exchange.get("hybrid") is not None:
        return "hybrid"
    return "single"


def _start_cpu_sampler(
    cpu_samples: list[float],
    stop_event: threading.Event,
) -> tuple[threading.Thread | None, str | None]:
    try:
        import psutil  # type: ignore
    except Exception:
        return None, "psutil not available; cpu.avg_percent and cpu.peak_percent set to null."

    def _sampler() -> None:
        try:
            psutil.cpu_percent(interval=None)
            while not stop_event.wait(CPU_SAMPLE_INTERVAL_S):
                cpu_samples.append(float(psutil.cpu_percent(interval=None)))
        except Exception:
            return

    thread = threading.Thread(target=_sampler, name="capacity-cpu-sampler", daemon=True)
    thread.start()
    return thread, None


def _summarize_cpu(cpu_samples: list[float]) -> dict[str, float | None]:
    if not cpu_samples:
        return {
            "avg_percent": None,
            "peak_percent": None,
            "sample_interval_s": CPU_SAMPLE_INTERVAL_S,
        }
    avg = sum(cpu_samples) / len(cpu_samples)
    peak = max(cpu_samples)
    return {
        "avg_percent": avg,
        "peak_percent": peak,
        "sample_interval_s": CPU_SAMPLE_INTERVAL_S,
    }


def _summarize_latencies(latencies_ms: list[float]) -> dict[str, float | int | None]:
    count = len(latencies_ms)
    if count == 0:
        return {
            "count": 0,
            "p50": None,
            "p95": None,
            "p99": None,
            "max": None,
        }
    ordered = sorted(latencies_ms)
    return {
        "count": count,
        "p50": _percentile(ordered, 0.50),
        "p95": _percentile(ordered, 0.95),
        "p99": _percentile(ordered, 0.99),
        "max": ordered[-1],
    }


def _percentile(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values:
        raise ValueError("sorted_values must not be empty")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _format_errors(errors: Counter[tuple[str, str]]) -> list[dict[str, Any]]:
    ordered_items = sorted(errors.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
    return [
        {"type": err_type, "msg_hash": msg_hash, "count": count}
        for (err_type, msg_hash), count in ordered_items
    ]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_internal_error_report(
    profile_path: Path,
    profile_dict: Mapping[str, Any],
    profile_obj: Profile,
    concurrency: int,
    duration_s: int,
    warmup_s: int,
    exc: Exception,
) -> dict[str, Any]:
    mode = _detect_mode(profile_dict)
    error_type = exc.__class__.__name__
    error_hash = _hash_message(exc)
    return {
        "profile_path": str(profile_path),
        "profile_name": profile_obj.name,
        "provider": profile_obj.provider or "mock",
        "mode": mode,
        "concurrency": concurrency,
        "warmup_s": warmup_s,
        "duration_s": duration_s,
        "timestamp_utc": _utc_now_iso(),
        "environment": {
            "type": "bare_metal_container",
            "image": "pqc-lab:pqc",
            "python": platform.python_version(),
            "cpu_count": int(os.cpu_count() or 0),
            "platform": platform.platform(),
            "processor": platform.processor() or "",
            "git_commit": os.environ.get("GIT_COMMIT", ""),
        },
        "workload": {
            "handshake_model": "burst",
            "iterations_per_handshake": 1,
        },
        "results": {
            "success_count": 0,
            "failure_count": 0,
            "throughput_hs_per_sec": 0.0,
        },
        "latency_ms": {
            "count": 0,
            "p50": None,
            "p95": None,
            "p99": None,
            "max": None,
        },
        "latency_truncated": False,
        "cpu": {
            "avg_percent": None,
            "peak_percent": None,
            "sample_interval_s": CPU_SAMPLE_INTERVAL_S,
        },
        "errors": [
            {
                "type": error_type,
                "msg_hash": error_hash,
                "count": 1,
            }
        ],
        "notes": ["Benchmark execution raised an internal error; see errors[] for hashed details."],
    }


if __name__ == "__main__":
    raise SystemExit(main())
