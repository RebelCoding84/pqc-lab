"""Minimal data-quality validation for finance research inputs."""

from __future__ import annotations

from typing import Iterable

from pqc_lab.finance.models import OptionSnapshot, ValidationResult

TRACKED_FIELDS = (
    "bid",
    "ask",
    "volume",
    "open_interest",
    "dte",
    "spread_pct",
    "iv",
    "delta",
    "iv_rank",
    "rv_20",
    "earnings_days",
)

CRITICAL_CONFIDENCE_FIELDS = ("iv", "delta", "iv_rank", "rv_20", "earnings_days")


def validate_snapshot(snapshot: OptionSnapshot) -> ValidationResult:
    """Validate a single option snapshot against v1 quality gates."""

    quality_flags: list[str] = []
    reject_reasons: list[str] = []

    if snapshot.snapshot_timestamp is None:
        reject_reasons.append("missing_snapshot_timestamp")
    if not snapshot.underlying:
        reject_reasons.append("missing_underlying")
    if snapshot.expiry is None:
        reject_reasons.append("missing_expiry")
    if snapshot.strike is None or snapshot.strike <= 0.0:
        reject_reasons.append("invalid_strike")
    if snapshot.option_type is None:
        reject_reasons.append("invalid_option_type")
    if snapshot.underlying_price is None or snapshot.underlying_price <= 0.0:
        reject_reasons.append("invalid_underlying_price")

    if snapshot.bid is None:
        reject_reasons.append("missing_bid")
    elif snapshot.bid < 0.0:
        reject_reasons.append("negative_bid")

    if snapshot.ask is None:
        reject_reasons.append("missing_ask")
    elif snapshot.ask < 0.0:
        reject_reasons.append("negative_ask")

    if snapshot.bid is not None and snapshot.ask is not None and snapshot.bid > snapshot.ask:
        reject_reasons.append("bid_gt_ask")

    if snapshot.volume is None:
        reject_reasons.append("missing_volume")
    elif snapshot.volume < 0:
        reject_reasons.append("negative_volume")

    if snapshot.open_interest is None:
        reject_reasons.append("missing_open_interest")
    elif snapshot.open_interest < 0:
        reject_reasons.append("negative_open_interest")

    if snapshot.dte is None:
        reject_reasons.append("missing_dte")
    elif snapshot.dte <= 0:
        reject_reasons.append("non_positive_dte")

    spread_present = snapshot.spread_pct is not None
    spread_computable = _spread_pct_computable(snapshot)
    if not spread_present and not spread_computable:
        reject_reasons.append("spread_pct_unavailable")
    elif snapshot.spread_pct is not None and snapshot.spread_pct < 0.0:
        reject_reasons.append("negative_spread_pct")

    _flag_optional_value(
        value=snapshot.iv,
        field_name="iv",
        validator=lambda item: item >= 0.0,
        quality_flags=quality_flags,
    )
    _flag_optional_value(
        value=snapshot.delta,
        field_name="delta",
        validator=lambda item: -1.0 <= item <= 1.0,
        quality_flags=quality_flags,
    )
    _flag_optional_value(
        value=snapshot.iv_rank,
        field_name="iv_rank",
        validator=lambda item: 0.0 <= item <= 100.0,
        quality_flags=quality_flags,
    )
    _flag_optional_value(
        value=snapshot.rv_20,
        field_name="rv_20",
        validator=lambda item: item >= 0.0,
        quality_flags=quality_flags,
    )
    _flag_optional_value(
        value=snapshot.earnings_days,
        field_name="earnings_days",
        validator=lambda item: item >= 0,
        quality_flags=quality_flags,
    )

    completeness_checks = {
        "bid": snapshot.bid is not None and snapshot.bid >= 0.0,
        "ask": snapshot.ask is not None and snapshot.ask >= 0.0,
        "volume": snapshot.volume is not None and snapshot.volume >= 0,
        "open_interest": snapshot.open_interest is not None and snapshot.open_interest >= 0,
        "dte": snapshot.dte is not None and snapshot.dte > 0,
        "spread_pct": (snapshot.spread_pct is not None and snapshot.spread_pct >= 0.0) or spread_computable,
        "iv": snapshot.iv is not None and snapshot.iv >= 0.0,
        "delta": snapshot.delta is not None and -1.0 <= snapshot.delta <= 1.0,
        "iv_rank": snapshot.iv_rank is not None and 0.0 <= snapshot.iv_rank <= 100.0,
        "rv_20": snapshot.rv_20 is not None and snapshot.rv_20 >= 0.0,
        "earnings_days": snapshot.earnings_days is not None and snapshot.earnings_days >= 0,
    }
    data_completeness = round(
        sum(1 for field_name in TRACKED_FIELDS if completeness_checks[field_name]) / len(TRACKED_FIELDS),
        3,
    )

    critical_gaps = sum(1 for field_name in CRITICAL_CONFIDENCE_FIELDS if not completeness_checks[field_name])
    confidence = 0.0 if reject_reasons else max(0.0, round(data_completeness - (0.12 * critical_gaps), 3))

    return ValidationResult(
        snapshot=snapshot,
        quality_flags=tuple(dict.fromkeys(quality_flags)),
        reject_reasons=tuple(dict.fromkeys(reject_reasons)),
        data_completeness=data_completeness,
        confidence=confidence,
    )


def validate_snapshots(snapshots: Iterable[OptionSnapshot]) -> list[ValidationResult]:
    """Validate a sequence of option snapshots."""

    return [validate_snapshot(snapshot) for snapshot in snapshots]


def accepted_snapshots(results: Iterable[ValidationResult]) -> list[OptionSnapshot]:
    """Return only snapshots that passed the quality gate."""

    return [result.snapshot for result in results if result.is_valid]


def _flag_optional_value(
    *,
    value: float | int | None,
    field_name: str,
    validator,
    quality_flags: list[str],
) -> None:
    if value is None:
        quality_flags.append(f"missing_{field_name}")
        return
    if not validator(value):
        quality_flags.append(f"invalid_{field_name}")


def _spread_pct_computable(snapshot: OptionSnapshot) -> bool:
    bid = snapshot.bid
    ask = snapshot.ask
    if bid is None or ask is None:
        return False
    mid = snapshot.mid if snapshot.mid is not None else (bid + ask) / 2.0
    return mid > 0.0
