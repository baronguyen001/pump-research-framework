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
