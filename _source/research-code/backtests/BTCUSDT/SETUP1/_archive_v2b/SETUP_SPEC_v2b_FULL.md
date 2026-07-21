# SETUP1 SHORT — MASTER SPEC v2.b

Status: LOCKED 2026-07-12
Nama: "Vortex Break" (v2.b Variant E + RAWBRK)

============================================================
I. TRIGGER ENGINE
============================================================

Nama: v2.b = Variant E (RESET-ONLY)
File: setup1_v2b_2023.py

Engine:
  FBF     = FBFEngine v11 (fbf_v11_backtest)
  SMI     = SMI Pro v3 (smi_events: FMB → PD → XDN)
  ST      = Supertrend(10, 3) DOWN saat entry
  Gate    = no-wait-C (C_LOCKED bukan syarat)
  Reset   = fmb_b=None, pd_b=None saat:
              WAVE_CANCELLED | WAVE_STRUCT_REJECTED |
              CANDIDATE_INVALIDATED | CANDIDATE_EVICTED
  Wave    = 1 wave = 1 posisi (clear_bar via TP1x/SL)

Syarat entry:
  1. FMB[i] → fmb_b
  2. PD[i] setelah fmb_b → pd_b
  3. XDN[i] setelah pd_b + ST[i]==-1 → FIRE

Lock rationale:
  - Variant E: 43 sinyal (2019-2026), ST_REV O1/O5 positif
  - Reset fix false signal #2 (wave cancel tp entry tetap fire)
  - Gate B/C/D terlalu sedikit sinyal (5/12/2), user mau simpel

============================================================
II. SL OPTIONS (6 opsi)

  KODE  NAMA          FORMULA                    KARAKTER
  ─────────────────────────────────────────────────────────
  O1    Liq10x        entry × 1.10               10% lebar
  O2    C+ATR14       C_high + ATR(14)           perlu C locked
  O3    ATR%30        entry×(1+apct/100)         ATR% current TF, ketat
  O4    Fix6%         entry × 1.06               6% fixed
  O5    ConfHi+ATR    ConfHi + ATR(14)           perlu confirmation high
  O6    ATR%1D        entry×(1+daily_atr_pct/100) ATR% anchor ke 1D, stabil

  Yang sudah di-backtest: O1 (Liq10x), O3 (ATR%)
  Belum: O2 (butuh C lock), O4 (fix%), O5 (butuh ConfHi), O6 (ATR% 1D)

  Catatan O6:
  - Sumber ATR% SELALU dari timeframe 1D, bukan TF entry
  - Gunanya: SL ter-anchor ke volatilitas makro, gak kegoyang noise intraday
  - Di TF rendah (4H/2H/1H), O6 lebih lebar & stabil dibanding O3
  - Risk = daily_atr_pct, bukan current TF atr_pct
  - Contoh: entry 4H di $64,000, ATR% 1D=4.7% → SL=$67,008
            vs O3 ATR% 4H=2.1% → SL=$65,344 (lebih ketat)

============================================================
III. TP PATOK & EXIT MEKANIK

Rule wajib:
  ST_REV, RAWBRK → TP patok SELALU 3x risk
  TP standalone → bisa 1x/2x/3x

Exit mekanik (3 jenis) + 1 DIARSIPKAN:

  A. TP standalone
     - TP 1x/2x/3x, gak ada exit mekanik lain
     - Outcome: TP | SL

  B. ST_REV (Supertrend Reversal)
     - TP3x patok, exit pas ST flip -1→+1
     - Outcome: TP3x | ST_REV | SL

  C. RAWBRK (Raw Break — LOCKED 2026-07-12)
     - TP3x patok
     - Exit: close < lastPivotLow → SL=HIGH rawbreak, trailing
     - Outcome: TP3x | RAWBRK_HIT | SL
     - Jika rawbreak gak muncul: TP3x | SL (2 outcome)

  X. TRAIL (Trailing Stop) — DIARSIPKAN 2026-07-13
     - Alasan: simulasi trailing belum diimplementasi dgn benar
       (trail gak di-ratchet, = TP3x biasa). User akan beri logic
       trailing baru kedepannya. Untuk sekarang jadi noise.
     - File arsip: ./archive/trail_draft_20260713.md

============================================================
IV. RAWBRK — DEFINISI (LOCKED 2026-07-12)

Sumber : FBF v11 Pine L452-453
Def    : close < lastPivotLow (fractal break mentah, 0 filter)

   rawBearCandidate = not na(lastPivotLow) and close < lastPivotLow

Mekanik:

  Fase 1 — PRA-RAW (floating, belum muncul):
    TP3x patok + SL awal aktif.
    Pantau tiap bar: close < lastPivotLow?

  Fase 2 — RAW BREAK TERKONFIRMASI:
    Trigger: candle CLOSE < lastPivotLow
    SL_rawbreak = HIGH candle rawbreak
    Update  : SETIAP rawbreak baru → SL_rawbreak = HIGH baru

  Fase 3 — EXIT setelah rawbreak:
    Harga balik > SL_rawbreak → RAWBRK_HIT
    TP3x kena duluan       → TP3x
    SL awal kena duluan     → SL

  Fase 4 — RAW BREAK TIDAK MUNCUL:
    Hanya 2 outcome: SL (-1R) atau TP3x (+3R)

Case study: Trade 2026-06-17
  Entry  : 64509.40
  PL ref : 62272.07
  RAW 24Jun: close=61077 → SL=63239
  RAW 25Jun: close=59794 → SL=61962
  RAW 26Jun: close=60097 → SL=60760
  RAW 27Jun: close=60029 → SL=60941
  28Jun+   : PL ganti 58115 → rawbreak STOP, SL final=60941
  Exit 01Jul: high=61334 > 60941 → RAWBRK_HIT (+3568)

============================================================
V. COMBO FORMAT

Format: [SL_opt] + [exit_mekanik] + [TP_patok]

  ST_REV, RAWBRK → TP SELALU 3x
  TP standalone → bebas

Contoh:
  O3 + RAWBRK + TP3x  = SL ATR% current TF, exit rawbreak, TP3x
  O6 + RAWBRK + TP3x  = SL ATR% 1D anchor, exit rawbreak, TP3x
  O5 + ST_REV + TP3x  = SL ConfHi+ATR, exit ST flip, TP3x
  O1 + TP2x           = SL Liq10x, TP 2x, no exit mech

Outcome GLOSSARY:
  HIT         : TP kena
  SL          : stop loss kena
  EXP         : expired (240 bar, gak kena apa2)
  ST_REV      : supertrend flip
  RAWBRK_HIT  : rawbreak SL kena
  ~~TRAIL_HIT~~ : DIARSIPKAN 2026-07-13

============================================================
VI. BACKTEST RESULTS

### Test 1: TP=1x, SL=ATR%/Liq10x, RAWBRK only (2023-2026)
File: setup1_v2b_2023.py  |  20 sinyal

  ATR%:
    TP(+1R): 9 | SL: 10 | RAWBRK_HIT: 1 | SumR: -1.34 | WR: 47.4%

  Liq10x:
    TP(+1R): 4 | SL: 6 | RAWBRK_HIT: 9 | EXP: 1 | SumR: -2.05 | WR: 40.0%

### Test 2: TP=3x, SL=ATR%/Liq10x, RAWBRK only (2023-2026)
File: setup1_v2b_2023.py  |  20 sinyal

  ATR%:
    TP(+3R): 1 | SL: 14 | RAWBRK_HIT: 5 | SumR: -10.36 | WR: 5.0%
    RAWBRK R: +0.64 (rata2 +0.13/hit)

  Liq10x:
    TP(+3R): 0 | SL: 7 | RAWBRK_HIT: 12 | EXP: 1 | SumR: -5.92 | WR: 0.0%
    RAWBRK R: +1.30 (rata2 +0.11/hit)

  Insight:
    - TP3x terlalu jauh utk BTC setup1 short
    - RAWBRK berfungsi sbg "damage control" (selamatkan 0.1-0.5R)
    - Rata-rata rawbreak cuma 1 candle → SL rawbreak dekat entry

### Historical: OLD 5-SL x EXIT (2019-2026, 43 sinyal, TP bervariasi)
Dari TRIGGER_SPEC_v2b.md:
  O1  TP1x:-4.23  TRAIL:-9.84  ST_REV:+0.31
  O2  TP1x:-7.00  TRAIL:-6.09  ST_REV:-3.89
  O3  TP1x:-3.00  TRAIL:-12.20 ST_REV:-7.99
  O4  TP1x:-0.38  TRAIL:-13.37 ST_REV:-3.56
  O5  TP1x:-0.33  TRAIL:-7.94  ST_REV:+2.82  ← BEST

  ⚠️ TRAIL column = archaic (DIARSIPKAN 2026-07-13). Data historis,
     logic trailing belum benar → jangan dipakai sbg acuan.

============================================================
VII. TODO

  [x] Lock Variant E sebagai v2.b trigger
  [x] RAWBRK definisi baru (close < PL, SL=HIGH rawbreak)
  [x] TP3x + RAWBRK test 2023-2026
  [ ] Re-test TRAIL+TP3x, ST_REV+TP3x dengan semua 5 SL
  [ ] Coba TP2x — midpoint antara 1x (sering kena) & 3x (jarang)
  [ ] Implement O4 (Fix6%), O5 (ConfHi+ATR), O6 (ATR% 1D)
  [ ] Backtest O6 + semua exit mekanik di 4H/2H/1H
  [ ] Test di 4H / 2H
  [ ] Verifikasi sinyal ke TradingView chart

============================================================
VIII. FILES

  TRIGGER_SPEC_v2b.md         : trigger spec (Variant E lock)
  SETUP_SPEC_v2b_FULL.md      : this file — master spec
  TRADE_TEMPLATE.md           : template per-trade journal
  setup1_v2b_2023.py          : backtest script (2023+, TP3x, RAWBRK)
  setup1_v2b_clean.py         : backtest script (full, 5-trade recent)
  sample_v2b.py (archive)     : v2.b trigger only
  fbf_v11_backtest.py         : FBF engine
  smi_events.py               : SMI Pro v3
  atr_percentage.py           : ATR% calculator
