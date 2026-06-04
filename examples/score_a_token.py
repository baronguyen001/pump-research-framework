from pumpscore import evaluate_checklist, goldilocks_gate, score, suggest_size
from pumpscore.io import _read_mapping, load_scorecard


def main() -> None:
    path = "examples/scorecard_example.yaml"
    raw = _read_mapping(path)
    card = load_scorecard(path)
    scored = score(card)
    checklist = evaluate_checklist(raw.get("patterns", {}), raw.get("red_flags", {}))
    gate = goldilocks_gate(card)
    size = suggest_size(card.total(), bankroll=10_000, asset_class="midcap")

    print(f"{scored['token']}: {scored['total']}/100 ({scored['band']})")
    print(f"Checklist: {checklist.verdict} ({checklist.patterns_hit}/10 patterns)")
    print(f"Goldilocks: {gate.passes}")
    print(f"Educational size cap: ${size['usd']}")


if __name__ == "__main__":
    main()
