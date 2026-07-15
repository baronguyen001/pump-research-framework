import json

import pytest

from pumpscore.explain import explain_card, format_explanation
from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard


def _card(points: dict[str, float], token: str = "TEST") -> Scorecard:
    return Scorecard(token, {name: LayerScore(name, points.get(name, 0.0)) for name in LAYER_NAMES})


def test_explain_contributions_reconcile_to_total_with_custom_weights() -> None:
    card = _card({"narrative": 24, "social": 0, "onchain": 12, "catalyst": 12})
    exp = explain_card(card, {"narrative": 2, "social": 2, "onchain": 1, "catalyst": 1})

    assert exp.total == 48
    assert exp.band == "WATCH"
    assert [row.name for row in exp.contributions] == [
        "narrative",
        "onchain",
        "catalyst",
        "social",
    ]
    reconciled = round(
        sum(row.contribution for row in exp.contributions) + exp.rounding_adjustment,
        2,
    )
    assert reconciled == exp.total
    assert exp.highest_leverage is not None
    assert exp.highest_leverage.name == "social"
    assert exp.highest_leverage.max_out_gain == 33.33
    assert exp.highest_leverage.resulting_band == "MEDIUM"


def test_explain_all_zero_distances() -> None:
    exp = explain_card(_card({}))
    assert exp.total == 0
    assert exp.distance_up == 40
    assert exp.distance_down == 0


def test_explain_all_25_has_no_leverage_and_high_conviction_distance() -> None:
    exp = explain_card(_card({name: 25 for name in LAYER_NAMES}))
    assert exp.band == "HIGH_CONVICTION"
    assert exp.distance_up == 0
    assert exp.distance_down == 10
    assert exp.highest_leverage is None


def test_format_explanation_text_markdown_and_json() -> None:
    exp = explain_card(_card({"narrative": 20, "social": 10, "onchain": 5, "catalyst": 0}))

    text = format_explanation(exp)
    assert "Score explanation for TEST" in text
    assert "not financial advice" in text

    markdown = format_explanation(exp, fmt="markdown")
    assert markdown.startswith("# Score explanation - TEST")
    assert "| Layer | Points |" in markdown

    parsed = json.loads(format_explanation(exp, fmt="json"))
    assert parsed["token"] == "TEST"
    assert parsed["contributions"][0]["name"] == "narrative"


def test_format_explanation_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        format_explanation(explain_card(_card({})), fmt="xml")
