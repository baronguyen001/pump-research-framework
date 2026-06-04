"""Position-size and ladder helpers for educational planning."""

from __future__ import annotations

from pumpscore.score import band_for

SCALE_IN: tuple[float, ...] = (0.30, 0.30, 0.25, 0.15)
TP_LADDER: tuple[tuple[float, float], ...] = ((2.0, 0.25), (5.0, 0.25), (10.0, 0.25))

ASSET_CAPS: dict[str, float] = {"memecoin": 0.03, "midcap": 0.05, "largecap": 0.10}
HARD_CAP_SUB_500M: float = 0.08

_BAND_SCALE: dict[str, float] = {
    "IGNORE": 0.0,
    "WATCH": 0.0,
    "SMALL": 0.40,
    "MEDIUM": 0.75,
    "HIGH_CONVICTION": 1.0,
}

_TRIGGERS = (
    "Initial score clears the entry gate and the thesis is written down.",
    "Price action confirms trend or volume expands with no new red flag.",
    "Catalyst becomes official or on-chain confirmation improves.",
    "Breakout confirms and the pre-written invalidation still holds.",
)


def suggest_size(
    total: float,
    bankroll: float,
    asset_class: str = "midcap",
    sub_500m_mcap: bool = True,
) -> dict[str, object]:
    if bankroll < 0:
        raise ValueError("Bankroll must be non-negative")
    if asset_class not in ASSET_CAPS:
        allowed = ", ".join(sorted(ASSET_CAPS))
        raise ValueError(f"Unknown asset_class. Use one of: {allowed}")
    band = band_for(total)
    cap = ASSET_CAPS[asset_class]
    if sub_500m_mcap:
        cap = min(cap, HARD_CAP_SUB_500M)
    pct = round(cap * _BAND_SCALE[band.label], 4)
    usd = round(bankroll * pct, 2)
    return {
        "asset_class": asset_class,
        "pct": pct,
        "usd": usd,
        "band": band.label,
        "note": "Educational sizing cap only; not financial advice.",
    }


def scale_in_plan(target_size_usd: float) -> list[dict[str, object]]:
    if target_size_usd < 0:
        raise ValueError("Target size must be non-negative")
    plan: list[dict[str, object]] = []
    allocated = 0.0
    for index, pct in enumerate(SCALE_IN, start=1):
        usd = round(target_size_usd * pct, 2)
        if index == len(SCALE_IN):
            usd = round(target_size_usd - allocated, 2)
        allocated += usd
        plan.append(
            {
                "tranche": index,
                "pct": pct,
                "usd": usd,
                "trigger": _TRIGGERS[index - 1],
            }
        )
    return plan


def tp_ladder(
    entry_price: float,
    position_size_usd: float,
    ladder: tuple[tuple[float, float], ...] = TP_LADDER,
) -> list[dict[str, object]]:
    if entry_price <= 0:
        raise ValueError("Entry price must be positive")
    if position_size_usd < 0:
        raise ValueError("Position size must be non-negative")
    rows: list[dict[str, object]] = []
    sold_frac = 0.0
    for multiple, sell_frac in ladder:
        sold_frac += sell_frac
        rows.append(
            {
                "multiple": multiple,
                "target_price": round(entry_price * multiple, 10),
                "sell_frac": sell_frac,
                "sell_usd_at_entry_value": round(position_size_usd * sell_frac, 2),
                "note": "Take profit rung.",
            }
        )
    runner_frac = max(0.0, round(1.0 - sold_frac, 4))
    rows.append(
        {
            "multiple": "runner",
            "target_price": None,
            "sell_frac": runner_frac,
            "sell_usd_at_entry_value": round(position_size_usd * runner_frac, 2),
            "note": "Trail the remaining position with the invalidation plan.",
        }
    )
    return rows
