# How To Use This Repo

1. Pick a token or category to research.
2. Read the four layer docs in `framework/`.
3. Fill `playbook/scorecard_template.md` or run:

```bash
pumpscore template --out card.yaml
```

4. Score only what you can support with public evidence.
5. Run:

```bash
pumpscore score card.yaml
pumpscore checklist card.yaml
pumpscore stage card.yaml
pumpscore size card.yaml --bankroll 10000
```

6. Read `framework/limitations.md` before acting on any score.

The result is a structured research note, not a command to trade.

For automation, use this as a design brief for Trawlkit and validate every
source, threshold, and false-positive mode yourself.
