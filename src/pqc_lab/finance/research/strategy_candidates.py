"""Strategy candidate generation for finance v1."""

from __future__ import annotations

from pqc_lab.finance.models import ScoredOption, StrategyCandidate


def build_strategy_candidates(scored_option: ScoredOption) -> tuple[StrategyCandidate, ...]:
    """Return simple, non-binding strategy candidates for one scored option."""

    snapshot = scored_option.snapshot
    if _quality_is_poor(scored_option):
        return ()
    if not _acceptable_dte(snapshot.dte):
        return ()

    candidates: list[StrategyCandidate] = []

    if _bullish_call_signal(snapshot) and _is_lower_iv(snapshot):
        candidates.append(
            StrategyCandidate(
                name="debit_call_spread_candidate",
                rationale=(
                    f"{snapshot.underlying} shows a bullish call profile with lower IV and acceptable DTE. "
                    "Candidate only for further analysis, not an execution recommendation."
                ),
            )
        )

    if _bullish_put_signal(snapshot) and _is_higher_iv(snapshot):
        candidates.append(
            StrategyCandidate(
                name="cash_secured_put_candidate",
                rationale=(
                    f"{snapshot.underlying} shows a bullish put profile with higher IV and acceptable DTE. "
                    "Candidate only for further analysis, not an execution recommendation."
                ),
            )
        )

    if _bullish_call_signal(snapshot) and _is_higher_iv(snapshot):
        candidates.append(
            StrategyCandidate(
                name="covered_call_candidate",
                rationale=(
                    f"{snapshot.underlying} call premium is elevated with acceptable DTE. "
                    "Candidate only for further analysis and requires existing share ownership."
                ),
                requires_existing_shares=True,
            )
        )

    return tuple(candidates)


def _quality_is_poor(scored_option: ScoredOption) -> bool:
    if scored_option.score_class not in {"A", "B"}:
        return True
    if scored_option.confidence < 0.75:
        return True
    if scored_option.score_breakdown.get("spread_quality", 0.0) < 50.0:
        return True
    if scored_option.score_breakdown.get("liquidity", 0.0) < 45.0:
        return True
    return False


def _bullish_call_signal(scored_option_snapshot) -> bool:
    return (
        scored_option_snapshot.option_type == "call"
        and scored_option_snapshot.delta is not None
        and 0.20 <= scored_option_snapshot.delta <= 0.55
    )


def _bullish_put_signal(scored_option_snapshot) -> bool:
    return (
        scored_option_snapshot.option_type == "put"
        and scored_option_snapshot.delta is not None
        and -0.40 <= scored_option_snapshot.delta <= -0.15
    )


def _acceptable_dte(dte: int | None) -> bool:
    return dte is not None and 14 <= dte <= 45


def _is_lower_iv(scored_option_snapshot) -> bool:
    iv = scored_option_snapshot.iv
    if iv is None:
        return False
    iv_rank = scored_option_snapshot.iv_rank if scored_option_snapshot.iv_rank is not None else 50.0
    return iv <= 0.30 or iv_rank <= 45.0


def _is_higher_iv(scored_option_snapshot) -> bool:
    iv = scored_option_snapshot.iv
    if iv is None:
        return False
    iv_rank = scored_option_snapshot.iv_rank if scored_option_snapshot.iv_rank is not None else 50.0
    rv_20 = scored_option_snapshot.rv_20 if scored_option_snapshot.rv_20 is not None else iv
    return iv >= 0.30 and (iv_rank >= 55.0 or (iv - rv_20) >= 0.06)
