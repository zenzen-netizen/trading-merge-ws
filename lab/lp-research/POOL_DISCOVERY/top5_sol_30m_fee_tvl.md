# Meteora raw discovery — SOL pairs, 30m, top 5 by fee/TVL

Source: `https://pool-discovery-api.datapi.meteora.ag/pools?page_size=1000&timeframe=30m&category=top`
Rule: only pools involving SOL; exclude USDC pairs; sort by fee_active_tvl_ratio desc; take top 5.

| # | Pool | Pair | Address | Fee/TVL | TVL | Volume | Volatility | H / Mcap |
|---|------|------|---------|---------|-----|--------|------------|----------|
| 1 | AFKHERO-SOL | AFKHERO/SOL | `6tF7ZzgAMLVdvkLtqYe2sLq27MJ6jT2CVkS1QohYvus3` | 173.091017 | 689.42 | 125.93 | 0.0000 | 4279 / 77631.41 |
| 2 | CXMT-SOL | CXMT/SOL | `3foaoyPDUQfmNHe7N9HdGjoxf66X5ZAy73x7qgLBx6QT` | 32.690426 | 16.07 | 7.54 | 136.3598 | 50 / 108931.46 |
| 3 | TOLY-SOL | TOLY/SOL | `2URheDFSeGmzDyh1NJBEXHSRDZtLvuzeAmj7pXTK1tmf` | 15.444902 | 0.56 | 2.42 | 5.9978 | 632 / 24312.87 |
| 4 | DEXBULL-SOL | DEXBULL/SOL | `6kbEH79zCW3R4w6DCNvZoPMBkLWQPgfaoD1jveiKwXAB` | 7.508294 | 6.91 | 16.88 | 0.7036 | 3244 / 37739.20 |
| 5 | BABYANSEM-SOL | BABYANSEM/SOL | `5TfEn12FKqSWi8ewWdKKRhmmPQq8pB3ZazS66iFVDpai` | 4.352500 | 188.45 | 34.44 | 1.8828 | 656 / 17071.21 |

- Total raw pools from API: 240374
- SOL-pair candidates after filter: 478
- Next step: define backtest mechanics for these 5 pools.