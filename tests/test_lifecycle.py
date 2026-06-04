from pumpscore.lifecycle import StageSignals, classify_stage, fomo_decision, goldilocks_gate
from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard


def card(layers: dict[str, LayerScore] | None = None, **kwargs: object) -> Scorecard:
    active_layers = layers or {name: LayerScore(name, 20) for name in LAYER_NAMES}
    defaults = {
        "pumped_x_30d": 2.0,
        "funding_rate_8h": 0.01,
        "catalyst_days_out": 30,
    }
    defaults.update(kwargs)
    return Scorecard(
        "TEST",
        active_layers,
        pumped_x_30d=defaults["pumped_x_30d"],
        funding_rate_8h=defaults["funding_rate_8h"],
        catalyst_days_out=defaults["catalyst_days_out"],
    )


def test_goldilocks_all_pass() -> None:
    result = goldilocks_gate(card())
    assert result.passes
    assert all(result.checks.values())


def test_goldilocks_each_check_flips() -> None:
    assert not goldilocks_gate(card(layers={"narrative": LayerScore("narrative", 10)})).checks[
        "macro_confirm"
    ]
    low_catalyst_layers = {name: LayerScore(name, 20) for name in LAYER_NAMES}
    low_catalyst_layers["catalyst"] = LayerScore("catalyst", 10)
    assert not goldilocks_gate(card(layers=low_catalyst_layers)).checks["meso_confirm"]
    low_micro_layers = {name: LayerScore(name, 20) for name in LAYER_NAMES}
    low_micro_layers["social"] = LayerScore("social", 10)
    assert not goldilocks_gate(card(layers=low_micro_layers)).checks["micro_confirm"]
    assert not goldilocks_gate(card(pumped_x_30d=6.0)).checks["not_too_hot"]
    assert not goldilocks_gate(card(catalyst_days_out=120)).checks["has_catalyst"]


def test_fomo_decision_branches() -> None:
    assert (
        fomo_decision(card(layers={name: LayerScore(name, 10) for name in LAYER_NAMES})) == "SKIP"
    )
    assert fomo_decision(card(pumped_x_30d=6.0)) == "WAIT_PULLBACK"
    assert fomo_decision(card(funding_rate_8h=0.06)) == "SKIP"
    assert fomo_decision(card(catalyst_days_out=None)) == "WATCH"
    assert fomo_decision(card()) == "ENTER_30"


def test_classify_stage_rules() -> None:
    assert classify_stage(StageSignals()) == "seed"
    assert classify_stage(StageSignals(smart_wallets_7d=3)) == "whisper"
    assert classify_stage(StageSignals(google_trends_rising=True)) == "public_awareness"
    assert (
        classify_stage(StageSignals(google_trends_rising=True, tier1_kol_covering=True))
        == "mainstream"
    )
    assert (
        classify_stage(
            StageSignals(mainstream_media=True, tier1_kol_covering=True, mention_rate_wow=400)
        )
        == "euphoria"
    )
    assert classify_stage(StageSignals(down_from_ath_pct=80)) == "collapse"
