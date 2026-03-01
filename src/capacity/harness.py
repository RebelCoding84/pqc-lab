from __future__ import annotations

"""Capacity harness with per-handshake latency and throughput reporting.

Examples:
    python -m src.capacity.harness \
      --profile profiles/real_mlkem.yaml \
      --concurrency 1 \
      --duration 30 \
      --warmup 5 \
      --repeats 3 \
      --percentiles "50,95,99,99.9" \
      --cpu-sample-interval 1.0 \
      --out reports/mlkem768_c1.json

    for c in 1 2 4 8 16; do
      python -m src.capacity.harness \
        --profile profiles/real_mlkem.yaml \
        --concurrency "$c" \
        --duration 30 \
        --warmup 5 \
        --repeats 3 \
        --percentiles "50,95,99,99.9" \
        --cpu-sample-interval 1.0 \
        --out "reports/mlkem768_c${c}.json";
    done
"""

import argparse
import copy
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
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
DEFAULT_PERCENTILES = [50.0, 95.0, 99.0]


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
    parser.add_argument(
        "--repeats",
        default=1,
        type=_positive_int,
        help="Number of warmup+measurement repeats.",
    )
    parser.add_argument(
        "--percentiles",
        default=list(DEFAULT_PERCENTILES),
        type=_percentiles_arg,
        help='Comma-separated latency percentiles (for example: "50,95,99,99.9").',
    )
    parser.add_argument(
        "--cpu-sample-interval",
        default=CPU_SAMPLE_INTERVAL_S,
        type=_cpu_sample_interval_arg,
        help="CPU sampling interval in seconds (must be >= 0.2).",
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
            repeats=args.repeats,
            requested_percentiles=list(args.percentiles),
            cpu_sample_interval_s=args.cpu_sample_interval,
        )
    except Exception as exc:  # Non-fatal benchmark errors are reported in JSON.
        report = _build_internal_error_report(
            profile_path=profile_path,
            profile_dict=profile_dict,
            profile_obj=profile_obj,
            concurrency=args.concurrency,
            duration_s=args.duration,
            warmup_s=args.warmup,
            repeats=args.repeats,
            requested_percentiles=list(args.percentiles),
            cpu_sample_interval_s=args.cpu_sample_interval,
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


def _percentiles_arg(value: str) -> list[float]:
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(part == "" for part in parts):
        raise argparse.ArgumentTypeError(
            'must be a comma-separated list of numbers (for example: "50,95,99")'
        )

    parsed_percentiles: list[float] = []
    seen_keys: set[str] = set()
    for part in parts:
        try:
            percentile = float(part)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid percentile value: {part!r}") from exc
        if not math.isfinite(percentile):
            raise argparse.ArgumentTypeError("percentiles must be finite numbers")
        if percentile < 0.0 or percentile > 100.0:
            raise argparse.ArgumentTypeError("percentiles must be between 0 and 100")
        key = _percentile_key(percentile)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        parsed_percentiles.append(percentile)

    if not parsed_percentiles:
        raise argparse.ArgumentTypeError("at least one percentile is required")
    return parsed_percentiles


def _cpu_sample_interval_arg(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a float") from exc
    if not math.isfinite(parsed):
        raise argparse.ArgumentTypeError("must be a finite float")
    if parsed < 0.2:
        raise argparse.ArgumentTypeError("must be >= 0.2")
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
    repeats: int,
    requested_percentiles: list[float],
    cpu_sample_interval_s: float,
) -> dict[str, Any]:
    mode = _detect_mode(profile_dict)
    provider = profile_obj.provider or "mock"
    notes: list[str] = []

    if warmup_s > 0:
        if repeats == 1:
            notes.append("Warmup completed; warmup metrics discarded and counters reset.")
        else:
            notes.append("Warmup completed before each repeat; warmup metrics discarded and counters reset.")

    repeat_payloads: list[dict[str, Any]] = []
    all_errors: Counter[tuple[str, str]] = Counter()
    truncated_repeats: list[int] = []
    for repeat_index in range(repeats):
        repeat_payload = _run_repeat(
            concurrency=concurrency,
            duration_s=duration_s,
            warmup_s=warmup_s,
            profile_template=profile_dict,
            requested_percentiles=requested_percentiles,
            cpu_sample_interval_s=cpu_sample_interval_s,
        )
        repeat_payloads.append(repeat_payload)
        all_errors.update(repeat_payload["errors_counter"])
        if repeat_payload["latency_truncated"]:
            truncated_repeats.append(repeat_index + 1)
        cpu_note = repeat_payload["cpu_note"]
        if cpu_note is not None and cpu_note not in notes:
            notes.append(cpu_note)

    if truncated_repeats:
        if repeats == 1 and truncated_repeats[0] == 1:
            notes.append("Latency list hit 2,000,000 samples; additional latencies were dropped.")
        else:
            notes.append(
                "Latency list hit 2,000,000 samples in repeats "
                f"{truncated_repeats}; additional latencies were dropped."
            )

    first_repeat = repeat_payloads[0]
    repeat_reports = [
        {
            "results": repeat_payload["results"],
            "latency_ms": repeat_payload["latency_ms"],
            "cpu": repeat_payload["cpu"],
            "success_count": repeat_payload["success_count"],
            "failure_count": repeat_payload["failure_count"],
        }
        for repeat_payload in repeat_payloads
    ]
    summary = _summarize_repeats(repeat_reports, requested_percentiles)
    errors = _format_errors(all_errors)

    return {
        "profile_path": str(profile_path),
        "profile_name": profile_obj.name,
        "provider": provider,
        "mode": mode,
        "concurrency": concurrency,
        "warmup_s": warmup_s,
        "duration_s": duration_s,
        "timestamp_utc": _utc_now_iso(),
        "environment": _build_environment(),
        "workload": {
            "handshake_model": "burst",
            "iterations_per_handshake": 1,
        },
        "results": first_repeat["results"],
        "latency_ms": first_repeat["latency_ms"],
        "latency_truncated": first_repeat["latency_truncated"],
        "cpu": first_repeat["cpu"],
        "percentiles": [_percentile_json_value(p) for p in requested_percentiles],
        "repeats": repeat_reports,
        "summary": summary,
        "errors": errors,
        "notes": notes,
    }


def _run_repeat(
    concurrency: int,
    duration_s: int,
    warmup_s: int,
    profile_template: dict[str, Any],
    requested_percentiles: list[float],
    cpu_sample_interval_s: float,
) -> dict[str, Any]:
    if warmup_s > 0:
        warmup_deadline = time.perf_counter() + float(warmup_s)
        _run_phase(
            concurrency=concurrency,
            deadline=warmup_deadline,
            profile_template=profile_template,
            metrics=None,
        )

    metrics = Metrics()
    system_cpu_samples: list[float] = []
    process_cpu_samples: list[float] = []
    cpu_stop = threading.Event()
    cpu_thread, cpu_note, psutil_available = _start_cpu_sampler(
        system_cpu_samples,
        process_cpu_samples,
        cpu_stop,
        cpu_sample_interval_s,
    )

    measurement_deadline = time.perf_counter() + float(duration_s)
    try:
        _run_phase(
            concurrency=concurrency,
            deadline=measurement_deadline,
            profile_template=profile_template,
            metrics=metrics,
        )
    finally:
        cpu_stop.set()
        if cpu_thread is not None:
            cpu_thread.join(timeout=2.0)

    total_handshakes = metrics.success_count + metrics.failure_count
    throughput_hs_per_sec = total_handshakes / float(duration_s)

    return {
        "results": {
            "success_count": metrics.success_count,
            "failure_count": metrics.failure_count,
            "throughput_hs_per_sec": throughput_hs_per_sec,
        },
        "latency_ms": _summarize_latencies(
            metrics.latencies_ms,
            requested_percentiles=requested_percentiles,
        ),
        "latency_truncated": metrics.latency_truncated,
        "cpu": _summarize_cpu(
            system_cpu_samples=system_cpu_samples,
            process_cpu_samples=process_cpu_samples,
            sample_interval_s=cpu_sample_interval_s,
            psutil_available=psutil_available,
        ),
        "success_count": metrics.success_count,
        "failure_count": metrics.failure_count,
        "errors_counter": Counter(metrics.errors),
        "cpu_note": cpu_note,
    }


def _summarize_repeats(
    repeats: list[dict[str, Any]],
    requested_percentiles: list[float],
) -> dict[str, float | None]:
    throughputs = [float(repeat["results"]["throughput_hs_per_sec"]) for repeat in repeats]
    throughput_mean = statistics.mean(throughputs)
    throughput_stdev = statistics.stdev(throughputs) if len(throughputs) > 1 else None

    p99_values = [_coerce_optional_float(repeat["latency_ms"].get("p99")) for repeat in repeats]
    p99_mean = _mean_or_none(p99_values)

    p99_9_key = _percentile_key(99.9)
    p99_9_requested = any(_percentile_key(percentile) == p99_9_key for percentile in requested_percentiles)
    if p99_9_requested:
        p99_9_values = [_coerce_optional_float(repeat["latency_ms"].get(p99_9_key)) for repeat in repeats]
        p99_9_mean = _mean_or_none(p99_9_values)
    else:
        p99_9_mean = None

    max_values = [_coerce_optional_float(repeat["latency_ms"].get("max")) for repeat in repeats]
    max_candidates = [value for value in max_values if value is not None]
    max_latency_max = max(max_candidates) if max_candidates else None

    return {
        "throughput_mean": throughput_mean,
        "throughput_stdev": throughput_stdev,
        "p99_mean": p99_mean,
        "p99_9_mean": p99_9_mean,
        "max_latency_max": max_latency_max,
    }


def _coerce_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean_or_none(values: list[float | None]) -> float | None:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return statistics.mean(numeric_values)


def _build_environment() -> dict[str, Any]:
    return {
        "type": "bare_metal_container",
        "image": "pqc-lab:pqc",
        "python": platform.python_version(),
        "cpu_count": int(os.cpu_count() or 0),
        "platform": platform.platform(),
        "processor": platform.processor() or "",
        # Always emit explicit metadata values for downstream report schemas.
        "git_commit": _detect_git_commit(),
        "in_container": bool(_detect_in_container()),
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


def _detect_git_commit() -> str:
    commit_from_env = os.environ.get("GIT_COMMIT", "").strip()
    if commit_from_env:
        return commit_from_env

    # Best-effort fallback for local runs when GIT_COMMIT is not injected.
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _detect_in_container() -> bool:
    if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists():
        return True
    try:
        cgroup = Path("/proc/1/cgroup").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    lowered = cgroup.lower()
    markers = ("/docker", "/kubepods", "/containerd", "/podman", "/lxc")
    return any(marker in lowered for marker in markers)


def _start_cpu_sampler(
    system_cpu_samples: list[float],
    process_cpu_samples: list[float],
    stop_event: threading.Event,
    sample_interval_s: float,
) -> tuple[threading.Thread | None, str | None, bool]:
    try:
        import psutil  # type: ignore
    except Exception:
        return (
            None,
            "psutil not available; cpu.avg_percent and cpu.peak_percent set to null.",
            False,
        )

    def _sampler() -> None:
        try:
            process = psutil.Process()
            psutil.cpu_percent(interval=None)
            process.cpu_percent(interval=None)
            while not stop_event.wait(sample_interval_s):
                try:
                    system_cpu_samples.append(float(psutil.cpu_percent(interval=None)))
                except Exception:
                    pass
                try:
                    process_cpu_samples.append(float(process.cpu_percent(interval=None)))
                except Exception:
                    pass
        except Exception:
            return

    thread = threading.Thread(target=_sampler, name="capacity-cpu-sampler", daemon=True)
    thread.start()
    return thread, None, True


def _summarize_cpu(
    system_cpu_samples: list[float],
    process_cpu_samples: list[float],
    sample_interval_s: float,
    psutil_available: bool,
) -> dict[str, float | int | None]:
    loadavg_1m, loadavg_5m, loadavg_15m = _get_loadavg()
    cpu_count_logical = os.cpu_count()
    if not psutil_available:
        return {
            "avg_percent": None,
            "peak_percent": None,
            "sample_interval_s": sample_interval_s,
            "process_avg_percent": None,
            "process_peak_percent": None,
            "system_avg_percent": None,
            "system_peak_percent": None,
            "loadavg_1m": loadavg_1m,
            "loadavg_5m": loadavg_5m,
            "loadavg_15m": loadavg_15m,
            "cpu_count_logical": cpu_count_logical,
        }

    system_avg = statistics.mean(system_cpu_samples) if system_cpu_samples else None
    system_peak = max(system_cpu_samples) if system_cpu_samples else None
    process_avg = statistics.mean(process_cpu_samples) if process_cpu_samples else None
    process_peak = max(process_cpu_samples) if process_cpu_samples else None
    return {
        "avg_percent": system_avg,
        "peak_percent": system_peak,
        "sample_interval_s": sample_interval_s,
        "process_avg_percent": process_avg,
        "process_peak_percent": process_peak,
        "system_avg_percent": system_avg,
        "system_peak_percent": system_peak,
        "loadavg_1m": loadavg_1m,
        "loadavg_5m": loadavg_5m,
        "loadavg_15m": loadavg_15m,
        "cpu_count_logical": cpu_count_logical,
    }


def _get_loadavg() -> tuple[float | None, float | None, float | None]:
    try:
        loadavg = os.getloadavg()
    except (AttributeError, OSError):
        return None, None, None
    return float(loadavg[0]), float(loadavg[1]), float(loadavg[2])


def _summarize_latencies(
    latencies_ms: list[float],
    requested_percentiles: list[float],
) -> dict[str, float | int | None]:
    count = len(latencies_ms)
    summary: dict[str, float | int | None] = {
        "count": count,
        "p50": None,
        "p95": None,
        "p99": None,
        "max": None,
    }
    for percentile in requested_percentiles:
        key = _percentile_key(percentile)
        if key not in summary:
            summary[key] = None

    if count == 0:
        return summary

    ordered = sorted(latencies_ms)
    summary["p50"] = _percentile(ordered, 0.50)
    summary["p95"] = _percentile(ordered, 0.95)
    summary["p99"] = _percentile(ordered, 0.99)
    summary["max"] = ordered[-1]
    for percentile in requested_percentiles:
        key = _percentile_key(percentile)
        if key in {"p50", "p95", "p99"}:
            continue
        summary[key] = _percentile(ordered, percentile / 100.0)
    return summary


def _percentile_key(percentile: float) -> str:
    label = _percentile_label(percentile)
    return f"p{label.replace('.', '_')}"


def _percentile_label(percentile: float) -> str:
    label = f"{percentile:.12f}".rstrip("0").rstrip(".")
    if label == "-0":
        return "0"
    return label


def _percentile_json_value(percentile: float) -> int | float:
    label = _percentile_label(percentile)
    if "." not in label:
        return int(label)
    return float(label)


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
    repeats: int,
    requested_percentiles: list[float],
    cpu_sample_interval_s: float,
    exc: Exception,
) -> dict[str, Any]:
    mode = _detect_mode(profile_dict)
    error_type = exc.__class__.__name__
    error_hash = _hash_message(exc)
    latency_summary = _summarize_latencies([], requested_percentiles=requested_percentiles)
    cpu_summary = _summarize_cpu(
        system_cpu_samples=[],
        process_cpu_samples=[],
        sample_interval_s=cpu_sample_interval_s,
        psutil_available=False,
    )
    default_results = {
        "success_count": 0,
        "failure_count": 0,
        "throughput_hs_per_sec": 0.0,
    }
    repeat_reports = [
        {
            "results": copy.deepcopy(default_results),
            "latency_ms": copy.deepcopy(latency_summary),
            "cpu": copy.deepcopy(cpu_summary),
            "success_count": 0,
            "failure_count": 0,
        }
        for _ in range(repeats)
    ]
    return {
        "profile_path": str(profile_path),
        "profile_name": profile_obj.name,
        "provider": profile_obj.provider or "mock",
        "mode": mode,
        "concurrency": concurrency,
        "warmup_s": warmup_s,
        "duration_s": duration_s,
        "timestamp_utc": _utc_now_iso(),
        "environment": _build_environment(),
        "workload": {
            "handshake_model": "burst",
            "iterations_per_handshake": 1,
        },
        "results": copy.deepcopy(default_results),
        "latency_ms": copy.deepcopy(latency_summary),
        "latency_truncated": False,
        "cpu": copy.deepcopy(cpu_summary),
        "percentiles": [_percentile_json_value(p) for p in requested_percentiles],
        "repeats": repeat_reports,
        "summary": _summarize_repeats(repeat_reports, requested_percentiles),
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
