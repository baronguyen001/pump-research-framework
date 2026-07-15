"""One-layer-at-a-time score sensitivity analysis."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard
from pumpscore.score import band_for, weighted_total

BOUNDARIES: tuple[float, ...] = (40.0, 60.0, 75.0, 90.0)


@dataclass(frozen=True)
class LayerSwing:
    layer: str
    total_at_0: float
    band_at_0: str
    total_at_25: float
    band_at_25: str
    swing: float
    pivotal: bool


@dataclass(frozen=True)
class SensitivityResult:
    token: str
    current_total: float
    current_band: str
    rows: list[LayerSwing]


def _forced_card(card: Scorecard, layer: str, points: float) -> Scorecard:
    layers = {
        name: LayerScore(name=name, points=card.layers[name].points, notes=card.layers[name].notes)
        if name in card.layers
        else LayerScore(name=name, points=0.0)
        for name in LAYER_NAMES
    }
    layers[layer] = LayerScore(name=layer, points=points)
    return Scorecard(
        token=card.token,
        layers=layers,
        mcap_usd=card.mcap_usd,
        days_since_launch=card.days_since_launch,
        pumped_x_30d=card.pumped_x_30d,
        funding_rate_8h=card.funding_rate_8h,
        catalyst_days_out=card.catalyst_days_out,
        cex_tier=card.cex_tier,
    )


def _is_pivotal(low: float, high: float) -> bool:
    return any(low < boundary <= high for boundary in BOUNDARIES)


def sensitivity(card: Scorecard, weights: dict[str, float] | None = None) -> SensitivityResult:
    """Return one-at-a-time layer swings, sorted by mechanical swing size."""
    rows: list[LayerSwing] = []
    for name in LAYER_NAMES:
        total_at_0 = weighted_total(_forced_card(card, name, 0.0), weights)
        total_at_25 = weighted_total(_forced_card(card, name, 25.0), weights)
        rows.append(
            LayerSwing(
                layer=name,
                total_at_0=total_at_0,
                band_at_0=band_for(total_at_0).label,
                total_at_25=total_at_25,
                band_at_25=band_for(total_at_25).label,
                swing=round(total_at_25 - total_at_0, 2),
                pivotal=_is_pivotal(total_at_0, total_at_25),
            )
        )
    rows.sort(key=lambda row: (-row.swing, LAYER_NAMES.index(row.layer)))
    current_total = weighted_total(card, weights)
    return SensitivityResult(
        token=card.token,
        current_total=current_total,
        current_band=band_for(current_total).label,
        rows=rows,
    )


def _format_text(result: SensitivityResult) -> str:
    lines = [
        f"Sensitivity analysis for {result.token}",
        "",
        f"Current total: {result.current_total:g}/100",
        f"Current band: {result.current_band}",
        "",
        "Layer        At 0   Band@0           At 25  Band@25          Swing  Pivotal",
        "--------------------------------------------------------------------------",
    ]
    for row in result.rows:
        pivotal = "yes" if row.pivotal else "no"
        lines.append(
            f"{row.layer:<12} {row.total_at_0:>5.1f}  {row.band_at_0:<15} "
            f"{row.total_at_25:>5.1f}  {row.band_at_25:<15} {row.swing:>6.2f}  {pivotal}"
        )
    lines.append("")
    lines.append("Swings are mechanical one-layer checks, not predictions or financial advice.")
    return "\n".join(lines) + "\n"


def _format_markdown(result: SensitivityResult) -> str:
    lines = [
        f"# Sensitivity analysis - {result.token}",
        "",
        f"- Current total: {result.current_total:g}/100",
        f"- Current band: {result.current_band}",
        "",
        "| Layer | Total at 0 | Band at 0 | Total at 25 | Band at 25 | Swing | Pivotal |",
        "|---|---:|---|---:|---|---:|---|",
    ]
    for row in result.rows:
        pivotal = "yes" if row.pivotal else "no"
        lines.append(
            f"| {row.layer} | {row.total_at_0:g} | {row.band_at_0} | "
            f"{row.total_at_25:g} | {row.band_at_25} | {row.swing:.2f} | {pivotal} |"
        )
    lines.append("")
    lines.append("> Swings are mechanical one-layer checks, not predictions or financial advice.")
    return "\n".join(lines) + "\n"


def format_sensitivity(result: SensitivityResult, fmt: str = "text") -> str:
    """Render sensitivity results as ``text``, ``markdown`` or ``json``."""
    if fmt == "json":
        return json.dumps(asdict(result), indent=2) + "\n"
    if fmt == "markdown":
        return _format_markdown(result)
    if fmt == "text":
        return _format_text(result)
    raise ValueError(f"Unknown format '{fmt}'. Use text, markdown or json.")
