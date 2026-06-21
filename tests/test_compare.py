import json

import pytest

from pumpscore.compare import compare_cards, format_comparison
from pumpscore.model import LayerScore, Scorecard


def _card(token: str, points: float) -> Scorecard:
    return Scorecard(
        token,
        {name: LayerScore(name, points) for name in ("narrative", "social", "onchain", "catalyst")},
    )


def test_compare_ranks_by_total_desc() -> None:
    cards = [_card("LOW", 5), _card("HIGH", 24), _card("MID", 15)]
    results = compare_cards(cards)
    assert [r["token"] for r in results] == ["HIGH", "MID", "LOW"]
    assert results[0]["total"] >= results[1]["total"] >= results[2]["total"]


def test_compare_tie_break_is_token_name() -> None:
    results = compare_cards([_card("B", 10), _card("A", 10)])
    assert [r["token"] for r in results] == ["A", "B"]


def test_format_text_has_header_and_rows() -> None:
    out = format_comparison(compare_cards([_card("AAA", 20), _card("BBB", 10)]))
    assert "Scorecard comparison" in out
    assert "AAA" in out and "BBB" in out
    assert "not a buy order" in out


def test_format_markdown_is_a_table() -> None:
    out = format_comparison(compare_cards([_card("AAA", 20)]), fmt="markdown")
    assert out.startswith("# Scorecard comparison")
    assert "| Rank | Token |" in out
    assert "| 1 | AAA |" in out


def test_format_json_round_trips() -> None:
    results = compare_cards([_card("AAA", 20), _card("BBB", 10)])
    out = format_comparison(results, fmt="json")
    parsed = json.loads(out)
    assert [r["token"] for r in parsed] == ["AAA", "BBB"]


def test_empty_comparison() -> None:
    assert "no scorecards" in format_comparison([])


def test_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        format_comparison([], fmt="xml")
