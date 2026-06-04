"""Structured pattern and red-flag checklist."""

from __future__ import annotations

from dataclasses import dataclass

PATTERNS: list[tuple[str, str]] = [
    ("hot_narrative_early", "Narrative is heating up before mainstream coverage."),
    ("small_starting_mcap", "Market cap is still small enough for asymmetric upside."),
    ("healthy_holder_distribution", "Top holders are not concentrated outside known venues."),
    ("liquidity_growing", "DEX liquidity is sufficient and trending up."),
    ("volume_mcap_accumulation", "Volume to market-cap ratio suggests accumulation."),
    ("smart_money_present", "Tracked profitable wallets or funds are present."),
    ("organic_mid_tier_social", "Mid-tier social accounts discuss it organically."),
    ("tier2_before_tier1", "Tier-2 CEX access exists before tier-1 listing."),
    ("active_development", "Developers or team are shipping visible work."),
    ("clear_30_90d_catalyst", "A clear catalyst exists inside 30 to 90 days."),
]

RED_FLAGS: list[tuple[str, str]] = [
    ("top10_over_50pct", "Top 10 holders control more than 50 percent."),
    ("liquidity_unlocked", "Liquidity is unlocked or too short-lived."),
    ("anon_team_sketchy_funding", "Anonymous team with low-quality funding signals."),
    ("single_venue_wash_volume", "Volume appears concentrated on one venue or wash-like."),
    ("large_unlock_or_emissions", "Large unlock or emissions arrive soon."),
    ("already_50x_week", "Token already ran more than 50x in less than a week."),
    ("paid_promo_social", "Social traffic is mostly paid promotion or spam."),
]


@dataclass(frozen=True)
class ChecklistResult:
    patterns_hit: int
    red_flags_hit: int
    verdict: str
    flagged: list[str]


def evaluate_checklist(patterns: dict[str, bool], red_flags: dict[str, bool]) -> ChecklistResult:
    known_patterns = {key for key, _ in PATTERNS}
    known_flags = {key for key, _ in RED_FLAGS}
    patterns_hit = sum(1 for key in known_patterns if bool(patterns.get(key, False)))
    flagged = [
        key for key, _ in RED_FLAGS if key in known_flags and bool(red_flags.get(key, False))
    ]
    red_flags_hit = len(flagged)
    if red_flags_hit:
        verdict = "CAUTION"
    elif patterns_hit >= 8:
        verdict = "STRONG"
    elif patterns_hit >= 6:
        verdict = "WATCHLIST"
    else:
        verdict = "PASS"
    return ChecklistResult(
        patterns_hit=patterns_hit,
        red_flags_hit=red_flags_hit,
        verdict=verdict,
        flagged=flagged,
    )
