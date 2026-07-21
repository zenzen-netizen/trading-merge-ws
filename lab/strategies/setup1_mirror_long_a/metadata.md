# SETUP1 MIRROR LONG A — Metadata

## Hipotesis

**Counter-trend LONG — sinyal bearish exhaustion dipakai buat entry LONG.**
Sinyal FBF bear wave + SMI FMB→PD→XDN + ST DOWN = bearish exhaustion.
Harga sering di area bottom saat signal fire — momentum turun sisa dikit.

Daripada SHORT (nangkap sisa bearish), buka LONG (nangkap reversal naik).

Teori regime:
- Bull market → LONG menang (counter-trend nyambung ke trend utama)
- Bear market → SHORT menang (trend-following)

## Root & Inspirasi

| Asal | Keterangan |
|------|-----------|
| **Root langsung** | `setup1_short_a` — trigger IDENTIK (FMB→PD→XDN), cuma arah dibalik |
| **Referensi riset** | `trading-research/backtests/BTCUSDT/SETUP1/_archive_v2b/TRIGGER_SPEC_v2b_REVERSE.md` |
| | `trading-research/backtests/BTCUSDT/SETUP1/_archive_v2b/SETUP_SPEC_v2b_REVERSE_LONG.md` |
| | `trading-research/backtests/BTCUSDT/SETUP1/1H/_whatif_reverse_long.py` |
| **Status riset** | WHAT-IF (exploratory, 2026-07-13). Belum divalidasi final. |

## Versi
**v3 (mirror)** — trigger v3, arah LONG.

| Versi | Status | Catatan |
|-------|--------|---------|
| v2.b reverse | WHAT-IF | Explore 1H, 1089 sinyal 2019-2026, regime-dependent |
| **v3 mirror A** | **AKTIF (eksperimental)** | Port ke trading-lab, 1 posisi per wave |

## Core Logic
- Trigger: IDENTIK short_a — bearish exhaustion signal
- Arah: LONG (counter-trend)
- Entry price: close bar XDN
- SL: O1 (entry*0.90), O3 (entry*(1-apct/100)), O6 (entry*(1-daily_apct/100)) — mirror
- Exit: TP standalone, ST_REV (ST flip +1→-1), RAWBRK (close > pivot high)
- Position: 1 wave = 1 posisi (sama short_a)

## Catatan Riset
- 1H backtest (2019-2026): 1089 sinyal, net R bervariasi per SL+exit combo
- 2026 Jan-Jun (86 sinyal): O3 TP1x +7.44R, O3 RAWBRK +9.58R (LONG menang)
- Tapi O1 TP3x -65.22R, O6 TP3x -21.74R (SHORT menang besar di bear 2026)
- **Kesimpulan: regime-dependent.** Bukan inherently profitable.

## Parameter
Lihat `config.py`.

## Referensi Design History
Lihat `setup1_short_a/DESIGN_HISTORY.md` — trigger evolution (v1→v2→v2.a→v2.b→v3).

## Dependencies
- `indicators/python/setup1_trigger.py` — shared trigger module (SAME)
- `indicators/python/atr_percentage.py` — ATR% untuk SL

## Riwayat Perubahan
| Versi | Tanggal | Apa yang berubah |
|-------|---------|------------------|
| v3 mirror A | (sekarang) | Port ke trading-lab — config + rules terpisah, LONG variant |
