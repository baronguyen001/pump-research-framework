"""YAML and JSON scorecard IO."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from pumpscore.checklist import PATTERNS, RED_FLAGS
from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard


def _read_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() in {".yaml", ".yml"}:
        loaded = yaml.safe_load(text)
    elif source.suffix.lower() == ".json":
        loaded = json.loads(text)
    else:
        raise ValueError("Scorecard path must end in .yaml, .yml, or .json")
    if not isinstance(loaded, dict):
        raise ValueError("Scorecard must be a mapping")
    return loaded


def load_scorecard(path: str | Path) -> Scorecard:
    return card_from_dict(_read_mapping(path))


def save_scorecard(card: Scorecard, path: str | Path) -> None:
    target = Path(path)
    data = card_to_dict(card)
    if target.suffix.lower() in {".yaml", ".yml"}:
        target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    elif target.suffix.lower() == ".json":
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        raise ValueError("Scorecard path must end in .yaml, .yml, or .json")


def card_to_dict(card: Scorecard) -> dict[str, Any]:
    data: dict[str, Any] = {
        "token": card.token,
        "layers": {
            name: {
                "points": (card.layers[name].points if name in card.layers else 0.0),
                "notes": (card.layers[name].notes if name in card.layers else ""),
            }
            for name in LAYER_NAMES
        },
        "context": {},
    }
    context = data["context"]
    assert isinstance(context, dict)
    for key in (
        "mcap_usd",
        "days_since_launch",
        "pumped_x_30d",
        "funding_rate_8h",
        "catalyst_days_out",
        "cex_tier",
    ):
        context[key] = getattr(card, key)
    return data


def card_from_dict(d: dict[str, Any]) -> Scorecard:
    token = str(d.get("token", "UNKNOWN"))
    raw_layers = d.get("layers", {})
    if not isinstance(raw_layers, dict):
        raise ValueError("layers must be a mapping")

    layers: dict[str, LayerScore] = {}
    for name in LAYER_NAMES:
        raw_layer = raw_layers.get(name, 0.0)
        if isinstance(raw_layer, dict):
            points = float(raw_layer.get("points", 0.0) or 0.0)
            notes = str(raw_layer.get("notes", "") or "")
        else:
            points = float(raw_layer or 0.0)
            notes = ""
        layers[name] = LayerScore(name=name, points=points, notes=notes)

    raw_context = d.get("context", {})
    if raw_context is None:
        raw_context = {}
    if not isinstance(raw_context, dict):
        raise ValueError("context must be a mapping")

    def optional_float(key: str) -> float | None:
        value = raw_context.get(key, d.get(key))
        if value is None or value == "":
            return None
        return float(value)

    def optional_int(key: str) -> int | None:
        value = raw_context.get(key, d.get(key))
        if value is None or value == "":
            return None
        return int(value)

    return Scorecard(
        token=token,
        layers=layers,
        mcap_usd=optional_float("mcap_usd"),
        days_since_launch=optional_int("days_since_launch"),
        pumped_x_30d=optional_float("pumped_x_30d"),
        funding_rate_8h=optional_float("funding_rate_8h"),
        catalyst_days_out=optional_int("catalyst_days_out"),
        cex_tier=optional_int("cex_tier"),
    )


def blank_template() -> dict[str, Any]:
    return {
        "token": "FICTIONAL_TOKEN",
        "layers": {name: {"points": 0, "notes": ""} for name in LAYER_NAMES},
        "context": {
            "mcap_usd": None,
            "days_since_launch": None,
            "pumped_x_30d": None,
            "funding_rate_8h": None,
            "catalyst_days_out": None,
            "cex_tier": None,
        },
        "patterns": {key: False for key, _ in PATTERNS},
        "red_flags": {key: False for key, _ in RED_FLAGS},
        "stage_signals": {
            "mention_rate_wow": None,
            "smart_wallets_7d": None,
            "google_trends_rising": None,
            "tier1_kol_covering": None,
            "mainstream_media": None,
            "down_from_ath_pct": None,
        },
        "execution_plan": {
            "asset_class": "midcap",
            "bankroll_usd": None,
            "entry_price": 1.0,
            "invalidation": "",
        },
    }
