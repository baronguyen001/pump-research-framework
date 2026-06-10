"""Self-contained HTML scorecard renderer.

Pure string templating: no JavaScript, no external assets, no network. Given a
``Scorecard`` (and optional checklist / stage-signal context already parsed from
the same card file), produce a single standalone ``.html`` page with the
four-layer bars, the total and band, the checklist verdict, the lifecycle stage,
and the educational sizing plan. The output is deterministic and offline so it
can be diffed and tested.
"""

from __future__ import annotations

import html
from typing import Any, cast

from pumpscore.checklist import ChecklistResult, evaluate_checklist
from pumpscore.lifecycle import StageSignals, classify_stage, fomo_decision, goldilocks_gate
from pumpscore.model import LAYER_NAMES, Scorecard
from pumpscore.score import band_for, score
from pumpscore.sizing import scale_in_plan, suggest_size, tp_ladder

_LAYER_COLORS: dict[str, str] = {
    "narrative": "#6366f1",
    "social": "#0ea5e9",
    "onchain": "#10b981",
    "catalyst": "#f59e0b",
}

_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
       margin: 0; padding: 2rem; line-height: 1.5; background: #0f172a; color: #e2e8f0; }
.card { max-width: 760px; margin: 0 auto; background: #1e293b; border-radius: 14px;
        padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,.35); }
h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
.sub { color: #94a3b8; margin: 0 0 1.5rem; font-size: .9rem; }
.total { font-size: 2.6rem; font-weight: 700; }
.band { display: inline-block; padding: .25rem .75rem; border-radius: 999px;
        font-size: .8rem; font-weight: 600; letter-spacing: .03em; background: #334155; }
.layer { margin: .65rem 0; }
.layer .row { display: flex; justify-content: space-between;
              font-size: .9rem; margin-bottom: .25rem; }
.track { background: #334155; border-radius: 8px; height: 14px; overflow: hidden; }
.fill { height: 100%; border-radius: 8px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem; }
.panel { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 1rem; }
.panel h2 { margin: 0 0 .5rem; font-size: .95rem; color: #cbd5e1; }
.kv { display: flex; justify-content: space-between; font-size: .85rem; padding: .15rem 0; }
table { width: 100%; border-collapse: collapse; font-size: .82rem; margin-top: .4rem; }
th, td { text-align: left; padding: .3rem .35rem; border-bottom: 1px solid #334155; }
.note { color: #94a3b8; font-size: .78rem; margin-top: 1.5rem; }
.tag-yes { color: #34d399; } .tag-no { color: #64748b; } .tag-flag { color: #f87171; }
"""


def _bar(name: str, points: float) -> str:
    pct = max(0.0, min(100.0, (points / 25.0) * 100.0))
    color = _LAYER_COLORS.get(name, "#6366f1")
    return (
        '<div class="layer">'
        f'<div class="row"><span>{html.escape(name.title())}</span>'
        f"<span>{points:g} / 25</span></div>"
        f'<div class="track"><div class="fill" style="width:{pct:.1f}%;'
        f'background:{color};"></div></div>'
        "</div>"
    )


def _checklist_panel(checklist: ChecklistResult | None) -> str:
    if checklist is None:
        return (
            '<div class="panel"><h2>Checklist</h2>'
            '<div class="kv"><span>Status</span><span class="tag-no">not provided</span></div>'
            "</div>"
        )
    flagged = (
        f'<div class="kv"><span>Flagged</span><span class="tag-flag">'
        f"{html.escape(', '.join(checklist.flagged))}</span></div>"
        if checklist.flagged
        else ""
    )
    return (
        '<div class="panel"><h2>Checklist</h2>'
        f'<div class="kv"><span>Verdict</span><span>{html.escape(checklist.verdict)}</span></div>'
        f'<div class="kv"><span>Patterns hit</span><span>{checklist.patterns_hit}/10</span></div>'
        f'<div class="kv"><span>Red flags</span><span>{checklist.red_flags_hit}/7</span></div>'
        f"{flagged}</div>"
    )


def _stage_panel(stage: str, decision: str, goldilocks_pass: bool) -> str:
    gate = "PASS" if goldilocks_pass else "FAIL"
    gate_class = "tag-yes" if goldilocks_pass else "tag-flag"
    return (
        '<div class="panel"><h2>Lifecycle</h2>'
        f'<div class="kv"><span>Stage</span><span>{html.escape(stage)}</span></div>'
        f'<div class="kv"><span>Goldilocks</span><span class="{gate_class}">{gate}</span></div>'
        f'<div class="kv"><span>Anti-FOMO</span><span>{html.escape(decision)}</span></div>'
        "</div>"
    )


def _sizing_panel(sizing: dict[str, Any], plan: list[dict[str, Any]]) -> str:
    pct = float(sizing["pct"])
    usd = float(sizing["usd"])
    rows = "".join(
        f"<tr><td>T{row['tranche']}</td><td>{float(row['pct']):.0%}</td>"
        f"<td>${row['usd']:g}</td></tr>"
        for row in plan
    )
    return (
        '<div class="panel"><h2>Educational sizing</h2>'
        f'<div class="kv"><span>Band</span><span>{html.escape(str(sizing["band"]))}</span></div>'
        f'<div class="kv"><span>Suggested cap</span><span>{pct:.2%} = ${usd:g}</span></div>'
        "<table><thead><tr><th>Tranche</th><th>Share</th><th>USD</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )


def _tp_panel(ladder: list[dict[str, Any]]) -> str:
    cells = []
    for row in ladder:
        target = row["target_price"]
        target_text = "-" if target is None else f"{float(target):g}"
        cells.append(
            f"<tr><td>{html.escape(str(row['multiple']))}</td>"
            f"<td>{target_text}</td>"
            f"<td>{float(row['sell_frac']):.0%}</td></tr>"
        )
    rows = "".join(cells)
    return (
        '<div class="panel"><h2>Take-profit ladder</h2>'
        "<table><thead><tr><th>Multiple</th><th>Target</th><th>Sell</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )


def render_html(
    card: Scorecard,
    *,
    checklist: ChecklistResult | None = None,
    stage_signals: StageSignals | None = None,
    weights: dict[str, float] | None = None,
    bankroll_usd: float = 10_000.0,
    asset_class: str = "midcap",
    entry_price: float = 1.0,
) -> str:
    """Render a complete, standalone HTML scorecard string. Pure and offline."""
    result = score(card, weights)
    total = cast(float, result["total"])
    band = band_for(total)

    stage = classify_stage(stage_signals) if stage_signals is not None else "unknown"
    decision = fomo_decision(card)
    goldilocks = goldilocks_gate(card)

    sub_500m = True if card.mcap_usd is None else card.mcap_usd < 500_000_000
    sizing = suggest_size(total, bankroll_usd, asset_class, sub_500m_mcap=sub_500m)
    usd = cast(float, sizing["usd"])
    plan = scale_in_plan(usd)
    ladder = tp_ladder(entry_price, usd)

    bars = "".join(
        _bar(name, card.layers[name].points if name in card.layers else 0.0) for name in LAYER_NAMES
    )

    sub_line = (
        '<p class="sub">Offline pump-research scorecard. '
        "Educational only, not financial advice.</p>"
    )
    body = (
        '<div class="card">'
        f"<h1>{html.escape(card.token)}</h1>"
        f"{sub_line}"
        f'<div class="total">{total:g}<span style="font-size:1rem;color:#94a3b8">/100</span> '
        f'<span class="band">{html.escape(band.label)}</span></div>'
        f'<p class="sub">{html.escape(band.action)}</p>'
        f"{bars}"
        '<div class="grid">'
        f"{_checklist_panel(checklist)}"
        f"{_stage_panel(stage, decision, goldilocks.passes)}"
        f"{_sizing_panel(sizing, plan)}"
        f"{_tp_panel(ladder)}"
        "</div>"
        '<p class="note">Generated by pumpscore, the offline scorer in the public '
        "pump-research-framework. No network calls, no wallet data, no price calls. "
        "Bands are calibration starting points, not a tuned edge.</p>"
        "</div>"
    )

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>pumpscore scorecard - {html.escape(card.token)}</title>"
        f"<style>{_STYLE}</style></head><body>{body}</body></html>\n"
    )


def render_from_card_dict(
    raw: dict[str, Any],
    card: Scorecard,
    weights: dict[str, float] | None = None,
) -> str:
    """Convenience: build checklist + stage signals from a raw card mapping.

    Mirrors how the CLI parses a single scorecard file so the HTML report
    reflects the same patterns, red flags, and stage signals as the text output.
    """
    patterns_raw = raw.get("patterns")
    red_flags_raw = raw.get("red_flags")
    checklist: ChecklistResult | None = None
    if isinstance(patterns_raw, dict) or isinstance(red_flags_raw, dict):
        patterns = patterns_raw if isinstance(patterns_raw, dict) else {}
        red_flags = red_flags_raw if isinstance(red_flags_raw, dict) else {}
        checklist = evaluate_checklist(
            {str(k): bool(v) for k, v in patterns.items()},
            {str(k): bool(v) for k, v in red_flags.items()},
        )

    stage_signals: StageSignals | None = None
    sig_raw = raw.get("stage_signals")
    if isinstance(sig_raw, dict):
        stage_signals = StageSignals(
            mention_rate_wow=_opt_float(sig_raw.get("mention_rate_wow")),
            smart_wallets_7d=_opt_int(sig_raw.get("smart_wallets_7d")),
            google_trends_rising=_opt_bool(sig_raw.get("google_trends_rising")),
            tier1_kol_covering=_opt_bool(sig_raw.get("tier1_kol_covering")),
            mainstream_media=_opt_bool(sig_raw.get("mainstream_media")),
            down_from_ath_pct=_opt_float(sig_raw.get("down_from_ath_pct")),
        )

    plan_raw = raw.get("execution_plan", {})
    plan = plan_raw if isinstance(plan_raw, dict) else {}
    bankroll = _opt_float(plan.get("bankroll_usd")) or 10_000.0
    entry_price = _opt_float(plan.get("entry_price")) or 1.0
    asset_class = str(plan.get("asset_class") or "midcap")

    return render_html(
        card,
        checklist=checklist,
        stage_signals=stage_signals,
        weights=weights,
        bankroll_usd=bankroll,
        asset_class=asset_class,
        entry_price=entry_price,
    )


def _opt_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _opt_int(value: object) -> int | None:
    result = _opt_float(value)
    return None if result is None else int(result)


def _opt_bool(value: object) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
