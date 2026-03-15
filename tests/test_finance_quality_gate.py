from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pqc_lab.finance.adapters import load_option_snapshots
from pqc_lab.finance.quality_gate import validate_snapshot, validate_snapshots


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "options_snapshot_sample.csv"


def test_csv_loader_supports_partial_finance_rows() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    contracts = {snapshot.contract_id: snapshot for snapshot in snapshots}

    assert len(snapshots) == 6
    assert contracts["MSFT:2026-04-24:call:430.00"].iv is None
    assert contracts["MSFT:2026-04-24:call:430.00"].spread_pct is not None
    assert contracts["AMD:2026-04-24:put:158.00"].earnings_days is None


def test_quality_gate_rejects_bad_rows_and_lowers_confidence_for_partial_rows() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    results = {result.snapshot.contract_id: result for result in validate_snapshots(snapshots)}

    assert results["AAPL:2026-04-17:call:210.00"].is_valid
    assert results["AAPL:2026-04-17:call:210.00"].confidence == 1.0

    assert results["MSFT:2026-04-24:call:430.00"].is_valid
    assert "missing_iv" in results["MSFT:2026-04-24:call:430.00"].quality_flags
    assert results["MSFT:2026-04-24:call:430.00"].confidence < 1.0
    assert results["MSFT:2026-04-24:call:430.00"].data_completeness < 1.0

    assert results["AMD:2026-04-24:put:158.00"].is_valid
    assert "missing_earnings_days" in results["AMD:2026-04-24:put:158.00"].quality_flags
    assert results["AMD:2026-04-24:put:158.00"].confidence < 1.0

    assert results["NVDA:2026-04-17:call:128.00"].is_rejected
    assert "bid_gt_ask" in results["NVDA:2026-04-17:call:128.00"].reject_reasons
    assert results["NVDA:2026-04-17:call:128.00"].confidence == 0.0

    assert results["TSLA:2026-03-14:call:260.00"].is_rejected
    assert "non_positive_dte" in results["TSLA:2026-03-14:call:260.00"].reject_reasons
    assert results["TSLA:2026-03-14:call:260.00"].confidence == 0.0


def test_quality_gate_tracks_data_completeness_and_confidence_explicitly() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    results = {result.snapshot.contract_id: result for result in validate_snapshots(snapshots)}

    msft_result = results["MSFT:2026-04-24:call:430.00"]
    amd_result = results["AMD:2026-04-24:put:158.00"]

    assert msft_result.data_completeness == 0.909
    assert msft_result.confidence == 0.789
    assert amd_result.data_completeness == 0.909
    assert amd_result.confidence == 0.789


def test_quality_gate_flags_invalid_optional_inputs_without_crashing() -> None:
    base_snapshot = load_option_snapshots(_fixture_path())[0]
    invalid_snapshot = replace(
        base_snapshot,
        iv=-0.1,
        delta=1.4,
        iv_rank=120.0,
        rv_20=-0.2,
        earnings_days=-3,
    )

    result = validate_snapshot(invalid_snapshot)

    assert result.is_valid
    assert "invalid_iv" in result.quality_flags
    assert "invalid_delta" in result.quality_flags
    assert "invalid_iv_rank" in result.quality_flags
    assert "invalid_rv_20" in result.quality_flags
    assert "invalid_earnings_days" in result.quality_flags
    assert result.confidence < 1.0
