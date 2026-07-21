# SETUP 1 SHORT — FINAL BACKTEST REPORT
BTCUSDT 1D | 2023-01-01 sd 2026-07-08 | 1285 candel
Raw: 63 sinyal | ST-gated: 27 sinyal

## 5 SL OPTIONS × 6 TP MODES — RAW (no ST filter)
                     1x      2x      3x   TRAIL    ST_REV   RAWBRK
O1 Liq10x          -5.0R   -2.0R  -24.0R   -8.0R    -2.2R  -28.1R
O2 C+ATR14        +10.0R★  -9.0R  -16.0R  -10.4R    +7.1R  -21.9R
O3 ATR%30          -9.0R  -12.0R  -22.0R  -15.7R   -18.5R  -34.6R
O4 Fix6%           +1.0R  -11.0R  -10.0R  -11.8R    -8.1R  -32.3R
O5 ConfHi+ATR      -1.0R  -20.0R  -14.0R  -10.6R   -10.8R  -27.4R

## 5 SL × 6 TP MODES — GATED (ST downtrend @ C + entry)
                     1x      2x      3x   TRAIL    ST_REV   RAWBRK
O1 Liq10x          -1.0R   -5.0R   -5.0R   -4.5R    -3.7R  -13.4R
O2 C+ATR14         -1.0R  -11.0R   -9.0R   -6.8R    -4.2R  -15.2R
O3 ATR%30          +1.0R   +6.0R★  -2.0R   -4.5R    -8.5R  -14.7R
O4 Fix6%           +3.0R   -5.0R   -6.0R   -5.0R    -7.1R  -14.5R
O5 ConfHi+ATR      -3.0R  -11.0R   -6.0R   -5.5R   -10.5R  -15.0R

## WINNERS
RAW   (no filter): O2 C+ATR14 × 1x → +10.0R (58.6% WR)
GATED (ST align):  O3 ATR%30   × 2x →  +6.0R (40.7% WR)
                   O4 Fix6%     × 1x →  +3.0R (55.6% WR)

## INSIGHTS
1. O2 (C+ATR14) best RAW karena jago nyekel reversal.
2. ST gate ngerusak O2 (-11R) tapi ngebenerin O3 (+15R).
3. TRAIL (½ATR aktivasi, 1×ATR gap) terlalu ketat buat daily BTC.
4. ST_REV lumayan di RAW-O2 (+7.1R) tp kalah 3R dari 1x.
5. RAWBRK (bear break tracking) gagal — SL kena lebih dulu.
6. O5 (ConfHi+ATR) gak unggul dari O2 di skenario manapun.
7. 2x/3x TP gak berguna — jarang kena, WR turun drastis.

## CANONICAL 2026
Entry 17 Jun @ 64,509 — ST_OK=True (lolos ST gate)
1x semua → TP dalam 6-14 hari (profit)
O3×2x → TP +2.0R (langka, best case)
RAWBRK → EXP (bear break tetep aktif, gak flip)
