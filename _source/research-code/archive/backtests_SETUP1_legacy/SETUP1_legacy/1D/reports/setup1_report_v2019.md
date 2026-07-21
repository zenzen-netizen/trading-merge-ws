# SETUP1 SHORT — BACKTEST v3 (2019-01-01 .. 2026-07-09)

BTCUSDT 1D | 2747 candles | 150 raw signals | 67 ST-gated
AB events: 210 | downtrend bars: 1297/2747 (47.2%)

## Key findings

- **2019 extended sample**: 150 raw (vs 65 in 2023-only), 67 gated (vs 29). 2.3x more signals.
- **Best GATED**: O5 ConfHi+ATR x ST_REV = +12.6R (net), WR 41.3%.
- **Best RAW**: O2 C+ATR14 x ST_REV = +9.5R (net), WR 54.5%.
- **ST_REV exit (Supertrend flip -1 to +1) dominates** all best configs — beats fixed TP on net R.
- **Fixed 1x TP** (O2 C+ATR14 x 1x) was best in 2023-only (+10R) but weak on 2019 sample (RAW +1R, GATED -5R). Larger sample reveals 1x TP unsustainable.
- **RAWBRK exit catastrophic**: -90 to -110R across options. Bear raw-break trailing fails hard.
- **Trailing stop (TRAIL) always negative net** despite high WR (70-80%) — trails too tight, gives back edge.

## Top configs by Net R (summary)

| Mode | Opt | Ratio | n | WR% | TotR | AvgR | SL% | APCT% | winR | lossR |
|------|-----|-------|---|-----|------|------|-----|-------|------|------|
| GATED | O5 | ST_REV | 67 | 41.3 | +16.6R | +0.248 | 8.5 | 5.5 | - | -1.00 |
| GATED | O2 | ST_REV | 67 | 60.3 | +13.4R | +0.200 | 11.2 | 5.5 | - | -1.00 |
| GATED | O3 | ST_REV | 67 | 23.8 | +18.1R | +0.270 | 5.5 | 5.5 | - | -1.00 |
| GATED | O3 | 2x | 67 | 35.4 | +4.5R | +0.067 | 5.5 | 5.5 | 1.0 | -1.00 |
| GATED | O3 | 3x | 67 | 26.6 | +5.7R | +0.086 | 5.5 | 5.5 | 1.0 | -1.00 |
| RAW | O2 | ST_REV | 139 | 54.5 | +16.3R | +0.117 | 11.1 | 4.8 | - | -1.00 |
| RAW | O2 | 1x | 139 | 50.4 | +1.2R | +0.009 | 11.1 | 4.8 | 1.0 | -1.00 |
| RAW | O3 | 2x | 150 | 26.4 | -30.5R | -0.203 | 4.7 | 4.7 | 1.0 | -1.00 |
| RAW | O5 | ST_REV | 150 | 32.4 | -7.1R | -0.047 | 7.9 | 4.7 | - | -1.00 |

## Ratio detail (avg % chg)

- SL% = average stop distance above entry (short SL sits above).
- TP% = fixed TP distance below entry (ST_REV has no fixed TP = 0).
- APCT% = ATR% at entry (volatility context).
- winR = avg R on winning exit; lossR = -1.0 (full SL hit).

## Files
- Full journal: setup1_v3_journal.csv (6510 trades)
- Per-scenario splits: journals_v3/<mode>_<opt>_<ratio>.csv
- Raw run log: setup1_v3_run.log