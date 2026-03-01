#!/usr/bin/env python3
"""Summarize capacity harness JSON outputs into a Markdown table.

Usage:
    python scripts/summarize_enterprise.py "reports/enterprise_proof/*.json"
"""

import glob
import json
from pathlib import Path
import statistics


COLUMNS = [
    "file",
    "concurrency",
    "throughput_mean",
    "throughput_stdev",
    "p99_mean",
    "p99_9_mean",
    "max_latency_max",
    "cpu_process_peak",
    "cpu_system_peak",
    "loadavg_1m",
]


def main() -> int:
    argv = __import__("sys").argv[1:]
    if not argv:
        print('Usage: python scripts/summarize_enterprise.py "reports/enterprise_proof/*.json"')
        return 1

    files = _expand_inputs(argv)
    if not files:
        print("No JSON files matched the provided input.")
        return 1

    print(_table_header())
    for file_path in files:
        payload = _read_json(Path(file_path))
        row = _row_from_payload(file_path, payload)
        print(_format_row(row))
    return 0


def _expand_inputs(patterns: list[str]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        for candidate in glob.glob(pattern):
            path = Path(candidate)
            if path.is_file():
                matches.append(str(path))
    return sorted(set(matches))


def _read_json(path: Path) -> dict:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(loaded, dict):
        return loaded
    return {}


def _row_from_payload(file_path: str, payload: dict) -> dict[str, object]:
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        summary = _minimal_summary(payload)

    cpu = payload.get("cpu")
    if not isinstance(cpu, dict):
        cpu = {}

    row = {
        "file": file_path,
        "concurrency": _to_int(payload.get("concurrency")),
        "throughput_mean": _to_float(summary.get("throughput_mean")),
        "throughput_stdev": _to_float(summary.get("throughput_stdev")),
        "p99_mean": _to_float(summary.get("p99_mean")),
        "p99_9_mean": _to_float(summary.get("p99_9_mean")),
        "max_latency_max": _to_float(summary.get("max_latency_max")),
        "cpu_process_peak": _to_float(cpu.get("process_peak_percent")),
        "cpu_system_peak": _to_float(cpu.get("system_peak_percent")),
        "loadavg_1m": _to_float(cpu.get("loadavg_1m")),
    }
    if row["cpu_system_peak"] is None:
        row["cpu_system_peak"] = _to_float(cpu.get("peak_percent"))
    return row


def _minimal_summary(payload: dict) -> dict[str, float | None]:
    results = payload.get("results")
    if not isinstance(results, dict):
        results = {}
    latency = payload.get("latency_ms")
    if not isinstance(latency, dict):
        latency = {}

    throughput = _to_float(results.get("throughput_hs_per_sec"))
    p99 = _to_float(latency.get("p99"))
    p99_9 = _to_float(latency.get("p99_9"))
    max_latency = _to_float(latency.get("max"))

    return {
        "throughput_mean": _single_mean(throughput),
        "throughput_stdev": None,
        "p99_mean": _single_mean(p99),
        "p99_9_mean": _single_mean(p99_9),
        "max_latency_max": max_latency,
    }


def _single_mean(value: float | None) -> float | None:
    if value is None:
        return None
    return statistics.mean([value])


def _to_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _table_header() -> str:
    header = "| " + " | ".join(COLUMNS) + " |"
    rule = "| " + " | ".join("---" for _ in COLUMNS) + " |"
    return header + "\n" + rule


def _format_row(row: dict[str, object]) -> str:
    cells = [_format_cell(row.get(column)) for column in COLUMNS]
    return "| " + " | ".join(cells) + " |"


def _format_cell(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return value.replace("|", "\\|")
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
