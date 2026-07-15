import json
from pathlib import Path

import pytest
import yaml

from pumpscore.cli import main

FIXTURE = Path("examples/scorecard_example.yaml")


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "template" in capsys.readouterr().out


def test_cli_template_stdout_yaml(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["template"]) == 0
    data = yaml.safe_load(capsys.readouterr().out)
    assert data["token"] == "FICTIONAL_TOKEN"


def test_cli_template_file_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "card.json"
    assert main(["template", "--format", "json", "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["layers"]["narrative"]["points"] == 0
    assert "Wrote" in capsys.readouterr().out


def test_cli_score(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["score", str(FIXTURE), "--weights", "narrative=2,social=1"]) == 0
    out = capsys.readouterr().out
    assert "FICTIONAL_RWA_AGENT" in out
    assert "Band: MEDIUM" in out


def test_cli_score_requires_card() -> None:
    with pytest.raises(SystemExit):
        main(["score"])


def test_cli_checklist(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["checklist", str(FIXTURE)]) == 0
    assert "Verdict: STRONG" in capsys.readouterr().out


def test_cli_stage(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["stage", str(FIXTURE)]) == 0
    out = capsys.readouterr().out
    assert "Goldilocks: PASS" in out
    assert "Decision: ENTER_30" in out


def test_cli_size(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["size", str(FIXTURE), "--bankroll", "10000", "--entry-price", "2"]) == 0
    out = capsys.readouterr().out
    assert "Suggested cap: 3.75%" in out
    assert "target=4.0" in out


def test_cli_score_html(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_html = tmp_path / "card.html"
    assert main(["score", str(FIXTURE), "--html", str(out_html)]) == 0
    assert "Wrote HTML scorecard" in capsys.readouterr().out
    text = out_html.read_text(encoding="utf-8")
    assert text.startswith("<!doctype html>")
    assert "FICTIONAL_RWA_AGENT" in text


def test_cli_report_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["report", str(FIXTURE)]) == 0
    out = capsys.readouterr().out
    assert "<!doctype html>" in out
    assert "Educational sizing" in out


def test_cli_report_to_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_html = tmp_path / "report.html"
    assert main(["report", str(FIXTURE), "--out", str(out_html)]) == 0
    assert "Wrote HTML scorecard" in capsys.readouterr().out
    assert out_html.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_cli_backtest(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["backtest", "examples/cases_example.csv"]) == 0
    out = capsys.readouterr().out
    assert "Per-strategy backtest stub" in out
    assert "Caveats:" in out


def test_cli_backtest_bad_csv(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("strategy,token\nA,X\n", encoding="utf-8")
    assert main(["backtest", str(bad)]) == 2
    assert "input error" in capsys.readouterr().err


def test_cli_narratives_degrades_gracefully(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Simulate being offline: the network entry point raises NarrativeError.
    from pumpscore import cli
    from pumpscore.narrative import NarrativeError

    def _boom(*args: object, **kwargs: object) -> object:
        raise NarrativeError("Could not reach the narrative source.")

    monkeypatch.setattr(cli, "fetch_narratives", _boom)
    assert main(["narratives"]) == 2
    err = capsys.readouterr().err
    assert "Narrative finder unavailable" in err
    assert "opt-in" in err


def test_cli_narratives_renders_with_stub(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from pumpscore import cli
    from pumpscore.narrative import NarrativeRow

    rows = [NarrativeRow("Test Narrative", 5.0, 9.0, 1_000_000_000.0, "coingecko")]
    monkeypatch.setattr(cli, "fetch_narratives", lambda **kwargs: rows)
    assert main(["narratives", "--top", "5"]) == 0
    out = capsys.readouterr().out
    assert "Test Narrative" in out
    assert "not a buy signal" in out


def test_cli_narratives_json_and_csv(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from pumpscore import cli
    from pumpscore.narrative import NarrativeRow

    rows = [NarrativeRow("Test Narrative", 5.0, 9.0, 1_000_000_000.0, "coingecko")]
    monkeypatch.setattr(cli, "fetch_narratives", lambda **kwargs: rows)
    assert main(["narratives", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["name"] == "Test Narrative"
    assert main(["narratives", "--format", "csv"]) == 0
    assert "rank,name,change_24h" in capsys.readouterr().out


def test_cli_compare_ranks(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["compare", str(FIXTURE), str(FIXTURE), "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert "# Scorecard comparison" in out
    assert "FICTIONAL_RWA_AGENT" in out


def test_cli_compare_to_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_file = tmp_path / "cmp.json"
    assert main(["compare", str(FIXTURE), "--format", "json", "--out", str(out_file)]) == 0
    assert "Wrote comparison" in capsys.readouterr().out
    assert json.loads(out_file.read_text(encoding="utf-8"))[0]["token"] == "FICTIONAL_RWA_AGENT"


def test_cli_explain_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["explain", str(FIXTURE), "--weights", "narrative=2", "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert "# Score explanation - FICTIONAL_RWA_AGENT" in out
    assert "Highest-leverage layer" in out


def test_cli_explain_to_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_file = tmp_path / "explain.json"
    assert main(["explain", str(FIXTURE), "--format", "json", "--out", str(out_file)]) == 0
    assert "Wrote explanation" in capsys.readouterr().out
    assert json.loads(out_file.read_text(encoding="utf-8"))["token"] == "FICTIONAL_RWA_AGENT"


def test_cli_sensitivity_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sensitivity", str(FIXTURE), "--format", "text"]) == 0
    out = capsys.readouterr().out
    assert "Sensitivity analysis for FICTIONAL_RWA_AGENT" in out
    assert "Swings are mechanical" in out


def test_cli_sensitivity_to_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_file = tmp_path / "sensitivity.json"
    assert main(["sensitivity", str(FIXTURE), "--format", "json", "--out", str(out_file)]) == 0
    assert "Wrote sensitivity analysis" in capsys.readouterr().out
    parsed = json.loads(out_file.read_text(encoding="utf-8"))
    assert parsed["token"] == "FICTIONAL_RWA_AGENT"
    assert len(parsed["rows"]) == 4


def test_cli_export_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["export", str(FIXTURE), "--weights", "catalyst=2"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("token,total,band,action")
    assert "FICTIONAL_RWA_AGENT" in out


def test_cli_export_to_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_file = tmp_path / "row.json"
    assert main(["export", str(FIXTURE), "--format", "json", "--out", str(out_file)]) == 0
    assert "Wrote export" in capsys.readouterr().out
    parsed = json.loads(out_file.read_text(encoding="utf-8"))
    assert parsed["token"] == "FICTIONAL_RWA_AGENT"
    assert parsed["patterns_hit"] == 9


def test_cli_score_markdown(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_md = tmp_path / "card.md"
    assert main(["score", str(FIXTURE), "--md", str(out_md)]) == 0
    assert "Wrote Markdown scorecard" in capsys.readouterr().out
    assert out_md.read_text(encoding="utf-8").startswith("# pumpscore - FICTIONAL_RWA_AGENT")


def test_cli_report_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["report", str(FIXTURE), "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# pumpscore - FICTIONAL_RWA_AGENT")
    assert "## Checklist" in out
