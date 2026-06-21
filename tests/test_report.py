from pathlib import Path

from pumpscore.io import _read_mapping, card_from_dict
from pumpscore.model import LayerScore, Scorecard
from pumpscore.report import render_from_card_dict, render_html, render_markdown

FIXTURE = Path("examples/scorecard_example.yaml")


def test_render_html_is_well_formed() -> None:
    card = Scorecard(
        "TEST",
        {name: LayerScore(name, 20) for name in ("narrative", "social", "onchain", "catalyst")},
    )
    out = render_html(card)
    assert out.startswith("<!doctype html>")
    assert out.strip().endswith("</html>")
    assert out.count("<body>") == 1
    assert out.count("</body>") == 1
    assert "TEST" in out
    # 80/100 -> MEDIUM band.
    assert "MEDIUM" in out


def test_render_from_card_dict_includes_panels() -> None:
    raw = _read_mapping(FIXTURE)
    card = card_from_dict(raw)
    out = render_from_card_dict(raw, card)
    assert "FICTIONAL_RWA_AGENT" in out
    assert "Checklist" in out
    assert "Lifecycle" in out
    assert "Educational sizing" in out
    assert "Take-profit ladder" in out
    # Checklist verdict from the example card is STRONG.
    assert "STRONG" in out
    # No JavaScript dependency.
    assert "<script" not in out.lower()


def test_render_escapes_token_label() -> None:
    card = Scorecard("<script>x</script>", {"narrative": LayerScore("narrative", 10)})
    out = render_html(card)
    assert "<script>x</script>" not in out
    assert "&lt;script&gt;" in out


def test_render_handles_missing_checklist_and_stage() -> None:
    card = Scorecard("BARE", {"narrative": LayerScore("narrative", 5)})
    out = render_from_card_dict({"token": "BARE", "layers": {"narrative": 5}}, card)
    assert "not provided" in out
    # Stage falls back to 'unknown' when no signals present.
    assert "unknown" in out


def test_bars_present_for_all_layers() -> None:
    card = Scorecard(
        "TEST",
        {name: LayerScore(name, 25) for name in ("narrative", "social", "onchain", "catalyst")},
    )
    out = render_html(card)
    for label in ("Narrative", "Social", "Onchain", "Catalyst"):
        assert label in out


def test_render_markdown_structure() -> None:
    card = Scorecard(
        "MDTEST",
        {name: LayerScore(name, 20) for name in ("narrative", "social", "onchain", "catalyst")},
    )
    out = render_markdown(card)
    assert out.startswith("# pumpscore - MDTEST")
    assert "**80/100 - MEDIUM**" in out
    assert "| Layer | Points |" in out
    assert "not financial advice" in out
    # no HTML tags in markdown output
    assert "<div" not in out


def test_render_from_card_dict_markdown_includes_context() -> None:
    raw = _read_mapping(FIXTURE)
    card = card_from_dict(raw)
    out = render_from_card_dict(raw, card, fmt="markdown")
    assert out.startswith("# pumpscore - FICTIONAL_RWA_AGENT")
    assert "## Checklist" in out
    assert "## Lifecycle" in out
