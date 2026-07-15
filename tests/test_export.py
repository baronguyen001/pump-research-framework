import csv
import io
import json

import pytest

from pumpscore.export import EXPORT_FIELDS, export_row, format_export
from pumpscore.io import blank_template, card_from_dict


def test_export_row_includes_score_layers_checklist_and_mcap() -> None:
    raw = blank_template()
    raw["token"] = "FICTIONAL_EXPORT"
    raw["layers"]["narrative"]["points"] = 20
    raw["layers"]["social"]["points"] = 15
    raw["layers"]["onchain"]["points"] = 10
    raw["layers"]["catalyst"]["points"] = 5
    raw["context"]["mcap_usd"] = 123_000_000
    raw["patterns"]["hot_narrative_early"] = True
    raw["patterns"]["small_starting_mcap"] = True
    raw["red_flags"]["paid_promo_social"] = True

    row = export_row(raw, card_from_dict(raw))

    assert list(row) == list(EXPORT_FIELDS)
    assert row["token"] == "FICTIONAL_EXPORT"
    assert row["total"] == 50
    assert row["band"] == "WATCH"
    assert row["narrative"] == 20
    assert row["patterns_hit"] == 2
    assert row["red_flags_hit"] == 1
    assert row["verdict"] == "CAUTION"
    assert row["mcap_usd"] == 123_000_000


def test_export_row_without_checklist_leaves_optional_fields_null() -> None:
    raw = {"token": "NO_CHECKLIST", "layers": {"narrative": 25}}
    row = export_row(raw, card_from_dict(raw))

    assert row["patterns_hit"] is None
    assert row["red_flags_hit"] is None
    assert row["verdict"] is None
    assert row["mcap_usd"] is None


def test_export_row_honors_weights() -> None:
    raw = {"token": "WEIGHTED", "layers": {"narrative": 25, "social": 0}}
    row = export_row(raw, card_from_dict(raw), {"narrative": 3, "social": 1})
    assert row["total"] == 50


def test_format_export_csv_and_json() -> None:
    row = {
        "token": "FICTIONAL_EXPORT",
        "total": 50.0,
        "band": "WATCH",
        "action": "Watchlist only.",
        "narrative": 20.0,
        "social": 15.0,
        "onchain": 10.0,
        "catalyst": 5.0,
        "patterns_hit": None,
        "red_flags_hit": None,
        "verdict": None,
        "mcap_usd": None,
    }

    csv_text = format_export(row)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert parsed[0]["token"] == "FICTIONAL_EXPORT"
    assert parsed[0]["patterns_hit"] == ""

    json_text = format_export(row, fmt="json")
    parsed_json = json.loads(json_text)
    assert parsed_json["patterns_hit"] is None
    assert parsed_json["mcap_usd"] is None


def test_format_export_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        format_export({}, fmt="xml")
