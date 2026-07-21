# Stage 4c — Panduan Core Eksekusi Trade (Backtest Engine)

Status: panduan siap, kode belum dibangun.

Pelengkap `stage_04_metrics_guide.md` (cara baca hasil) dan `stage_04b_leverage_biaya_data.md` (data pendukung leverage). Dokumen ini adalah bagian **paling inti** dari backtest engine — logika yang benar-benar menghasilkan trade list dan equity curve, yang baru kemudian diproses `metrics.py`.

---

## Kenapa Ini Bagian Paling Rawan Bug Halus

Beda dengan metrics calculator (yang cuma memproses angka yang sudah jadi), core eksekusi ini menentukan **apakah trade list itu sendiri representasi realistis** dari bagaimana strategi akan berjalan di dunia nyata. Bug di sini tidak kelihatan salah — backtest tetap jalan, angka tetap keluar, tapi hasilnya terlalu optimis dibanding kenyataan. Jenis bug seperti ini yang paling berbahaya karena baru ketahuan setelah live trading.

---

## Loop Bar-by-Bar, Bukan Vectorized

Karena ada **state posisi** (sedang terbuka atau tidak) yang mempengaruhi logic candle berikutnya — misalnya, sinyal exit cuma relevan dicek kalau posisi sedang terbuka — eksekusi wajib diproses berurutan candle demi candle, bukan dihitung sekaligus secara vectorized di seluruh dataset. Ini menyambung ke poin lookahead bias yang sudah disinggung di `stage_03_replikasi_indikator.md`: kalau logic ditulis vectorized tanpa hati-hati terhadap ketergantungan urutan, gampang tanpa sadar "melihat" kondisi yang seharusnya belum diketahui pada titik itu.

Pola dasar loop:
- Kalau tidak ada posisi terbuka: cek sinyal entry di candle ini, kalau aktif → buka posisi
- Kalau ada posisi terbuka: cek sinyal exit, atau apakah stop loss/take profit/liquidation kena → kalau salah satu terpenuhi, tutup posisi

---

## Timing Eksekusi: Sinyal vs Harga Eksekusi (Gotcha Paling Klasik)

Sinyal entry dihitung dari data candle yang **sudah closed**. Secara realistis, order baru bisa benar-benar dieksekusi paling cepat di **open candle berikutnya** — bukan di harga close candle yang memicu sinyal, karena harga close itu sendiri baru diketahui persis pada saat candle itu selesai terbentuk.

Kalau backtest memakai harga close candle sinyal sebagai harga entry, itu artinya sistem berasumsi bisa entry persis di harga yang baru saja "diketahui" pada momen yang sama — ini bentuk halus dari lookahead bias, dan hasilnya akan terlalu optimis dibanding eksekusi nyata.

**Rekomendasi**: harga entry dan exit berbasis sinyal indikator memakai **open candle setelah candle sinyal**, bukan close candle sinyal itu sendiri.

---

## Ambiguitas Stop Loss vs Take Profit dalam Satu Candle

Begitu posisi terbuka, tiap candle berikutnya dicek: apakah high candle menyentuh take profit, atau low candle menyentuh stop loss (kebalikannya untuk posisi short).

**Masalahnya**: kalau dalam satu candle yang sama, high menyentuh TP **dan** low menyentuh SL sekaligus, data OHLC candle itu sendiri tidak memberi tahu urutan kejadian sebenarnya — cuma empat angka (open, high, low, close), tanpa informasi kapan tepatnya harga menyentuh masing-masing level dalam rentang waktu candle itu.

Ini kebijakan yang **wajib disepakati secara eksplisit**, bukan dibiarkan default tanpa disadari:

- **Opsi konservatif**: asumsikan stop loss kena duluan (skenario terburuk) — direkomendasikan sebagai default awal, karena bias ke arah lebih realistis/hati-hati dibanding asumsi optimis.
- **Opsi data granular**: kalau tersedia data timeframe lebih kecil untuk candle yang sama, pakai itu untuk menentukan urutan sebenarnya.
- **Opsi heuristik posisi open**: asumsikan level yang lebih dekat ke harga open candle itu yang kena duluan.

Kebijakan yang dipilih harus dicatat eksplisit di journal strategi — ini termasuk "assumption fee/slippage" yang sudah direncanakan dicatat sejak awal project, cuma diperluas ke assumption ambiguitas SL/TP juga.

---

## MAE/MFE — Wajib Di-Track Tiap Candle, Bukan Cuma di Akhir

Sudah disinggung sebagai catatan di `stage_04_metrics_guide.md`: MAE dan MFE cuma valid kalau dihitung dari titik ekstrem **selama posisi berjalan**, bukan cuma dari harga exit akhir. Konkretnya, engine harus:

- Tiap candle selama posisi masih terbuka, update dua angka berjalan: jarak terjauh melawan posisi (pakai low candle untuk long, high untuk short) dan jarak terjauh searah profit (kebalikannya).
- Setelah posisi ditutup, nilai akhir dari dua angka berjalan ini yang dicatat sebagai MAE dan MFE trade tersebut.

Kalau ini dilewatkan dan MAE/MFE cuma dihitung dari harga entry-exit saja, hasilnya akan meremehkan risiko sebenarnya yang sempat dialami posisi selama berjalan.

---

## Posisi Sizing dan Compounding — Keputusan yang Harus Eksplisit

Ada dua pendekatan berbeda untuk menentukan besar risiko tiap trade:

- **Fixed fractional**: risk per trade dihitung dari persentase **modal awal** yang tetap, tidak berubah seiring waktu.
- **Compounding**: risk per trade dihitung dari persentase **modal saat ini**, ikut naik turun mengikuti equity curve.

Dua pendekatan ini menghasilkan bentuk equity curve yang jauh berbeda (compounding cenderung pertumbuhan eksponensial, fixed fractional cenderung lebih linear) — dan mempengaruhi semua metric turunan (net profit, drawdown, recovery). Ini harus dipilih secara sadar dan dicatat di journal strategi, bukan default diam-diam yang bisa membingungkan saat membandingkan hasil antar strategi atau antar run.

---

## Struktur Trade Record yang Harus Dihasilkan

Field yang dihasilkan tiap trade harus **persis cocok** dengan struktur `Trade` di `backtest_engine/metrics.py`: waktu entry, waktu exit, arah posisi, harga entry, harga exit, stop loss, take profit, pnl, risk amount, MAE, MFE. `risk_amount` dihitung dari config risk strategi (lihat `stage_05_definisi_strategi.md`) — persentase risk per trade dikalikan modal yang relevan (awal atau saat ini, tergantung keputusan fixed fractional vs compounding di atas).

---

## Interface ke Komponen Lain (Jahitan Antar Stage)

- **Input data**: OHLCV + kolom indikator dan fase, sudah dalam boundary waktu yang benar (lihat `stage_02_data_dan_waktu.md`)
- **Input logic**: `entry_signal()` dan `exit_signal()` dari strategi (lihat `stage_05_definisi_strategi.md`)
- **Input config**: parameter risk dan metode SL/TP dari config strategi
- **Kalau strategi pakai leverage**: cek liquidation price tiap candle berjalan (formula ada di `stage_04b_leverage_biaya_data.md`) — kalau harga menyentuh liquidation price, posisi dianggap closed paksa di titik itu, terlepas dari SL manual yang dipasang
- **Output**: daftar trade lengkap + equity curve, dilempar ke `calculate_all_metrics()` di `metrics.py`

---

## Checklist Stage 4c

- [ ] Loop diproses bar-by-bar berurutan, bukan vectorized, untuk menjaga state posisi terbuka/tertutup
- [ ] Harga entry/exit berbasis sinyal indikator memakai open candle setelah candle sinyal, bukan close candle sinyal
- [ ] Kebijakan ambiguitas SL/TP dalam satu candle disepakati eksplisit dan dicatat di journal
- [ ] MAE/MFE di-track tiap candle selama posisi terbuka, pakai high/low candle, bukan cuma harga entry-exit
- [ ] Field trade record cocok persis dengan struktur `Trade` di `metrics.py`
- [ ] Posisi sizing (fixed fractional vs compounding) diputuskan eksplisit, dicatat di journal
- [ ] Liquidation check terintegrasi kalau strategi memakai leverage
- [ ] Candle yang belum closed (in-progress) tidak pernah dipakai sebagai data final (menyambung ke `stage_02_data_dan_waktu.md`)
