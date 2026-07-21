# SETUP1 SHORT — TRIGGER SPEC v2.b (LOCKED: Variant E)

Status: LOCKED 2026-07-12. v2.b = Variant E (RESET ONLY).
Sederhana: tambah reset SMI tracker saat wave batal, TANPA gate tambahan.

## Keputusan User
"lock variant e aja, yang sederhana dulu untuk v2a kita"
→ v2.b = #1 reset only (WAVE_CANCELLED / WAVE_STRUCT_REJECTED /
  CANDIDATE_INVALIDATED / CANDIDATE_EVICTED → fmb_b=None, pd_b=None)
→ TIDAK pakai gate depth / maturity / smi_pd / st_cont (Variant B/C/D ditolak
  karena terlalu agresif / terlalu sedikit sinyal).

## Rationale (dari tes 2019-2026)
- Variant E: 43 sinyal, ST_REV O1 (+0.31) & O5 (+2.82) positif,
  sisanya negatif tapi JAUH lebih bersih dari BASE (47 sig, semua negatif).
- Reset tracker fix false signal #2 (Apr 12 2026: wave cancel tapi entry tetap fire).
- Gate B/C/D memang lebih "bersih" (ST_REV semua +) TAPI sample cuma 5 / 12 /
  2 → terlalu sedikit untuk di-lock sekarang. User mau yang sederhana dulu.

## Implementasi
File: sample_v2b.py (copy sample_v2a.py + 1 baris reset di event loop).
START sudah di 2019-01-01.

```python
elif e["event"] in ("WAVE_CANCELLED", "WAVE_STRUCT_REJECTED",
                     "CANDIDATE_INVALIDATED", "CANDIDATE_EVICTED"):
    fmb_b=None; pd_b=None
```

## EXIT Convention (LOCKED 2026-07-12, updated 2026-07-13)

ST_REV & RAWBRK → TP patok SELALU 3x risk.

ST_REV → Outcome: TP3x | ST_REV | SL
RAWBRK → Outcome: TP3x | RAWBRK_HIT | SL
  (Jika rawbreak tidak muncul → hanya 2: TP3x | SL)

TP standalone bisa 1x/2x/3x.

TRAIL → DIARSIPKAN 2026-07-13. Logic trailing belum benar
  (trail gak di-ratchet turun, = TP3x biasa). Akan diganti
  dengan logic baru kedepannya.

## RAWBRK Definition (LOCKED 2026-07-12)

Definisi dari Pine script FBF v11 (line 452-453):
```
rawBearCandidate = not na(lastPivotLow) and close < lastPivotLow
```

**close < pivot low terakhir. Tanpa filter apapun. Fractal break mentah.**

### Mekanik RAWBRK Exit
```
Fase 1 — PRA-RAW BREAK (floating, belum muncul):
  TP3x patok + SL awal aktif.
  Pantau: close < lastPivotLow?

Fase 2 — RAW BREAK TERKONFIRMASI:
  Trigger: candle CLOSE < lastPivotLow
  Action : SL_rawbreak = HIGH candle rawbreak tersebut
  Update : SETIAP rawbreak baru → SL update ke HIGH candle baru

Fase 3 — EXIT setelah rawbreak muncul:
  Harga balik > SL_rawbreak → RAWBRK_HIT (profit)
  TP3x kena duluan       → TP3x
  SL awal kena duluan     → SL

Fase 4 — RAW BREAK TIDAK PERNAH MUNCUL:
  Hanya 2 outcome: SL (-1R) atau TP3x (+3R)
```

### Case Study: Trade 2026-06-17
```
Entry: 64509.40 (bar 1993)
PL saat entry: 62272.07 (bar 1994)

Raw breaks:
  24 Jun (bar 2000): close=61077 < PL=62272 → RAW! SL=HIGH=63239.06
  25 Jun (bar 2001): close=59794 < PL=62272 → RAW! SL=HIGH=61962.40
  26 Jun (bar 2002): close=60097 < PL=62272 → RAW! SL=HIGH=60759.99
  27 Jun (bar 2003): close=60029 < PL=62272 → RAW! SL=HIGH=60941.17
  28 Jun+: PL ganti ke 58115, rawbreak STOP. SL final=60941.17

Exit:
  01 Jul (bar 2007): high=61334 > 60941.17 → RAWBRK_HIT!
  Profit: 64509.40 - 60941.17 = +3568.23
```

## Hasil Tes 2019-2026 (OLD — TP patok bervariasi, perlu RE-TEST dgn TP3x!)
Per-SL x EXIT (TotR):
  SL     TP1x    TRAIL   ST_REV
  O1    -4.23    -9.84    +0.31
  O2    -7.00    -6.09    -3.89
  O3    -3.00   -12.20    -7.99
  O4    -0.38   -13.37    -3.56
  O5    -0.33    -7.94    +2.82

Net per EXIT (sum O1-O5):
  TP1x  -14.94  WR 45.6%
  TRAIL -49.45  WR 31.6%
  ST_REV -12.30  WR 30.6%   ← O1/O5 positif

Note: RAWBRK LOCKED 2026-07-12 — close < lastPivotLow, SL=HIGH candle rawbreak.
TRAIL DIARSIPKAN 2026-07-13 — logic trailing gak benar, akan diganti baru.
⚠️ ST_REV di atas pakai TP patok bervariasi (bukan TP3x wajib).
   Perlu BACKTEST ULANG dengan aturan baru: ST_REV+TP3x.

## Catatan
- no-wait-C = C-lock BUKAN gate. Entry BOLEH sebelum C lock ATAU
  setelah C lock, asal SMI confirm. C gak syarat masuk maupun
  penghalang. (v2.b gak balik ke v1 wajib C_LOCKED.)
  SYARAT: tetap di dalam FBF window (wave/candidate masih hidup).
  Kalau keluar window → reset, SMI confirm jadi gugur:
    · keluar break ke ATAS (bear_active hilang)
    · WAVE_CANCELLED / WAVE_STRUCT_REJECTED
    · CANDIDATE_INVALIDATED / CANDIDATE_EVICTED
    · muncul wave BARU sebelum SMI sempat confirm
  → fmb_b=None, pd_b=None (reset v2.b). Setelah reset, nunggu
    wave/candidate baru + SMI confirm lagi.
- O2 (C+ATR14) lemah di semua variant kr no-wait-C → Ch=NaN → sering INV.
- O6 (ATR% 1D) — SL option baru (2026-07-13). ATR% diambil dari TF 1D,
  bukan TF entry. Gunanya: anchor SL ke volatilitas makro, lebih stabil
  di TF rendah (4H/2H/1H). Formula: entry × (1 + daily_atr_pct / 100).
  Belum di-backtest.
- Belum diuji di 4H/2H.
- Variant B (maturity>=10) tetep menarik buat future, simpan di
  TRIGGER_SPEC_v2b_PROPOSAL.md sebagai "strict alternative".

## TODO
- [x] Lock Variant E sebagai v2.b
- [ ] (optional) Test v2.b di 4H / 2H
- [ ] (optional) Verifikasi 43 sinyal ke TradingView
- [ ] (optional) Tweak: coba maturity=8/12 buat dapat ~8-10 sinyal (Variant B)
