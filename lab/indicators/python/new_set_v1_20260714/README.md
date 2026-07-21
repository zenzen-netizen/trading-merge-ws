# new_set_v1 — Batch Replikasi Indikator (2026-07-14)

Batch **BARU**, terpisah dari replika lama di `indicators/python/` root.
Dibangun dari nol mengikuti `stage_01_struktur_folder.md` + `stage_03_replikasi_indikator.md`.
File lama (`smi_pro.py`, `ema_ribbon.py`, `atr_percentage.py`, `fbf_v11/`) **tidak disentuh**.

## Mapping pine → python

| # | Pine source (`pine_source/new_set_v1_20260714/`) | Python (`python/new_set_v1_20260714/`) | Indikator |
|---|---|---|---|
| 1 | `fbf_v11_1.pine`        | `fbf_v11_1.py`        | Fractal Break Filter v11.1 |
| 2 | `smi_pro_v3.pine`       | `smi_pro_v3.py`       | TOP SMI Pro Enhanced v3 |
| 3 | `atr_percentage.pine`   | `atr_percentage.py`   | ATR Percentage + BB |
| 4 | `robust_momcand.pine`   | `robust_momcand.py`   | Robust + MomCand Signal |
| 5 | `ema_ribbon_v11.pine`   | `ema_ribbon_v11.py`   | EMA Ribbon Pro v11 |
| 6 | `rsi_pro_enhanced.pine` | `rsi_pro_enhanced.py` | RSI Pro Enhanced |

## Aturan replikasi (wajib per file)

- **2 layer**: numerik (nilai mentah) + fase/state (kategori/label), sesuai stage_03.
- **Kolom teks-fase gabungan** = target validasi visual utama.
- `==` persis vs `>=` dijaga sesuai asli (counter PA/PD = pulse 1-bar).
- Referensi antar-bar diproses berurutan per-bar, no lookahead.
- Sinyal pivot (divergence) = delay konfirmasi sebesar `rightBars`/`lbR`.
- HTF via resample, no lookahead (barmerge.lookahead_off).
- Urutan if-elif cascade dijaga persis.

## Runner / validasi

Tiap `.py` punya blok `__main__`:
- baca `data/raw/BTCUSDT_1d_20260705_20260713.csv`
- hasilkan tabel per-candle: `timestamp`, nilai numerik, kolom fase/state, kolom teks-fase gabungan
- tulis CSV ke `results/new_set_v1_20260714/<name>_percandle.csv`
- print ringkas (tail window) ke stdout

Jalankan dari root repo: `python -m indicators.python.new_set_v1_20260714.<name>`
