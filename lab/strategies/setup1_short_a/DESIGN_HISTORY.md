# SETUP1 SHORT — Design History

Evolusi trigger logic SETUP1 SHORT dari awal sampai v3 final.

---

## v1 — Base FBF v6.10 (engine lama)

**Trigger:** AB manual (scan pivot) + SMI FMB→PD→XDN + ST down.
- A = pivot high, B = pivot low, syarat A_val > B_val
- bear break: close < B_val
- C confirm manual: close > B
- Entry: close bar XDN **setelah** C > B
- Gate: ST downtrend di bar C + bar XDN
- Validitas: close > A_val (wave bull batal) / C belum > B saat entry

**Engine:** `backtest.py` (archived).
**FBF:** v6.10 — manual AB, scan pivot.

---

## v2 (plain) — Alur Umum FBF v11

**Trigger upgrade:**
- FBF v11 (wave tracker + juri + ST-ATR + fibo zone) — engine default
- WAVE_STARTED (LOCK di B) cukup sebagai lock — **tidak perlu nunggu C**
- SMI dipantau paralel selama tracking C? (belum cancel)
- Begitu SMI 3-step lengkap (XDN) → **LANGSUNG entry** — tidak perlu C_LOCKED
- Entry = close XDN
- ST gate cukup di bar entry (gak perlu di bar C seperti v1)

**Karakter:** **free fire** — semua wave valid + SMI confirm = entry. Tidak ada batasan posisi per wave. Satu cluster wave bisa menghasilkan >1 posisi.

**File:** `TRIGGER_SPEC.md` (baris 57-95).

---

## v2.a — 1 Wave = 1 Posisi

**Tambahan rule di atas v2 plain:**
- Satu wave (WAVE_STARTED sampai wave selesai/cancel) = **maks 1 posisi**
- Setelah 1 posisi terbuka, wave-wave berikutnya diabaikan sampai posisi clear
- Clear = SL / TP / exit kena
- Tujuan: cegah over-trade / stacking posisi dalam 1 sesi

**Trigger engine SAMA dengan v2** — bedanya cuma di gate posisi.

**File:** `TRIGGER_SPEC.md` (baris 96-111).

---

## v2.b — Variant E (Reset Only)

**Locked 2026-07-12.** User memilih Variant E dari 5 proposal (A/B/C/D/E).

**Tambahan vs v2.a:**
- Reset SMI tracker saat wave batal:
  - WAVE_CANCELLED → `fmb_b=None; pd_b=None`
  - WAVE_STRUCT_REJECTED → `fmb_b=None; pd_b=None`
  - CANDIDATE_INVALIDATED → `fmb_b=None; pd_b=None`
  - CANDIDATE_EVICTED → `fmb_b=None; pd_b=None`

**Kenapa cuma reset?** (bukan variant B/C/D dengan gate depth/maturity/smi_pd):
- Variant B (maturity>=10): cuma 5-12 sinyal — sample terlalu kecil
- Variant C/D: terlalu agresif, sample sedikit
- E: 43 sinyal, ST_REV O1 (+0.31) & O5 (+2.82) positif — paling stabil

**BUG (ditemukan 14 Jul 2026):** Reset conditional:
```python
# v2.b — partial reset (BUG)
if pd_b is None: fmb_b = None
```
71% ARMED state di watcher false (cross-wave carry-over).
2-6% sinyal backtest false (tergantung TF).

**File:** `_archive_v2b/TRIGGER_SPEC_v2b.md`.

---

## v3 — Full Reset (FIX)

**Aktif sejak 14 Jul 2026.** Fix bug v2.b.

**Perubahan:**
- Full reset unconditional tiap WAVE_STARTED
- Drop forming candle sebelum compute (unclosed candle fix)
- fmb_b/pd_b timing: reset AFTER bar snapshot (not saat XDN fire)
- ARM guard: once ARMED, tidak overwrite

```python
# v3 — full reset
if e["event"] == "WAVE_STARTED":
    fmb_b = None; pd_b = None
```

**Dampak sinyal:**
| TF | v2.b | v3 | Delta |
|----|------|----|-------|
| 1D | 43 | 41 | -2 |
| 4H | 252 | 241 | -11 |
| 2H | 482 | 457 | -25 |
| 1H | 1090 | 1048 | -42 |

**SumR delta:** Minor (0-9R per SL/TF). Arah kesimpulan backtest tidak berubah.

**File:** `SETUP_SPEC_v3.md`, `CHANGELOG_v3.md`, `indicators/setup1_trigger.py`.

---

## Ringkasan Trigger Evolution

```
v1 (FBF v6.10, manual AB, wajib C)
 └─ v2 (FBF v11, no-wait-C, free fire)
      └─ v2.a (+ 1 wave = 1 posisi)
           └─ v2.b (+ reset on wave cancel — BUG: conditional)
                └─ v3 (full reset, unconditional — FIXED)
```

---

## Ringkasan Bug History

| Bug | Versi | Dampak | Fix |
|-----|-------|--------|-----|
| Cross-wave FMB/PD carry-over | v2.b | 71% false ARMED, 2-6% false signal | v3: full reset tiap WAVE_STARTED |
| Conditional reset | v2.b | Sisa tracker dari wave sebelumnya | v3: unconditional |
| Unclosed candle counted | v2.b | Sinyal di forming candle | v3: drop last candle |
| Order of operations | v2.b | Reset sebelum bar snapshot | v3: reset after snapshot |
| ARM overwrite | v2.b | ARMED state bisa diganti | v3: ARM guard |

---

## Varian Strategies (trading-lab)

| Strategy | Direction | Position Gate | Root |
|----------|-----------|---------------|------|
| `setup1_short_a` | SHORT | 1/wave (v3 final) | Direct — v3 |
| `setup1_short_b` | SHORT | Free fire (multi) | v2 plain |
| `setup1_mirror_long_a` | LONG | 1/wave | setup1_short_a (mirror) |
