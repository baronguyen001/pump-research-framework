"""Core scorecard dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

LAYER_NAMES: tuple[str, ...] = ("narrative", "social", "onchain", "catalyst")


def _clamp_points(value: float) -> float:
    if not isfinite(value):
        raise ValueError("Layer points must be a finite number")
    return min(25.0, max(0.0, float(value)))


@dataclass
class LayerScore:
    name: str
    points: float
    notes: str = ""

    def __post_init__(self) -> None:
        if self.name not in LAYER_NAMES:
            joined = ", ".join(LAYER_NAMES)
            raise ValueError(f"Layer name must be one of: {joined}")
        self.points = _clamp_points(self.points)


@dataclass
class Scorecard:
    token: str
    layers: dict[str, LayerScore]
    mcap_usd: float | None = None
    days_since_launch: int | None = None
    pumped_x_30d: float | None = None
    funding_rate_8h: float | None = None
    catalyst_days_out: int | None = None
    cex_tier: int | None = None

    def __post_init__(self) -> None:
        normalized: dict[str, LayerScore] = {}
        for name, layer in self.layers.items():
            if name not in LAYER_NAMES:
                continue
            if layer.name != name:
                layer = LayerScore(name=name, points=layer.points, notes=layer.notes)
            normalized[name] = layer
        self.layers = normalized

    def total(self) -> float:
        return sum(self.layers.get(name, LayerScore(name, 0.0)).points for name in LAYER_NAMES)
