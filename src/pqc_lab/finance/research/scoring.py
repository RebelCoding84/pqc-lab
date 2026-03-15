"""Weighted scoring for offline finance research candidates."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable, Iterable, Mapping

from pqc_lab.finance.models import OptionSnapshot, ScoredOption, ValidationResult
from pqc_lab.finance.research.strategy_candidates import build_strategy_candidates

try:
    import yaml
except ImportError:  # pragma: no cover - fallback for minimal environments.
    yaml = None

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parents[1] / "config" / "weights_v1.yaml"


def load_weights(path: str | Path | None = None) -> dict[str, float]:
    """Load flat v1 scoring weights from a local YAML file."""

    source = Path(path) if path is not None else DEFAULT_WEIGHTS_PATH
    text = source.read_text(encoding="utf-8")
    raw_weights = _parse_weights(text)
    weights = {name: float(value) for name, value in raw_weights.items()}
    unknown = sorted(set(weights) - set(_FEATURE_BUILDERS))
    if unknown:
        raise ValueError(f"unsupported scoring weights: {', '.join(unknown)}")
    total = sum(value for value in weights.values() if value > 0.0)
    if total <= 0.0:
        raise ValueError("weight total must be positive")
    return {name: value / total for name, value in weights.items()}


def score_snapshot(
    snapshot: OptionSnapshot,
    *,
    validation_result: ValidationResult | None = None,
    weights: dict[str, float] | None = None,
) -> ScoredOption:
    """Score one option snapshot with the v1 weighted model."""

    effective_weights = weights or load_weights()
    validation = validation_result or ValidationResult(
        snapshot=snapshot,
        data_completeness=1.0,
        confidence=1.0,
    )

    if validation.is_rejected:
        return ScoredOption(
            snapshot=snapshot,
            total_score=0.0,
            score_class="Reject",
            score_breakdown={name: 0.0 for name in _FEATURE_BUILDERS},
            top_score_drivers=tuple(f"reject:{reason}" for reason in validation.reject_reasons[:3]),
            strategy_candidates=(),
            confidence=round(validation.confidence, 3),
            quality_flags=validation.quality_flags,
            reject_reasons=validation.reject_reasons,
        )

    breakdown = {
        name: round(_clamp_100(builder(snapshot)), 3)
        for name, builder in _FEATURE_BUILDERS.items()
        if name in effective_weights
    }
    total_score = round(sum(breakdown[name] * effective_weights[name] for name in breakdown), 3)
    scored_option = ScoredOption(
        snapshot=snapshot,
        total_score=total_score,
        score_class=_score_class(total_score),
        score_breakdown=breakdown,
        top_score_drivers=_top_score_drivers(breakdown, effective_weights),
        strategy_candidates=(),
        confidence=round(validation.confidence, 3),
        quality_flags=validation.quality_flags,
        reject_reasons=validation.reject_reasons,
    )
    return replace(scored_option, strategy_candidates=build_strategy_candidates(scored_option))


def score_snapshots(
    snapshots: Iterable[OptionSnapshot],
    *,
    validation_results: Iterable[ValidationResult] | Mapping[str, ValidationResult] | None = None,
    weights: dict[str, float] | None = None,
) -> list[ScoredOption]:
    """Score and rank a sequence of option snapshots."""

    effective_weights = weights or load_weights()
    validation_map = _validation_map(validation_results)
    scored = [
        score_snapshot(
            snapshot,
            validation_result=validation_map.get(snapshot.contract_id),
            weights=effective_weights,
        )
        for snapshot in snapshots
    ]
    return sorted(scored, key=lambda item: item.total_score, reverse=True)


def _parse_weights(text: str) -> dict[str, float]:
    if yaml is not None:
        payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise ValueError("weights YAML must be a flat mapping")
        return {str(name): float(value) for name, value in payload.items()}

    weights: dict[str, float] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"invalid weights line: {raw_line!r}")
        weights[name.strip()] = float(value.strip())
    return weights


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(value, upper))


def _clamp_100(value: float) -> float:
    return _clamp(value, lower=0.0, upper=100.0)


def _spread_quality_score(snapshot: OptionSnapshot) -> float:
    if snapshot.spread_pct is None:
        return 0.0
    return 100.0 * (1.0 - _clamp(snapshot.spread_pct / 0.12))


def _liquidity_score(snapshot: OptionSnapshot) -> float:
    volume_score = 100.0 * _clamp((snapshot.volume or 0) / 1000.0)
    open_interest_score = 100.0 * _clamp((snapshot.open_interest or 0) / 5000.0)
    return (volume_score + open_interest_score) / 2.0


def _iv_level_score(snapshot: OptionSnapshot) -> float:
    if snapshot.iv is None:
        return 0.0
    target_iv = 0.30
    distance = abs(snapshot.iv - target_iv)
    return 100.0 * (1.0 - _clamp(distance / 0.30))


def _iv_minus_rv_score(snapshot: OptionSnapshot) -> float:
    if snapshot.iv is None or snapshot.rv_20 is None:
        return 0.0
    iv_gap = snapshot.iv - snapshot.rv_20
    return 100.0 * _clamp((iv_gap + 0.05) / 0.20)


def _delta_moneyness_suitability_score(snapshot: OptionSnapshot) -> float:
    if snapshot.delta is None:
        return 0.0
    target_delta = 0.30
    distance = abs(abs(snapshot.delta) - target_delta)
    return 100.0 * (1.0 - _clamp(distance / target_delta))


def _dte_suitability_score(snapshot: OptionSnapshot) -> float:
    if snapshot.dte is None or snapshot.dte <= 0:
        return 0.0
    target_dte = 30.0
    return 100.0 * (1.0 - _clamp(abs(snapshot.dte - target_dte) / target_dte))


def _earnings_proximity_penalty_score(snapshot: OptionSnapshot) -> float:
    if snapshot.earnings_days is None:
        return 0.0
    return 100.0 * _clamp((snapshot.earnings_days - 7) / 21.0)


def _score_class(total_score: float) -> str:
    if total_score >= 80.0:
        return "A"
    if total_score >= 65.0:
        return "B"
    if total_score >= 50.0:
        return "C"
    return "Reject"


def _top_score_drivers(breakdown: dict[str, float], weights: Mapping[str, float]) -> tuple[str, ...]:
    driver_impacts = []
    for name, score in breakdown.items():
        impact = (score - 50.0) * weights.get(name, 0.0)
        driver_impacts.append((name, impact))
    driver_impacts.sort(key=lambda item: abs(item[1]), reverse=True)
    return tuple(
        f"{name}:{'+' if impact >= 0.0 else '-'}{abs(impact):.1f}"
        for name, impact in driver_impacts[:3]
    )


def _validation_map(
    validation_results: Iterable[ValidationResult] | Mapping[str, ValidationResult] | None,
) -> dict[str, ValidationResult]:
    if validation_results is None:
        return {}
    if isinstance(validation_results, Mapping):
        return dict(validation_results)
    return {result.snapshot.contract_id: result for result in validation_results}


_FEATURE_BUILDERS: dict[str, Callable[[OptionSnapshot], float]] = {
    "spread_quality": _spread_quality_score,
    "liquidity": _liquidity_score,
    "iv_level": _iv_level_score,
    "iv_minus_rv": _iv_minus_rv_score,
    "delta_moneyness_suitability": _delta_moneyness_suitability_score,
    "dte_suitability": _dte_suitability_score,
    "earnings_proximity_penalty": _earnings_proximity_penalty_score,
}
