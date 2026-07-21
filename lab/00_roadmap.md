# Roadmap & Alur Kerja — Project Backtest Multi-Strategi

> **Dokumen ini adalah pegangan utama project.** Kalau file ini dibawa sendirian ke sesi baru atau ke AI lain, dokumen ini cukup untuk memahami tujuan, struktur, alur kerja, dan kriteria validasi project tanpa penjelasan tambahan.

## Project Brief (Baca Ini Duluan)

**Tujuan project**: membangun sistem backtest multi-strategi untuk trading crypto. Indikator direplikasi dari Pine Script (TradingView) ke Python, dijalankan terhadap data historis dari Binance, untuk menguji secara matematis apakah sebuah strategi (kombinasi indikator + rule entry/exit) layak dipertimbangkan sebelum masuk forward test atau live.

**Prinsip inti yang dipegang** (dasar dari diskusi awal project): keputusan strategi tidak didasarkan pada win rate tinggi atau feeling, tapi pada expected value (EV), manajemen risiko per trade, dan validitas statistik (jumlah sample cukup) sebelum sebuah strategi dianggap layak dijalankan.

**Cakupan yang belum dikunci** (sengaja dibiarkan fleksibel): pair Binance mana yang dites, dan timeframe berapa — belum ditentukan spesifik. Pendekatan yang disarankan: validasi di satu pair likuid dan satu timeframe dulu, baru diperluas setelah pipeline terbukti solid.

**Kriteria "strategi layak"** (ringkasan dari `stage_04_metrics_guide.md`, urutan prioritas baca):
1. Sample size cukup (idealnya di atas 30 trade, makin banyak makin reliable)
2. EV per trade dalam satuan R positif, dengan gap win rate aktual vs breakeven win rate yang cukup lebar (bukan mepet)
3. Max drawdown dan beban recovery-nya masih dalam toleransi psikologis dan finansial
4. Probabilitas loss beruntun (5/7/10 kali) sudah diperhitungkan dalam penentuan risk per trade
5. Baru setelah empat poin di atas aman, metric pelengkap (Sharpe, Sortino, edge ratio, dst) dipakai untuk membandingkan dan memilih antar strategi yang sudah lolos filter dasar

**Kalau mulai sesi baru, urutan baca yang disarankan**: Project Brief ini → tree Status Pembangunan (lihat progress sejauh mana) → Alur Kerja Operasional (proses kerja rutinnya) → baru masuk ke guide detail per stage di `journal/` sesuai kebutuhan spesifik.

---

Dokumen ini punya dua bagian utama setelah brief di atas. Bagian pertama adalah tree status pembangunan tiap stage (progress tracker). Bagian kedua adalah gambaran alur kerja operasional — bagaimana nanti proses kerja sehari-hari berjalan setelah semua stage selesai dibangun, supaya tetap rapi dan efisien walau strategi sudah banyak.

Status terakhir: lihat tanggal update di bawah. File ini diperbarui tiap kali sebuah stage kelar atau berubah status.

## Status Pembangunan Sistem

```
Project Backtest Multi-Strategi
│
├─ 1. Struktur folder [selesai]
│   └─ trading-lab/ (data, indicators, strategies, backtest_engine, results, journal)
│   └─ sandbox/ [selesai] — eksperimen bebas sebelum masuk siklus resmi
│   └─ guide: journal/stage_01_struktur_folder.md
│
├─ 2. Data layer [selesai]
│   ├─ Fetcher Binance API [selesai] → data/fetch_ohlcv.py
│   ├─ Cache OHLCV ke data/raw/ → CSV UTC + kolom WIB
│   └─ guide: journal/stage_02_data_dan_waktu.md (logika UTC vs WIB, boundary candle)
│
├─ 3. Replikasi indikator [selesai]
│   ├─ Pine script → Python: SMI Pro v3, SMI Events, FBF v11, ATR%, EMA Ribbon
│   ├─ Source .pine → indicators/pine_source/fbf_v11.pine
│   ├─ Validasi angka + fase/state via smi_events.py (vectorized)
│   └─ guide: journal/stage_03_replikasi_indikator.md
│
├─ 4. Backtest engine [selesai]
│   ├─ Metrics calculator [selesai] → backtest_engine/metrics.py
│   │   └─ guide: journal/stage_04_metrics_guide.md
│   ├─ Data pendukung leverage (fee, funding, liq price, MMR) [selesai, riset]
│   │   └─ guide: journal/stage_04b_leverage_biaya_data.md
│   └─ Core eksekusi trade [selesai] → backtest_engine/engine.py
│       └─ guide: journal/stage_04c_core_eksekusi_trade.md
│
├─ 5. Definisi strategi [selesai]
│   ├─ Skema config/rules/metadata per strategi → strategies/_template/
│   ├─ Interface kontrak ke backtest engine → entry_signal/exit_signal/sl_price/tp_price
│   └─ guide: journal/stage_05_definisi_strategi.md
│
├─ 6. Run + jurnal [selesai]
│   ├─ Pipeline end-to-end teruji: sandbox/experiments/exp_001_first_run/
│   ├─ Output: 91 trades, metrics lengkap (EV +0.032R, WR 36.3%, DD -14.3%)
│   └─ guide: -
│
└─ 7. Iterasi [belum]
    └─ Expand pair, timeframe, parameter setelah 1 pair solid
    └─ guide: -
```

## Aturan Update File Ini

- Status berubah jadi `[selesai]` hanya kalau komponennya benar-benar sudah jadi file/kode, bukan cuma dibahas konsep.
- Tiap stage `[selesai]` wajib punya guide di `journal/`, link-nya dicatat di baris `guide:` node terkait.
- Setelah semua 7 stage `[selesai]`, semua guide di `journal/` digabung jadi satu README master di root project.

---

## Alur Kerja Operasional (Setelah Semua Stage Selesai)

Bagian tree di atas adalah roadmap *pembangunan* sistem — sekali jalan, sampai semua komponen jadi. Bagian ini adalah roadmap *pemakaian* sistem — siklus yang berulang terus tiap kali ada ide strategi baru, setelah semua komponen di atas sudah siap.

```
Siklus Satu Strategi
│
├─ 1. Hipotesis strategi
│   └─ Tulis kenapa masuk akal, sebelum coding
│
├─ 2. Indikator siap
│   └─ Cek indicators/python/, kalau belum ada → replikasi + validasi dulu
│
├─ 3. Kalibrasi setup via studi kasus riil
│   └─ Kasih window waktu nyata, AI identifikasi event tiap indikator,
│      dikoreksi sampai interpretasinya sama persis dengan maksud lu
│
├─ 4. Rule strategi
│   └─ Buat strategies/[nama]/, entry-exit + parameter, mengacu ke hasil kalibrasi
│
├─ 5. Data siap
│   └─ Cek data/raw/, kalau belum ada → fetch, otomatis kecache
│
├─ 6. Run backtest
│   └─ Engine jalan, metrics.py otomatis terpanggil
│
├─ 7. Update journal
│   └─ Catat versi, parameter, hasil, insight
│
└─ 8. Keputusan
    ├─ Tuning parameter → balik ke langkah 4
    ├─ Expand pair/timeframe → balik ke langkah 5
    └─ Tidak layak → arsip, catat alasannya, selesai
```

### Kenapa Kalibrasi Setup Perlu Jadi Step Sendiri (Bukan Cuma Bagian dari Rule Strategi)

Validasi indikator (stage 3, tahap pembangunan sistem) itu soal **angka** — memastikan RSI Python sama dengan RSI TradingView. Kalibrasi setup ini beda lapisan: soal **interpretasi logic**. Dua indikator bisa sama-sama akurat angkanya, tapi kombinasi "kapan dianggap sinyal valid" itu sering ambigu kalau cuma dideskripsikan abstrak (misalnya "RSI oversold dan MA cross ke atas" — oversold di angka berapa persis, cross-nya harus di candle yang sama atau boleh beda beberapa candle, dst). Ambiguitas ini enggak ketahuan sampai diuji ke kasus riil.

Studi kasus riil (kasih window tanggal tertentu, suruh identifikasi event dari tiap indikator, dikoreksi kalau salah) adalah cara memastikan pemahaman logic-nya sinkron **sebelum** dituliskan jadi kode rule — supaya rule yang jadi kode beneran merepresentasikan maksud lu, bukan tebakan AI atas deskripsi yang ambigu.

### Format Studi Kasus (Disimpan di `strategies/[nama_strategi]/case_studies/`)

Tiap kasus kalibrasi dicatat sebagai file terpisah, penamaan pakai versi (`case_v1.md`, `case_v2.md`, dst) — bukan nomor urut acak, karena tiap kasus baru sebetulnya iterasi/koreksi atas pemahaman versi sebelumnya, bukan sekadar contoh lepas yang berdiri sendiri.

Isi tiap file:

- **Versi** (`v{N}`, sesuai nama file)
- **Pair + timeframe** yang dipakai contoh
- **Window waktu** (tanggal mulai — selesai)
- **State/kondisi tiap indikator** yang teridentifikasi di window itu
- **Event yang dianggap valid** sebagai sinyal (dan near-miss yang **bukan** sinyal valid, kalau ada — ini penting buat nge-batasi ambiguitas)
- **Koreksi dari lu** kalau interpretasi awal AI meleset
- **Apa yang berubah dari versi sebelumnya** (kosong/"versi awal" kalau ini v1)
- **Kesimpulan aturan final** yang disepakati dari kasus tersebut

**Tracker wajib**: folder `case_studies/` juga punya file `00_case_tree.md` — living document yang rangkum semua versi jadi satu tree, plus versi aturan final yang paling baru selalu ditaruh di paling atas file itu. Update tracker ini setiap selesai bikin case baru, supaya enggak perlu buka semua file case satu-satu untuk tahu pemahaman terkini. Template kosong keduanya (`case_v00_template.md` dan `00_case_tree.md`) ada di `strategies/_template/case_studies/`, tinggal copy ke folder strategi masing-masing.

**Manfaat tambahan**: kumpulan case study ini jadi semacam "golden test set". Begitu rule sudah jadi kode di step 4, jalankan kode itu ke window waktu yang sama persis dengan tiap case study — kalau hasil deteksi kode cocok dengan yang sudah disepakati manual, itu bukti rule terkoding dengan benar. Kalau enggak cocok, ketahuan ada gap antara logic yang dimaksud dan logic yang ketulis di kode.

### Siklus Hidup Satu Strategi, dari Ide sampai Keputusan (Versi Detail)

1. **Hipotesis dulu, sebelum coding apapun.** Tulis di journal kenapa strategi ini masuk akal secara logika. Ini mencegah strategi asal comot kombinasi indikator tanpa alasan jelas — kebiasaan itu yang biasanya berujung overfitting.

2. **Cek indikator yang dibutuhkan sudah ada atau belum**, lihat isi `indicators/python/`.
   - Kalau belum ada: replikasi dari `indicators/pine_source/` dulu, validasi akurasinya (alur stage 3), baru lanjut.
   - Kalau sudah ada: langsung reuse. Jangan bikin ulang fungsi yang sama.

3. **Kalibrasi setup lewat studi kasus riil.** Kasih window waktu spesifik (misalnya tanggal xx sampai xx), minta identifikasi event dari tiap indikator di window itu, koreksi sampai interpretasinya sama persis dengan maksud lu. Simpan tiap kasus di `strategies/[nama_strategi]/case_studies/`. Lewati step ini kalau setup-nya sudah cukup sederhana dan tidak ambigu, tapi untuk kombinasi indikator yang rumit, step ini yang mencegah salah paham logic terbawa sampai ke kode.

4. **Buat folder baru di `strategies/[nama_strategi]/`.** Isi rule entry/exit dan file konfigurasi parameter, mengacu ke hasil kalibrasi di langkah 3.

5. **Pastikan data pair-timeframe yang mau dites sudah tersedia** di `data/raw/`.
   - Kalau belum: jalankan fetcher, hasilnya otomatis kecache untuk dipakai lagi nanti.

6. **Jalankan backtest engine**, arahkan ke strategi dan data yang sudah disiapkan.

7. **Engine otomatis memanggil `metrics.py`** di akhir run. Hasil ringkas masuk ke `results/summary/[run_name].json`, detail trade masuk ke `results/raw/`.

8. **Baca hasil dengan urutan prioritas** sesuai `stage_04_metrics_guide.md`: cek dulu sample size, lalu EV dan gap breakeven win rate, lalu drawdown dan beban recovery-nya, lalu tabel probabilitas loss beruntun — baru metric pelengkap lainnya.

9. **Update journal strategi**: catat versi, parameter yang dipakai, hasil, insight yang didapat, dan langkah berikutnya.

10. **Ambil keputusan** — ada tiga jalan:
    - Lanjut tuning parameter → balik ke langkah 4 dengan versi baru.
    - Layak diperluas ke pair/timeframe lain → balik ke langkah 5.
    - Tidak layak (EV negatif, terlalu rapuh, dsb) → diarsipkan, tapi **tetap dicatat alasannya**, jangan dihapus begitu saja.

### Prinsip Supaya Tetap Efisien Walau Strategi Sudah Banyak

- **Satu strategi, satu hipotesis jelas.** Jangan gabung banyak ide sekaligus dalam satu strategi — kalau hasilnya bagus atau jelek, jadi tidak jelas elemen mana yang berkontribusi.
- **Validasi kecil dulu sebelum expand luas.** Satu pair, satu timeframe, baru perluas setelah terbukti solid. Kombinasi pair x timeframe x parameter bisa meledak jumlahnya kalau langsung disapu semua tanpa penyaringan awal.
- **Punya semacam daftar status semua strategi** (bisa sesederhana satu file ringkas) — mana yang masih dikembangkan, mana yang sudah diarsipkan, mana yang sedang dipantau. Tanpa ini, begitu strategi lebih dari sepuluh, gampang lupa mana yang sudah pernah dicoba.
- **Strategi gagal tetap punya nilai kalau dicatat.** Alasan kenapa sebuah ide tidak jalan itu sendiri adalah informasi berharga — mencegah mengulang ide yang sama di masa depan tanpa sadar sudah pernah dicoba dan gagal.
- **Naming convention run wajib konsisten**, supaya folder `results/` tidak jadi kacau seiring waktu.
- **Jangan loncat ke live trading langsung dari satu backtest yang kelihatan bagus.** Strategi yang lolos semua kriteria di metrics guide baru masuk tahap pertimbangan forward test atau live dengan modal kecil — bukan langsung all-in.

### Jalur Opsional: Eksperimen Bebas di `sandbox/` (Sebelum Komit ke Siklus Resmi)

Enggak semua ide harus langsung masuk siklus 8 langkah di atas. Untuk coba-coba kombinasi indikator/parameter secara bebas — pakai data dan engine asli, tapi belum mau komit ke proses formal — ada jalur pintas opsional:

```
[Opsional] Eksperimen Bebas di sandbox/
│
├─ Coba kombinasi/parameter bebas, pakai data + engine yang sudah ada
├─ Cek hasil kasar aja (EV, drawdown) — enggak perlu proses lengkap
│
└─ Keputusan:
    ├─ Menjanjikan → "naik kelas" ke strategies/, mulai siklus resmi 8 langkah
    │                 dari awal (hipotesis, kalibrasi setup serius, dst)
    └─ Enggak menjanjikan → dibuang atau dicatat ringkas di sandbox/log.md, selesai
```

Ini yang menjaga `strategies/` dan `results/` tetap bersih — cuma isi hal yang sudah lewat proses resmi. Detail struktur `sandbox/` ada di `stage_01_struktur_folder.md`.

### Kapan Baca Guide yang Mana

- Baru mulai kerja di stage tertentu → baca guide stage terkait di `journal/`.
- Lagi analisis hasil satu run backtest → baca `stage_04_metrics_guide.md`.
- Bingung sebuah file harus ditaruh di mana → baca `stage_01_struktur_folder.md`.
- Mau lihat progress pembangunan sistem secara keseluruhan → baca tree di bagian atas file ini.
- Mau tahu proses kerja rutin setelah sistem jadi → baca section ini.

---

## Riwayat Update

- Struktur folder awal dibuat, stage 1 selesai.
- `metrics.py` selesai dibuat dan diuji dengan dummy data, stage 4 sebagian (metrics calculator) selesai.
- Riset data pendukung leverage (fee, funding rate, liquidation price, MMR) selesai — sumber API resmi Binance didokumentasikan di stage_04b.
- Guide logika waktu (UTC vs WIB, boundary candle) selesai untuk stage 2 — kode fetcher-nya sendiri belum dibangun, diserahkan ke AI agent lain.
- Guide replikasi indikator selesai untuk stage 3 — termasuk prinsip replikasi layer fase/state, bukan cuma angka mentah. Kode replikasi belum dibangun.
- Guide definisi strategi selesai untuk stage 5 — skema config/rules/metadata dan interface kontrak ke backtest engine, plus penjelasan bedanya dengan alur operasional kalibrasi setup. Skema belum diimplementasikan.
- Guide core eksekusi trade selesai untuk stage 4c — timing eksekusi, ambiguitas SL/TP dalam satu candle, tracking MAE/MFE, posisi sizing. Ini bagian backtest engine yang paling rawan bug halus. Kode belum dibangun.
- Ditambah folder `sandbox/` untuk eksperimen bebas (coba kombo/parameter tanpa proses formal), plus jalur opsional di alur kerja.
- Playbook eksekusi dibuat (`00_playbook_eksekusi_ai_agent.md`) — urutan konkret handoff ke AI coding agent, per langkah: file yang dirujuk, command, cara verifikasi, tanda bahaya.
- Folder `sandbox/` dibuat di filesystem + dokumentasi README dan log.md. Struktur folder project lengkap (data/, indicators/, strategies/, backtest_engine/, results/, journal/, notebooks/, sandbox/) sudah ada di filesystem, siap diisi.
- Playbook eksekusi v2 dibuat (`00_playbook_eksekusi_v2.md`) — lebih detail, tambah integrasi `trading-research/` sebagai aset reusable, daftar keputusan wajib eksplisit, dan panduan per-stage yang lebih operasional.
- Index guide diupdate — tambah referensi ke playbook v2, sandbox, dan `trading-research/`.
