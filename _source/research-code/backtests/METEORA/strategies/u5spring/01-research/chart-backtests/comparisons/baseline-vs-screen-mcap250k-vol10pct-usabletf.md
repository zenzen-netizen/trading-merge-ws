# Baseline vs Screen MCAP250k + Vol10pct (Usable TF Only, Auxiliary Lens)

Status: rerun completed after pool-name collision fix
Date: 2026-07-19

Important positioning
- This note is an auxiliary analytical lens.
- It does NOT replace the main experiment definition.
- The user's intended main experiment remains:
  - screening universe sourced from Meteora `timeframe=30m`
  - backtest also tries `30m` as one TF candidate
- This auxiliary note only asks:
  - if `30m` verdict rows are temporarily excluded because of insufficient data depth, does the stricter screen still look stronger on `1m`, `5m`, `15m`?

Integrity note
- This auxiliary note also supersedes the earlier 2026-07-19 figures.
- Same root issue was fixed first: same-name pools had previously collided at cache/summary level because the scripts keyed by name instead of `pool_address`.
- Current numbers come from the patched reruns.

Compared paths
- Baseline: `../rsi-fractal-mhermes-be/`
- Main mixed experiment: `../rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/`
- Auxiliary clean lens: `../rsi-fractal-mhermes-be-screen-mcap250k-vol10pct-usabletf/`

Experiment summary
- Baseline summary rows: 408
- Auxiliary summary rows: 296
- Baseline total simulated trades: 2984
- Auxiliary total simulated trades: 6280
- Baseline pools represented: 20
- Auxiliary pools represented: 13
- Baseline family-best rows (pool × tf × sl): 102
- Auxiliary family-best rows (pool × tf × sl): 74
- Baseline positive family-best rows: 42
- Auxiliary positive family-best rows: 45

Per-TF comparison (family-best)

15m
- Baseline: 11 / 34 positive, median best SumR = `0.0000`, mean best SumR = `-0.3989`
- Auxiliary: 11 / 22 positive, median best SumR = `+0.0484`, mean best SumR = `+2.0879`

1m
- Baseline: 16 / 34 positive, median best SumR = `0.0000`, mean best SumR = `+0.2862`
- Auxiliary: 17 / 26 positive, median best SumR = `+0.4380`, mean best SumR = `+0.4481`

5m
- Baseline: 15 / 34 positive, median best SumR = `-0.0653`, mean best SumR = `-0.4843`
- Auxiliary: 17 / 26 positive, median best SumR = `+0.5151`, mean best SumR = `+2.4582`

What this auxiliary lens means
- After the clean rerun, the stricter pool screen still improves the research picture when the verdict is narrowed to usable TFs only.
- So the positive signal on screening quality survives independently of the current `30m` data-depth problem.
- Breadth narrowed materially (20 pools -> 13 pools), but the surviving universe still looked healthier on `1m`, `5m`, and `15m`.

What this auxiliary lens does NOT mean
- It does NOT mean the main experiment should be redefined as a screening-only experiment.
- It does NOT prove anything positive or negative about `30m` backtest.
- It only helps separate Lens A (screening effect) from Lens B (`30m` backtest feasibility).

Auxiliary verdict
- Screening effect: still validated as a promising research improvement after the clean rerun
- `30m` effect: outside the scope of this auxiliary note
- Strategy-family status: stays inside `u5spring`
- Propagation status from this note alone:
  - `01-research`: yes
  - anything above that still depends on the main experiment framing and follow-up evidence
