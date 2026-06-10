"""Command line interface for pumpscore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

import yaml

from pumpscore.backtest import BacktestError, backtest, format_report
from pumpscore.checklist import PATTERNS, RED_FLAGS, evaluate_checklist
from pumpscore.io import _read_mapping, blank_template, card_from_dict, load_scorecard
from pumpscore.lifecycle import StageSignals, classify_stage, fomo_decision, goldilocks_gate
from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard
from pumpscore.narrative import SOURCES, NarrativeError, fetch_narratives, format_table
from pumpscore.report import render_from_card_dict
from pumpscore.score import score
from pumpscore.sizing import scale_in_plan, suggest_size, tp_ladder


def _parse_weights(value: str | None) -> dict[str, float] | None:
    if not value:
        return None
    weights: dict[str, float] = {}
    for part in value.split(","):
        if not part.strip():
            continue
        key, sep, raw = part.partition("=")
        if not sep:
            raise argparse.ArgumentTypeError("Weights must use layer=value pairs")
        weights[key.strip()] = float(raw)
    return weights


def _print_score(result: dict[str, object]) -> None:
    print(f"Token: {result['token']}")
    print(f"Total: {result['total']}/100")
    print(f"Band: {result['band']}")
    print(f"Action: {result['action']}")
    print("")
    print("Layer        Points")
    print("-------------------")
    per_layer = result["per_layer"]
    assert isinstance(per_layer, dict)
    for name in LAYER_NAMES:
        print(f"{name:<12} {per_layer.get(name, 0.0):>6}")


def _interactive_card() -> Scorecard:
    print("Enter 0..25 points for each layer. Leave blank for 0.")
    layers: dict[str, LayerScore] = {}
    token = input("Token label: ").strip() or "INTERACTIVE_TOKEN"
    for name in LAYER_NAMES:
        raw = input(f"{name} points: ").strip() or "0"
        notes = input(f"{name} notes: ").strip()
        layers[name] = LayerScore(name=name, points=float(raw), notes=notes)
    return Scorecard(token=token, layers=layers)


def cmd_template(args: argparse.Namespace) -> int:
    data = blank_template()
    text = (
        json.dumps(data, indent=2) + "\n"
        if args.format == "json"
        else yaml.safe_dump(data, sort_keys=False)
    )
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(text, end="")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    weights = _parse_weights(args.weights)
    if args.interactive:
        card = _interactive_card()
        raw: dict[str, Any] = {}
    else:
        raw = _read_mapping(args.card)
        card = card_from_dict(raw)
    _print_score(score(card, weights))
    if getattr(args, "html", None):
        html_text = render_from_card_dict(raw, card, weights)
        Path(args.html).write_text(html_text, encoding="utf-8")
        print("")
        print(f"Wrote HTML scorecard to {args.html}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    raw = _read_mapping(args.card)
    card = card_from_dict(raw)
    html_text = render_from_card_dict(raw, card, _parse_weights(args.weights))
    if args.out:
        Path(args.out).write_text(html_text, encoding="utf-8")
        print(f"Wrote HTML scorecard to {args.out}")
    else:
        print(html_text, end="")
    return 0


def cmd_narratives(args: argparse.Namespace) -> int:
    try:
        rows = fetch_narratives(source=args.source, top=args.top)
    except NarrativeError as exc:
        print(f"Narrative finder unavailable: {exc}", file=sys.stderr)
        print(
            "This is the only opt-in network feature. Install the extra with "
            "'pip install pump-research-framework[net]' and retry when online.",
            file=sys.stderr,
        )
        return 2
    print(format_table(rows, args.source), end="")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    try:
        stats = backtest(args.cases, hit_threshold=args.hit_threshold)
    except BacktestError as exc:
        print(f"Backtest input error: {exc}", file=sys.stderr)
        return 2
    print(format_report(stats, hit_threshold=args.hit_threshold), end="")
    return 0


def cmd_checklist(args: argparse.Namespace) -> int:
    raw = _read_mapping(args.card)
    patterns = raw.get("patterns", {})
    red_flags = raw.get("red_flags", {})
    if not isinstance(patterns, dict) or not isinstance(red_flags, dict):
        raise ValueError("patterns and red_flags must be mappings")
    result = evaluate_checklist(
        {str(key): bool(value) for key, value in patterns.items()},
        {str(key): bool(value) for key, value in red_flags.items()},
    )
    print(f"Patterns hit: {result.patterns_hit}/10")
    print(f"Red flags hit: {result.red_flags_hit}/7")
    print(f"Verdict: {result.verdict}")
    if result.flagged:
        print("Flagged: " + ", ".join(result.flagged))
    print("")
    print("Patterns")
    for key, label in PATTERNS:
        mark = "yes" if bool(patterns.get(key, False)) else "no"
        print(f"- {mark:<3} {key}: {label}")
    print("")
    print("Red flags")
    for key, label in RED_FLAGS:
        mark = "yes" if bool(red_flags.get(key, False)) else "no"
        print(f"- {mark:<3} {key}: {label}")
    return 0


def _stage_signals(raw: dict[str, Any]) -> StageSignals:
    data = raw.get("stage_signals", {})
    if not isinstance(data, dict):
        data = {}
    return StageSignals(
        mention_rate_wow=_maybe_float(data.get("mention_rate_wow")),
        smart_wallets_7d=_maybe_int(data.get("smart_wallets_7d")),
        google_trends_rising=_maybe_bool(data.get("google_trends_rising")),
        tier1_kol_covering=_maybe_bool(data.get("tier1_kol_covering")),
        mainstream_media=_maybe_bool(data.get("mainstream_media")),
        down_from_ath_pct=_maybe_float(data.get("down_from_ath_pct")),
    )


def _maybe_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, str | int | float):
        return float(value)
    raise ValueError("Expected a numeric value")


def _maybe_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, str | int | float):
        return int(value)
    raise ValueError("Expected an integer value")


def _maybe_bool(value: object) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def cmd_stage(args: argparse.Namespace) -> int:
    raw = _read_mapping(args.card)
    card = card_from_dict(raw)
    stage = classify_stage(_stage_signals(raw))
    gate = goldilocks_gate(card)
    decision = fomo_decision(card)
    print(f"Stage: {stage}")
    print(f"Goldilocks: {'PASS' if gate.passes else 'FAIL'}")
    for key, ok in gate.checks.items():
        print(f"- {key}: {'yes' if ok else 'no'}")
    if gate.reasons:
        print("Missing: " + ", ".join(gate.reasons))
    print(f"Decision: {decision}")
    return 0


def cmd_size(args: argparse.Namespace) -> int:
    card = load_scorecard(args.card)
    total = card.total()
    sub_500m = True if card.mcap_usd is None else card.mcap_usd < 500_000_000
    size = suggest_size(total, args.bankroll, args.asset_class, sub_500m_mcap=sub_500m)
    pct = cast(float, size["pct"])
    usd = cast(float, size["usd"])
    print(f"Band: {size['band']}")
    print(f"Suggested cap: {pct:.2%} = ${usd}")
    print(size["note"])
    print("")
    print("Scale-in plan")
    for row in scale_in_plan(usd):
        print(f"- T{row['tranche']}: {row['pct']:.0%} = ${row['usd']} | {row['trigger']}")
    print("")
    print("Take-profit ladder")
    for row in tp_ladder(args.entry_price, usd):
        print(
            f"- {row['multiple']}: target={row['target_price']} "
            f"sell={row['sell_frac']:.0%} entry_value=${row['sell_usd_at_entry_value']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pumpscore",
        description="Offline scorecard companion for the pump research framework.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    template = sub.add_parser("template", help="Write a blank scorecard")
    template.add_argument("--out")
    template.add_argument("--format", choices=["yaml", "json"], default="yaml")
    template.set_defaults(func=cmd_template)

    score_cmd = sub.add_parser("score", help="Score a card")
    score_cmd.add_argument("card", nargs="?")
    score_cmd.add_argument("--weights")
    score_cmd.add_argument("--interactive", action="store_true")
    score_cmd.add_argument("--html", help="Also write a standalone HTML scorecard to this path")
    score_cmd.set_defaults(func=cmd_score)

    report = sub.add_parser("report", help="Render a standalone HTML scorecard")
    report.add_argument("card")
    report.add_argument("--out", help="Write HTML here instead of stdout")
    report.add_argument("--weights")
    report.set_defaults(func=cmd_report)

    narratives = sub.add_parser(
        "narratives",
        help="Opt-in: rank hot narratives from public category APIs (needs network)",
    )
    narratives.add_argument("--source", choices=list(SOURCES), default="coingecko")
    narratives.add_argument("--top", type=int, default=15)
    narratives.set_defaults(func=cmd_narratives)

    backtest_cmd = sub.add_parser(
        "backtest", help="Per-strategy backtest stubs over a public cases CSV"
    )
    backtest_cmd.add_argument("cases")
    backtest_cmd.add_argument("--hit-threshold", type=float, default=2.0)
    backtest_cmd.set_defaults(func=cmd_backtest)

    checklist = sub.add_parser("checklist", help="Evaluate patterns and red flags")
    checklist.add_argument("card")
    checklist.set_defaults(func=cmd_checklist)

    stage = sub.add_parser("stage", help="Classify lifecycle and anti-FOMO gate")
    stage.add_argument("card")
    stage.set_defaults(func=cmd_stage)

    size = sub.add_parser("size", help="Print educational sizing ladders")
    size.add_argument("card")
    size.add_argument("--bankroll", type=float, required=True)
    size.add_argument("--asset-class", choices=["memecoin", "midcap", "largecap"], default="midcap")
    size.add_argument("--entry-price", type=float, default=1.0)
    size.set_defaults(func=cmd_size)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "score" and not args.interactive and not args.card:
        parser.error("score requires CARD unless --interactive is used")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
