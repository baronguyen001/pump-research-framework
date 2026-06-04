from pumpscore.sizing import ASSET_CAPS, scale_in_plan, suggest_size, tp_ladder


def test_suggest_size_respects_asset_cap_and_hard_cap() -> None:
    mid = suggest_size(92, 10_000, "midcap")
    assert mid["pct"] == ASSET_CAPS["midcap"]
    large_sub_500 = suggest_size(92, 10_000, "largecap", sub_500m_mcap=True)
    assert large_sub_500["pct"] == 0.08


def test_suggest_size_scales_by_band() -> None:
    assert suggest_size(50, 10_000, "midcap")["usd"] == 0
    assert suggest_size(65, 10_000, "midcap")["usd"] == 200
    assert suggest_size(80, 10_000, "midcap")["usd"] == 375


def test_scale_in_plan_sums_to_target() -> None:
    plan = scale_in_plan(1234.56)
    assert round(sum(float(row["usd"]) for row in plan), 2) == 1234.56
    assert [row["pct"] for row in plan] == [0.30, 0.30, 0.25, 0.15]


def test_tp_ladder_math() -> None:
    ladder = tp_ladder(2.0, 1000.0)
    assert ladder[0]["target_price"] == 4.0
    assert ladder[0]["sell_usd_at_entry_value"] == 250.0
    assert ladder[-1]["multiple"] == "runner"
    assert ladder[-1]["sell_frac"] == 0.25
