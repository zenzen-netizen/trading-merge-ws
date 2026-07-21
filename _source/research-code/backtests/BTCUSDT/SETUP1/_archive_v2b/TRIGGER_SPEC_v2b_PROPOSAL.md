# SETUP1 SHORT — TRIGGER SPEC v2.b (PROPOSAL — SUPERSEDED)

Dokumen usulan awal (5 gate: #1 reset + #2 depth + #3 maturity + #4 smi + #5 st).
STATUS: DITOLAK untuk lock penuh. User pilih Variant E (RESET ONLY, sederhana).
Lihat TRIGGER_SPEC_v2b.md untuk spec yang DI-LOCK.

File ini tetap disimpan sebagai referensi "strict alternative" (Variant B/C/D)
kalau suatu saat mau naikkan kualitas filter.

## Temuan dari 4 trade 2026 (v2.a)

| # | Date | Entry | B | Hasil | Masalah |
|---|------|-------|-----|--------|---------|
| 1 | 12 Feb | 66272 | 60000 | ❌ LOSS | Entry dekat bottom, wave baru 6 hari, bounce kena SL |
| 2 | 12 Apr | 70741 | 65712 | ❌ FALSE | WAVE_CANCELLED 10 Apr tapi SMI tracker gak reset → entry 12 Apr, ST flip UP |
| 3 | 17 Jun | 64509 | 59131 | ✅ WIN | B dalam, SMI pullback 65, XDN clean, lanjut turun |
| 4 | 08 Jul | 62290 | 58115 | ⏳ OPEN | Mirror #3, SMI spike 72, masih floating |

SMI 3-step KONSISTEN di ke-4 trade. Bedanya ada di FBF wave quality + timing.

## 5 Usulan Perubahan (v2.b)

### #1 BUG FIX — reset SMI tracker
Saat event `WAVE_CANCELLED` / `WAVE_STRUCT_REJECTED` /
`CANDIDATE_INVALIDATED` → `fmb_b=None; pd_b=None`.
Fix #2 false signal (entry setelah wave batal). WAJIB.

### #2 WAVE DEPTH GATE (kualitas struktur)
Syarat: `(A - B) / A >= 0.15` (15%).
#2 gagal kr A-B cuma 8.8% (shallow noise). #3 lolos kr 28.6%.
Filter wave sampah.

### #3 WAVE MATURITY (umur minimal)
Syarat: `bar - WAVE_STARTED_bar >= 10`.
#1 gagal kr cuma 6 hari (terlalu segar). Cegah entry di awal wave.

### #4 SMI PULLBACK STRENGTH
Syarat: `SMI[pd_b] >= 40`.
#3/#4 punya SMI 65/72 (pullback kuat). Pastikan momentum reload.

### #5 ST CONTINUITY (konfirmasi arah)
Syarat: `ST[i]==-1` DAN `ST[i+1]==-1` (ST masih down setelah entry).
#2 gagal kr ST flip +1 besok. Cegah entry pasar mau balik up.

## Catatan "no-wait C"
Di 2026, C_LOCKED TDK PERNAH kejadian (semua entry sebelum C confirm).
Tapi #3/#4 TETAP menang → no-wait C boleh dipertahankan ASAL
gate #2+#3+#4 aktif. Alternatif: balikin ke v1 (wajib C_LOCKED),
tapi kurangi sinyal drastis.

## Estimasi dampak (2026)
- #2 → ilang (false signal, setelah fix #1)
- #1 → mungkin ilang (maturity <10)
- #3 → TETAP masuk (lolos semua gate)
- #4 → TETAP masuk (lolos semua gate)
Net: 4 → 2 sinyal, tapi kualitas naik.

## TODO
- [ ] Patch sample_v2a.py → sample_v2b.py (NEW file, jangan ubah v2.a)
- [ ] Test 2021-2026: v2.a vs v2.b, bandingkan jumlah + kualitas sinyal
- [ ] Pakai param SL/TP SAMA (O1-O5 × TP1x/TRAIL/ST_REV/RAWBRK) buat apple-to-apple
- [ ] Decida: lock v2.b atau tune threshold
