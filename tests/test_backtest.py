from pathlib import Path

import pytest

from pumpscore.backtest import (
    BacktestError,
    backtest,
    format_report,
    parse_rows,
    read_cases,
    summarize,
)

EXAMPLE = Path("examples/cases_example.csv")


def test_example_csv_parses() -> None:
    rows = read_cases(EXAMPLE)
    assert len(rows) == 15
    strategies = {row.strategy for row in rows}
    assert strategies == {"A", "B", "C", "D", "E"}


def test_summary_math_for_strategy_e() -> None:
    stats = {s.strategy: s for s in backtest(EXAMPLE)}
    e = stats["E"]
    # E rows: multiples 12, 0, 1, 8 -> hits (>=2x): 12 and 8 = 2/4 = 0.5
    assert e.n == 4
    assert e.hit_rate == 0.5
    # median of [12, 0, 1, 8] = (1 + 8) / 2 = 4.5
    assert e.median_multiple == 4.5
    # survived: 12, 1, 8 survived; the rug (0) did not -> 3/4
    assert e.survival_rate == 0.75
    # survivorship-adjusted hits: both 12x and 8x survived -> 2/4 = 0.5
    assert e.survivorship_adjusted_hit_rate == 0.5


def test_threshold_changes_hit_rate() -> None:
    low = {s.strategy: s for s in backtest(EXAMPLE, hit_threshold=2.0)}["A"]
    high = {s.strategy: s for s in backtest(EXAMPLE, hit_threshold=3.5)}["A"]
    # A multiples: 2.4, 1.1, 3.0. At 2.0x -> 2 hits. At 3.5x -> 0 hits.
    assert low.hit_rate > high.hit_rate
    assert high.hit_rate == 0.0


def test_flagged_hit_rate_present() -> None:
    a = {s.strategy: s for s in backtest(EXAMPLE)}["A"]
    # flagged A rows: 2.4 (yes) and 3.0 (yes) -> both hit -> 2/2 = 1.0
    assert a.flagged_hit_rate == 1.0


def test_small_sample_caveat_added() -> None:
    stats = backtest(EXAMPLE)
    for stat in stats:
        if stat.n < 10:
            assert any("tiny" in c for c in stat.caveats)


def test_missing_columns_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("strategy,token\nA,X\n", encoding="utf-8")
    with pytest.raises(BacktestError, match="missing required columns"):
        read_cases(bad)


def test_empty_csv_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(BacktestError, match="header"):
        read_cases(empty)


def test_unknown_strategy_raises() -> None:
    with pytest.raises(BacktestError, match="unknown strategy"):
        parse_rows(
            [
                {
                    "strategy": "Z",
                    "token": "X",
                    "entry_date": "2024-01-01",
                    "multiple": "2",
                    "flagged_by_framework": "no",
                    "survived": "yes",
                }
            ]
        )


def test_bad_number_raises() -> None:
    with pytest.raises(BacktestError, match="not a number"):
        parse_rows(
            [
                {
                    "strategy": "A",
                    "token": "X",
                    "entry_date": "2024-01-01",
                    "multiple": "abc",
                    "flagged_by_framework": "no",
                    "survived": "yes",
                }
            ]
        )


def test_bad_bool_raises() -> None:
    with pytest.raises(BacktestError, match="yes/no"):
        parse_rows(
            [
                {
                    "strategy": "A",
                    "token": "X",
                    "entry_date": "2024-01-01",
                    "multiple": "2",
                    "flagged_by_framework": "maybe",
                    "survived": "yes",
                }
            ]
        )


def test_negative_multiple_raises() -> None:
    with pytest.raises(BacktestError, match="non-negative"):
        parse_rows(
            [
                {
                    "strategy": "A",
                    "token": "X",
                    "entry_date": "2024-01-01",
                    "multiple": "-1",
                    "flagged_by_framework": "no",
                    "survived": "yes",
                }
            ]
        )


def test_summarize_empty_rows() -> None:
    assert summarize([]) == []


def test_summarize_bad_threshold() -> None:
    with pytest.raises(BacktestError):
        summarize([], hit_threshold=0.0)


def test_format_report_contains_strategies_and_caveats() -> None:
    report = format_report(backtest(EXAMPLE))
    assert "Per-strategy backtest stub" in report
    assert "Memecoin micro-bet" in report
    assert "Caveats:" in report
    assert "survivorship bias" in report.lower()


def test_format_report_empty() -> None:
    assert "No rows matched" in format_report([])
