"""Per-strategy backtest stubs over a user CSV of public case outcomes.

Deterministic and offline. Reads a CSV of *public, after-the-fact* case
outcomes and produces simple, honest aggregates per strategy (A/B/C/D/E from
``framework/strategies.md``): hit rate, median multiple, and a
survivorship-adjusted hit rate. These are stubs, not an edge. Every result ships
with caveats because the inputs are hand-collected, survivorship-biased, and
small. The point is to make the limitations of a "backtest" explicit, not to
manufacture confidence.

Expected CSV columns (header required):

    strategy,token,entry_date,multiple,flagged_by_framework,survived

* ``strategy``            one of A, B, C, D, E (case-insensitive)
* ``token``               label only; never a real position
* ``entry_date``          ISO date string, informational
* ``multiple``            realized multiple of the entry value (e.g. 2.5)
* ``flagged_by_framework`` whether the framework would have flagged it (yes/no)
* ``survived``            whether the token still trades / was not a rug (yes/no)

A "hit" is a multiple >= ``hit_threshold`` (default 2.0). The
survivorship-adjusted hit rate counts rows that did *not* survive as misses,
which lowers optimistic numbers from movers-only datasets.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import median

STRATEGY_LABELS: dict[str, str] = {
    "A": "Pre-listing CEX play",
    "B": "Smart-wallet copy",
    "C": "Narrative rotation",
    "D": "Airdrop farming",
    "E": "Memecoin micro-bet",
}

REQUIRED_COLUMNS: tuple[str, ...] = (
    "strategy",
    "token",
    "entry_date",
    "multiple",
    "flagged_by_framework",
    "survived",
)

_TRUE_TOKENS = {"1", "true", "yes", "y", "t"}
_FALSE_TOKENS = {"0", "false", "no", "n", "f", ""}

DEFAULT_HIT_THRESHOLD = 2.0


class BacktestError(ValueError):
    """Raised when the CSV is malformed enough that math would be meaningless."""


@dataclass(frozen=True)
class CaseRow:
    strategy: str
    token: str
    entry_date: str
    multiple: float
    flagged_by_framework: bool
    survived: bool


@dataclass(frozen=True)
class StrategyStats:
    strategy: str
    label: str
    n: int
    hit_rate: float
    median_multiple: float
    survival_rate: float
    survivorship_adjusted_hit_rate: float
    flagged_hit_rate: float | None
    caveats: list[str]


def _parse_bool(value: str, *, field: str, row_index: int) -> bool:
    token = value.strip().lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    raise BacktestError(f"Row {row_index}: field '{field}' is not a yes/no value: {value!r}")


def _parse_float(value: str, *, field: str, row_index: int) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise BacktestError(f"Row {row_index}: field '{field}' is not a number: {value!r}") from exc
    if result != result or result in (float("inf"), float("-inf")):
        raise BacktestError(f"Row {row_index}: field '{field}' must be finite: {value!r}")
    if result < 0:
        raise BacktestError(f"Row {row_index}: '{field}' must be non-negative: {value!r}")
    return result


def parse_rows(reader: list[dict[str, str]]) -> list[CaseRow]:
    """Validate and coerce raw CSV dict rows into ``CaseRow`` records. Pure."""
    rows: list[CaseRow] = []
    for offset, raw in enumerate(reader, start=2):  # row 1 is the header
        strategy = str(raw.get("strategy", "")).strip().upper()
        if strategy not in STRATEGY_LABELS:
            allowed = ", ".join(sorted(STRATEGY_LABELS))
            raise BacktestError(
                f"Row {offset}: unknown strategy {strategy!r}. Use one of: {allowed}"
            )
        rows.append(
            CaseRow(
                strategy=strategy,
                token=str(raw.get("token", "")).strip(),
                entry_date=str(raw.get("entry_date", "")).strip(),
                multiple=_parse_float(
                    str(raw.get("multiple", "")), field="multiple", row_index=offset
                ),
                flagged_by_framework=_parse_bool(
                    str(raw.get("flagged_by_framework", "")),
                    field="flagged_by_framework",
                    row_index=offset,
                ),
                survived=_parse_bool(
                    str(raw.get("survived", "")), field="survived", row_index=offset
                ),
            )
        )
    return rows


def read_cases(path: str | Path) -> list[CaseRow]:
    """Read and validate a cases CSV from disk. Offline, stdlib csv only."""
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None:
        raise BacktestError("CSV is empty; a header row is required")
    header = {name.strip() for name in reader.fieldnames}
    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise BacktestError("CSV is missing required columns: " + ", ".join(missing))
    return parse_rows(list(reader))


def _safe_rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator, 4)


def _caveats(n: int, survival_rate: float) -> list[str]:
    notes = [
        "Hand-collected, after-the-fact outcomes; survivorship bias is likely.",
        "Not out-of-sample and not an edge. Treat as a sanity check, not a forecast.",
    ]
    if n < 10:
        notes.append(f"Sample is tiny (n={n}); a single row swings every percentage.")
    if survival_rate < 1.0:
        notes.append("Some rows did not survive; the raw hit rate over-counts winners.")
    return notes


def summarize(
    rows: list[CaseRow], hit_threshold: float = DEFAULT_HIT_THRESHOLD
) -> list[StrategyStats]:
    """Aggregate per-strategy stats over parsed rows. Pure and deterministic."""
    if hit_threshold <= 0:
        raise BacktestError("hit_threshold must be positive")
    stats: list[StrategyStats] = []
    for key in sorted(STRATEGY_LABELS):
        bucket = [row for row in rows if row.strategy == key]
        n = len(bucket)
        if n == 0:
            continue
        hits = sum(1 for row in bucket if row.multiple >= hit_threshold)
        survived = sum(1 for row in bucket if row.survived)
        survivorship_hits = sum(
            1 for row in bucket if row.multiple >= hit_threshold and row.survived
        )
        flagged = [row for row in bucket if row.flagged_by_framework]
        flagged_hits = sum(1 for row in flagged if row.multiple >= hit_threshold)
        survival_rate = _safe_rate(survived, n)
        stats.append(
            StrategyStats(
                strategy=key,
                label=STRATEGY_LABELS[key],
                n=n,
                hit_rate=_safe_rate(hits, n),
                median_multiple=round(median(row.multiple for row in bucket), 4),
                survival_rate=survival_rate,
                survivorship_adjusted_hit_rate=_safe_rate(survivorship_hits, n),
                flagged_hit_rate=(_safe_rate(flagged_hits, len(flagged)) if flagged else None),
                caveats=_caveats(n, survival_rate),
            )
        )
    return stats


def backtest(path: str | Path, hit_threshold: float = DEFAULT_HIT_THRESHOLD) -> list[StrategyStats]:
    """Read a cases CSV and return per-strategy stats. Offline end to end."""
    return summarize(read_cases(path), hit_threshold=hit_threshold)


def format_report(stats: list[StrategyStats], hit_threshold: float = DEFAULT_HIT_THRESHOLD) -> str:
    """Render per-strategy stats as a plain-text report. Pure, offline."""
    lines = [
        f"Per-strategy backtest stub (hit = multiple >= {hit_threshold:g}x)",
        "",
    ]
    if not stats:
        lines.append("No rows matched any known strategy (A-E).")
        return "\n".join(lines) + "\n"
    lines.append(
        f"{'Strat':<6} {'N':>4} {'Hit%':>7} {'Median':>8} "
        f"{'Surv%':>7} {'AdjHit%':>8} {'FlagHit%':>9}"
    )
    lines.append(f"{'-' * 6} {'-' * 4} {'-' * 7} {'-' * 8} {'-' * 7} {'-' * 8} {'-' * 9}")
    for stat in stats:
        flagged = "n/a" if stat.flagged_hit_rate is None else f"{stat.flagged_hit_rate:.0%}"
        lines.append(
            f"{stat.strategy:<6} {stat.n:>4} {stat.hit_rate:>7.0%} "
            f"{stat.median_multiple:>7.2f}x {stat.survival_rate:>7.0%} "
            f"{stat.survivorship_adjusted_hit_rate:>8.0%} {flagged:>9}"
        )
    lines.append("")
    lines.append("Legend: " + ", ".join(f"{k}={v}" for k, v in STRATEGY_LABELS.items()))
    lines.append("")
    lines.append("Caveats:")
    seen: set[str] = set()
    for stat in stats:
        for note in stat.caveats:
            if note not in seen:
                seen.add(note)
                lines.append(f"- {note}")
    return "\n".join(lines) + "\n"
