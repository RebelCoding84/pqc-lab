"""CSV loader for offline option snapshot fixtures."""

from __future__ import annotations

import csv
import math
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from pqc_lab.finance.models import OptionSnapshot

REQUIRED_COLUMNS = (
    "snapshot_timestamp",
    "underlying",
    "expiry",
    "strike",
    "option_type",
    "underlying_price",
    "bid",
    "ask",
    "mid",
    "iv",
    "delta",
    "volume",
    "open_interest",
    "spread_pct",
    "dte",
    "atr_14",
    "rv_20",
    "iv_rank",
    "earnings_days",
)


def load_option_snapshots(path: str | Path) -> list[OptionSnapshot]:
    """Load option snapshots from a local CSV file."""

    source = Path(path)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(f"{source} is missing required columns: {', '.join(missing)}")
        return [_row_to_snapshot(source, row_number, row) for row_number, row in _enumerate_rows(reader)]


def _enumerate_rows(rows: Iterable[dict[str, str]]) -> Iterable[tuple[int, dict[str, str]]]:
    for row_number, row in enumerate(rows, start=2):
        yield row_number, row


def _row_to_snapshot(source: Path, row_number: int, row: dict[str, str]) -> OptionSnapshot:
    del source, row_number
    bid = _parse_float(_cell(row, "bid"))
    ask = _parse_float(_cell(row, "ask"))
    mid = _parse_mid(_cell(row, "mid"), bid=bid, ask=ask)
    spread_pct = _parse_spread_pct(_cell(row, "spread_pct"), bid=bid, ask=ask, mid=mid)
    return OptionSnapshot(
        snapshot_timestamp=_parse_datetime(_cell(row, "snapshot_timestamp")),
        underlying=_cell(row, "underlying").upper(),
        expiry=_parse_date(_cell(row, "expiry")),
        strike=_parse_float(_cell(row, "strike")),
        option_type=_parse_option_type(_cell(row, "option_type")),
        underlying_price=_parse_float(_cell(row, "underlying_price")),
        bid=bid,
        ask=ask,
        mid=mid,
        iv=_parse_float(_cell(row, "iv")),
        delta=_parse_float(_cell(row, "delta")),
        volume=_parse_int(_cell(row, "volume")),
        open_interest=_parse_int(_cell(row, "open_interest")),
        spread_pct=spread_pct,
        dte=_parse_int(_cell(row, "dte")),
        atr_14=_parse_float(_cell(row, "atr_14")),
        rv_20=_parse_float(_cell(row, "rv_20")),
        iv_rank=_parse_float(_cell(row, "iv_rank")),
        earnings_days=_parse_int(_cell(row, "earnings_days")),
    )


def _parse_option_type(value: str) -> str | None:
    option_type = value.strip().lower()
    if option_type not in {"call", "put"}:
        return None
    return option_type


def _parse_float(value: str) -> float | None:
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _parse_int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        try:
            parsed = float(value)
        except ValueError:
            return None
        if not math.isfinite(parsed) or not parsed.is_integer():
            return None
        return int(parsed)


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_mid(value: str, *, bid: float | None, ask: float | None) -> float | None:
    parsed_mid = _parse_float(value)
    if parsed_mid is not None:
        return parsed_mid
    if bid is None or ask is None:
        return None
    return round((bid + ask) / 2.0, 6)


def _parse_spread_pct(value: str, *, bid: float | None, ask: float | None, mid: float | None) -> float | None:
    parsed_spread = _parse_float(value)
    if parsed_spread is not None:
        return parsed_spread
    return _compute_spread_pct(bid=bid, ask=ask, mid=mid)


def _compute_spread_pct(*, bid: float | None, ask: float | None, mid: float | None) -> float | None:
    if bid is None or ask is None:
        return None
    computed_mid = mid
    if computed_mid is None:
        computed_mid = (bid + ask) / 2.0
    if computed_mid <= 0.0:
        return None
    return (ask - bid) / computed_mid


def _cell(row: dict[str, str], key: str) -> str:
    value = row.get(key, "")
    return value.strip() if value is not None else ""
