# SETUP1 — Batch Backtest (BTCUSDT SHORT)

Rumah untuk backtest SETUP1 versi BARU (batch-based).
Data lama SUDAH DIARSIP: `archive/backtests_SETUP1_legacy/`
(freeze, jangan diutak-atik).

## Struktur Sekarang (2026-07-12 cleanup)
- ENGINE utama cuma SATU: `1D/setup1_v2b_clean.py`
  (FBF v11 + SMI Pro v3 + v2.b Variant E).
- DATA tiap TF di-CACHE sekali jadi CSV
  (`data_BTCUSDT_<tf>_2021now.csv`). Gak perlu
  fetch ulang — engine tinggal baca CSV.
- Logic engine bisa di-copy ke TF lain
  (2H/4H) tergantung metode test saat itu.

## Data Cache (fetch sekali)
- `1D/data_BTCUSDT_1d_2021now.csv`   (2021..now)
- `2H/data_BTCUSDT_2h_2021now.csv`   (2021..now)
- `4H/data_BTCUSDT_4h_2021now.csv`   (2021..now)
Cara refresh: `python3 fetch_data_tf.py`

## Engine (RECENT only)
- `1D/setup1_v2b_clean.py`  ★ MAIN
  Engine v2.b terbaru. 5-trade backtest +
  chart. Dipakai sbg basis utk test lain.
- OLD engine (backtest_v11.py, backtest_2H/
  4H_legacy.py) SUDAH DIARSIP ke
  `1D/archive_clutter_2026-07-12/`.

## Trigger Spec Versions
- `TRIGGER_SPEC.md`     — v1 (FBF v6.10) & v2 (FBF v11) umum + v2.a rule
- `TRIGGER_SPEC_v2b.md` — **LOCKED v2.b = Variant E (reset only, sederhana)**
- `TRIGGER_SPEC_v2b_PROPOSAL.md` — proposal 5-gate (SUPERSEDED, strict alt)

## Helper
- `fetch_data_tf.py` — fetch & cache 2H/4H sekali.
- `run_all.sh`       — jalankan batch (legacy pattern).

## Indikator acuan (`../../../indicators/`)
- `smi_events.py`        — SMI Pro v3 (FMB→PD→XDN), trigger v2.b
- `fbf_v11/fbf_v11_mhermes.py` — FBF v11 strict
- `atr_percentage.py`    — ATR% (SL O3)
- Engine default FBF v11 ada di `/home/ubuntu/fbf_v11_backtest.py`

## Konvensi penamaan combo
- Kode: `S{SL}{EXIT}{TP}` → SL 1-5 (O1-O5), EXIT T=TP/L=TRAIL/S=STREV/R=RAWBRK,
  TP 1/2/3 atau `-`. Contoh: `S1T1`, `S4S-`, `S2R2`
- SL: LIQ/CATR/TATR/FIX/CHATR · EXIT: FIX/TRAIL/STREV/RAWBRK

## Catatan
- TF di engine: 1D=`1d`, 2H=`2h`, 4H=`4h`.
- START/END di-set di engine (`START`, `END`).
