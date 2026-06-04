from pumpscore.checklist import PATTERNS, RED_FLAGS, evaluate_checklist


def test_checklist_strong_threshold() -> None:
    patterns = {key: i < 8 for i, (key, _) in enumerate(PATTERNS)}
    result = evaluate_checklist(patterns, {})
    assert result.verdict == "STRONG"
    assert result.patterns_hit == 8


def test_checklist_watchlist_threshold() -> None:
    patterns = {key: i < 6 for i, (key, _) in enumerate(PATTERNS)}
    result = evaluate_checklist(patterns, {})
    assert result.verdict == "WATCHLIST"


def test_checklist_caution_overrides_patterns() -> None:
    patterns = {key: True for key, _ in PATTERNS}
    red_flags = {RED_FLAGS[0][0]: True}
    result = evaluate_checklist(patterns, red_flags)
    assert result.verdict == "CAUTION"
    assert result.flagged == [RED_FLAGS[0][0]]


def test_checklist_unknown_keys_ignored() -> None:
    result = evaluate_checklist({"unknown": True}, {"unknown": True})
    assert result.patterns_hit == 0
    assert result.red_flags_hit == 0
    assert result.verdict == "PASS"
