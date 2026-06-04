from pathlib import Path

from pumpscore.io import blank_template, card_from_dict, load_scorecard, save_scorecard
from pumpscore.model import LayerScore, Scorecard


def test_yaml_round_trip(tmp_path: Path) -> None:
    card = Scorecard("TEST", {"narrative": LayerScore("narrative", 12)})
    path = tmp_path / "card.yaml"
    save_scorecard(card, path)
    loaded = load_scorecard(path)
    assert loaded.token == "TEST"
    assert loaded.layers["narrative"].points == 12
    assert loaded.layers["social"].points == 0


def test_json_round_trip(tmp_path: Path) -> None:
    card = Scorecard("TEST", {"social": LayerScore("social", 14)}, mcap_usd=100.0)
    path = tmp_path / "card.json"
    save_scorecard(card, path)
    loaded = load_scorecard(path)
    assert loaded.mcap_usd == 100.0
    assert loaded.layers["social"].points == 14


def test_card_from_dict_accepts_numeric_layers_and_missing_layers() -> None:
    card = card_from_dict({"token": "TEST", "layers": {"narrative": 10}})
    assert card.layers["narrative"].points == 10
    assert card.layers["catalyst"].points == 0


def test_blank_template_has_checklist_blocks() -> None:
    template = blank_template()
    assert "patterns" in template
    assert "red_flags" in template
