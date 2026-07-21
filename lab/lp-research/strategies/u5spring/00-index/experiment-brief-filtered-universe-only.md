# U5Spring Experiment Brief — Filtered Universe Only (Auxiliary Lens)

## 1. Identity
- Experiment name: `filtered-universe-only`
- Date: 2026-07-19
- Owner / agent: Hermes-Server
- Status: `re-executed as auxiliary follow-up after pool-name collision fix`

## 2. Purpose
- This is NOT the original canonical interpretation of the user's experiment ask.
- It was created as an auxiliary follow-up lens after the main mixed experiment hit insufficient `30m` candle depth.
- Current artifacts supersede the earlier same-day run because the backtest scripts were patched to key cache/summary data by `pool_address`, not just pool name.
- Purpose:
  - isolate screening effect only
  - keep the same stricter universe
  - remove `30m` from the verdict layer temporarily

## 3. Relation to the main experiment
- Main intended experiment:
  - screening universe sourced from Meteora `timeframe=30m`
  - backtest also tries `30m` as one TF candidate
- This auxiliary follow-up:
  - keeps screening source on Meteora `30m`
  - keeps the same stricter filter set
  - but evaluates only `1m`, `5m`, `15m`
- Therefore this file is a secondary analytical lens, not a replacement for the main experiment brief.

## 4. Main question
- If we hold the stricter screen constant and temporarily exclude untestable `30m` verdict rows, does the surviving universe still look healthier on usable TFs?

## 5. Scope
- What changes from the main experiment:
  - evaluation restricted to `1m`, `5m`, `15m`
- What stays fixed:
  - screening source still Meteora `timeframe=30m`
  - market cap filter
  - volume/tvl filter
  - age floor
  - SOL-only / exclude USDC
  - entry logic
  - TP logic
  - SL families
  - BE families
  - metrics format

## 6. Evaluation role
- This follow-up is valid only for:
  - isolating the screening effect
  - checking whether the positive signal survives after removing `30m` from the verdict layer
- This follow-up is NOT valid for:
  - redefining the user's original experiment intent
  - concluding anything positive or negative about `30m` backtest

## 7. Paths
- Main experiment path:
  - `/home/ubuntu/trading-research/backtests/METEORA/strategies/u5spring/01-research/chart-backtests/rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/`
- Auxiliary experiment path:
  - `/home/ubuntu/trading-research/backtests/METEORA/strategies/u5spring/01-research/chart-backtests/rsi-fractal-mhermes-be-screen-mcap250k-vol10pct-usabletf/`
- Auxiliary comparison note path:
  - `/home/ubuntu/trading-research/backtests/METEORA/strategies/u5spring/01-research/chart-backtests/comparisons/baseline-vs-screen-mcap250k-vol10pct-usabletf.md`

## 8. Metrics / evaluation
- Primary metrics:
  - family-best `sum_R`
  - median family-best `sum_R` per TF
  - positive family-best rows per TF
- Secondary metrics:
  - trade count
  - pool breadth
  - win rate resolved
  - BE dependence

## 9. Guardrail note
- Keep this brief clearly labeled as auxiliary.
- Do not let another agent mistake this as the user's canonical experiment definition.
