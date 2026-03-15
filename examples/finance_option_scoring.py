"""Offline example for the finance v1 research pipeline."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from pqc_lab.finance.adapters import load_option_snapshots
from pqc_lab.finance.quality_gate import accepted_snapshots, validate_snapshots
from pqc_lab.finance.reports import export_scored_options_csv, export_scored_options_json
from pqc_lab.finance.research import load_weights, score_snapshots


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_path = root / "fixtures" / "options_snapshot_sample.csv"
    weights_path = root / "src" / "pqc_lab" / "finance" / "config" / "weights_v1.yaml"
    report_dir = root / "reports" / "finance"

    snapshots = load_option_snapshots(fixture_path)
    validation_results = validate_snapshots(snapshots)
    valid_snapshots = accepted_snapshots(validation_results)
    rejected_results = [result for result in validation_results if result.is_rejected]
    low_confidence_results = [result for result in validation_results if result.is_valid and result.confidence < 1.0]
    scored = score_snapshots(snapshots, validation_results=validation_results, weights=load_weights(weights_path))
    class_counts = Counter(option.score_class for option in scored)
    candidate_rows = sum(1 for option in scored if option.strategy_candidates)

    json_path = export_scored_options_json(scored, report_dir / "option_scores_v1.json")
    csv_path = export_scored_options_csv(scored, report_dir / "option_scores_v1.csv")

    print("Finance option scoring v1")
    print(
        f"loaded={len(snapshots)} valid={len(valid_snapshots)} rejected={len(rejected_results)} "
        f"low_confidence={len(low_confidence_results)} scored={len(scored)}"
    )
    print(
        "classes="
        f"A:{class_counts.get('A', 0)} "
        f"B:{class_counts.get('B', 0)} "
        f"C:{class_counts.get('C', 0)} "
        f"Reject:{class_counts.get('Reject', 0)} "
        f"candidate_rows={candidate_rows}"
    )
    print(f"exports={json_path.name},{csv_path.name}")


if __name__ == "__main__":
    main()
