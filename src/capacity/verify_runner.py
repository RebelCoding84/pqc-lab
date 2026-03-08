from __future__ import annotations

"""Verify-only capacity benchmark runner (phase 1)."""

import argparse
import json
import math
import statistics
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from .signature_pool import SignaturePool, load_pool
from .verify_providers import (
    ProviderError,
    VerifyProvider,
    list_provider_statuses,
    get_provider,
)

PROFILE_SCHEMA_VERSION = 1
MAX_LATENCY_SAMPLES = 2_000_000


@dataclass(frozen=True)
class VerifyBenchmarkProfile:
    schema_version: int
    benchmark_name: str
    operation: str
    provider: str
    algorithm: str
    pool_path: Path
    concurrency: int
    warmup_s: float
    duration_s: float
    repeats: int
    output_dir: Path
    notes: dict[str, str | int | float | bool]


@dataclass
class RepeatMetrics:
    total_verify_ops: int = 0
    worker_errors: int = 0
    requests_in_flight: int = 0
    requests_in_flight_max: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    latency_truncated: bool = False
    error_types: Counter[str] = field(default_factory=Counter)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


@dataclass
class PoolCursor:
    size: int
    next_index: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def acquire_index(self) -> int:
        with self.lock:
            index = self.next_index
            self.next_index = (self.next_index + 1) % self.size
            return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Signature verify capacity benchmark runner.")
    parser.add_argument("--profile", help="Path to benchmark YAML profile.")
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List provider availability and exit.",
    )
    args = parser.parse_args(argv)

    if args.list_providers:
        statuses = [status.__dict__ for status in list_provider_statuses()]
        print(json.dumps({"providers": statuses}, indent=2, sort_keys=True))
        return 0

    if not args.profile:
        print("fatal: --profile is required unless --list-providers is set", file=sys.stderr)
        return 1

    profile_path = Path(args.profile)
    try:
        profile = load_verify_profile(profile_path)
        report = run_verify_benchmark(profile, profile_path=profile_path)
    except (OSError, yaml.YAMLError, ValueError, ProviderError) as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    output_path = _build_output_path(profile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, sort_keys=True)
    output_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    print(f"report_path={output_path}")
    return 0


def load_verify_profile(path: Path) -> VerifyBenchmarkProfile:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ValueError("profile YAML must be a mapping at top level")
    plain = _to_plain_object(loaded)
    if not isinstance(plain, dict):
        raise ValueError("profile YAML root must be a mapping")
    return _parse_verify_profile(plain)


def _parse_verify_profile(data: Mapping[str, Any]) -> VerifyBenchmarkProfile:
    allowed = {
        "schema_version",
        "benchmark_name",
        "operation",
        "provider",
        "algorithm",
        "pool_path",
        "concurrency",
        "warmup_s",
        "duration_s",
        "repeats",
        "output_dir",
        "notes",
    }
    required = {
        "schema_version",
        "benchmark_name",
        "operation",
        "provider",
        "algorithm",
        "pool_path",
        "concurrency",
        "warmup_s",
        "duration_s",
        "repeats",
        "output_dir",
    }
    _require_keys(data, allowed=allowed, required=required, context="verify profile")

    schema_version = data["schema_version"]
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != PROFILE_SCHEMA_VERSION
    ):
        raise ValueError(
            f"schema_version must be {PROFILE_SCHEMA_VERSION}; got {schema_version!r}"
        )

    benchmark_name = _parse_non_empty_str(data["benchmark_name"], field="benchmark_name")
    operation = _parse_non_empty_str(data["operation"], field="operation")
    if operation != "verify":
        raise ValueError("operation must be 'verify'")

    provider = _parse_non_empty_str(data["provider"], field="provider")
    if provider not in {"mock_verify", "real_mldsa"}:
        raise ValueError("provider must be one of ['mock_verify', 'real_mldsa']")

    algorithm = _parse_non_empty_str(data["algorithm"], field="algorithm")
    pool_path = Path(_parse_non_empty_str(data["pool_path"], field="pool_path"))
    output_dir = Path(_parse_non_empty_str(data["output_dir"], field="output_dir"))

    concurrency = _parse_positive_int(data["concurrency"], field="concurrency")
    warmup_s = _parse_non_negative_number(data["warmup_s"], field="warmup_s")
    duration_s = _parse_positive_number(data["duration_s"], field="duration_s")
    repeats = _parse_positive_int(data["repeats"], field="repeats")
    notes = _parse_notes(data.get("notes", {}))

    return VerifyBenchmarkProfile(
        schema_version=PROFILE_SCHEMA_VERSION,
        benchmark_name=benchmark_name,
        operation=operation,
        provider=provider,
        algorithm=algorithm,
        pool_path=pool_path,
        concurrency=concurrency,
        warmup_s=warmup_s,
        duration_s=duration_s,
        repeats=repeats,
        output_dir=output_dir,
        notes=notes,
    )


def run_verify_benchmark(
    profile: VerifyBenchmarkProfile,
    profile_path: Path | None = None,
) -> dict[str, Any]:
    provider = get_provider(profile.provider)
    resolved_algorithm = provider.resolve_algorithm(profile.algorithm)
    pool = load_pool(profile.pool_path)
    if not pool.entries:
        raise ValueError("signature pool has zero entries")
    _validate_pool_compatibility(profile, pool)

    repeat_metrics: list[dict[str, Any]] = []
    for repeat_index in range(profile.repeats):
        repeat_metrics.append(
            _run_repeat(
                provider=provider,
                provider_name=profile.provider,
                operation=profile.operation,
                algorithm_name=profile.algorithm,
                repeats=profile.repeats,
                algorithm=resolved_algorithm,
                pool=pool,
                duration_s=profile.duration_s,
                warmup_s=profile.warmup_s,
                concurrency=profile.concurrency,
                repeat_index=repeat_index + 1,
            )
        )

    report = {
        "schema_version": profile.schema_version,
        "benchmark_name": profile.benchmark_name,
        "profile_path": str(profile_path) if profile_path is not None else "",
        "operation": profile.operation,
        "provider": profile.provider,
        "algorithm": profile.algorithm,
        "resolved_algorithm": resolved_algorithm,
        "pool_path": str(profile.pool_path),
        "pool_size": len(pool.entries),
        "concurrency": profile.concurrency,
        "warmup_s": profile.warmup_s,
        "duration_s": profile.duration_s,
        "repeats": profile.repeats,
        "repeat_metrics": repeat_metrics,
        "summary": _summarize_repeats(repeat_metrics),
        "notes": dict(profile.notes),
    }
    if provider.test_only:
        report["notes"]["provider_mode"] = (
            "mock provider is test-only harness validation, not a cryptographic claim"
        )
    return report


def _validate_pool_compatibility(
    profile: VerifyBenchmarkProfile,
    pool: SignaturePool,
) -> None:
    metadata = pool.metadata
    if metadata.provider != profile.provider:
        raise ValueError(
            "pool metadata provider mismatch: "
            f"profile={profile.provider!r}, pool={metadata.provider!r}"
        )

    profile_algorithm_norm = _normalize_token(profile.algorithm)
    pool_algorithm_norm = _normalize_token(metadata.algorithm)
    if profile_algorithm_norm != pool_algorithm_norm:
        raise ValueError(
            "pool metadata algorithm mismatch: "
            f"profile={profile.algorithm!r}, pool={metadata.algorithm!r}"
        )

    if profile.provider == "real_mldsa" and not pool_algorithm_norm.startswith("mldsa"):
        raise ValueError(
            "real_mldsa profile requires an ML-DSA pool; "
            f"found pool metadata algorithm {metadata.algorithm!r}"
        )


def _run_repeat(
    provider: VerifyProvider,
    provider_name: str,
    operation: str,
    algorithm_name: str,
    repeats: int,
    algorithm: str,
    pool: SignaturePool,
    duration_s: float,
    warmup_s: float,
    concurrency: int,
    repeat_index: int,
) -> dict[str, Any]:
    if warmup_s > 0:
        _run_phase(
            provider=provider,
            algorithm=algorithm,
            entries=pool.entries,
            duration_s=warmup_s,
            concurrency=concurrency,
            metrics=None,
        )

    metrics = RepeatMetrics()
    start = time.perf_counter()
    _run_phase(
        provider=provider,
        algorithm=algorithm,
        entries=pool.entries,
        duration_s=duration_s,
        concurrency=concurrency,
        metrics=metrics,
    )
    wall_time_s = time.perf_counter() - start
    return _build_repeat_report(
        repeat_index=repeat_index,
        pool_size=len(pool.entries),
        concurrency=concurrency,
        repeats=repeats,
        provider_name=provider_name,
        operation=operation,
        algorithm_name=algorithm_name,
        wall_time_s=wall_time_s,
        metrics=metrics,
    )


def _run_phase(
    provider: VerifyProvider,
    algorithm: str,
    entries: tuple[Any, ...],
    duration_s: float,
    concurrency: int,
    metrics: RepeatMetrics | None,
) -> None:
    deadline = time.perf_counter() + duration_s
    cursor = PoolCursor(size=len(entries))
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                _worker_loop,
                provider=provider,
                algorithm=algorithm,
                entries=entries,
                deadline=deadline,
                cursor=cursor,
                metrics=metrics,
            )
            for _ in range(concurrency)
        ]
        for future in futures:
            future.result()


def _worker_loop(
    provider: VerifyProvider,
    algorithm: str,
    entries: tuple[Any, ...],
    deadline: float,
    cursor: PoolCursor,
    metrics: RepeatMetrics | None,
) -> None:
    session = provider.create_verify_session(algorithm)
    try:
        while time.perf_counter() < deadline:
            index = cursor.acquire_index()
            entry = entries[index]
            if metrics is None:
                try:
                    session.verify(entry.public_key, entry.message, entry.signature)
                except Exception:
                    pass
                continue

            start = time.perf_counter()
            with metrics.lock:
                metrics.requests_in_flight += 1
                if metrics.requests_in_flight > metrics.requests_in_flight_max:
                    metrics.requests_in_flight_max = metrics.requests_in_flight

            had_error = False
            error_type = ""
            try:
                verified = session.verify(entry.public_key, entry.message, entry.signature)
                if not verified:
                    had_error = True
                    error_type = "VerifyFailed"
            except Exception as exc:
                verified = False
                had_error = True
                error_type = exc.__class__.__name__

            latency_ms = (time.perf_counter() - start) * 1000.0
            with metrics.lock:
                metrics.total_verify_ops += 1
                if len(metrics.latencies_ms) < MAX_LATENCY_SAMPLES:
                    metrics.latencies_ms.append(latency_ms)
                else:
                    metrics.latency_truncated = True
                if had_error:
                    metrics.worker_errors += 1
                    metrics.error_types[error_type] += 1
                metrics.requests_in_flight -= 1
    finally:
        session.close()


def _build_repeat_report(
    repeat_index: int,
    pool_size: int,
    concurrency: int,
    repeats: int,
    provider_name: str,
    operation: str,
    algorithm_name: str,
    wall_time_s: float,
    metrics: RepeatMetrics,
) -> dict[str, Any]:
    if wall_time_s <= 0.0:
        verify_per_sec = 0.0
    else:
        verify_per_sec = metrics.total_verify_ops / wall_time_s

    latency_summary = _summarize_latencies(metrics.latencies_ms)
    return {
        "repeat_index": repeat_index,
        "repeats": repeats,
        "operation": operation,
        "provider": provider_name,
        "algorithm": algorithm_name,
        "pool_size": pool_size,
        "concurrency": concurrency,
        "requests_in_flight_max": metrics.requests_in_flight_max,
        "total_verify_ops": metrics.total_verify_ops,
        "verify_per_sec": verify_per_sec,
        "p50_ms": latency_summary["p50_ms"],
        "p95_ms": latency_summary["p95_ms"],
        "p99_ms": latency_summary["p99_ms"],
        "max_ms": latency_summary["max_ms"],
        "worker_errors": metrics.worker_errors,
        "wall_time_s": wall_time_s,
        "latency_samples": len(metrics.latencies_ms),
        "latency_truncated": metrics.latency_truncated,
        "error_types": dict(sorted(metrics.error_types.items())),
    }


def _summarize_repeats(repeats: list[dict[str, Any]]) -> dict[str, Any]:
    if not repeats:
        return {
            "total_verify_ops_sum": 0,
            "verify_per_sec_mean": 0.0,
            "verify_per_sec_stdev": None,
            "p50_ms_mean": None,
            "p95_ms_mean": None,
            "p99_ms_mean": None,
            "max_ms_max": None,
            "worker_errors_sum": 0,
            "requests_in_flight_max_max": 0,
            "wall_time_s_sum": 0.0,
        }

    verify_per_sec_values = [float(item["verify_per_sec"]) for item in repeats]
    p50_values = [_coerce_optional_float(item.get("p50_ms")) for item in repeats]
    p95_values = [_coerce_optional_float(item.get("p95_ms")) for item in repeats]
    p99_values = [_coerce_optional_float(item.get("p99_ms")) for item in repeats]
    max_values = [_coerce_optional_float(item.get("max_ms")) for item in repeats]
    max_candidates = [value for value in max_values if value is not None]

    return {
        "total_verify_ops_sum": int(sum(int(item["total_verify_ops"]) for item in repeats)),
        "verify_per_sec_mean": statistics.mean(verify_per_sec_values),
        "verify_per_sec_stdev": (
            statistics.stdev(verify_per_sec_values)
            if len(verify_per_sec_values) > 1
            else None
        ),
        "p50_ms_mean": _mean_or_none(p50_values),
        "p95_ms_mean": _mean_or_none(p95_values),
        "p99_ms_mean": _mean_or_none(p99_values),
        "max_ms_max": max(max_candidates) if max_candidates else None,
        "worker_errors_sum": int(sum(int(item["worker_errors"]) for item in repeats)),
        "requests_in_flight_max_max": int(
            max(int(item["requests_in_flight_max"]) for item in repeats)
        ),
        "wall_time_s_sum": float(sum(float(item["wall_time_s"]) for item in repeats)),
    }


def _summarize_latencies(latencies_ms: list[float]) -> dict[str, float | None]:
    if not latencies_ms:
        return {
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "max_ms": None,
        }
    ordered = sorted(latencies_ms)
    return {
        "p50_ms": _percentile(ordered, 0.50),
        "p95_ms": _percentile(ordered, 0.95),
        "p99_ms": _percentile(ordered, 0.99),
        "max_ms": ordered[-1],
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


def _build_output_path(profile: VerifyBenchmarkProfile) -> Path:
    filename = (
        f"{_slug(profile.benchmark_name)}"
        f"_{_slug(profile.provider)}"
        f"_{_slug(profile.algorithm)}"
        f"_c{profile.concurrency}.json"
    )
    return profile.output_dir / filename


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    chars = []
    for char in lowered:
        if char.isalnum():
            chars.append(char)
        elif char in {"-", "_"}:
            chars.append(char)
        else:
            chars.append("_")
    while "__" in "".join(chars):
        chars = list("".join(chars).replace("__", "_"))
    return "".join(chars).strip("_") or "benchmark"


def _to_plain_object(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _to_plain_object(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain_object(item) for item in value]
    return value


def _normalize_token(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _parse_non_empty_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _parse_positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if value <= 0:
        raise ValueError(f"{field} must be > 0")
    return value


def _parse_non_negative_number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be finite")
    if parsed < 0.0:
        raise ValueError(f"{field} must be >= 0")
    return parsed


def _parse_positive_number(value: Any, field: str) -> float:
    parsed = _parse_non_negative_number(value, field=field)
    if parsed <= 0.0:
        raise ValueError(f"{field} must be > 0")
    return parsed


def _parse_notes(value: Any) -> dict[str, str | int | float | bool]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("notes must be a mapping if provided")
    result: dict[str, str | int | float | bool] = {}
    for key, note_value in value.items():
        if not isinstance(key, str):
            raise ValueError("notes keys must be strings")
        if not isinstance(note_value, (str, int, float, bool)):
            raise ValueError("notes values must be scalar (str/int/float/bool)")
        result[key] = note_value
    return result


def _require_keys(
    data: Mapping[str, Any],
    allowed: set[str],
    required: set[str],
    context: str,
) -> None:
    extra = set(data.keys()) - allowed
    if extra:
        raise ValueError(f"unknown fields in {context}: {sorted(extra)}")
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"missing required fields in {context}: {sorted(missing)}")


def _coerce_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean_or_none(values: list[float | None]) -> float | None:
    numeric = [value for value in values if value is not None]
    if not numeric:
        return None
    return statistics.mean(numeric)


if __name__ == "__main__":
    raise SystemExit(main())
