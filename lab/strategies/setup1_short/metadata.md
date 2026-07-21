# SETUP1 SHORT — Metadata

## Hipotesis

**Masuk short saat bear wave terkonfirmasi:**
FBF v11 deteksi fractal bear break (wave) + Supertrend(10,3) downtrend = trend bear.
SMI cross-confluence (FMB→PD→XDN) = momentum bear distribution.
Kombinasi tiga: struktur bear + distribusi momentum + trend confirm.

Kenapa masuk akal:
- Tiga filter independen — bukan satu indikator doang
- FBF struktur (wave fractal) gak bisa dipalsukan oleh noise biasa
- SMI distribution = smart money distribution phase
- ST downtrend = trend agreement dari sisi arah
- Logic: entry di fase distribusi bear dalam trend bear yang sudah terkonfirmasi struktur

## Versi
**v3** — aktif (sejak 14 Jul 2026)

| Versi | Status | Catatan |
|-------|--------|---------|
| v1 | ARSIP | Base FBF v6.10 (engine lama) |
| v2 | ARSIP | Base FBF v11, alur umum |
| v2.b | ARSIP | Variant E — reset conditional, bug cross-wave carry-over |
| **v3** | **AKTIF** | Full reset tiap WAVE_STARTED (fixed) |

## Core Logic
- Trigger: FMB → PD → XDN dalam **satu wave yang sama**
- Entry price: close bar XDN
- SL: O1 (Liq10x), O3 (ATR%30), O6 (ATR%1D)
- Exit: TP standalone (1x/2x/3x), ST_REV (TP3x + ST flip), RAWBRK (TP3x + raw break)
- Gate (implicit): Supertrend(10,3) downtrend saat entry
- Shared module: `indicators/python/setup1_trigger.py`

## Bug History
- **v2.b**: conditional reset (`if pd_b is None: fmb_b = None`) — 71% false ARMED di watcher, ~2-6% false signals di backtest
- **v3 fixed**: full reset (`fmb_b = None; pd_b = None`) setiap WAVE_STARTED

## Parameter
Lihat `config.py`.

## Acuan Case Study
`case_studies/` — belum ada (perlu kalibrasi setup).

## Dependencies
- `indicators/python/setup1_trigger.py` — shared trigger module (v3)
- `indicators/python/atr_percentage.py` — ATR% untuk SL O3
- Data harus punya kolom: SMI_FMB, SMI_PD, SMI_XDN, FBF_EVENT

## Riwayat Perubahan
| Versi | Tanggal | Apa yang berubah |
|-------|---------|------------------|
| v3 | 14 Jul 2026 | Full reset logic, drop unclosed candle, ARM guard |
| v3 | (sekarang) | Port ke trading-lab — config + rules terpisah, shared module terpisah |
