# Changelog

## v0.2.0 - 2026-06-10

- Added an opt-in, keyless current-narrative finder (`pumpscore narratives`)
  that ranks hot categories by momentum from the public CoinGecko and DefiLlama
  category endpoints. Read-only, no API keys, no scraping; degrades to a clear
  message when offline. Network code is isolated in `narrative.py` and gated
  behind the new `[net]` extra.
- Added per-strategy backtest stubs (`pumpscore backtest cases.csv`) over a user
  CSV of public, fictional case outcomes. Deterministic and offline; reports
  hit-rate, median multiple, survivorship-adjusted hit-rate, and honesty caveats
  for each A/B/C/D/E strategy. Ships `examples/cases_example.csv`.
- Added a self-contained HTML scorecard (`pumpscore report CARD.yaml` and
  `pumpscore score CARD.yaml --html out.html`). Pure string templating, no
  JavaScript, four-layer bars plus checklist, lifecycle, and sizing panels.
- Bumped version to 0.2.0 and added the optional `[net]` dependency extra.
- The deterministic core stays pure stdlib + pyyaml, offline, and keyless.

## v0.1.0 - 2026-06-04

- Initial public framework: four signal layers, lifecycle, strategy variants,
  limitations, case studies, and generic risk playbook.
- Added `pumpscore`, an offline deterministic scorecard CLI.
- Added tests, CI, notebook smoke check, and fictional examples.

## Roadmap

- v0.2: optional keyless current-narrative finder using public category APIs.
- v0.2: per-strategy backtest stubs with explicit data limitations.
- v0.3: static HTML or Streamlit scorecard UI.
