from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard
from pumpscore.score import band_for, score, weighted_total


def make_card(points: float) -> Scorecard:
    return Scorecard("TEST", {name: LayerScore(name, points) for name in LAYER_NAMES})


def test_layer_points_clamp_to_range() -> None:
    assert LayerScore("narrative", -5).points == 0
    assert LayerScore("social", 30).points == 25


def test_total_missing_layers_treated_as_zero() -> None:
    card = Scorecard("TEST", {"narrative": LayerScore("narrative", 10)})
    assert card.total() == 10


def test_weighted_total_normalizes_perfect_card() -> None:
    card = make_card(25)
    assert weighted_total(card, {"narrative": 5, "social": 1, "onchain": 0, "catalyst": 2}) == 100


def test_weighted_total_ignores_unknown_weight_keys() -> None:
    card = make_card(25)
    assert weighted_total(card, {"unknown": 999}) == 100


def test_band_boundaries() -> None:
    assert band_for(39.99).label == "IGNORE"
    assert band_for(40).label == "WATCH"
    assert band_for(60).label == "SMALL"
    assert band_for(75).label == "MEDIUM"
    assert band_for(90).label == "HIGH_CONVICTION"


def test_score_shape() -> None:
    result = score(make_card(20))
    assert result["total"] == 80
    assert result["band"] == "MEDIUM"
    assert result["per_layer"] == {
        "narrative": 20.0,
        "social": 20.0,
        "onchain": 20.0,
        "catalyst": 20.0,
    }
