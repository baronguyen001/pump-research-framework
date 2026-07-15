"""Flat scorecard export for spreadsheets and pipelines."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from pumpscore.checklist import evaluate_checklist
from pumpscore.model import Scorecard
from pumpscore.score import score

EXPORT_FIELDS: tuple[str, ...] = (
    "token",
    "total",
    "band",
    "action",
    "narrative",
    "social",
    "onchain",
    "catalyst",
    "patterns_hit",
    "red_flags_hit",
    "verdict",
    "mcap_usd",
)


def _layer_points(card: Scorecard, name: str) -> float:
    layer = card.layers.get(name)
    return 0.0 if layer is None else layer.points


def export_row(
    raw: dict[str, Any],
    card: Scorecard,
    weights: dict[str, float] | None = None,
) -> dict[str, object]:
    """Flatten one scorecard into a stable single-row mapping."""
    result = score(card, weights)
    row: dict[str, object] = {
        "token": result["token"],
        "total": result["total"],
        "band": result["band"],
        "action": result["action"],
        "narrative": _layer_points(card, "narrative"),
        "social": _layer_points(card, "social"),
        "onchain": _layer_points(card, "onchain"),
        "catalyst": _layer_points(card, "catalyst"),
        "patterns_hit": None,
        "red_flags_hit": None,
        "verdict": None,
        "mcap_usd": card.mcap_usd,
    }

    patterns = raw.get("patterns")
    red_flags = raw.get("red_flags")
    if isinstance(patterns, dict) and isinstance(red_flags, dict):
        checklist = evaluate_checklist(
            {str(key): bool(value) for key, value in patterns.items()},
            {str(key): bool(value) for key, value in red_flags.items()},
        )
        row["patterns_hit"] = checklist.patterns_hit
        row["red_flags_hit"] = checklist.red_flags_hit
        row["verdict"] = checklist.verdict

    return row


def _format_csv(row: dict[str, object]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(EXPORT_FIELDS), extrasaction="ignore")
    writer.writeheader()
    writer.writerow({key: ("" if row.get(key) is None else row.get(key)) for key in EXPORT_FIELDS})
    return output.getvalue()


def format_export(row: dict[str, object], fmt: str = "csv") -> str:
    """Render a flat export row as ``csv`` or ``json``."""
    ordered = {key: row.get(key) for key in EXPORT_FIELDS}
    if fmt == "csv":
        return _format_csv(ordered)
    if fmt == "json":
        return json.dumps(ordered, indent=2) + "\n"
    raise ValueError(f"Unknown format '{fmt}'. Use csv or json.")
