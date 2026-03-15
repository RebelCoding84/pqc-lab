"""Minimal finance research datamodels."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any, Literal

OptionType = Literal["call", "put"]
ScoreClass = Literal["A", "B", "C", "Reject"]


@dataclass(frozen=True, slots=True)
class OptionSnapshot:
    snapshot_timestamp: datetime | None
    underlying: str
    expiry: date | None
    strike: float | None
    option_type: OptionType | None
    underlying_price: float | None
    bid: float | None
    ask: float | None
    mid: float | None
    iv: float | None
    delta: float | None
    volume: int | None
    open_interest: int | None
    spread_pct: float | None
    dte: int | None
    atr_14: float | None
    rv_20: float | None
    iv_rank: float | None
    earnings_days: int | None

    @property
    def contract_id(self) -> str:
        expiry_text = self.expiry.isoformat() if self.expiry is not None else "unknown-expiry"
        option_type = self.option_type if self.option_type is not None else "unknown-option"
        strike_text = f"{self.strike:.2f}" if self.strike is not None else "unknown-strike"
        underlying = self.underlying or "unknown-underlying"
        return f"{underlying}:{expiry_text}:{option_type}:{strike_text}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["snapshot_timestamp"] = (
            self.snapshot_timestamp.isoformat() if self.snapshot_timestamp is not None else None
        )
        payload["expiry"] = self.expiry.isoformat() if self.expiry is not None else None
        payload["contract_id"] = self.contract_id
        return payload


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    snapshot: OptionSnapshot
    quality_flags: tuple[str, ...] = ()
    reject_reasons: tuple[str, ...] = ()
    data_completeness: float = 0.0
    confidence: float = 0.0

    @property
    def is_valid(self) -> bool:
        return not self.reject_reasons

    @property
    def is_rejected(self) -> bool:
        return bool(self.reject_reasons)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot": self.snapshot.to_dict(),
            "quality_flags": list(self.quality_flags),
            "reject_reasons": list(self.reject_reasons),
            "data_completeness": round(self.data_completeness, 3),
            "confidence": round(self.confidence, 3),
            "is_valid": self.is_valid,
        }


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    name: str
    rationale: str
    requires_existing_shares: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rationale": self.rationale,
            "requires_existing_shares": self.requires_existing_shares,
        }


@dataclass(frozen=True, slots=True)
class ScoredOption:
    snapshot: OptionSnapshot
    total_score: float
    score_class: ScoreClass
    score_breakdown: dict[str, float]
    top_score_drivers: tuple[str, ...] = ()
    strategy_candidates: tuple[StrategyCandidate, ...] = ()
    confidence: float = 1.0
    quality_flags: tuple[str, ...] = ()
    reject_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot.to_dict()
        payload["total_score"] = round(self.total_score, 3)
        payload["score_class"] = self.score_class
        payload["confidence"] = round(self.confidence, 3)
        payload["quality_flags"] = list(self.quality_flags)
        payload["reject_reasons"] = list(self.reject_reasons)
        payload["score_breakdown"] = {name: round(value, 3) for name, value in self.score_breakdown.items()}
        payload["top_score_drivers"] = list(self.top_score_drivers)
        payload["strategy_candidates"] = [candidate.to_dict() for candidate in self.strategy_candidates]
        return payload
