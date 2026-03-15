"""File exporters for finance research outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from pqc_lab.finance.models import ScoredOption


def export_scored_options_json(scored_options: Iterable[ScoredOption], path: str | Path) -> Path:
    """Export scored options as JSON."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = [option.to_dict() for option in scored_options]
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return destination


def export_scored_options_csv(scored_options: Iterable[ScoredOption], path: str | Path) -> Path:
    """Export scored options as CSV."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for option in scored_options:
        row = option.to_dict()
        row["score_breakdown"] = json.dumps(row["score_breakdown"], sort_keys=True)
        row["quality_flags"] = json.dumps(row["quality_flags"])
        row["reject_reasons"] = json.dumps(row["reject_reasons"])
        row["top_score_drivers"] = json.dumps(row["top_score_drivers"])
        row["strategy_candidates"] = json.dumps(row["strategy_candidates"], sort_keys=True)
        rows.append(row)

    fieldnames = list(rows[0].keys()) if rows else []
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
    return destination


def export_candidates_json(scored_options: Iterable[ScoredOption], path: str | Path) -> Path:
    """Backward-compatible wrapper for the original export function name."""

    return export_scored_options_json(scored_options, path)


def export_candidates_csv(scored_options: Iterable[ScoredOption], path: str | Path) -> Path:
    """Backward-compatible wrapper for the original export function name."""

    return export_scored_options_csv(scored_options, path)
