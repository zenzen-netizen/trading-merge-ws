# CHANGELOG v3 — SETUP1 Trigger Logic Consolidation

## Date: 14 Jul 2026

### What changed

Backtest trigger logic di-upgrade dari **v2.b → v3** untuk mencocokkan fix yang
sudah diterapkan di live watcher (14 Jul 2026).

### The bug (v2.b)

```python
# OLD — v2.b (watcher & backtest)
if e["event"] == "WAVE_STARTED":
    wave_entry_done = False
    if pd_b is None: fmb_b = None   # ← conditional reset
```

Hanya reset `fmb_b` kalau `pd_b` belum pernah fire. Akibatnya:
- Wave baru mewarisi FMB dari wave sebelumnya kalau PD sudah pernah terjadi
- 71% ARMED state di watcher adalah false (cross-wave carry-over)
- ~2-6% sinyal backtest adalah false (tergantung TF)

### The fix (v3)

```python
# NEW — v3 (watcher & backtest)
if e["event"] == "WAVE_STARTED":
    wave_entry_done = False
    fmb_b = None; pd_b = None      # ← full reset setiap wave baru
```

FMB, PD, dan XDN harus terjadi **dalam satu wave yang sama** biar signal valid.

### Additional fixes applied (same as watcher)

| Issue | v2.b | v3 |
|-------|------|----|
| Unclosed candle | ❌ Tidak di-drop | ✅ Drop forming candle sebelum compute |
| fmb_b/pd_b timing | ❌ Reset di bar XDN fire | ✅ Reset setelah bar snapshot |
| ARM guard | ❌ Tidak ada | ✅ Once ARMED, tidak overwrite |

### Impact on backtest results

**Signal count:**
- 1D: 43→41 (-2)
- 4H: 252→241 (-11)
- 2H: 482→457 (-25)
- 1H: 1090→1048 (-42)

**SumR delta:** Minor (0-9R per SL/TF dari 7 tahun). Arah kesimpulan backtest
tidak berubah — tetap negatif semua.

### Files archived

`_archive_v2b/` berisi:
- `setup1_v2b_1H.py`, `setup1_v2b_2H.py`, `setup1_v2b_4H.py`
- `setup1_v2b_1D_2019.py`, `setup1_v2b_1D_2023.py`, `setup1_v2b_1D_clean.py`
- `o6_backtest_v2b.py`
- `archive_clutter_1D/` — backtest v1/v11/v2a

### Shared module

`indicators/setup1_trigger.py` — SINGLE SOURCE OF TRUTH untuk logic trigger v3.
Import oleh backtest dan (via komentar referensi) watcher.

### Current files (v3, aktif)

| File | Purpose |
|------|---------|
| `setup1_v3_2019.py` | Multi-TF backtest with OLD vs NEW comparison |
| `setup1_v3_peryear.py` | Per-year breakdown (TP1x / RAWBRK / ST_REV) |
| `indicators/setup1_trigger.py` | Shared trigger logic module |
