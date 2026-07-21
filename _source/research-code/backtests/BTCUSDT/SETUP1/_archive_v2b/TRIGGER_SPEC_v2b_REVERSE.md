# SETUP1 REVERSE LONG — TRIGGER SPEC v2.b

Status: WHAT-IF (exploratory, NOT locked).
Trigger IDENTIK dengan v2.b SHORT — gak ada perubahan logic entry.
Yang berubah cuma ARAH POSISI: sinyal bearish → buka LONG (counter-trend).

## Trigger Engine (IDENTIK v2.b Variant E)

```
FBF     = FBFEngine v11 (fbf_v11_backtest) — bear wave
SMI     = SMI Pro v3 (smi_events) — FMB → PD → XDN
ST      = Supertrend(10, 3) DOWN saat entry
Gate    = no-wait-C
Reset   = fmb_b=None, pd_b=None saat:
            WAVE_CANCELLED | WAVE_STRUCT_REJECTED |
            CANDIDATE_INVALIDATED | CANDIDATE_EVICTED
Wave    = 1 wave = 1 posisi (clear_bar via TP1x/SL)
```

Syarat entry (identik):
1. FMB[i] → fmb_b
2. PD[i] setelah fmb_b → pd_b
3. XDN[i] setelah pd_b + ST[i]==-1 → FIRE

## Rasional "Reverse"

Sinyal v2.b = bearish exhaustion. Saat FMB→PD→XDN komplit + ST DOWN,
harga sering udah di area bottom — momentum turun sisa dikit.

- **SHORT**: nangkap sisa momentum bearish → sering loss kecil (kena SL/reversal)
- **LONG**: nangkap reversal naik → lebih sering profit

Bukti session 2026-07-13:
- Entry 09 Jul 07:00 @ 62130 (SHORT #2 = LONG #1)
  SHORT → -0.234R, LONG → +0.162R — sinyal sama, arah beda.

## Regime Dependence (finding 2026-07-13)

| Periode        | Market      | Pemenang |
|----------------|-------------|----------|
| 2019-2025      | Bull market | LONG     |
| 2026 (Jan-Jun) | Bear market | SHORT    |

Di bull market → sinyal bearish = counter-trend → LONG menang.
Di bear market → sinyal bearish = trend-following → SHORT menang.

## File Referensi

- TRIGGER_SPEC_v2b.md — trigger asli (SHORT, LOCKED)
- SETUP_SPEC_v2b_REVERSE_LONG.md — setup LONG mirror
- _whatif_reverse_long.py — implementasi 1H (LONG)
