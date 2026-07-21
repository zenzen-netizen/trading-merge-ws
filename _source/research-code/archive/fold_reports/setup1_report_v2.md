# SETUP 1 SHORT — BACKTEST v2 REPORT
BTCUSDT 1D | 2023-01-01 sd 2026-07-08
1285 candles | 63 sinyal Setup 1

## SUMMARY PER OPSI × TP RATIO
O1  Liq10x  (E×1.1)
      1×:  29W 34L | 46.0%   |  -5.0R   |  avg 19d   [NEGATIF]
      2×:  20W 42L | 32.3%   |  -2.0R   |  avg 31d   [NEGATIF]
      3×:   9W 51L | 15.0%   | -24.0R   |  avg 52d   [NEGATIF]
   TRAIL:  53TR 10T| 84.1%   |  -8.0R   |  avg  5d   [NEGATIF — R trail terlalu kecil]

O2  C+ATR14  [★ BEST]
      1×:  34W 24L | 58.6%   | +10.0R   |  avg 16d   [POSITIF]
      2×:  16W 41L | 28.1%   |  -9.0R   |  avg 31d   [NEGATIF]
      3×:  10W 46L | 17.9%   | -16.0R   |  avg 44d   [NEGATIF]
   TRAIL:  46TR 12T| 79.3%   | -10.4R   |  avg  5d   [NEGATIF — trail terlalu ketat]

O3  ATR%30   (E × (1+atr_pct%))
      1×:  27W 36L | 42.9%   |  -9.0R   |  avg  4d   [NEGATIF]
      2×:  17W 46L | 27.0%   | -12.0R   |  avg  6d   [NEGATIF]
      3×:  10W 52L | 16.1%   | -22.0R   |  avg  8d   [NEGATIF]
   TRAIL:  41TR 22T| 65.1%   | -15.7R   |  avg  3d   [NEGATIF]

O4  Fix 6%  (E×1.06)
      1×:  32W 31L | 50.8%   |  +1.0R   |  avg  8d   [BREAKEVEN]
      2×:  17W 45L | 27.4%   | -11.0R   |  avg 15d   [NEGATIF]
      3×:  13W 49L | 21.0%   | -10.0R   |  avg 20d   [NEGATIF]
   TRAIL:  47TR 16T| 74.6%   | -11.8R   |  avg  4d   [NEGATIF]

## TRAILING STOP ANALYSIS
Trailing aktif ketika harga turun = ½ × ATR%
Trail gap = 1× ATR% dari titik terendah

Semua opsi trailing net NEGATIF. Penyebab:
  - ATR% BTC daily ~3.6% → aktivasi di 1.8% terjadi H+1 atau H+2
  - Trail gap 3.6% terlalu ketat untuk pergerakan daily BTC
  - Trailing exit sering di R~0.00 s/d +0.15 (sangat tipis)
  - 10-12× loss full -1R masih kena

Rekomendasi: trailing perlu gap lebih lebar (2× ATR%) atau
aktivasi lebih lambat (misal sudah profit 1× risk dulu).

## CANONICAL 2026
Entry 17 Jun @ 64,509 | APCT=3.6%
Semua 1× → TP dalam 6-14 hari
ATR%30×2× → TP +2.0R (terbaik)
Trailing → TRAIL H+1, R=0 (nyaris impas)

## WINNER
O2 C+ATR14 × 1× : 58.6% WR, +10.0R
Ini satu-satunya yg konsisten positif.
