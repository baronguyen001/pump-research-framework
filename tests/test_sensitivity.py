import json

import pytest

from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard
from pumpscore.sensitivity import format_sensitivity, sensitivity


def _card(points: dict[str, float], token: str = "TEST") -> Scorecard:
    return Scorecard(token, {name: LayerScore(name, points.get(name, 0.0)) for name in LAYER_NAMES})


def test_sensitivity_reports_sorted_layer_swings() -> None:
    card = _card({"narrative": 10, "social": 10, "onchain": 10, "catalyst": 10})
    result = sensitivity(card)

    assert result.current_total == 40
    assert result.current_band == "WATCH"
    assert [row.layer for row in result.rows] == list(LAYER_NAMES)
    assert result.rows[0].total_at_0 == 30
    assert result.rows[0].band_at_0 == "IGNORE"
    assert result.rows[0].total_at_25 == 55
    assert result.rows[0].band_at_25 == "WATCH"
    assert result.rows[0].swing == 25
    assert result.rows[0].pivotal is True


def test_sensitivity_custom_weights_can_make_layer_non_pivotal() -> None:
    card = _card({"narrative": 12, "social": 12, "onchain": 12, "catalyst": 12})
    result = sensitivity(card, {"narrative": 0, "social": 1, "onchain": 1, "catalyst": 1})

    narrative = result.rows[-1]
    assert narrative.layer == "narrative"
    assert narrative.swing == 0
    assert narrative.pivotal is False


def test_sensitivity_all_25_context() -> None:
    result = sensitivity(_card({name: 25 for name in LAYER_NAMES}))
    assert result.current_total == 100
    assert result.current_band == "HIGH_CONVICTION"
    assert result.rows[0].total_at_0 == 75
    assert result.rows[0].band_at_25 == "HIGH_CONVICTION"


def test_format_sensitivity_text_markdown_and_json() -> None:
    result = sensitivity(_card({"narrative": 5, "social": 15, "onchain": 15, "catalyst": 15}))

    text = format_sensitivity(result)
    assert "Sensitivity analysis for TEST" in text
    assert "not predictions" in text

    markdown = format_sensitivity(result, fmt="markdown")
    assert markdown.startswith("# Sensitivity analysis - TEST")
    assert "| Layer | Total at 0 |" in markdown

    parsed = json.loads(format_sensitivity(result, fmt="json"))
    assert parsed["token"] == "TEST"
    assert len(parsed["rows"]) == 4


def test_format_sensitivity_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        format_sensitivity(sensitivity(_card({})), fmt="xml")
