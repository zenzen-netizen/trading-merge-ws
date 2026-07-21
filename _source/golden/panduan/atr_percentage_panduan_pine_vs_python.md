# ATR Percentage — Panduan Review Pine ↔ Python

> Bagian dari seri deep-dive review indikator (`handoff_review_indikator.md`).
> Indikator ke-3 yang direview, setelah FBF (Fractal Break Filter v11.1) dan
> SMI Pro Enhanced v3.

**Status akhir: SELESAI. Tidak ada patch kode. `atr_percentage.py` (v1.0) tetap dipakai apa adanya.**

---

## 0. Kenapa Review Ini Lebih Singkat dari FBF/SMI Pro

Ini indikator paling sederhana dari semua yang sudah/akan direview:

- **Nggak ada state persisten antar-bar** (nggak ada `var`, nggak ada counter kayak `bCnt`/`aCnt` di SMI, nggak ada candidate array kayak FBF).
- **Nggak ada cascade if-elif banyak tingkat.**
- **Cuma 1 lapisan output** (bukan 3 kayak SMI Pro v3 yang punya Zone/Phase/BarColor beda-beda).

Jadi node tree-nya cuma 1 alur linear, dan cross-check-nya jauh lebih cepat. Tapi tetap ada 2 hal yang wajib dicatat eksplisit (lihat bagian 4).

---

## 1. Node Tree Alur (Linear, Tanpa State)

```
ATR Percentage — 1 alur, dihitung ulang tiap bar, independen dari bar sebelumnya
(kecuali ATR sendiri yang butuh smoothing Wilder, itu wajar & sudah lazim)
│
├─ 1. Hitung True Range (TR) tiap bar
│     TR = max(high-low, |high-prevclose|, |low-prevclose|)
│
├─ 2. ATR = Wilder RMA(TR, ATRPeriods)
│     └─ seed = rata-rata TR dari N bar pertama, lanjut smoothing rekursif
│
├─ 3. atrPercent = (ATR / close) × 100
│
├─ 4. Pilih basis buat Bollinger Band:
│     useAtrAsPercent = true  → basis = atrPercent   (DEFAULT)
│     useAtrAsPercent = false → basis = ATR mentah
│
├─ 5. Bollinger Band dari basis:
│     middle = SMA(basis, BBPeriods)
│     stdev  = population stdev(basis, BBPeriods)   ← dibagi N, bukan N-1
│     top    = middle + stdev × StdDevMult
│     bottom = middle - stdev × StdDevMult
│
└─ 6. Visual (lihat bagian 4 soal showBollingerBands)
      ├─ Garis oscillator (atrPercent/ATR) — SELALU tampil
      ├─ Garis top/middle/bottom — tampil HANYA kalau showBollingerBands = true
      ├─ Fill merah "High Volatility Zone" antara top↔middle
      └─ Fill hijau "Low Volatility Zone" antara middle↔bottom
```

Karena semua langkah 1-5 murni fungsi dari window rolling (tidak bergantung hasil keputusan bar sebelumnya selain smoothing ATR yang memang wajar), Python **boleh** dihitung vectorized penuh — dan memang begitu caranya di `atr_percentage.py`. Ini konsisten dengan prinsip stage_03 (loop bar-by-bar cuma wajib kalau ada state/keputusan persisten yang berisiko lookahead — di sini nggak ada).

---

## 2. Glossary — Parameter & Fase

| Nama Pine | Nama Python | Default | Fungsi | Status Replikasi |
|---|---|---|---|---|
| `useAtrAsPercent` | `use_atr_as_percent` | `True` | Basis BB: ATR% (true) atau ATR mentah (false) | ✅ Aktif, sesuai |
| `ATRPeriods` | `atr_periods` | `22` | Panjang smoothing Wilder ATR | ✅ Aktif, sesuai |
| `showBollingerBands` | *(tidak ada parameter Python)* | `True` | **Visual-only** — tampil/sembunyikan garis BB + fill zona di chart | ⚠️ Lihat bagian 4 — sengaja tidak direplikasi, alasannya di bawah |
| `BBPeriods` | `bb_periods` | `20` | Panjang SMA & stdev buat BB | ✅ Aktif, sesuai |
| `StdDev` | `bb_stddev` | `2.0` | Pengali stdev buat lebar band | ✅ Aktif, sesuai |
| `atr` (var Pine) | `atr` (kolom) | — | Nilai ATR mentah (Wilder) | ✅ |
| `atrPercent` | `atr_percent` | — | ATR sebagai % dari close | ✅ |
| `middle` | `bb_middle` | — | SMA dari basis | ✅ |
| `top` | `bb_top` | — | Upper band | ✅ |
| `bottom` | `bb_bottom` | — | Lower band | ✅ |
| *(tidak ada di Pine — hasil warna fill saja)* | `volatility_zone` | — | Kategori posisi basis vs band, 4 kelas | ⚠️ Lihat bagian 4 — 2 dari 4 kategori adalah turunan Python, bukan zona berwarna eksplisit di Pine |

---

## 3. Cross-Check Baris-per-Baris — Hasil

Poin yang wajib dicek ketat sesuai checklist stage_03 (`==` vs `>=`, smoothing ganda vs tunggal, default implisit source Pine, dsb) — semua **aman**:

- **ATR smoothing**: Pine v4 `atr()` = Wilder RMA (bukan EMA/SMA biasa). Python `wilder_atr()` sudah RMA yang benar (seed = rata-rata N bar pertama, lanjut rekursif `(prev×(N-1)+cur)/N`), pola ini sama persis dengan yang sudah dipakai & belum ada masalah di `fbf_break_filter.py` dan `robust_momcand.py` — konsisten lintas file.
- **True Range**: dihitung dengan gap (pakai `prev_close`), bukan cuma `high-low` polos. Sesuai — Pine `atr()` built-in selalu pakai TR yang menghitung gap.
- **Population vs sample stdev**: Pine `bb()` built-in pakai population stdev (dibagi N, bukan N-1). Python pakai `.std(ddof=0)` — **cocok**. (Catatan: ini asumsi yang diambil dari pemahaman umum Pine, bukan dicross-check numerik langsung ke TradingView — tetap pending di to-do numerik, sama seperti indikator lain yang nunggu stage 2).
- **Basis BB ikut `useAtrAsPercent`**: `bb_*` di Python selalu ikut basis yang aktif sesuai parameter, bukan dihitung dua-duanya. Sesuai baris Pine `bb(useAtrAsPercent ? atrPercent : atr, ...)`.
- **Nggak ada state tersembunyi yang kelewat** — dicek ulang, source Pine ini murni fungsi-of-window, nggak ada `var` sama sekali.

**Kesimpulan cross-check: nol gap komputasi.**

---

## 4. Klasifikasi Elemen Visual — 2 Catatan yang WAJIB Dipahami

Ini bagian yang beda dari sekadar "kode sudah benar" — dua catatan di bawah nggak butuh patch kode, tapi butuh dipahami supaya nggak salah baca pas kalibrasi setup pakai chart TradingView asli nanti.

### 4a. `showBollingerBands` — Murni Gerbang Tampilan, Bukan Gerbang Logic

Beda dari kasus Supertrend di FBF (yang nge-gate APAKAH event BREAK dianggap terjadi), `showBollingerBands` di sini **tidak mengubah nilai apa pun** — `middle`/`top`/`bottom` selalu dihitung sama persis di balik layar, cuma nggak digambar di chart kalau toggle ini `false`.

**Kenapa Python sengaja tidak punya parameter ini**: karena Python tidak melakukan rendering chart — kolom `bb_top`/`bb_middle`/`bb_bottom`/`volatility_zone` selalu terisi, itu sudah benar dan tidak perlu opsi "sembunyikan". Yang perlu diingat justru pas **kalibrasi manual lawan TradingView**: kalau di TV toggle `showBollingerBands` sedang OFF, band dan fill warna nggak akan kelihatan di chart sama sekali — jadi pastikan toggle ini **ON** (defaultnya memang ON) saat mau mencocokkan kolom Python dengan tampilan visual band.

### 4b. `volatility_zone` Python Punya 4 Kategori, Tapi Pine Cuma Kasih Warna Eksplisit ke 2 di Antaranya

Di chart TradingView, yang benar-benar diwarnai adalah:
- **Area fill merah** ("High Volatility Zone") = daerah antara garis `top` dan `middle`.
- **Area fill hijau** ("Low Volatility Zone") = daerah antara garis `middle` dan `bottom`.

Kalau nilai oscillator (ATR% atau ATR mentah) **melewati** `top` (di atasnya) atau **melewati** `bottom` (di bawahnya), area itu **tidak** punya warna fill khusus di Pine — cuma kelihatan sebagai garis oscillator yang "menembus keluar" dari band, tanpa highlight warna tambahan.

Python tetap membedakan 4 kategori (`above_top`, `high_zone`, `low_zone`, `below_bottom`) karena itu tetap informasi berguna secara numerik (ekstrem tinggi vs sekadar "di zona merah"). Tapi kalau nanti proses kalibrasi setup ngerujuk ke chart dan nyebut "zona", yang kelihatan visual di TV cuma 2 warna (merah/hijau) + "di luar band" (nggak berwarna) — bukan 4 label eksplisit. Jadi kalau ngobrol soal "zone" pas kalibrasi, perlu disepakati dulu: mau pakai bahasa 2-warna-TV (merah/hijau/di luar), atau bahasa 4-kategori Python (above_top/high_zone/low_zone/below_bottom) — supaya nggak ambigu antara AI dan Zenlol pas nyebut "masuk zona apa".

**Rekomendasi**: pakai 4 kategori Python sebagai bahasa resmi (lebih presisi), tapi dicatat eksplisit bahwa `above_top` dan `below_bottom` itu "di luar kedua fill berwarna" — bukan warna ketiga/keempat yang ada di TV.

---

## 5. Tabel Dampak ON/OFF

| Parameter | ON/Default | OFF | Efek ke kolom Python |
|---|---|---|---|
| `use_atr_as_percent` | Basis = ATR% | Basis = ATR mentah | Semua kolom `bb_*` & `volatility_zone` ikut basis yang dipilih — perlu tahu mode mana yang aktif di TV pas kalibrasi |
| `showBollingerBands` | Band+fill kelihatan di chart | Band+fill hilang dari chart (nilai tetap dihitung) | **Nggak ada efek ke kolom Python** — cuma efek ke apa yang kelihatan visual di TV |

---

## 6. Status Akhir

| Item | Status |
|---|---|
| Node tree alur | ✅ Selesai (1 alur linear, tanpa state) |
| Glossary parameter & fase | ✅ Selesai |
| Cross-check baris-per-baris | ✅ Selesai — **nol gap komputasi** |
| Klasifikasi elemen visual | ✅ Selesai — 2 catatan dokumentasi (bagian 4), bukan bug |
| Patch kode | ❌ Tidak perlu — `atr_percentage.py` (v1.0) tetap dipakai apa adanya |
| Validasi numerik ke data real TradingView | ⏳ **Pending**, blocked nunggu stage 2 (fetcher Binance) — sama seperti semua indikator lain |
| Validasi asumsi population stdev (ddof=0) | ⏳ Pending, masuk paket validasi numerik di atas — prioritas cek pertama kalau nanti ketemu selisih kecil konsisten |

---

## 7. Indikator yang Masih Menunggu Deep-Dive

Sesuai catatan di `handoff_review_indikator.md` bagian 5:

- **RSI Pro Enhanced** — belum dibedah sama sekali.
- **EMA Ribbon Pro [Krypt v11]** — belum dibedah sama sekali.
- **Robust + MomCand Signal** — sudah ada draft Python (`robust_momcand.py`), tapi belum deep-dive sedalam FBF/SMI Pro (perlu dicek terutama bagian scope-decision CRT yang di-skip, dan observasi `rob_dir_mode` yang diduga redundant — keduanya sudah dicatat di docstring file, tapi belum lewat proses review formal 9-langkah).

ATR Percentage sekarang masuk daftar **selesai** bareng FBF dan SMI Pro v3.
