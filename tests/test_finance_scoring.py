from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pqc_lab.finance.adapters import load_option_snapshots
from pqc_lab.finance.quality_gate import validate_snapshot, validate_snapshots
from pqc_lab.finance.research import load_weights, score_snapshot, score_snapshots


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "options_snapshot_sample.csv"


def test_score_snapshot_returns_range_class_drivers_and_debit_call_candidate() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    validation_results = {result.snapshot.contract_id: result for result in validate_snapshots(snapshots)}
    weights = load_weights()
    aapl_call = next(snapshot for snapshot in snapshots if snapshot.contract_id == "AAPL:2026-04-17:call:210.00")

    scored = score_snapshot(aapl_call, validation_result=validation_results[aapl_call.contract_id], weights=weights)

    assert 0.0 <= scored.total_score <= 100.0
    assert scored.score_class in {"A", "B", "C", "Reject"}
    assert scored.top_score_drivers
    assert "debit_call_spread_candidate" in {candidate.name for candidate in scored.strategy_candidates}


def test_score_snapshots_scores_all_rows_and_returns_expected_output_shape() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    scored = score_snapshots(snapshots, validation_results=validate_snapshots(snapshots), weights=load_weights())

    assert len(scored) == len(snapshots)
    payload = scored[0].to_dict()
    assert {
        "contract_id",
        "total_score",
        "score_class",
        "score_breakdown",
        "top_score_drivers",
        "strategy_candidates",
        "confidence",
        "quality_flags",
        "reject_reasons",
    } <= set(payload)


def test_score_snapshot_returns_reject_for_hard_rejected_quality_gate_rows() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    validation_results = {result.snapshot.contract_id: result for result in validate_snapshots(snapshots)}
    nvda_call = next(snapshot for snapshot in snapshots if snapshot.contract_id == "NVDA:2026-04-17:call:128.00")

    scored = score_snapshot(nvda_call, validation_result=validation_results[nvda_call.contract_id], weights=load_weights())

    assert scored.total_score == 0.0
    assert scored.score_class == "Reject"
    assert scored.strategy_candidates == ()
    assert scored.reject_reasons == ("bid_gt_ask",)


def test_score_class_assignment_uses_a_b_c_and_reject_bands() -> None:
    base_snapshot = load_option_snapshots(_fixture_path())[0]
    dte_only_weights = {"dte_suitability": 1.0}

    class_a = score_snapshot(
        replace(base_snapshot, dte=30),
        validation_result=validate_snapshot(replace(base_snapshot, dte=30)),
        weights=dte_only_weights,
    )
    class_b = score_snapshot(
        replace(base_snapshot, dte=21),
        validation_result=validate_snapshot(replace(base_snapshot, dte=21)),
        weights=dte_only_weights,
    )
    class_c = score_snapshot(
        replace(base_snapshot, dte=15),
        validation_result=validate_snapshot(replace(base_snapshot, dte=15)),
        weights=dte_only_weights,
    )
    rejected = score_snapshot(
        replace(base_snapshot, dte=0),
        validation_result=validate_snapshot(replace(base_snapshot, dte=0)),
        weights=dte_only_weights,
    )

    assert class_a.score_class == "A"
    assert class_b.score_class == "B"
    assert class_c.score_class == "C"
    assert rejected.score_class == "Reject"


def test_score_snapshot_returns_cash_secured_put_candidate_for_higher_iv_put() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    validation_results = {result.snapshot.contract_id: result for result in validate_snapshots(snapshots)}
    aapl_put = next(snapshot for snapshot in snapshots if snapshot.contract_id == "AAPL:2026-04-17:put:195.00")

    scored = score_snapshot(aapl_put, validation_result=validation_results[aapl_put.contract_id], weights=load_weights())

    assert scored.score_class in {"A", "B"}
    assert "cash_secured_put_candidate" in {candidate.name for candidate in scored.strategy_candidates}


def test_score_snapshot_marks_covered_call_candidate_as_requiring_existing_shares() -> None:
    base_snapshot = load_option_snapshots(_fixture_path())[0]
    call_snapshot = replace(base_snapshot, iv=0.38, iv_rank=72.0, rv_20=0.26, delta=0.28, dte=28)

    scored = score_snapshot(call_snapshot, validation_result=validate_snapshot(call_snapshot), weights=load_weights())

    covered_call = next(candidate for candidate in scored.strategy_candidates if candidate.name == "covered_call_candidate")
    assert covered_call.requires_existing_shares is True


def test_low_confidence_rows_do_not_emit_strategy_candidates() -> None:
    snapshots = load_option_snapshots(_fixture_path())
    scored = score_snapshots(snapshots, validation_results=validate_snapshots(snapshots), weights=load_weights())
    msft_call = next(option for option in scored if option.snapshot.contract_id == "MSFT:2026-04-24:call:430.00")

    assert msft_call.confidence < 1.0
    assert msft_call.strategy_candidates == ()
