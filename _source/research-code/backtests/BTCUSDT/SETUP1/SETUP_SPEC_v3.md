# SETUP1 SHORT — MASTER SPEC v3

Status: **AKTIF**  (sejak 14 Jul 2026)
Ini menggantikan v2.b yang diarsipkan.

| Version | Status  | Catatan                                |
|---------|---------|----------------------------------------|
| v2.b    | ARSIP   | Bug: cross-wave FMB/PD carry-over      |
| **v3**  | **AKTIF** | Full reset tiap WAVE_STARTED (fixed) |

## Core File

**Trigger logic (source of truth):**
  `indicators/setup1_trigger.py` — dipake sama watcher cron + backtest.

**Backtest scripts (multi-TF):**
  `backtests/BTCUSDT/SETUP1/setup1_v3_2019.py`    — main (all TFs, OLD vs NEW)
  `backtests/BTCUSDT/SETUP1/setup1_v3_peryear.py` — per-year breakdown

---

## I. TRIGGER ENGINE

Nama: v3
Engine:
  FBF     = FBFEngine v11 (fbf_v11_backtest)
  SMI     = SMI Pro v3 (smi_events: FMB → PD → XDN)
  ST      = Supertrend(10, 3) DOWN saat entry
  Gate    = no-wait-C (C_LOCKED bukan syarat)

**Reset logic (FIX vs v2.b):**
```python
# v2.b (BUG) — partial reset
if e["event"] == "WAVE_STARTED":
    if pd_b is None: fmb_b = None   # ← conditional

# v3 (FIXED) — full reset setiap wave baru
if e["event"] == "WAVE_STARTED":
    fmb_b = None; pd_b = None        # ← unconditional
```

FMB → PD → XDN harus terjadi dalam **satu wave yang sama**.
Tidak ada carry-over FMB/PD dari wave sebelumnya.

**Reset juga di (sama seperti v2.b):**
- WAVE_CANCELLED
- WAVE_STRUCT_REJECTED
- CANDIDATE_INVALIDATED
- CANDIDATE_EVICTED

**Syarat entry:**
1. WAVE_STARTED sudah terjadi (AB locked di B)
2. FMB[i] → fmb_b tercatat
3. PD[i] setelah fmb_b → pd_b tercatat
4. XDN[i] setelah pd_b + ST[i]==-1 → FIRE entry
5. Entry price = close bar XDN

---

## II. SL OPTIONS (3 opsi, di-backtest)

| KODE | NAMA          | FORMULA                         | KARAKTER                      |
|------|---------------|---------------------------------|-------------------------------|
| O1   | Liq10x        | entry × 1.10                    | Fixed 10%, simple, lebar      |
| O3   | ATR%30        | entry × (1 + apct/100)          | ATR% current TF, dinamis      |
| O6   | ATR%1D        | entry × (1 + daily_apct/100)    | ATR% 1D anchor, stabil        |

Semua sudah diuji di 1D/4H/2H/1H (2019-2026).

---

## III. EXIT MEKANIK

Aturan TP:
- ST_REV, RAWBRK → TP patok = 3x risk
- TP standalone → bebas (1x/2x/3x)

**A. TP standalone**
  Exit saat TP atau SL kena.
  Outcome: TP | SL | EXP

**B. ST_REV (Supertrend Reversal)**
  TP3x patok, exit pas ST flip -1→+1.
  Outcome: TP3x | ST_REV | SL | EXP

**C. RAWBRK (Raw Break)**
  TP3x patok.
  Fase 1 — floating: pantau close < lastPivotLow
  Fase 2 — rawbreak: close < PL → SL_rawbreak = HIGH candle
  Fase 3 — exit: harga > SL_rawbreak → RAWBRK_HIT
  Outcome: TP3x | RAWBRK_HIT | SL | EXP
  Jika rawbreak tidak muncul: TP3x | SL | EXP

---

## IV. SHARED MODULE

`indicators/setup1_trigger.py` adalah **single source of truth**.

Fungsi:
- `detect_signals_v3()` — trigger detection (full wave reset)
- `supertrend_full()` — ST(10,3)
- `find_pivot_lows()` — pivot lows (left=3, right=3)
- `sim_rawbrk()` — trade sim with rawbreak
- `sim_strev()` — trade sim with ST reversal
- `sl_o1()`, `sl_o3()`, `sl_o6()` — SL helpers

Imported oleh:
- `setup1_v3_2019.py` — via `from indicators.setup1_trigger import ...`
- `setup1_v3_peryear.py` — via `from setup1_trigger import ...`
- `live_signal_watcher.py` — logic sama (inline, fix diterapkan 14 Jul)

---

## V. BACKTEST RESULTS (v3 vs v2.b)

Semua data di 1D/4H/2H/1H BTCUSDT, 2019-2026.

### Signal count
```
TF     v2.b    v3    Δ
1D      43     41    -2   (-4.7%)
4H     252    241   -11   (-4.4%)
2H     482    457   -25   (-5.2%)
1H    1090   1048   -42   (-3.9%)
```

### Dampak ke SumR
Selisih 0-9R per SL/TF per tahun. KECIL — karena backtest punya
skip-ahead (clear_bar) yang alami nge-filter false signals.
*Arah kesimpulan backtest tidak berubah.*

---

## VI. FILE STRUCTURE

```
SETUP1/
├── setup1_v3_2019.py          ← Multi-TF backtest (OLD vs NEW)
├── setup1_v3_peryear.py       ← Per-year breakdown
├── SETUP_SPEC_v3.md           ← THIS FILE — master spec v3
├── TRIGGER_SPEC.md            ← Conceptual trigger spec (umum)
├── CHANGELOG_v3.md            ← Catatan perubahan v2.b→v3
├── _archive_v2b/              ← Semua file v2.b (spec + script)
├── 1H/ 2H/ 4H/ 1D/           ← CSV data per TF
└── ...
```

---

## VII. REVERSE LONG

Trigger sama persis (FMB→PD→XDN), arah dibalik ke LONG.
Mirror SL/TP:
  - Untuk SHORT: SL > entry, TP < entry
  - Untuk LONG:  SL < entry, TP > entry

Trigger berlaku di ST uptrend (+1), ST flips ke -1 untuk exit ST_REV.
Untuk pivot reference pakai pivot HIGH (bukan pivot LOW).
Active file: `indicators/setup1_trigger.py` — detect_signals_v3()
bisa di-reuse dengan param dibalik.
