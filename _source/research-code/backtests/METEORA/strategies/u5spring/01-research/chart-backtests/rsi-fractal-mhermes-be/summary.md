# RSI Fractal mHermes BE Backtest — Rerun Summary

Integrity note: this baseline was rerun after fixing Meteora duplicate-name collisions by keying cache and grouping on `pool_address` instead of pool display name.

- sample pools: 20
- strategy rows: 408
- family-best rows (pool × tf × sl): 102
- positive family-best rows: 42

## Best-mode frequency (family best)
- BE1: 60/102
- BE50: 21/102
- BE75: 11/102
- TP_FRACTAL: 10/102

## Per-TF family-best view
- 1m: 16/34 positive, median SumR +0.000
- 5m: 15/34 positive, median SumR -0.065
- 15m: 11/34 positive, median SumR +0.000
