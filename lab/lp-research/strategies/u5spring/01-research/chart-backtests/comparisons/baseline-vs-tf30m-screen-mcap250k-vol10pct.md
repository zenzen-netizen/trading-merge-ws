# Baseline vs TF30m Backtest + Screen MCAP250k + Vol10pct

Status: rerun completed after pool-name collision fix
Date: 2026-07-19

Integrity note
- This note supersedes the earlier 2026-07-19 figures.
- Root issue found: same-name pools were being keyed by `pool` name instead of `pool_address` in both OHLCV cache filenames and summary grouping.
- Effect of the bug:
  - distinct pools with the same token symbol could reuse the wrong cache file
  - summary rows could merge different pool addresses into one name bucket
- Fix applied before this rerun:
  - cache files now include pool-address key material
  - summary grouping now keys by `pool_address`
  - baseline and experiment were rerun from the patched scripts

Interpretation lock
- This experiment has two separate `30m` meanings:
  1. screening universe stays sourced from Meteora `timeframe=30m`
  2. backtest also tries `30m` as one TF candidate
- So this remains the user's intended mixed experiment, not a screening-only rewrite.

Baseline
- Canonical path: `../rsi-fractal-mhermes-be/`
- Fresh rerun source: `/home/ubuntu/trading-research/backtests/METEORA/POOL_DISCOVERY/rsi_fractal_backtest_mhermes_be/`
- Summary rows: 408
- Family-best rows (pool × tf × sl): 102
- Total simulated trades: 2984
- Positive family-best rows: 42 / 102
- Pools represented: 20

Experiment variant
- Path: `../rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/`
- Summary rows: 296
- Family-best rows (pool × tf × sl): 74
- Total simulated trades: 6232
- Positive family-best rows: 44 / 74
- Pools represented: 13

What changed
- Screening source stayed at Meteora `timeframe=30m`
- Added screen: `base_token_market_cap >= 250000`
- Added screen: `volume_tvl_ratio >= 0.10`
- Kept age floor 15h, SOL-only, exclude USDC
- Kept ranking focus: fee/TVL-first universe
- Backtest tried TFs: `1m`, `5m`, `15m`, `30m`
- Kept core U5Spring backtest rule, SL families, BE families, metrics structure

Execution reality
- `1m`, `5m`, `15m` produced usable backtest rows
- `30m` fetch path was attempted as intended
- But fetched `30m` series still stayed far too short for EMA50 + fractal warmup
- Result: `summary.csv` still contains zero final `30m` rows

Aggregate comparison by timeframe (family-best median SumR)
- Baseline 15m: `0.0000`
- Experiment 15m: `+0.0338`
- Baseline 1m: `0.0000`
- Experiment 1m: `+0.4233`
- Baseline 5m: `-0.0653`
- Experiment 5m: `+0.5151`

Aggregate comparison by timeframe (positive family-best rows)
- 15m: baseline `11/34` -> experiment `11/22`
- 1m: baseline `16/34` -> experiment `17/26`
- 5m: baseline `15/34` -> experiment `16/26`
- 30m: no valid rows yet

Interpretation by lens

Lens A — screening effect
- After the address-keying fix, the stricter pool screen still improves the quality of the surviving universe on the usable verdict TFs.
- Median family-best SumR improved on all three usable TFs: `15m`, `1m`, and `5m`.
- Breadth clearly narrowed: pool count fell from 20 to 13.
- Even with that narrower breadth, positive family-best rows rose slightly in absolute count: 42 -> 44.

Lens B — 30m backtest effect
- `30m` was part of the intended experiment and was actually attempted again in the clean rerun.
- Current `30m` history depth is still not enough to clear warmup requirements.
- Therefore this run still does NOT prove or disprove `30m`; it only shows `30m` is not yet testable with the currently fetched datasets.

Correct verdict
- Screening filter verdict: still promising after the clean rerun
- `30m` backtest verdict: intended and attempted, but still not evidence-bearing
- Family verdict: still valid inside `u5spring/`; no need for a new family
- Propagation verdict:
  - `01-research`: yes
  - `02-thesis`: only tentative note about stricter screening so far
  - `03-operator` / `04-meridian` / `05-payloads`: not yet

Follow-up structure
- Main experiment remains this mixed design, because it matches user intent.
- Auxiliary follow-up `...-usabletf/` remains only a secondary lens to isolate screening effect, not a replacement for the main experiment definition.

Files
- Canonical baseline summary: `../rsi-fractal-mhermes-be/summary.csv`
- Canonical baseline report: `../rsi-fractal-mhermes-be/report.md`
- Experiment report: `../rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/report.md`
- Experiment summary: `../rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/summary.csv`
- Experiment trade journal: `../rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/trade-journal.csv`
- Auxiliary screening-only lens: `../rsi-fractal-mhermes-be-screen-mcap250k-vol10pct-usabletf/`
