import json
from pathlib import Path

import pytest

from pumpscore.narrative import (
    NarrativeError,
    NarrativeRow,
    format_csv,
    format_json,
    format_table,
    parse_coingecko,
    parse_defillama,
    rank_narratives,
    rows_to_dicts,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_coingecko_fixture() -> None:
    rows = parse_coingecko(_load("coingecko_categories.json"))
    assert len(rows) == 5
    by_name = {row.name: row for row in rows}
    assert by_name["Meme"].change_24h == 9.73
    assert by_name["Meme"].market_cap_usd == 52000000000
    # Null change parses to None, not a crash.
    assert by_name["Quiet Category"].change_24h is None


def test_parse_defillama_fixture() -> None:
    rows = parse_defillama(_load("defillama_categories.json"))
    by_name = {row.name: row for row in rows}
    assert by_name["Dexes"].change_24h == 5.6
    assert by_name["Dexes"].change_7d == 12.0
    assert by_name["Bridge"].change_24h is None


def test_rank_orders_by_momentum_desc() -> None:
    rows = parse_coingecko(_load("coingecko_categories.json"))
    ranked = rank_narratives(rows, top=3)
    assert [r.name for r in ranked] == [
        "Meme",
        "Real World Assets (RWA)",
        "Artificial Intelligence (AI)",
    ]


def test_rank_top_zero_returns_empty() -> None:
    rows = parse_coingecko(_load("coingecko_categories.json"))
    assert rank_narratives(rows, top=0) == []


def test_rank_missing_momentum_sinks_to_bottom() -> None:
    rows = parse_coingecko(_load("coingecko_categories.json"))
    ranked = rank_narratives(rows, top=99)
    # The category with a null 24h change must be last.
    assert ranked[-1].name == "Quiet Category"


def test_parse_rejects_wrong_shape() -> None:
    with pytest.raises(NarrativeError):
        parse_coingecko({"not": "a list"})
    with pytest.raises(NarrativeError):
        parse_defillama(["not", "a", "mapping"])


def test_format_table_contains_header_and_caveat() -> None:
    rows = rank_narratives(parse_coingecko(_load("coingecko_categories.json")), top=2)
    text = format_table(rows, "coingecko")
    assert "Hot narratives by momentum" in text
    assert "Meme" in text
    assert "MarketCap" in text
    assert "not a buy signal" in text


def test_format_table_empty_rows() -> None:
    text = format_table([], "defillama")
    assert "no categories returned" in text
    assert "TVL" in text


def test_narrative_row_is_frozen() -> None:
    row = NarrativeRow("X", 1.0, 2.0, 3.0, "coingecko")
    with pytest.raises(AttributeError):
        row.name = "Y"  # type: ignore[misc]


def test_rows_to_dicts_numbers_ranks() -> None:
    rows = rank_narratives(parse_coingecko(_load("coingecko_categories.json")), top=2)
    dicts = rows_to_dicts(rows)
    assert [d["rank"] for d in dicts] == [1, 2]
    assert dicts[0]["name"] == "Meme"
    assert dicts[0]["source"] == "coingecko"


def test_format_json_round_trips() -> None:
    rows = rank_narratives(parse_coingecko(_load("coingecko_categories.json")), top=2)
    parsed = json.loads(format_json(rows))
    assert len(parsed) == 2
    assert parsed[0]["rank"] == 1


def test_format_csv_has_header_and_blanks_for_none() -> None:
    rows = [NarrativeRow("Solo", None, None, None, "defillama")]
    csv_text = format_csv(rows)
    lines = csv_text.strip().split("\n")
    assert lines[0] == "rank,name,change_24h,change_7d,market_cap_usd,source"
    assert lines[1] == "1,Solo,,,,defillama"
