# SETUP1 REVERSE LONG — SETUP SPEC

Status: WHAT-IF (exploratory, 2026-07-13).
Trigger v2.b TETAP SAMA, arah posisi LONG (counter-trend).

============================================================
I. KONSEP
============================================================

Sinyal v2.b = bearish exhaustion (FBF bear wave + SMI FMB→PD→XDN + ST DOWN).
Begitu sinyal firing, harga sering di bottom area → momentum turun sisa dikit.

Daripada SHORT (nangkap sisa bearish), buka LONG (nangkap reversal naik).

============================================================
II. SL OPTIONS (mirror SHORT → LONG)
============================================================

SHORT: SL di ATAS entry.
LONG:  SL di BAWAH entry.

  KODE  NAMA          SHORT                        LONG
  ─────────────────────────────────────────────────────────
  O1    Liq10x        entry × 1.10                 entry × 0.90
  O3    ATR%curr      entry×(1+apct/100)           entry×(1-apct/100)
  O6    ATR%1D        entry×(1+daily_apct/100)     entry×(1-daily_apct/100)

Valid check:
  SHORT: sl > entry
  LONG:  sl < entry

============================================================
III. TP PATOK (mirror)
============================================================

SHORT: tp = entry - n × (sl - entry)
LONG:  tp = entry + n × (entry - sl)

Risk distance:
  SHORT: risk = sl - entry
  LONG:  risk = entry - sl

Exit convention SAMA:
  ST_REV, RAWBRK → TP patok SELALU 3x risk
  TP standalone → bisa 1x/2x/3x

============================================================
IV. RAWBRK — LONG VERSION
============================================================

Mirror sempurna dari SHORT rawbreak:

  SHORT:  close < lastPivotLow  → rb_sl = HIGH candle rawbreak
          exit saat high >= rb_sl
          update: rb_sl = max(rb_sl, HIGH baru)

  LONG:   close > lastPivotHigh → rb_sl = LOW candle rawbreak
          exit saat low <= rb_sl
          update: rb_sl = min(rb_sl, LOW baru)

Fase:

  Fase 1 — PRA-RAW (floating, belum muncul):
    TP3x patok + SL awal aktif.
    Pantau tiap bar: close > lastPivotHigh?

  Fase 2 — RAW BREAK TERKONFIRMASI:
    Trigger: candle CLOSE > lastPivotHigh
    SL_rawbreak = LOW candle rawbreak
    Update  : SETIAP rawbreak baru → SL_rawbreak = LOW baru (turun)

  Fase 3 — EXIT setelah rawbreak:
    Harga balik < SL_rawbreak → RAWBRK_HIT
    TP3x kena duluan       → TP3x
    SL awal kena duluan     → SL

  Fase 4 — RAW BREAK TIDAK MUNCUL:
    Hanya 2 outcome: SL (-1R) atau TP3x (+3R)

Pivot detection: find_pivot_highs (bukan find_pivot_lows).

============================================================
V. ST_REV — LONG VERSION
============================================================

Mirror:

  SHORT:  exit saat ST flip -1 → +1
  LONG:   exit saat ST flip +1 → -1

TP3x patok sama.

============================================================
VI. COMBO FORMAT (sama)
============================================================

Format: [SL_opt] + [exit_mekanik] + [TP_patok]

  ST_REV, RAWBRK → TP SELALU 3x
  TP standalone → bebas

Contoh:
  O3 + RAWBRK + TP3x  = SL ATR%, exit rawbreak, TP3x LONG
  O6 + ST_REV + TP3x  = SL daily ATR%, exit ST flip, TP3x LONG
  O3 + TP1x           = SL ATR%, TP 1x, no exit mech

Outcome GLOSSARY (identik):
  HIT         : TP kena
  SL          : stop loss kena
  EXP         : expired (240 bar)
  ST_REV      : supertrend flip DOWN (long exit)
  RAWBRK_HIT  : rawbreak SL kena (long exit)

============================================================
VII. BACKTEST RESULTS (1H, 2019-2026)
============================================================

Dari session 2026-07-13, 1089 sinyal:

  FULL 2019-2026:
```
               SHORT        LONG
O1 TP1x        -59.07       ???      (LONG better)
O3 TP1x        +15.06       ???      (LONG better)
O6 TP1x        -66.71       ???
O1 TP3x       -295.86       ???
O3 TP3x        -65.00       ???
O6 TP3x       -296.80       ???
O1 RAWBRK      -52.88       ???
O3 RAWBRK      -88.08       ???      (LONG wins)
O6 RAWBRK     -118.39       ???
O1 ST_REV      -23.28       ???
O3 ST_REV      -65.50       ???
O6 ST_REV      -69.83       ???
```

  2026 ONLY (86 sinyal, Jan-Jun):
```
               SHORT        LONG
O1 TP1x         +2.22       -1.56    (SHORT wins di bear)
O3 TP1x         -9.60       +7.44    (LONG wins)
O6 TP1x         -3.34       -1.11
O1 TP3x        +47.14      -65.22    (SHORT BESAR)
O3 TP3x        +10.00       +5.57
O6 TP3x        +10.20      -21.74
O1 RAWBRK      +15.44       -8.15
O3 RAWBRK      -13.27       +9.58
O6 RAWBRK       +2.90       -9.46
O1 ST_REV       +2.23       +0.12
O3 ST_REV       +5.38       -0.86
O6 ST_REV       +6.70       +0.23
```

  Insight regime:
  - 2019-2025 bull market → LONG menang (counter-trend)
  - 2026 bear market → SHORT menang (trend-following)
  - Setup v2.b REGIME-DEPENDENT, bukan inherently counter/trend

============================================================
VIII. FILES
============================================================

  TRIGGER_SPEC_v2b_REVERSE.md      : trigger (v2.b, same)
  SETUP_SPEC_v2b_REVERSE_LONG.md   : this file
  _whatif_reverse_long.py          : implementasi 1H LONG
  SETUP_SPEC_v2b_FULL.md           : master SHORT (LOCKED)
  TRIGGER_SPEC_v2b.md              : trigger SHORT (LOCKED)
