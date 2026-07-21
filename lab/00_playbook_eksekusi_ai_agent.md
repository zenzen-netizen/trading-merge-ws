# Playbook Eksekusi — Cara Pakai Siklus & Struktur Ini dengan AI Coding Agent

Dokumen ini beda dari guide lain: ini bukan penjelasan konsep, tapi **urutan tindakan konkret** — file apa dikasih ke AI agent (Claude Code atau sejenisnya), command seperti apa, dan cara verifikasi tiap tahap supaya hasilnya benar-benar sesuai rencana yang sudah disusun, bukan interpretasi bebas dari agent.

Prinsip dasar: **agent membangun kode, tapi guide di `journal/` yang jadi spesifikasi kebenaran.** Kalau ada perbedaan antara apa yang agent bikin dan apa yang tertulis di guide, guide yang benar — bukan sebaliknya.

---

## Langkah 0 — Setup Awal

**Yang dikasih ke agent**: seluruh folder `trading-lab/` (termasuk `journal/`, `backtest_engine/metrics.py`, `strategies/_template/`, `sandbox/`).

**Command pertama**:
> "Baca `journal/00_roadmap.md` dulu sampai selesai sebelum melakukan apa pun. Itu berisi tujuan project, status pembangunan, dan alur kerja. Konfirmasi ke aku ringkasan pemahamanmu sebelum lanjut ke instruksi berikutnya."

**Kenapa langkah ini enggak boleh dilewat**: `00_roadmap.md` sengaja dibuat sebagai anchor mandiri (lihat isi filenya sendiri) — kalau agent langsung disuruh "bikin fetcher" tanpa baca ini dulu, dia enggak akan tahu prinsip inti (EV framework, kriteria strategi layak) yang harus dipegang di semua keputusan berikutnya.

**Verifikasi**: baca ringkasan yang agent kasih balik. Kalau dia enggak menyebut soal EV, risk management, atau validitas statistik sebagai prinsip inti, kemungkinan dia cuma skimming — minta baca ulang lebih teliti.

---

## Langkah 1 — Stage 2: Data Fetcher

**File yang dirujuk**: `journal/stage_02_data_dan_waktu.md`

**Command**:
> "Baca `journal/stage_02_data_dan_waktu.md`. Buat fetcher data OHLCV dari Binance sesuai panduan di file itu — perhatikan khusus bagian penyimpanan UTC dan boundary candle. Sebelum bilang selesai, jalankan checklist di akhir file itu satu per satu dan laporkan hasil tiap poinnya ke aku."

**Test konkret buat verifikasi** (bukan cuma baca laporan agent, tapi cek sendiri):
1. Minta agent fetch 1 pair 1 timeframe kecil (misalnya BTCUSDT 1h, beberapa hari data saja)
2. Ambil satu baris data mentah dari hasilnya, cek kolom timestamp — pastikan itu UTC (bukan WIB, bukan format ambigu)
3. Manual hitung pakai tabel boundary di guide: kalau openTime candle itu jam sekian UTC, harusnya jam sekian WIB — cocokkan dengan yang seharusnya
4. Cek baris paling akhir data — pastikan bukan candle yang belum closed

**Tanda bahaya**: kalau agent menyimpan timestamp langsung dalam WIB tanpa kolom UTC sebagai sumber utama, atau enggak ada penjelasan soal candle yang belum closed dibuang — itu artinya guide enggak diikuti dengan benar, bukan cuma detail kecil yang bisa diabaikan.

---

## Langkah 2 — Stage 3: Replikasi Indikator

**File yang dirujuk**: `journal/stage_03_replikasi_indikator.md`, plus source `.pine` indikator spesifik yang mau direplikasi.

**Command**:
> "Baca `journal/stage_03_replikasi_indikator.md`. Replikasi indikator dari script Pine ini [tempel/lampirkan script] ke Python, ikuti prinsip di guide — termasuk layer numerik DAN layer fase/state, bukan cuma angka mentah. Output harus punya kolom teks fase gabungan yang bisa dicocokkan langsung ke tampilan dashboard di chart."

**Verifikasi dua layer** (sesuai yang ditekankan di guide):
1. **Layer angka**: ambil beberapa titik sample dari kondisi market berbeda (trending, sideways, volatile), bandingkan nilai indikator Python dengan yang tampil di TradingView di candle yang sama persis
2. **Layer fase**: di titik sample yang sama, cocokkan teks fase/label yang dihasilkan Python dengan warna bar atau teks dashboard yang tampil di chart

**Tanda bahaya**: kalau agent cuma validasi angka tapi enggak ada kolom fase sama sekali, atau validasi cuma dilakukan di satu-dua titik random tanpa mewakili kondisi market yang beragam — minta diulang dengan sampling yang lebih sistematis.

---

## Langkah 3 — Kalibrasi Setup (Bukan Tugas Coding, Tapi Bisa Dibantu Agent)

Ini bukan tugas "bikin kode", tapi proses kalibrasi yang sudah dibahas di alur operasional. Agent bisa membantu di sisi teknis (baca data hasil stage 2-3, sajikan dalam bentuk yang gampang dibaca), tapi **keputusan final soal apa yang dianggap sinyal valid tetap di tangan lo**, bukan diserahkan ke agent.

**Command**:
> "Ambil data [pair/timeframe] dari `[tanggal mulai]` sampai `[tanggal selesai]`. Tampilkan kondisi tiap indikator dan kolom fase di window itu, candle demi candle. Jangan simpulkan sendiri mana yang sinyal valid — aku yang akan tentukan setelah lihat datanya."

**Verifikasi**: pastikan agent menyajikan data mentah + fase, bukan langsung menyimpulkan "ini sinyal buy". Setelah lo tentukan sendiri, baru minta agent bantu tuliskan ke `case_v{N}.md` sesuai template, dan update `00_case_tree.md`.

---

## Langkah 4 — Stage 5 & 4c: Skema Strategi dan Core Engine

Dua ini bisa dikerjakan berurutan atau paralel karena saling terhubung lewat kontrak fungsi yang sama.

**File yang dirujuk**: `journal/stage_05_definisi_strategi.md`, `journal/stage_04c_core_eksekusi_trade.md`

**Command**:
> "Baca `journal/stage_05_definisi_strategi.md` dan `journal/stage_04c_core_eksekusi_trade.md`. Buat skema `config.py`/`rules.py`/`metadata.md` di `strategies/_template/`, dan bangun core eksekusi backtest engine di `backtest_engine/`. Sebelum lapor selesai, jalankan checklist di akhir masing-masing file dan laporkan satu per satu."

**Keputusan yang WAJIB dikonfirmasi eksplisit ke lo, bukan diputuskan sendiri oleh agent** (ini poin paling penting dari kedua guide):
- Kebijakan ambiguitas SL/TP dalam satu candle (rekomendasi default: SL dianggap kena duluan)
- Fixed fractional vs compounding untuk posisi sizing
- Metode stop loss yang dipakai (fixed persen, ATR, structure-based)

**Tanda bahaya**: kalau agent langsung mengimplementasikan salah satu pilihan di atas tanpa nanya dulu ke lo, atau enggak menyebutkan sama sekali bahwa itu adalah keputusan yang perlu disepakati — itu tanda dia enggak benar-benar mencerna bagian "wajib eksplisit" di guide.

---

## Langkah 5 — Uji Coba di `sandbox/` Dulu

Sebelum strategi pertama masuk `strategies/` secara resmi, coba dulu di `sandbox/experiments/` dengan parameter longgar. Ini kesempatan buat lihat apakah seluruh pipeline (data → indikator → engine → metrics) nyambung dengan benar secara end-to-end, tanpa tekanan harus langsung sempurna.

**Command**:
> "Jalankan backtest percobaan di `sandbox/experiments/exp_001_[nama]/` pakai kombinasi [indikator/parameter] ini. Ini masih eksperimen, belum resmi — hasilnya cukup ringkasan kasar dulu."

**Verifikasi**: cek `results/summary/` (kalau sandbox juga nulis ke sana — atau taruh hasil sandbox terpisah, sesuai kesepakatan) apakah semua metric dari `metrics.py` muncul lengkap dan angkanya masuk akal (bukan `NaN`, bukan `inf` yang enggak masuk akal).

---

## Langkah 6 — Strategi Resmi Pertama, Siklus Penuh 8 Langkah

Begitu sandbox testing lancar, mulai strategi resmi pertama ikuti 8 langkah alur operasional di `00_roadmap.md` dari awal: hipotesis → indikator siap → kalibrasi setup → rule strategi → data siap → run backtest → update journal → keputusan.

**Verifikasi keseluruhan** sebelum sebuah strategi dianggap "selesai dites" (bukan berarti langsung live, tapi selesai tahap backtest): cross-check hasil `results/summary/` dengan urutan prioritas baca di `stage_04_metrics_guide.md` (sample size → EV → drawdown → ruin probability → metric pelengkap).

---

## Prinsip Pengawasan Umum (Berlaku di Semua Langkah)

1. **Selalu minta agent merujuk nomor/nama guide yang dipakai** di tiap penjelasan atau commit message — kalau dia enggak bisa sebutkan guide mana yang jadi acuan, kemungkinan dia enggak benar-benar mengikuti spesifikasi, cuma menebak dari pengetahuan umum.
2. **Jangan biarkan keputusan besar diputuskan diam-diam.** Semua guide sudah menandai eksplisit poin-poin yang "wajib dicatat/disepakati" — kalau itu dilewat tanpa dikonfirmasi ke lo, hentikan dan minta diulang.
3. **Selalu minta tes kecil dulu sebelum full run** — 1 pair, 1 timeframe, rentang waktu pendek. Lebih gampang mendeteksi bug di skala kecil daripada nyari di antara ribuan baris hasil.
4. **Update `00_roadmap.md` tiap satu bagian kelar** — ubah status di tree, tambah baris di Riwayat Update. Ini bukan basa-basi administratif — ini yang bikin project tetap bisa "dibawa ke sesi lain" kapan pun tanpa kehilangan konteks.
5. **Kalau ragu, minta agent jelasin balik pakai bahasa awam** apa yang barusan dia bangun, sebelum lo commit ke keputusan berikutnya. Kalau penjelasannya enggak masuk akal atau muter-muter, itu sinyal ada yang enggak beres — bahkan sebelum lo sempat baca kodenya baris per baris.
