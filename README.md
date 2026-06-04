# Pump Research Framework

[![CI](https://github.com/baronguyen001/pump-research-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/baronguyen001/pump-research-framework/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Why does a token 100x, and why do most not? This repo is a four-layer research
framework for narrative, social, on-chain, and catalyst evidence, distilled from
public case studies of winners and failures. It also ships `pumpscore`, a small
offline tool for scoring a token by hand.

![Four-layer framework](screenshots/framework_diagram.png)

This is research infrastructure, not alpha. It is not financial advice, not an
automated signal service, not a price-call list, and not a wallet list. The point
is to make a decision process explicit enough that you can challenge it.

## What is inside

- [framework/](framework/) explains the four layers, the lifecycle, strategy
  variants, and the limitations.
- [case_studies/](case_studies/) groups public market history into reusable
  patterns and counterexamples.
- [playbook/](playbook/) covers sizing, entries, exits, wallet hygiene, and
  anti-FOMO rules.
- [src/pumpscore/](src/pumpscore/) provides a deterministic local scorer with
  no network calls and no secrets.

## Four layers

| Layer | Question |
|---|---|
| Narrative | Is capital rotating into this category before the crowd notices? |
| Social | Is attention rising organically without looking like paid spam? |
| On-chain | Are holders, liquidity, and wallet behavior healthy? |
| Catalyst | Is there a dated event that can pull attention into the token? |

The default band table is intentionally simple:

| Score | Band | Default reading |
|---:|---|---|
| 0-40 | Ignore | Too little evidence. |
| 40-60 | Watch | Re-score later. |
| 60-75 | Small | Small risk budget only. |
| 75-90 | Medium | Stronger confluence, still capped. |
| 90-100 | High conviction | Strong case, never all-in. |

These bands are starting points for calibration. They are not a tuned edge.

## Quickstart

```bash
pip install pump-research-framework
pumpscore --help
```

From a checkout:

```bash
pip install -e ".[dev]"
pumpscore score examples/scorecard_example.yaml
pumpscore checklist examples/scorecard_example.yaml
pumpscore stage examples/scorecard_example.yaml
pumpscore size examples/scorecard_example.yaml --bankroll 10000
```

Example output is based on a fictional token:

![Pumpscore CLI output](screenshots/scorecard_cli.png)

Create a blank scorecard:

```bash
pumpscore template --out card.yaml
```

Then fill in the four layer scores, pattern checklist, red flags, and context
fields from your own research.

## The honest part

Most "alpha" writeups stop at the winners. This repo keeps the uncomfortable
pieces: survivorship bias, hindsight bias, memecoins that move before any
framework can catch them, and the 5/30 anti-FOMO rule that can also kill fast
runners. Read [limitations.md](framework/limitations.md) before using any score.

## Public case studies

The case-study library includes public examples such as SHIB, PEPE, WIF, BONK,
SOL, JUP, HYPE, VIRTUAL, and AI16Z, plus failure or dump cases such as ICP,
LayerZero and EigenLayer airdrop pressure, and the 2025 AI-agent drawdown. All
figures are approximate and sourced from public reports or market history at the
time of writing.

## Pair it with the portfolio

- [wallet-cluster-detector](https://github.com/baronguyen001/wallet-cluster-detector):
  the on-chain layer implemented as an open-source case study.
- [confluence-scanner](https://github.com/baronguyen001/confluence-scanner):
  the multi-factor scoring pattern for market signals.
- [Trawlkit](https://github.com/baronguyen001/Trawlkit): the private paid kit
  for building a live scrape-to-AI-to-alert workflow.
- [ai-automation-skills](https://github.com/baronguyen001/ai-automation-skills):
  free automation skills that feed the same funnel.

## Disclaimer

Crypto assets are high risk. This repo is educational software and public
research only. Backtests, case studies, and score bands do not predict future
returns. Bring your own research, risk management, jurisdictional advice, and
tax records.

PyPI publish status: pending until a release token is available.
