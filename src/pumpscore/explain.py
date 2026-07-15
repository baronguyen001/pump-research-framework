"""Plain-language explanation of a single scorecard."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import cast

from pumpscore.model import LAYER_NAMES, Scorecard
from pumpscore.score import BANDS, band_for, score


@dataclass(frozen=True)
class LayerContribution:
    name: str
    points: float
    weight: float
    contribution: float


@dataclass(frozen=True)
class LeverageLayer:
    name: str
    headroom: float
    max_out_gain: float
    resulting_total: float
    resulting_band: str


@dataclass(frozen=True)
class Explanation:
    token: str
    total: float
    band: str
    action: str
    distance_up: float
    distance_down: float
    contributions: list[LayerContribution]
    rounding_adjustment: float
    highest_leverage: LeverageLayer | None


def _layer_points(card: Scorecard, name: str) -> float:
    layer = card.layers.get(name)
    return 0.0 if layer is None else layer.points


def _distance_up(total: float) -> float:
    current = band_for(total)
    if current.label == "HIGH_CONVICTION":
        return 0.0
    for band in BANDS:
        if band.low > total:
            return round(band.low - total, 2)
    return 0.0


def _distance_down(total: float) -> float:
    current = band_for(total)
    return round(total - current.low, 2)


def explain_card(card: Scorecard, weights: dict[str, float] | None = None) -> Explanation:
    """Explain the weighted total, band distance and highest-leverage layer."""
    result = score(card, weights)
    active_weights = cast("dict[str, float]", result["weights"])
    total = float(cast(float, result["total"]))
    weight_sum = sum(active_weights[name] for name in LAYER_NAMES)

    contributions = [
        LayerContribution(
            name=name,
            points=_layer_points(card, name),
            weight=active_weights[name],
            contribution=round(
                _layer_points(card, name) * active_weights[name] / (25.0 * weight_sum) * 100.0,
                2,
            ),
        )
        for name in LAYER_NAMES
    ]
    contributions.sort(key=lambda row: (-row.contribution, LAYER_NAMES.index(row.name)))
    rounding_adjustment = round(total - sum(row.contribution for row in contributions), 2)

    candidates: list[tuple[float, float, int, str, float]] = []
    for index, name in enumerate(LAYER_NAMES):
        headroom = round(25.0 - _layer_points(card, name), 2)
        if headroom > 0:
            weight_share = active_weights[name] / weight_sum
            candidates.append((weight_share, headroom, -index, name, headroom))

    leverage: LeverageLayer | None = None
    if candidates:
        _, _, _, name, headroom = max(candidates)
        gain = round(headroom * active_weights[name] / (25.0 * weight_sum) * 100.0, 2)
        resulting_total = round(min(100.0, total + gain), 2)
        leverage = LeverageLayer(
            name=name,
            headroom=headroom,
            max_out_gain=gain,
            resulting_total=resulting_total,
            resulting_band=band_for(resulting_total).label,
        )

    return Explanation(
        token=str(result["token"]),
        total=total,
        band=str(result["band"]),
        action=str(result["action"]),
        distance_up=_distance_up(total),
        distance_down=_distance_down(total),
        contributions=contributions,
        rounding_adjustment=rounding_adjustment,
        highest_leverage=leverage,
    )


def _format_text(exp: Explanation) -> str:
    lines = [
        f"Score explanation for {exp.token}",
        "",
        f"Total: {exp.total:g}/100",
        f"Band: {exp.band}",
        f"Action: {exp.action}",
        f"Distance up: {exp.distance_up:g} total points",
        f"Distance down: {exp.distance_down:g} total points",
        "",
        "Weighted contributions",
        "Layer        Points  Weight  Contribution",
        "-------------------------------------------",
    ]
    for row in exp.contributions:
        lines.append(f"{row.name:<12} {row.points:>6g} {row.weight:>7g} {row.contribution:>11.2f}")
    if exp.rounding_adjustment:
        lines.append(f"Rounding adjustment: {exp.rounding_adjustment:+.2f}")
    lines.append("")
    if exp.highest_leverage is None:
        lines.append("Highest-leverage layer: none; every layer is already maxed.")
    else:
        leverage = exp.highest_leverage
        lines.append(
            "Highest-leverage layer: "
            f"{leverage.name} (+{leverage.max_out_gain:.2f} total points if maxed; "
            f"{leverage.resulting_total:g}/100, {leverage.resulting_band})"
        )
    lines.append("")
    lines.append("This explanation is educational research context, not financial advice.")
    return "\n".join(lines) + "\n"


def _format_markdown(exp: Explanation) -> str:
    lines = [
        f"# Score explanation - {exp.token}",
        "",
        f"- Total: {exp.total:g}/100",
        f"- Band: {exp.band}",
        f"- Action: {exp.action}",
        f"- Distance up: {exp.distance_up:g} total points",
        f"- Distance down: {exp.distance_down:g} total points",
        "",
        "| Layer | Points | Weight | Contribution |",
        "|---|---:|---:|---:|",
    ]
    for row in exp.contributions:
        lines.append(f"| {row.name} | {row.points:g} | {row.weight:g} | {row.contribution:.2f} |")
    if exp.rounding_adjustment:
        lines.extend(["", f"Rounding adjustment: {exp.rounding_adjustment:+.2f} total points."])
    lines.append("")
    if exp.highest_leverage is None:
        lines.append("Highest-leverage layer: none; every layer is already maxed.")
    else:
        leverage = exp.highest_leverage
        lines.append(
            "Highest-leverage layer: "
            f"**{leverage.name}** adds {leverage.max_out_gain:.2f} total points if maxed, "
            f"ending at {leverage.resulting_total:g}/100 ({leverage.resulting_band})."
        )
    lines.append("")
    lines.append("> This explanation is educational research context, not financial advice.")
    return "\n".join(lines) + "\n"


def format_explanation(exp: Explanation, fmt: str = "text") -> str:
    """Render an explanation as ``text``, ``markdown`` or ``json``."""
    if fmt == "json":
        return json.dumps(asdict(exp), indent=2) + "\n"
    if fmt == "markdown":
        return _format_markdown(exp)
    if fmt == "text":
        return _format_text(exp)
    raise ValueError(f"Unknown format '{fmt}'. Use text, markdown or json.")
