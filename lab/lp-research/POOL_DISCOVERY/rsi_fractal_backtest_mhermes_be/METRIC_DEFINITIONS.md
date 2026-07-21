# Meteora RSI(2) + Fractal(3) — Metric Definitions

Dokumen ini menjelaskan definisi tiap metric yang muncul di report / summary.

## Strategy frame
- Entry rule: RSI(2) + confirmed upper fractal(3) on bullish trend filter.
- Exit rule checked in this order on each candle:
  1. SL first
  2. TP second
  3. BE gate last
- Same-candle handling is conservative: if SL and TP both appear on one candle, SL wins.

## Core columns

### Trades
Total valid trade setups that passed pre-entry filters and were simulated.

### TP
Jumlah trade yang exit via target profit fractal.

### SL
Jumlah trade yang exit via stop loss.

### BE
Jumlah trade yang exit breakeven via BE gate.

### EXP
Trade yang tidak kena TP/SL/BE sampai akhir data, lalu ditutup di close terakhir (expired).

### WR%
Win rate dari trade resolved biasa:
- denominator = TP + SL
- formula = TP / (TP + SL) * 100
- BE dan EXP tidak masuk denominator WR%

### SumR
Total R multiple dari seluruh trade pada scenario itu.
- win = positive R
- loss = negative R
- BE biasanya sekitar 0R

### AvgR
Average R per trade:
- formula = SumR / Trades

### AvgHold
Rata-rata lama trade bertahan dalam menit.

## BE metrics

### BE gate hit
Jumlah trade yang sempat memenuhi kondisi dasar untuk boleh BE.
Untuk versi detail BE ini, base condition = trade pernah floating loss (price sempat lawan arah).

### BE gate rec
Jumlah trade yang benar-benar exit BE setelah gate terpenuhi.

### BE gate%
Recovery rate dari BE gate:
- formula = BE gate rec / BE gate hit * 100

### EverLoss
Jumlah trade yang pernah floating loss sebelum exit.

### D50
Jumlah trade yang sempat turun sampai minimal 50% dari jarak entry ke SL.

### D50rec
Jumlah trade D50 yang kemudian balik ke entry dan berhasil BE.

### D50%
Recovery rate untuk group D50:
- formula = D50rec / D50 * 100

### D75
Jumlah trade yang sempat turun sampai minimal 75% dari jarak entry ke SL.

### D75rec
Jumlah trade D75 yang kemudian balik ke entry dan berhasil BE.

### D75%
Recovery rate untuk group D75:
- formula = D75rec / D75 * 100

## Streak metrics

### MaxW / MaxL
- MaxW = streak menang terpanjang
- MaxL = streak loss terpanjang

Streak dihitung hanya pada outcome resolved TP vs SL, bukan BE/EXP.

## SL option definitions

### O1_SL50
SL = 50% dari entry price (fixed 50% stop distance).

### O2_ST2X
SL = 2x jarak dari confirmation close ke garis Supertrend.

Formula ringkas:
- dist_pct = (close_confirm - st_line_confirm) / close_confirm
- SL = entry * (1 - 2 * dist_pct)

## BE modes

### BE1
BE aktif setelah 1 candle minimum sejak entry, selama trade pernah floating loss.

### BE50
BE aktif setelah 2 candle minimum sejak entry, selama trade pernah turun minimal 50% risk.

### BE75
BE aktif setelah 3 candle minimum sejak entry, selama trade pernah turun minimal 75% risk.

Catatan: pada report final yang dipakai sekarang, mode BE50/BE75 tetap disimpan sebagai opsi tambahan untuk stress test, tapi BE1 adalah default praktis.

## Notes
- Semua metric dihitung per scenario: pool × TF × SL option × exit mode.
- Journal split per mode ada di `split_by_mode/`.
- Report detail memakai kalender WIB untuk timestamp yang ditampilkan.
