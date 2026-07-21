# Playbook Eksekusi v2 — Handoff ke AI Coding Agent (Lengkap)

Dokumen ini versi lebih detail dari `00_playbook_eksekusi_ai_agent.md` (v1).
Tambahan utama: daftar aset reusable dari `trading-research/`, integrasi eksplisit
antar folder, keputusan wajib per stage, dan verifikasi end-to-end.

**Prinsip dasar**: agent membangun kode, guide di `journal/` yang jadi spesifikasi
kebenaran. Kalau ada perbedaan antara apa yang agent bikin dan apa yang tertulis
di guide, guide yang benar — bukan sebaliknya.

---

## Aset Reusable — Yang Sudah Ada & Bisa Langsung Dipakai

Sebelum mulai bangun dari nol, cek dulu apa yang sudah jadi di VPS:

### Dari `trading-research/` (`/home/ubuntu/trading-research/`)

| Aset | Path | Status | Bisa Dipakai Untuk |
|------|------|--------|-------------------|
| **Data Fetcher** | `fetchers/data_fetcher.py` | Jadi, teruji | Stage 2 — fetch OHLCV Binance (spot + futures), UTC, auto-drop unclosed candle |
| **SMI Pro v3** | `indicators/smi_pro.py` | Jadi, teruji | Stage 3 — SMI with zone, cross, momentum, PA/PD states |
| **SMI Events** | `indicators/smi_events.py` | Jadi, teruji | Stage 3 — FMB→PD→XDN trigger logic |
| **FBF v11** | `indicators/fbf_v11/fbf_v11_mhermes.py` | Jadi, teruji | Stage 3 — Fractal Break Filter with state machine |
| **FBF v11 Pine** | `indicators/fbf_v11/fbf_v11.pine` | Source asli | Stage 3 — bahan validasi akurasi replikasi (1075 lines) |
| **ATR%** | `indicators/atr_percentage.py` | Jadi | Stage 3 — ATR sebagai persentase harga |
| **EMA Ribbon** | `indicators/ema_ribbon.py` | Jadi | Stage 3 — multi-EMA indicator |
| **Engine v2.b** | `backtests/BTCUSDT/SETUP1/1D/setup1_v2b_clean.py` | Jadi, teruji | Referensi arsitektur untuk Stage 4c + 5 |
| **Trigger Spec** | `backtests/BTCUSDT/SETUP1/TRIGGER_SPEC_v2b.md` | LOCKED | Stage 5 — spesifikasi lengkap SETUP1 SHORT |
| **Data Cache** | `backtests/BTCUSDT/SETUP1/*/data_*.csv` | Siap pakai | BTCUSDT 1D/2H/4H/1H, tinggal baca |
| **VenV** | `.venv_chart/` | numpy, pandas, matplotlib | Environment Python siap pakai |
| **Trade Template** | `TRADE_TEMPLATE.md` | Work-tree concept | Format pencatatan trade: entry→exit→combo→outcome |
| **Lib Helpers** | `lib/format_trade.py`, `lib/extract_exact.py` | Jadi | Format/extract trade records |

### Dari `trading-lab/` sendiri

| Aset | Path | Status | Catatan |
|------|------|--------|---------|
| **Metrics Calculator** | `metrics.py` | Jadi, teruji | Semua fungsi metric: EV, drawdown, Sharpe, ruin prob, dll |
| **Trade dataclass** | `metrics.py` (baris 21-44) | Sudah defined | Struktur `Trade` — wajib dipatuhi engine |

### Dari `meridian/` (Meridian DLMM bot)

| Aset | Path | Bisa Dipakai Untuk |
|------|------|-------------------|
| **Lessons Engine** | `lessons.js` | Referensi konsep: learning dari closed position, threshold evolution |
| **Reports** | `reports.js` | Referensi: profit factor, drawdown, breakdown format |
| **Config System** | `config.js` | Referensi: runtime config mutation + persist pattern |

---

## Langkah 0 — Setup Awal (Agent Baru)

**Yang dikasih**: seluruh folder `trading-lab/` + path ke `trading-research/`.

**Command**:
> "Baca `00_roadmap.md` dulu sampai selesai. Itu anchor project — isinya tujuan,
> status pembangunan, dan alur kerja. Setelah itu baca `00_playbook_eksekusi_v2.md`
> (file ini) untuk tahu aset apa yang sudah ada dan urutan konkretnya.
> Konfirmasi ke aku ringkasan pemahamanmu — sebutkan prinsip EV framework,
> daftar aset reusable yang akan kamu pakai, dan stage mana yang akan kamu
> kerjakan duluan."

**Verifikasi**: agent harus menyebut EV, risk management, dan sample size
sebagai prinsip inti. Kalau cuma nyebut "backtest system" tanpa framework
evaluasi, minta baca ulang.

---

## Langkah 1 — Stage 2: Data Fetcher

**Aset reusable**: `trading-research/fetchers/data_fetcher.py`

**Yang sudah ada**: fetcher lengkap — Binance spot + futures, UTC timestamp,
auto-drop unclosed candle. Fungsi `fetch_ohlcv(symbol, interval, limit, market_type)`.

**Yang perlu disesuaikan ke trading-lab**:
1. Output disimpan ke `data/raw/PAIR_TF_daterange.csv` (format nama sesuai stage_01)
2. Tambah kolom `open_time_wib` di CSV (UTC+8, untuk jurnal/laporan)
3. Verifikasi boundary candle mengikuti tabel di `stage_02_data_dan_waktu.md`

**File yang dirujuk**: `stage_02_data_dan_waktu.md`

**Command**:
> "Baca `stage_02_data_dan_waktu.md`. Adaptasi fetcher dari
> `trading-research/fetchers/data_fetcher.py` ke `data/fetch_ohlcv.py` di
> trading-lab. Output simpan di `data/raw/` dengan format nama standar.
> Tambah kolom `open_time_wib`. Pastikan UTC tetap sumber utama.
> Jalankan checklist di akhir guide dan laporkan satu per satu."

**Test verifikasi** (cek sendiri, bukan cuma laporan agent):
1. Minta fetch BTCUSDT 1h, beberapa hari data
2. Cek kolom timestamp — harus UTC (bukan WIB)
3. Manual hitung 1-2 baris pakai tabel boundary: UTC x → WIB x+7
4. Baris terakhir — pastikan bukan candle unclosed

**Tanda bahaya**: timestamp disimpan WIB, candle unclosed tidak dibuang.

---

## Langkah 2 — Stage 3: Replikasi Indikator

**Aset reusable**: `trading-research/indicators/` — SMI Pro v3, FBF v11,
ATR%, EMA Ribbon. Semua sudah jadi dan teruji.

**Yang perlu diverifikasi ulang**: akurasi layer fase/state. Kode di
trading-research mungkin fokus ke angka — cek apakah kolom fase
(zone_path, hist_state, pa_pd, cross event) sudah ada di output.

**Jika indikator sudah ada fase-nya**: tinggal copy ke `indicators/python/`,
validasi ulang ke beberapa candle sample, selesai.

**Jika indikator belum ada fase-nya**: perlu ditambah kolom fase mengikuti
spesifikasi di `stage_03_replikasi_indikator.md`.

**File yang dirujuk**: `stage_03_replikasi_indikator.md`, + source `.pine`

**Command**:
> "Baca `stage_03_replikasi_indikator.md`. Indikator yang sudah jadi ada di
> `trading-research/indicators/`. Copy yang relevan ke `indicators/python/`.
> Verifikasi DUA layer: angka mentah DAN teks fase/state. Output harus punya
> kolom teks fase gabungan yang bisa dicocokkan langsung ke tampilan dashboard
> chart. Kalau ada yang belum ada kolom fase-nya, tambahkan."

**Verifikasi dua layer**:
1. Layer angka: ambil 3-5 candle dari kondisi market berbeda, bandingkan
   nilai Python vs TradingView di candle yang sama
2. Layer fase: di candle yang sama, cocokkan teks fase/label Python dengan
   warna bar atau teks dashboard di chart

**Tanda bahaya**: cuma validasi angka, tidak ada kolom fase.

---

## Langkah 3 — Kalibrasi Setup (Bukan Tugas Coding)

Ini proses kalibrasi — agent bantu sajikan data, **keputusan sinyal valid
tetap di tangan lo**, bukan agent.

**Command**:
> "Ambil data [pair/timeframe] dari `[tanggal mulai]` sampai `[tanggal selesai]`.
> Tampilkan kondisi tiap indikator dan kolom fase di window itu, candle demi
> candle. Jangan simpulkan sendiri mana yang sinyal valid — aku yang akan
> tentukan setelah lihat datanya."

**Output agent**: tabel per candle: timestamp, nilai indikator, fase, + flag
event (cross, zone change, dll).

**Tugas lo**: tentukan mana sinyal valid, mana near-miss, koreksi interpretasi.
Lalu minta agent tuliskan ke `case_v{N}.md` sesuai template dan update
`00_case_tree.md`.

---

## Langkah 4 — Stage 5 & 4c: Skema Strategi + Core Engine

Ini bagian paling berat dan paling rawan bug.

**Aset referensi**: `trading-research/backtests/BTCUSDT/SETUP1/1D/setup1_v2b_clean.py`
— engine v2.b yang sudah teruji. Bisa jadi referensi arsitektur loop bar-by-bar,
tapi perlu di-generic-kan supaya tidak hardcode ke SETUP1 saja.

**Tiga keputusan WAJIB eksplisit** (jangan biarkan agent mutusin sendiri):

| # | Keputusan | Opsi | Default Disarankan |
|---|-----------|------|--------------------|
| 1 | Ambiguitas SL/TP dalam satu candle | SL duluan / TP duluan / granular data / heuristik | **SL duluan** (konservatif) |
| 2 | Posisi sizing | Fixed fractional / Compounding | **Fixed fractional** dulu (lebih mudah dibandingkan antar run) |
| 3 | Metode Stop Loss | Fixed % / ATR-based / Structure-based | Catat eksplisit per strategi |

**File yang dirujuk**: `stage_05_definisi_strategi.md`, `stage_04c_core_eksekusi_trade.md`

**Command**:
> "Baca `stage_05_definisi_strategi.md` dan `stage_04c_core_eksekusi_trade.md`.
> Buat skema `config.py`/`rules.py`/`metadata.md` di `strategies/_template/`,
> bangun core eksekusi di `backtest_engine/engine.py`, dan pastikan interface
> kontrak input-output ke semua strategi konsisten.
>
> Sebelum lapor selesai, konfirmasi eksplisit tiga hal ini ke aku:
> 1. Kebijakan ambiguitas SL/TP dalam satu candle (rekomendasi: SL duluan)
> 2. Fixed fractional vs compounding (rekomendasi: fixed fractional dulu)
> 3. Metode stop loss yang dipakai
>
> Jangan implementasikan pilihanmu sendiri tanpa konfirmasi."

**Verifikasi teknis**:
- Loop bar-by-bar (bukan vectorized)
- Entry pakai open candle setelah sinyal (bukan close candle sinyal)
- MAE/MFE di-track tiap candle
- Trade record cocok dengan struktur `Trade` di `metrics.py`
- Checklist stage 4c dan 5 dijalankan satu per satu

**Tanda bahaya**: agent langsung implementasi tanpa nanya 3 keputusan di atas,
atau enggak menyebutkan sama sekali bahwa itu keputusan yang perlu disepakati.

---

## Langkah 5 — Uji Coba di `sandbox/`

Sebelum strategi pertama masuk `strategies/` secara resmi, tes end-to-end
di sandbox dulu.

**Command**:
> "Jalankan backtest percobaan di `sandbox/experiments/exp_001_first_run/`
> pakai kombinasi [indikator/parameter] ini. Pakai data BTCUSDT 1D dari
> `trading-research/backtests/BTCUSDT/SETUP1/1D/data_BTCUSDT_1d_2021now.csv`.
> Ini masih eksperimen — hasilnya cukup ringkasan kasar dulu.
> Jalankan `metrics.py` di akhir, laporkan: total trades, EV per trade (R),
> win rate, max drawdown, sample size warning."

**Verifikasi**:
- Semua metric muncul lengkap, tidak ada NaN/inf
- Sample size warning sesuai (true kalau <30 trades)
- Cek `sandbox/log.md` terupdate

**Kalau lancar**: lanjut ke langkah 6 (strategi resmi).
**Kalau ada bug**: perbaiki dulu, jangan lanjut — bug di sandbox = bug di production.

---

## Langkah 6 — Strategi Resmi Pertama, Siklus 8 Langkah Penuh

Setelah sandbox lancar, mulai strategi resmi pertama mengikuti 8 langkah
alur operasional di `00_roadmap.md`:

1. Hipotesis → tulis di journal kenapa masuk akal
2. Indikator siap → cek `indicators/python/`, reuse kalau sudah ada
3. Kalibrasi setup → studi kasus riil, simpan di `case_studies/`
4. Rule strategi → tulis config+rules+metadata di `strategies/[nama]/`
5. Data siap → cek `data/raw/`, fetch kalau belum ada
6. Run backtest → engine jalan, metrics.py otomatis terpanggil
7. Update journal → catat versi, parameter, hasil, insight
8. Keputusan → tuning / expand / arsip

**Verifikasi akhir** sebelum strategi dianggap "selesai dites":
cross-check hasil dengan urutan prioritas baca di `stage_04_metrics_guide.md`:
sample size → EV → drawdown → ruin probability → metric pelengkap.

---

## Langkah 7 — Iterasi & Ekspansi

Setelah satu strategi solid di satu pair + satu timeframe:
- Expand ke pair lain → `data/raw/` fetch baru
- Expand ke timeframe lain → engine tinggal ganti config
- Tuning parameter → ubah `config.py`, bukan kode

---

## Prinsip Pengawasan Umum (Berlaku di Semua Langkah)

1. **Selalu minta agent merujuk nomor/nama guide** — kalau enggak bisa sebutkan
   guide mana yang jadi acuan, kemungkinan dia menebak dari pengetahuan umum.
2. **Jangan biarkan keputusan besar diputuskan diam-diam** — 3 keputusan di
   langkah 4 wajib dikonfirmasi eksplisit.
3. **Selalu minta tes kecil dulu sebelum full run** — 1 pair, 1 timeframe,
   rentang pendek.
4. **Update `00_roadmap.md` tiap satu bagian kelar** — ubah status di tree,
   tambah baris di Riwayat Update.
5. **Kalau ragu, minta agent jelasin balik pakai bahasa awam** — kalau
   penjelasannya muter-muter, ada yang enggak beres.
6. **Gunakan `sandbox/` untuk semua tes awal** — jangan langsung commit ke
   `strategies/` sebelum yakin.

---

## Mapping Stage ke Aset

| Stage | Apa yang Dibangun | Aset dari trading-research | Aset dari trading-lab |
|-------|-------------------|---------------------------|----------------------|
| 1 | Struktur folder | — | `stage_01_struktur_folder.md` |
| 2 | Data fetcher | `fetchers/data_fetcher.py` | `stage_02_data_dan_waktu.md` |
| 3 | Indikator Python | `indicators/smi_pro.py`, `fbf_v11/`, `atr_percentage.py`, `ema_ribbon.py` | `stage_03_replikasi_indikator.md` |
| 4 | Backtest engine | `backtests/BTCUSDT/SETUP1/1D/setup1_v2b_clean.py` (referensi) | `metrics.py`, `stage_04_metrics_guide.md`, `stage_04b`, `stage_04c` |
| 5 | Definisi strategi | `TRIGGER_SPEC_v2b.md`, `TRADE_TEMPLATE.md` | `stage_05_definisi_strategi.md`, `case_v00_template.md` |
| 6 | Run + jurnal | Data cache CSV | `results/` |
| 7 | Iterasi | Pola dari `backtests/BTCUSDT/SETUP1/` | Alur operasional di roadmap |

---

## Quick Reference — Folder yang Dipakai

```
trading-lab/                        trading-research/
├─ 00_roadmap.md                    ├─ fetchers/data_fetcher.py    ★
├─ 00_playbook_eksekusi_v2.md  ★    ├─ indicators/
├─ stage_02_data_dan_waktu.md       │   ├─ smi_pro.py              ★
├─ stage_03_replikasi_indikator.md  │   ├─ smi_events.py           ★
├─ stage_04_metrics_guide.md        │   ├─ fbf_v11/
├─ stage_04b_leverage_biaya_data.md │   │   ├─ fbf_v11_mhermes.py  ★
├─ stage_04c_core_eksekusi_trade.md │   │   └─ fbf_v11.pine        ★
├─ stage_05_definisi_strategi.md    │   ├─ atr_percentage.py
├─ metrics.py                  ★    │   └─ ema_ribbon.py
├─ data/raw/                        ├─ backtests/BTCUSDT/SETUP1/
├─ indicators/python/               │   ├─ TRIGGER_SPEC_v2b.md     ★
├─ strategies/_template/            │   ├─ 1D/setup1_v2b_clean.py  ★
├─ backtest_engine/                 │   └─ */data_*.csv            ★
├─ results/                         ├─ TRADE_TEMPLATE.md
├─ journal/                         ├─ lib/
├─ notebooks/                       └─ .venv_chart/
└─ sandbox/                    ★
    ├─ README.md
    ├─ log.md
    └─ experiments/

★ = file kunci, kasih ke agent di awal
```
