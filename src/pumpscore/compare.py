"""Side-by-side comparison of several scorecards.

Pure, offline and deterministic: score every card with the same weights and
rank them so you can see which research case is strongest at a glance. No
network, no wallet data, no price calls — just the four-layer scores you already
entered by hand.
"""

from __future__ import annotations

import json
from typing import Any, cast

from pumpscore.model import LAYER_NAMES, Scorecard
from pumpscore.score import score


def compare_cards(
    cards: list[Scorecard],
    weights: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Score each card and return results ranked by total (desc, then token)."""
    results = [score(card, weights) for card in cards]
    results.sort(key=lambda r: (-float(cast(float, r["total"])), str(r["token"])))
    return results


def _per_layer(result: dict[str, Any], name: str) -> float:
    per_layer = cast("dict[str, float]", result["per_layer"])
    return float(per_layer.get(name, 0.0))


def _format_text(results: list[dict[str, Any]]) -> str:
    header = f"{'#':>2}  {'Token':<20} {'Total':>6} {'Band':<16}"
    header += " ".join(f"{name[:8]:>8}" for name in LAYER_NAMES)
    lines = ["Scorecard comparison (ranked by total)", "", header, "-" * len(header)]
    for index, result in enumerate(results, start=1):
        row = (
            f"{index:>2}  {str(result['token'])[:20]:<20} "
            f"{float(cast(float, result['total'])):>6.1f} {str(result['band']):<16}"
        )
        row += " ".join(f"{_per_layer(result, name):>8.1f}" for name in LAYER_NAMES)
        lines.append(row)
    if not results:
        lines.append("(no scorecards given)")
    lines.append("")
    lines.append("Ranking compares research strength only — it is not a buy order.")
    return "\n".join(lines) + "\n"


def _format_markdown(results: list[dict[str, Any]]) -> str:
    cols = ["Rank", "Token", "Total", "Band", *(name.title() for name in LAYER_NAMES)]
    lines = [
        "# Scorecard comparison",
        "",
        "| " + " | ".join(cols) + " |",
        "|" + "|".join(["---"] * len(cols)) + "|",
    ]
    for index, result in enumerate(results, start=1):
        cells = [
            str(index),
            str(result["token"]),
            f"{float(cast(float, result['total'])):g}",
            str(result["band"]),
            *(f"{_per_layer(result, name):g}" for name in LAYER_NAMES),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("> Ranking compares research strength only — not financial advice.")
    return "\n".join(lines) + "\n"


def format_comparison(results: list[dict[str, Any]], fmt: str = "text") -> str:
    """Render comparison results as ``text``, ``markdown`` or ``json``."""
    if fmt == "json":
        return json.dumps(results, indent=2) + "\n"
    if fmt == "markdown":
        return _format_markdown(results)
    if fmt == "text":
        return _format_text(results)
    raise ValueError(f"Unknown format '{fmt}'. Use text, markdown or json.")
