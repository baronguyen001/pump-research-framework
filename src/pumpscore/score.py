"""Weighted confluence scoring and recommendation bands."""

from __future__ import annotations

from dataclasses import dataclass

from pumpscore.model import LAYER_NAMES, Scorecard

DEFAULT_WEIGHTS: dict[str, float] = {
    "narrative": 1.0,
    "social": 1.0,
    "onchain": 1.0,
    "catalyst": 1.0,
}


@dataclass(frozen=True)
class Band:
    label: str
    low: float
    high: float
    action: str


BANDS: list[Band] = [
    Band("IGNORE", 0.0, 40.0, "Ignore. The research case is not strong enough to track."),
    Band("WATCH", 40.0, 60.0, "Watchlist only. Re-score after more public evidence appears."),
    Band("SMALL", 60.0, 75.0, "Small educational risk budget only, if it fits your plan."),
    Band("MEDIUM", 75.0, 90.0, "Medium conviction research case. Pre-commit risk first."),
    Band("HIGH_CONVICTION", 90.0, 100.0, "Strong confluence, still never all-in."),
]


def _normalized_weights(weights: dict[str, float] | None) -> dict[str, float]:
    merged = dict(DEFAULT_WEIGHTS)
    if weights:
        merged.update({key: float(value) for key, value in weights.items() if key in LAYER_NAMES})
    if any(value < 0 for value in merged.values()):
        raise ValueError("Weights must be non-negative")
    if sum(merged.values()) <= 0:
        raise ValueError("At least one layer weight must be positive")
    return merged


def weighted_total(card: Scorecard, weights: dict[str, float] | None = None) -> float:
    active_weights = _normalized_weights(weights)
    numerator = 0.0
    denominator = 25.0 * sum(active_weights[name] for name in LAYER_NAMES)
    for name in LAYER_NAMES:
        layer = card.layers.get(name)
        points = 0.0 if layer is None else layer.points
        numerator += points * active_weights[name]
    return round((numerator / denominator) * 100.0, 2)


def band_for(total: float) -> Band:
    clamped = min(100.0, max(0.0, float(total)))
    for band in BANDS[:-1]:
        if band.low <= clamped < band.high:
            return band
    return BANDS[-1]


def score(card: Scorecard, weights: dict[str, float] | None = None) -> dict[str, object]:
    active_weights = _normalized_weights(weights)
    total = weighted_total(card, active_weights)
    band = band_for(total)
    return {
        "token": card.token,
        "total": total,
        "band": band.label,
        "action": band.action,
        "per_layer": {
            name: (card.layers[name].points if name in card.layers else 0.0) for name in LAYER_NAMES
        },
        "weights": active_weights,
    }
