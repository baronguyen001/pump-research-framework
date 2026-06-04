"""Lifecycle, Goldilocks gate, and anti-FOMO decision helpers."""

from __future__ import annotations

from dataclasses import dataclass

from pumpscore.model import Scorecard

STAGES: tuple[str, ...] = (
    "seed",
    "whisper",
    "public_awareness",
    "mainstream",
    "euphoria",
    "collapse",
)


@dataclass(frozen=True)
class GoldilocksResult:
    passes: bool
    checks: dict[str, bool]
    reasons: list[str]


def _layer_points(card: Scorecard, name: str) -> float:
    layer = card.layers.get(name)
    return 0.0 if layer is None else layer.points


def goldilocks_gate(
    card: Scorecard,
    hot_multiple: float = 5.0,
    max_funding_8h: float = 0.05,
    catalyst_window_days: int = 90,
    micro_layer_min: float = 18.0,
) -> GoldilocksResult:
    narrative = _layer_points(card, "narrative")
    social = _layer_points(card, "social")
    onchain = _layer_points(card, "onchain")
    catalyst = _layer_points(card, "catalyst")

    macro_confirm = narrative >= 18.0
    meso_confirm = catalyst >= 18.0
    micro_confirm = social >= micro_layer_min and onchain >= micro_layer_min
    too_hot_price = card.pumped_x_30d is not None and card.pumped_x_30d > hot_multiple
    too_hot_funding = card.funding_rate_8h is not None and card.funding_rate_8h > max_funding_8h
    not_too_hot = not too_hot_price and not too_hot_funding
    has_catalyst = (
        card.catalyst_days_out is not None and 0 <= card.catalyst_days_out <= catalyst_window_days
    )
    checks = {
        "macro_confirm": macro_confirm,
        "meso_confirm": meso_confirm,
        "micro_confirm": micro_confirm,
        "not_too_hot": not_too_hot,
        "has_catalyst": has_catalyst,
    }
    reasons = [name for name, ok in checks.items() if not ok]
    return GoldilocksResult(passes=all(checks.values()), checks=checks, reasons=reasons)


def fomo_decision(card: Scorecard, **gate_kwargs: float | int) -> str:
    total = card.total()
    hot_multiple = float(gate_kwargs.get("hot_multiple", 5.0))
    max_funding_8h = float(gate_kwargs.get("max_funding_8h", 0.05))
    catalyst_window_days = int(gate_kwargs.get("catalyst_window_days", 90))
    micro_layer_min = float(gate_kwargs.get("micro_layer_min", 18.0))

    if total < 70.0:
        return "SKIP"
    if card.pumped_x_30d is not None and card.pumped_x_30d > hot_multiple:
        return "WAIT_PULLBACK"
    if card.funding_rate_8h is not None and card.funding_rate_8h > max_funding_8h:
        return "SKIP"
    if card.catalyst_days_out is None or card.catalyst_days_out > catalyst_window_days:
        return "WATCH"
    gate = goldilocks_gate(
        card,
        hot_multiple=hot_multiple,
        max_funding_8h=max_funding_8h,
        catalyst_window_days=catalyst_window_days,
        micro_layer_min=micro_layer_min,
    )
    if not gate.passes:
        return "WATCH"
    return "ENTER_30"


@dataclass(frozen=True)
class StageSignals:
    mention_rate_wow: float | None = None
    smart_wallets_7d: int | None = None
    google_trends_rising: bool | None = None
    tier1_kol_covering: bool | None = None
    mainstream_media: bool | None = None
    down_from_ath_pct: float | None = None


def classify_stage(sig: StageSignals) -> str:
    if sig.down_from_ath_pct is not None and sig.down_from_ath_pct >= 70.0:
        return "collapse"
    mention = sig.mention_rate_wow or 0.0
    if sig.mainstream_media and sig.tier1_kol_covering and mention >= 300.0:
        return "euphoria"
    if sig.mainstream_media or (sig.google_trends_rising and sig.tier1_kol_covering):
        return "mainstream"
    if sig.tier1_kol_covering or sig.google_trends_rising or mention >= 100.0:
        return "public_awareness"
    if (sig.smart_wallets_7d or 0) >= 3 or mention >= 30.0:
        return "whisper"
    return "seed"
