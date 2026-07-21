# ARCHIVE — Indicators (dead / legacy)

Dipindah dari `indicators/` saat PHASE 1 cleanup (2026-07-12).
Tidak dipakai oleh engine aktif SETUP1 v2.b.

## File
- `fbf_v610.py`      — FBF v6.10 engine lama (AB manual). Cuma dipakai v1.
- `fbf_v64.py`       — FBF v6.4 Pine port. Tidak dipakai di backtest.
- `correlation.py`   — korelasi antar pair. Riset, tidak dipakai SETUP1.
- `fbf_breaks_*.csv` — output event FBF sampel (1h/4h alt + mhermes).
- `fbf_events_*.csv` — output event FBF sampel.

## Yang TETAP hidup di indicators/
- `smi_events.py`    — SMI Pro v3 (FMB→PD→XDN), engine v2.b AKTIF.
- `smi_pro.py`       — SMI Pro v3 base.
- `atr_percentage.py` — ATR% + BB (O3 SL).
- `ema_ribbon.py`    — EMA ribbon (filter trend opsional).
- `fbf_v11/`         — `fbf_v11_mhermes.py` (engine strict) + `fbf_v11.pine` (sumber).
                       Engine DEFAULT ada di `/home/ubuntu/fbf_v11_backtest.py`.
