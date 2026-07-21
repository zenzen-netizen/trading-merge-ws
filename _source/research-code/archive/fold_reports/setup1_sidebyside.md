# SETUP 1 SHORT — SIDE-BY-SIDE DETAIL
BTCUSDT 1D | 2023-01-01..2026-07-08 | 1285 candles
RAW = 63 sinyal (tanpa filter) | GATED = 27 sinyal (ST downtrend @ C + entry)

Setiap baris = 1 kombinasi SL×TP.
Kolom: WR% (win rate), R (net R), D (avg hari hold).
RAW dan GATED ditampilkan berdampingan.

====================================================================
O1 Liq10x  (SL = E×1.1, TP = E×0.9)
--------------------------------------------------------------------
TP     | RAW  WR   R      | GATED WR   R
1x     | 46.0% -5.0R      | 48.1% -1.0R      (avg 19d | 14d)
2x     | 32.3% -2.0R      | 26.9% -5.0R      (avg 31d | 22d)
3x     | 15.0% -24.0R     | 20.0% -5.0R      (avg 52d | 36d)
TRAIL  | 84.1% -8.0R      | 77.8% -4.5R      (avg 5d  | 5d)
ST_REV | 63.3% -2.2R      | 64.0% -3.7R      (avg 29d | 25d)
RAWBRK | 41.4% -28.1R     | 34.8% -13.4R     (avg 20d | 16d)

Trade counts RAW:  1x 29W/34L | 2x 20W/42L | 3x 9W/51L
                   TRAIL 53TR/10SL | ST_REV 38SRV/22SL | RAWBRK 24(2RBK+22RTL)/34SL
Trade counts GATED: 1x 13W/14L | 2x 7W/19L | 3x 5W/20L
                   TRAIL 21TR/6SL | ST_REV 16SRV/9SL | RAWBRK 8(1RBK+7RTL)/15SL

====================================================================
O2 C+ATR14  (SL = C_high + ATR14, TP = 2E - SL)  ★ RAW WINNER
--------------------------------------------------------------------
TP     | RAW  WR   R      | GATED WR   R
1x     | 58.6% +10.0R ★   | 48.1% -1.0R      (avg 16d | 12d)
2x     | 28.1% -9.0R      | 19.2% -11.0R     (avg 31d | 17d)
3x     | 17.9% -16.0R     | 16.0% -9.0R      (avg 44d | 25d)
TRAIL  | 79.3% -10.4R     | 70.4% -6.8R      (avg 5d  | 4d)
ST_REV | 61.8% +7.1R      | 56.0% -4.2R      (avg 26d | 23d)
RAWBRK | 40.0% -21.9R     | 28.0% -15.2R     (avg 20d | 16d)

Trade counts RAW:  1x 34W/24L | 2x 16W/41L | 3x 10W/46L
                   TRAIL 46TR/12SL | ST_REV 34SRV/21SL | RAWBRK 22(3RBK+19RTL)/33SL
Trade counts GATED: 1x 13W/14L | 2x 5W/21L | 3x 4W/21L
                   TRAIL 19TR/8SL | ST_REV 14SRV/11SL | RAWBRK 7(2RBK+5RTL)/18SL

====================================================================
O3 ATR%30  (SL = E×(1+ATR%), TP = E×(1-ATR%))  ★ GATED WINNER
--------------------------------------------------------------------
TP     | RAW  WR   R      | GATED WR   R
1x     | 42.9% -9.0R      | 51.9% +1.0R      (avg 4d  | 4d)
2x     | 27.0% -12.0R     | 40.7% +6.0R ★    (avg 6d  | 5d)
3x     | 16.1% -22.0R     | 23.1% -2.0R      (avg 8d  | 7d)
TRAIL  | 65.1% -15.7R     | 66.7% -4.5R      (avg 3d  | 3d)
ST_REV | 11.5% -18.5R     | 12.0% -8.5R      (avg 13d | 16d)
RAWBRK | 16.4% -34.6R     | 16.0% -14.7R     (avg 8d  | 8d)

Trade counts RAW:  1x 27W/36L | 2x 17W/46L | 3x 10W/52L
                   TRAIL 41TR/22SL | ST_REV 7SRV/54SL | RAWBRK 10RTL/51SL
Trade counts GATED: 1x 14W/13L | 2x 11W/16L | 3x 6W/20L
                   TRAIL 18TR/9SL | ST_REV 3SRV/22SL | RAWBRK 4RTL/21SL

====================================================================
O4 Fix6%  (SL = E×1.06, TP = E×0.94)
--------------------------------------------------------------------
TP     | RAW  WR   R      | GATED WR   R
1x     | 50.8% +1.0R      | 55.6% +3.0R      (avg 8d  | 7d)
2x     | 27.4% -11.0R     | 26.9% -5.0R      (avg 15d | 12d)
3x     | 21.0% -10.0R     | 19.2% -6.0R      (avg 20d | 15d)
TRAIL  | 74.6% -11.8R     | 70.4% -5.0R      (avg 4d  | 4d)
ST_REV | 43.3% -8.1R      | 36.0% -7.1R      (avg 24d | 22d)
RAWBRK | 31.7% -32.3R     | 28.0% -14.5R     (avg 16d | 14d)

Trade counts RAW:  1x 32W/31L | 2x 17W/45L | 3x 13W/49L
                   TRAIL 47TR/16SL | ST_REV 26SRV/34SL | RAWBRK 19RTL/41SL
Trade counts GATED: 1x 15W/12L | 2x 7W/19L | 3x 5W/21L
                   TRAIL 19TR/8SL | ST_REV 9SRV/16SL | RAWBRK 7RTL/18SL

====================================================================
O5 ConfHi+ATR  (SL = high(entry_bar) + ATR14, TP = 2E - SL)
--------------------------------------------------------------------
TP     | RAW  WR   R      | GATED WR   R
1x     | 49.2% -1.0R      | 44.4% -3.0R      (avg 8d  | 8d)
2x     | 22.6% -20.0R     | 19.2% -11.0R     (avg 14d | 14d)
3x     | 19.4% -14.0R     | 19.2% -6.0R      (avg 23d | 20d)
TRAIL  | 77.8% -10.6R     | 70.4% -5.5R      (avg 4d  | 4d)
ST_REV | 31.7% -10.8R     | 28.0% -10.5R     (avg 21d | 21d)
RAWBRK | 35.0% -27.4R     | 28.0% -15.0R     (avg 15d | 14d)

Trade counts RAW:  1x 31W/32L | 2x 14W/48L | 3x 12W/50L
                   TRAIL 49TR/14SL | ST_REV 19SRV/41SL | RAWBRK 21RTL/39SL
Trade counts GATED: 1x 12W/15L | 2x 5W/21L | 3x 5W/21L
                   TRAIL 19TR/8SL | ST_REV 7SRV/18SL | RAWBRK 7RTL/18SL

====================================================================
LEGEND
--------------------------------------------------------------------
1x / 2x / 3x  = TP pada 1× / 2× / 3× risk (fixed)
TRAIL         = trailing stop (½ ATR% activasi, 1× ATR% gap)
ST_REV        = exit saat Supertrend flip -1→+1
RAWBRK        = exit saat bear raw-break FBF jadi inactive
                (RBK = break lost, RTL = kena trail high)
WR%           = win rate (TP/TRAIL/SRV/RBK/RTL vs SL)
R             = net R (total reward dalam unit risk)
D             = avg hari hold sampai exit
