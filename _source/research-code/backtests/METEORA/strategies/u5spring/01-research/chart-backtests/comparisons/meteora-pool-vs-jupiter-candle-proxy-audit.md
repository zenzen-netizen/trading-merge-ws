# Meteora Pool Candle vs Jupiter Candle Proxy Audit

Date: 2026-07-19
Status: exploratory audit

## Question
Can Jupiter mint-level candles be used as a fallback proxy when a screened Meteora pool lacks enough pool-level candle history, especially for 30m research?

## Sources compared
1. Meteora-screened pools from:
   `/home/ubuntu/trading-research/backtests/METEORA/strategies/u5spring/01-research/chart-backtests/rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/filtered-top20-sol-30m-fee-tvl-age15h-mcap250k-vol10pct.json`
2. Existing Meteora/GeckoTerminal pool OHLCV cache files in the experiment folder.
3. Jupiter-backed mint candle feed used by Meridian chart-indicator API:
   `https://api.agentmeridian.xyz/api/chart-indicators/{mint}`
   with response meta showing `source: jupiter`.

## What Meridian actually uses
- Pool screening: Meteora pool discovery (`pool-discovery-api.datapi.meteora.ag`)
- Token intel: Jupiter Data API
- Chart indicator candles: Meridian API `chart-indicators/{mint}`
- Verified from live response metadata: the chart indicator candle source is `jupiter`

So a mixed model is already real in Meridian architecture:
- discover/select pool on Meteora
- read indicator candle behavior from a mint-level Jupiter-backed source

## Availability audit
Per sampled top-20 filtered pools:
- Meteora 30m pool candles: median `10` rows, max `10`
- Jupiter 15m mint candles: median `298` rows, max `298`
- Jupiter-derived 30m (aggregate from 15m): median `149` rows, max `149`

This is the main practical advantage of the Jupiter proxy path:
- Meteora 30m is too shallow for backtest use right now
- Jupiter-backed 15m is often deep enough that a derived 30m series is possible

## Shape comparison methodology
Because pool candles and mint candles can differ by price scale/quote convention, comparison used two views:
1. raw return-shape agreement
2. scale-adjusted close-path agreement

Metrics used:
- return correlation
- same-direction % per candle
- median close difference after scaling Jupiter to Meteora level
- RSI(2) mean absolute difference
- agreement of `close > EMA50`
- supertrend direction agreement

## 15m comparison — pools with meaningful overlap
Only pools with >= 50 overlapping candles are useful for judging shape.

| Pool | Overlap | Scale-adjusted median close diff | Return corr | Same dir | RSI(2) mean abs diff | Close>EMA50 agree | Supertrend agree |
|---|---:|---:|---:|---:|---:|---:|---:|
| BULLCAT-SOL [7D7T92] | 269 | 1.232% | 0.9374 | 89.9% | 6.01 | 95.2% | 95.5% |
| BULLCAT-SOL [AFFuFY] | 212 | 0.933% | 0.8058 | 90.0% | 6.18 | 98.6% | 91.0% |
| Mouse-SOL [FbBGvD] | 108 | 2.603% | 0.9693 | 82.2% | 6.43 | 98.1% | 100.0% |
| BISCOTTI-SOL [Ft5Cxg] | 175 | 1.910% | 0.9414 | 90.8% | 6.25 | 96.6% | 94.9% |
| Tilly-SOL [BMi3TK] | 129 | 1.874% | 0.9139 | 94.5% | 4.70 | 94.6% | 88.4% |
| Mouse-SOL [12yWMg] | 86 | 2.016% | 0.9513 | 88.2% | 6.58 | 100.0% | 73.3% |
| TOESCOIN-SOL [CpKbsv] | 107 | 0.856% | 0.8026 | 76.4% | 10.84 | 96.3% | 86.0% |
| BULLCAT-SOL [3smCBC] | 257 | 3.201% | 0.8367 | 82.0% | 10.06 | 94.2% | 83.3% |
| JTVO-SOL [5rtYzK] | 237 | 0.888% | 0.9199 | 80.5% | 11.37 | 93.2% | 98.7% |
| SOLdiers-SOL [6iL24Y] | 292 | 0.985% | 0.9823 | 89.0% | 6.17 | 99.0% | 91.4% |
| USWR-SOL [qf3ExN] | 292 | 0.484% | 0.7932 | 66.0% | 23.00 | 66.1% | 82.2% |
| NEEGY-SOL [9mZ2tE] | 124 | 1.636% | 0.9132 | 83.7% | 5.56 | 99.2% | 93.5% |
| febu-SOL [2CVnAQ] | 264 | 1.574% | 0.8622 | 84.8% | 10.79 | 95.8% | 89.4% |

Takeaway from 15m:
- After scale normalization, many pools sit around ~0.5% to ~3.2% median close-path difference.
- Return correlation is usually high (`~0.80` to `~0.98`).
- `close > EMA50` agreement is often very high (`~93%` to `100%`).
- Supertrend direction agreement is often high too, though weaker on some names.
- RSI(2) can diverge more than trend-state metrics on some names.

## 30m proxy check
Where Meteora 30m existed at all (usually only 9–10 rows), Jupiter 15m was aggregated into synthetic 30m and compared over the same recent window.

| Pool | Meteora 30m rows | Jup-derived 30m rows | Overlap | Scale-adjusted median close diff | Return corr | Same dir |
|---|---:|---:|---:|---:|---:|---:|
| BULLCAT-SOL [7D7T92] | 10 | 148 | 10 | 0.791% | 0.9795 | 100.0% |
| BULLCAT-SOL [AFFuFY] | 10 | 148 | 10 | 0.513% | 0.9642 | 100.0% |
| Mouse-SOL [FbBGvD] | 10 | 60 | 10 | 2.045% | 0.9832 | 77.8% |
| BISCOTTI-SOL [Ft5Cxg] | 10 | 94 | 10 | 1.599% | 0.9233 | 100.0% |
| Tilly-SOL [BMi3TK] | 10 | 107 | 10 | 1.354% | 0.9401 | 100.0% |
| Mouse-SOL [12yWMg] | 10 | 60 | 10 | 0.907% | 0.9912 | 88.9% |
| TOESCOIN-SOL [CpKbsv] | 9 | 148 | 9 | 1.017% | 0.6306 | 75.0% |
| BULLCAT-SOL [3smCBC] | 10 | 148 | 10 | 2.428% | 0.7025 | 77.8% |
| JTVO-SOL [5rtYzK] | 10 | 129 | 9 | 0.464% | 0.8481 | 62.5% |
| SOLdiers-SOL [6iL24Y] | 10 | 148 | 10 | 1.233% | 0.9443 | 66.7% |
| NEEGY-SOL [9mZ2tE] | 10 | 148 | 10 | 1.301% | 0.9844 | 100.0% |
| febu-SOL [2CVnAQ] | 10 | 148 | 10 | 1.240% | 0.9045 | 55.6% |

30m recent-window summary:
- Median scale-adjusted close diff: `1.2365%`
- Median return correlation: `0.9422`
- Median same-direction rate: `83.35%`

## Interpretation
### What looks promising
If the backtest thesis is mainly about:
- price behavior
- RSI / EMA / Supertrend / fractal-style structure
- directional/trend-state timing

then the Jupiter-backed mint candle path looks plausibly usable as a fallback proxy when pool-level 30m is missing.

Why:
- shape similarity is often fairly high
- trend-state agreement is often high
- data depth is dramatically better than current Meteora 30m

### What does NOT transfer cleanly
A Jupiter mint candle is still NOT the same thing as a specific Meteora DLMM pool candle.
It does not directly encode pool-specific microstructure such as:
- pool-local execution quirks
- pool-local liquidity distortions
- fee / IL / active-liquidity behavior
- exact pool-only price dislocations if a particular pool temporarily trades away from broader token price

### Practical meaning for this project
Given the current backtest design, this matters less than it would for a full LP economics simulator, because the current chart backtest is mostly about candle behavior + indicator response, not fee/IL path modeling.

So the mixed approach is technically defensible as an explicit proxy model:
- pool selection / screening from Meteora
- indicator candle history from Jupiter-backed mint series when pool history is too shallow

## Caveats
- One live Jupiter-backed fetch returned a transient `502` during audit; availability is better than Meteora 30m but not perfect.
- Very short-lived pools still may not have enough Jupiter history either.
- Some pools showed weaker same-direction or RSI alignment, so this should not be called a perfect substitute.

## Bottom line
For the current stage of this research, Jupiter-backed mint candles appear good enough to test as a fallback proxy for missing Meteora 30m pool candles, provided the workflow is explicitly labeled as a proxy-price backtest rather than a pure pool-candle backtest.

Recommended next step:
- build a proxy mode in the backtester:
  - first try canonical pool candles
  - if 30m pool history is insufficient, fall back to Jupiter-backed mint candles (or Jupiter-derived 30m from 15m)
  - record the candle source used per pool/TF in summary and trade journal outputs
