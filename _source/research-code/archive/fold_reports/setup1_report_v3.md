# SETUP 1 SHORT — BACKTEST v3 REPORT (ST GATE + ST-REVERSAL TP)
BTCUSDT 1D | 2023-01-01 sd 2026-07-08
1285 candles

## ST GATE (downtrend @ C-bar DAN @ entry-bar)
Raw signals: 63 → Gated: 27 (57% filtered by ST)

## BEST PER MODE
RAW   (no ST): O2 C+ATR14 × 1x → +10.0R  (58.6% WR)
GATED (ST on): O3 ATR%30   × 2x →  +6.0R  (40.7% WR 2x)
                          O4 Fix6%   × 1x →  +3.0R

## RAW vs GATED (best TP per option)
             RAW        GATED      ΔR
O1 Liq10x  -2.0R×2x   -1.0R×1x   +1.0
O2 C+ATR14 +10.0R×1x  -1.0R×1x  -11.0  ← ST gate RUINS O2
O3 ATR%30   -9.0R×1x  +6.0R×2x  +15.0  ← ST gate FIXES O3
O4 Fix6%    +1.0R×1x  +3.0R×1x   +2.0

## INSIGHT
- O2 C+ATR14 = counter-trend reversal edge.
  ST gate (searah) malah ngerusak edge-nya (-11R).
- O3 ATR%30 = trend-following stop.
  ST alignment bikin dia jadi profit (+6R @ 2x).
- O4 Fix6% = robust di kedua mode.

## CANONICAL 2026 (lolos ST gate: ST@C=DOWN, ST@Entry=DOWN)
Entry 17 Jun @ 64,509 | APCT=3.6%
1x semua → TP | O3×2x → TP +2.0R

## NEXT: ST-REVERSAL TP
Exit short pas ST flip -1 → +1 (let-it-run).
Bandngin dgn 1x/2x/3x/trailing.
