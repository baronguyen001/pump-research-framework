"""Offline scoring helpers for the pump research framework.

The deterministic core (model, score, checklist, lifecycle, sizing, io, report)
is pure stdlib + pyyaml and never touches the network. The narrative finder is
opt-in and isolated; importing this package does not make any request.
"""

from pumpscore.backtest import (
    BacktestError,
    CaseRow,
    StrategyStats,
    backtest,
    read_cases,
    summarize,
)
from pumpscore.checklist import ChecklistResult, evaluate_checklist
from pumpscore.compare import compare_cards, format_comparison
from pumpscore.lifecycle import StageSignals, classify_stage, fomo_decision, goldilocks_gate
from pumpscore.model import LAYER_NAMES, LayerScore, Scorecard
from pumpscore.narrative import (
    NarrativeError,
    NarrativeRow,
    fetch_narratives,
    format_csv,
    format_json,
    parse_coingecko,
    parse_defillama,
    rank_narratives,
    rows_to_dicts,
)
from pumpscore.report import render_from_card_dict, render_html, render_markdown
from pumpscore.score import Band, band_for, score, weighted_total
from pumpscore.sizing import scale_in_plan, suggest_size, tp_ladder

__all__ = [
    "Band",
    "BacktestError",
    "CaseRow",
    "ChecklistResult",
    "LAYER_NAMES",
    "LayerScore",
    "NarrativeError",
    "NarrativeRow",
    "Scorecard",
    "StageSignals",
    "StrategyStats",
    "backtest",
    "band_for",
    "classify_stage",
    "compare_cards",
    "evaluate_checklist",
    "fetch_narratives",
    "fomo_decision",
    "format_comparison",
    "format_csv",
    "format_json",
    "goldilocks_gate",
    "parse_coingecko",
    "parse_defillama",
    "rank_narratives",
    "read_cases",
    "render_from_card_dict",
    "render_html",
    "render_markdown",
    "rows_to_dicts",
    "scale_in_plan",
    "score",
    "suggest_size",
    "summarize",
    "tp_ladder",
    "weighted_total",
]
