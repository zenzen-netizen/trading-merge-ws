# Index & Peta Semua Guide

File ini jawab dua pertanyaan: **guide apa aja yang udah ada**, dan **kapan masing-masing dibaca**. Bukan pengganti `00_roadmap.md` (itu tetap anchor utama), ini cuma peta supaya gampang nemuin guide yang relevan tanpa bongkar folder satu-satu.

---

## Tree Kategori

```
Semua Guide Project
│
├─ ANCHOR — baca duluan, kapan pun, terutama pas mulai sesi baru
│   ├─ 00_roadmap.md
│   │   (project brief, status build tiap stage, alur kerja operasional)
│   ├─ 00_playbook_eksekusi_ai_agent.md
│   │   (urutan tindakan konkret: file apa dikasih ke AI agent, command
│   │    apa, cara verifikasi tiap tahap — dipakai pas mulai eksekusi beneran)
│   └─ 00_playbook_eksekusi_v2.md  ★ TERBARU
│       (versi lebih detail: integrasi trading-research/, daftar aset
│        reusable, keputusan wajib eksplisit per stage)
│
├─ PANDUAN BANGUN SISTEM — dibaca pas lagi ngerjain bagian itu
│   ├─ stage_01_struktur_folder.md       → bingung naruh file di mana
│   ├─ stage_02_data_dan_waktu.md        → kerja data/fetcher, timezone WIB vs UTC
│   ├─ stage_03_replikasi_indikator.md   → replikasi indikator Pine → Python
│   ├─ stage_04_metrics_guide.md         → baca/analisis hasil backtest
│   ├─ stage_04b_leverage_biaya_data.md  → strategi pakai leverage/perp
│   ├─ stage_04c_core_eksekusi_trade.md  → bangun logic eksekusi backtest engine
│   └─ stage_05_definisi_strategi.md     → formalize rule strategi jadi kode
│
├─ TEMPLATE OPERASIONAL — dipakai berulang, tiap kali ada strategi baru
│   └─ strategies/_template/case_studies/
│       ├─ case_v00_template.md   (copy jadi case_v1.md, v2, dst)
│       └─ 00_case_tree.md        (copy juga, jadi tracker versi per strategi)
│
├─ SANDBOX — eksperimen bebas sebelum komit ke siklus resmi
│   └─ sandbox/
│       ├─ README.md   (aturan main sandbox)
│       ├─ log.md      (ringkasan semua eksperimen)
│       └─ experiments/ (satu folder per eksperimen: exp_NNN_nama/)
│
└─ ASET EKSTERNAL — folder lain di VPS yang bisa dipakai
    └─ trading-research/  (/home/ubuntu/trading-research/)
        ├─ fetchers/data_fetcher.py     (Binance OHLCV, UTC, drop unclosed)
        ├─ indicators/ (SMI Pro v3, FBF v11, ATR%, EMA Ribbon)
        ├─ backtests/BTCUSDT/SETUP1/    (engine v2.b, spec, data cache CSV)
        ├─ lib/ (format/extract helpers)
        └─ .venv_chart/ (venv: numpy, pandas, matplotlib)
```

---

## Urutan Baca Kalau Baru Mulai (Onboarding Diri Sendiri atau AI Baru)

1. `00_roadmap.md` — selalu paling awal.
2. `stage_01_struktur_folder.md` — biar paham peta folder.
3. Sisanya **tidak perlu urut** — tinggal loncat ke guide sesuai stage yang lagi dikerjakan (lihat tabel kategori di atas).

---

## Cara Pakai Cepat (Skenario Sehari-hari)

| Situasi | Buka File |
|---|---|
| Lupa lagi progress di mana / ngapain | `00_roadmap.md` |
| Mau mulai strategi baru | Copy folder `case_studies/` dari template, ikuti 8 langkah alur operasional di `00_roadmap.md` |
| Lagi baca hasil backtest, bingung angkanya | `stage_04_metrics_guide.md` |
| Strategi bakal pakai leverage | `stage_04b_leverage_biaya_data.md` |
| Mau tau kenapa suatu keputusan diambil di masa lalu | Riwayat Update di `00_roadmap.md`, atau `metadata.md` strategi terkait |
| Bingung status stage tertentu udah sejauh mana | Tree "Status Pembangunan Sistem" di `00_roadmap.md` |
| Mau mulai eksekusi beneran pakai AI coding agent | `00_playbook_eksekusi_v2.md` (atau v1 untuk versi ringkas) |
| Mau coba-coba ide tanpa proses formal | `sandbox/README.md`, lalu `sandbox/experiments/` |
| Mau lihat aset kode yang sudah ada & bisa dipakai ulang | `00_playbook_eksekusi_v2.md` bagian "Aset Reusable" |

---

## Aturan Menambah Guide Baru

Setiap kali guide baru dibuat untuk stage yang belum punya:

1. Tambahkan baris guide-nya di tree kategori file ini.
2. Update link guide di tree `00_roadmap.md` (bagian Status Pembangunan Sistem).
3. Tambahkan satu baris di Riwayat Update `00_roadmap.md`.

Tiga langkah ini yang bikin semua dokumen tetap sinkron satu sama lain — jangan cuma bikin file guide-nya doang tanpa nyambungin ke dua tempat itu.
