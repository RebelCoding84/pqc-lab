"""Simple research filters for finance v1."""

from __future__ import annotations

from typing import Iterable

from pqc_lab.finance.models import OptionSnapshot


def filter_by_dte(snapshots: Iterable[OptionSnapshot], *, min_dte: int = 7, max_dte: int = 45) -> list[OptionSnapshot]:
    return [snapshot for snapshot in snapshots if snapshot.dte is not None and min_dte <= snapshot.dte <= max_dte]


def filter_by_earnings_buffer(
    snapshots: Iterable[OptionSnapshot], *, min_earnings_days: int = 7
) -> list[OptionSnapshot]:
    return [
        snapshot
        for snapshot in snapshots
        if snapshot.earnings_days is not None and snapshot.earnings_days >= min_earnings_days
    ]


def filter_by_iv_rank(snapshots: Iterable[OptionSnapshot], *, min_iv_rank: float = 25.0) -> list[OptionSnapshot]:
    return [snapshot for snapshot in snapshots if snapshot.iv_rank is not None and snapshot.iv_rank >= min_iv_rank]


def filter_by_delta(
    snapshots: Iterable[OptionSnapshot],
    *,
    min_abs_delta: float = 0.15,
    max_abs_delta: float = 0.45,
) -> list[OptionSnapshot]:
    return [
        snapshot
        for snapshot in snapshots
        if snapshot.delta is not None and min_abs_delta <= abs(snapshot.delta) <= max_abs_delta
    ]


def apply_v1_filters(
    snapshots: Iterable[OptionSnapshot],
    *,
    min_dte: int = 7,
    max_dte: int = 45,
    min_earnings_days: int = 7,
    min_iv_rank: float = 25.0,
    min_abs_delta: float = 0.15,
    max_abs_delta: float = 0.45,
) -> list[OptionSnapshot]:
    """Apply the minimal finance v1 research filters."""

    filtered = filter_by_dte(snapshots, min_dte=min_dte, max_dte=max_dte)
    filtered = filter_by_earnings_buffer(filtered, min_earnings_days=min_earnings_days)
    filtered = filter_by_iv_rank(filtered, min_iv_rank=min_iv_rank)
    return filter_by_delta(filtered, min_abs_delta=min_abs_delta, max_abs_delta=max_abs_delta)
