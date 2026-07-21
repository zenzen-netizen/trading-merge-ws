# SETUP1 SHORT B — Metadata

## Hipotesis

**Short multi position — entry di setiap wave valid tanpa nunggu.**
Sama seperti A: FBF bear wave + SMI FMB→PD→XDN + ST DOWN = signal bear.
Bedanya: A nunggu posisi clear dulu, B gas terus tiap ada wave baru.

Kenapa B ada:
- Di cluster wave (beberapa wave bear beruntun), price sering lanjut turun
- A ketinggalan entry karena nunggu posisi clear
- B nangkap setiap wave — potensi lebih banyak profit, resiko over-exposure

## Root & Inspirasi

| Asal | Keterangan |
|------|-----------|
| **Root langsung** | `setup1_short_a` — config + rules 95% sama |
| **Inspirasi asli** | `v2 (plain)` di TRIGGER_SPEC.md — alur umum tanpa rule "1 wave = 1 posisi" |
| **Kondisi awal** | Ini yg dipake di watcher pertama kali sebelum v2.a nambahin gate |

B = yang awal sekali — free fire, deteksi semua wave, entry semua wave aktif.

## Versi
**v3 (multi position)** — trigger logic v3, beda: no position gate.

| Versi | Status | Catatan |
|-------|--------|---------|
| v2 (plain) | ARSIP | Free fire, base FBF v11, no gate |
| v3 B | **AKTIF** | Sama trigger v3, no position gate |

## Core Logic
- Trigger: IDENTIK A — FMB→PD→XDN dalam 1 wave (v3)
- Gate: TIDAK ADA posisi gate — tiap wave valid = tiap entry
- Entry price: close bar XDN
- SL: O1/O3/O6 (sama A)
- Exit: TP standalone, ST_REV, RAWBRK (sama A)

## Parameter
Lihat `config.py`.

## Referensi Design History
Lihat `setup1_short_a/DESIGN_HISTORY.md` — trigger evolution (v1→v2→v2.a→v2.b→v3).

## Dependencies
- `indicators/python/setup1_trigger.py` — shared trigger module
- `indicators/python/atr_percentage.py` — ATR% untuk SL

## Riwayat Perubahan
| Versi | Tanggal | Apa yang berubah |
|-------|---------|------------------|
| v3 B | (sekarang) | Port ke trading-lab — config + rules terpisah, multi position |
