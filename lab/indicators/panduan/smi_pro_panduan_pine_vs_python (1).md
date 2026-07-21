# Panduan Pine vs Python — TOP SMI Pro Enhanced v3

> Hasil deep-dive review sesuai metodologi `handoff_review_indikator.md`.
> Dokumen ini pegangan kalau lupa cara kerja indikator SMI Pro v3 nanti —
> jangan buka source Pine dari nol lagi, cukup baca ini dulu.

**Source Pine**: `TOP SMI Pro Enhanced v3` (Pine v6)
**Python (setelah patch)**: `smi_pro_v3_v1_1.py`
**Status validasi numerik ke data real**: **PENDING** — nunggu stage 2 (fetcher Binance) selesai. Semua yang dibahas di sini adalah cross-check *logic* Pine vs Python, bukan validasi angka ke chart TradingView asli.

---

## 1. Ringkasan Eksekutif

- Layer numerik (SMI, SMI EMA, histogram): **cocok 100%** dengan Pine.
- Layer fase/state (zone, cross, PA/PD, failed mid hold, signal, phase label): **cocok 100%** setelah 1 patch.
- Layer divergensi: **cocok 100%**, delay konfirmasi sudah benar (tidak lookahead).
- Lapisan visibility: **tidak ada elemen yang nge-gate** di indikator ini — beda dari FBF kemarin. Semua toggle (`showBarColor`, `showLbl`, `showDash`, `sMk`) murni kosmetik.
- **1 gap ditemukan dan sudah dipatch** (lihat bagian 6) — edge case di batas OS zone, sumbernya inkonsistensi kecil di source Pine itu sendiri.
- **Ada 3 konsep "fase" berbeda di Pine yang gampang ketuker** — dijelaskan lengkap di bagian 2. Ini yang jadi alasan utama dokumen ini di-update.

---

## 2. Klasifikasi Definisi Fase — 3 Sumber yang Sering Ketuker

Ini bagian paling penting buat dibaca pelan-pelan, karena ini yang jadi istilah acuan kamu ke agent nanti.

Di chart TradingView, ada **3 tempat berbeda** yang sama-sama "kasih tau kondisi SMI saat ini", tapi definisinya tidak identik satu sama lain:

### 2.1 Peta Tiga Sumber

| # | Nama di Pine | Muncul di mana di chart | Tipe output | Berapa kategori |
|---|---|---|---|---|
| A | `sZone` | Dashboard, baris **"Zone"** | Teks | 5 kategori (OB / Upper N / Middle / Lower N / OS) |
| B | `barStateTxt` | Dashboard, baris **"Phase"** | Teks | 13 kategori (cascade gabungan) |
| C | `barCol` | **Warna candle** di chart itu sendiri | Warna | 13 kategori (cascade gabungan — **sama persis** dengan B) |

**Temuan kunci**: B (`barStateTxt`) dan C (`barCol`) itu **cascade yang sama persis** — urutan prioritas pengecekannya identik, dan threshold angkanya identik (termasuk sama-sama pakai `smi < smiOS` versi *strict*, bukan `<=`). Satu-satunya beda: B keluarnya berupa teks di tabel dashboard, C keluarnya berupa warna yang mengecat candle di chart. **Kalau kamu baca warna candle di chart, itu 100% setara dengan baca baris "Phase" di dashboard** — dua-duanya representasi dari kondisi yang sama.

A (`sZone`) itu **konsep terpisah**, lebih sederhana — cuma baca posisi SMI relatif ke 4 garis batas (OB, MID, 0, OS), tanpa peduli histogram, tanpa peduli cross, tanpa peduli PA/PD. Ini semacam "ringkasan kasar", sedangkan B/C itu "cerita lengkap".

### 2.2 Kenapa A Beda dari B/C (Bukan Cuma Beda Nama)

Ini bukan cuma soal istilah — ada 1 titik di mana A dan B/C **secara matematis bisa kasih jawaban beda** untuk kondisi yang sama:

- `sZone` bilang "OS" kalau `smi <= smiOS` (pakai else, non-strict)
- `barStateTxt`/`barCol` bilang "OS Zone" kalau `smi < smiOS` (strict)

Beda persis di titik `smi == smiOS` (default -40.000...). Ini sumber gap yang dibahas detail di bagian 6 (dan sudah dipatch).

### 2.3 Kamus Istilah — Bar Color (Pine) ↔ Phase Text (Pine) ↔ Python

Ini tabel yang bisa langsung kamu copy-paste ke agent kalau lagi ngobrolin case study. Kolom "Istilah buat komunikasi" itu rekomendasi kata yang konsisten dipakai — biar kamu, aku, dan agent semua ngerti maksud yang sama.

| Nama warna di Pine (`bc...`) | Warna | Teks di Dashboard "Phase" | **Kolom Python `phase_label`** (v1.1) | Kondisi pemicu |
|---|---|---|---|---|
| `bcCrossUp` | Cyan | `[X] Cross UP` | `"Cross UP"` | SMI baru cross ke atas EMA-nya |
| `bcCrossDown` | Putih | `[X] Cross DN` | `"Cross DOWN"` | SMI baru cross ke bawah EMA-nya |
| `bcOBZone` | Merah | `[!!] OB Zone` | `"OB Zone"` | `smi > smiOB` (default 80) |
| `bcOSZone` | Biru | `[!!] OS Zone` | `"OS Zone"` | `smi < smiOS` (default -40, **strict**) |
| `bcPADip` | Hijau tua | `[~] PA - Dip Mungkin` | `"PA - Dip Mungkin"` | Pre-akumulasi trigger, histogram masih melemah |
| `bcPAReady` | Hijau terang | `[OK] PA - Siap Balik` | `"PA - Siap Balik"` | Pre-akumulasi trigger, histogram mulai menguat |
| `bcPDDip` | Amber tua | `[~] PD - Dip Mungkin` | `"PD - Dip Mungkin"` | Pre-distribusi trigger, histogram masih menguat |
| `bcPDReady` | Oranye terang | `[OK] PD - Siap Balik` | `"PD - Siap Balik"` | Pre-distribusi trigger, histogram mulai melemah |
| `bcFailMIDBuy` | Biru pastel | `[!] Fail MID Buy` | `"Fail MID Buy"` | Cross MID ke atas tapi gagal, balik lagi |
| `bcFailMIDSell` | Pink pastel | `[!] Fail MID Sell` | `"Fail MID Sell"` | Cross MID ke bawah tapi gagal, balik lagi |
| `bcBgBull` | Abu medium | `[S] Bias Atas` | `"Bias Atas"` | SMI di atas MID, tanpa event spesial lain |
| `bcBgBear` | Abu gelap | `[B] Bias Bawah` | `"Bias Bawah"` | SMI di bawah MID, tanpa event spesial lain |
| `bcBgNeutral` | Abu paling gelap | `[-] Netral` | `"Netral"` | SMI persis di MID (edge case jarang) |

Urutan prioritas cascade (kalau beberapa kondisi ketemu bareng di 1 candle, yang PALING ATAS yang menang):

```
Cross UP/DOWN  >  OB Zone  >  OS Zone  >  PA Dip  >  PA Ready  >
PD Dip  >  PD Ready  >  Fail MID Buy  >  Fail MID Sell  >  Bias Atas/Bawah  >  Netral
```

### 2.4 Rekomendasi Istilah Buat Kamu Pakai

Karena kamu bilang mau fokus deteksi fase berdasarkan **bar color** (warna candle), ini rekomendasi konkret:

- **Sebutan resmi yang dipakai konsisten mulai sekarang**: **"Phase Label"** — merujuk ke kolom `phase_label` di Python, yang mewakili baik `barStateTxt` (teks dashboard) MAUPUN `barCol` (warna candle) sekaligus, karena keduanya sudah terbukti cascade yang identik.
- Kalau ngomong ke agent soal case study nanti, kamu **cukup bilang "Phase Label"**, tidak perlu spesifik nyebut "warna candle" vs "teks dashboard" — dua-duanya sudah sama, jadi 1 istilah cukup.
- **Kolom `zone` (Zone/sZone)** tetap ada di Python sebagai referensi terpisah kalau suatu saat kamu butuh kategori kasar (misal cuma mau tau "lagi di area ekstrem atau tidak" tanpa peduli histogram/cross), tapi **bukan** yang jadi acuan utama buat deteksi fase — itu cuma pelengkap.

### 2.5 Jawaban Langsung: Keduanya Diadopsi ke Python?

**Ya, dua-duanya diadopsi**, tapi jadi 2 kolom terpisah dengan peran beda:

| Konsep Pine | Kolom di Python | Peran |
|---|---|---|
| `sZone` (Zone) | `zone` | Referensi kasar, 5 kategori, independen dari histogram/cross/PA-PD |
| `barStateTxt` **dan** `barCol` (sama persis) | `phase_label` | **Acuan utama** kamu — representasi penuh "Phase" dashboard = warna candle chart |

Sebelum patch v1.1, `phase_label` di Python ternyata masih nurunin sebagian logikanya dari `zone` (bukan independen), jadi ada 1 titik edge case (dibahas bagian 6) di mana dia salah ikut definisi `sZone`, bukan definisi `barStateTxt`/`barCol` yang seharusnya. Setelah dipatch, `phase_label` sekarang murni independen dan cocok 100% sama `barStateTxt`/`barCol`.

---

## 3. Node Tree Alur (Text)

Indikator ini jauh lebih sederhana dari FBF — tidak ada multi-slot candidate, tidak ada tracker/judge terpisah. Satu alur linear per bar, plus satu jalur terpisah untuk divergence (butuh delay konfirmasi pivot).

### Tree A — Alur Utama (per bar, urutan proses)

```
Bar baru masuk
│
├─ 1. Hitung layer numerik
│   ├─ hh = highest(high, lenK), ll = lowest(low, lenK)
│   ├─ rel = close - midpoint(hh,ll), rng = hh - ll
│   ├─ smi = 200 * emaEma(rel,lenD) / emaEma(rng,lenD)   [double EMA!]
│   ├─ smiEma = ema(smi, lenE)                           [EMA tunggal]
│   └─ smiH = smi - smiEma
│
├─ 2. Kalau smi/smiEma masih NaN (warm-up)
│   └─ semua kolom fase = "warmup", phase_label = "Warm-up" → skip ke bar berikutnya
│
├─ 3. Hitung status dasar
│   ├─ above (sAb) = smi >= smiEma
│   ├─ hist_momentum = kombinasi (naik/turun histogram) x (smiH>0 / smiH<=0)
│   ├─ zone (sZone) = kategori 5-level dari smi (OB/Upper N/Middle/Lower N/OS)
│   └─ cross_event = crossover/crossunder resmi (smi vs smiEma)
│
├─ 4. Update counter persisten (var, nempel dari bar sebelumnya)
│   ├─ b_cnt naik kalau smi < smiMID (reset a_cnt)
│   ├─ a_cnt naik kalau smi > smiMID (reset b_cnt)
│   ├─ preAkum = (b_cnt == akumCandles)   ← EXACT equality, bukan >=
│   └─ preDist = (a_cnt == distCandles)   ← EXACT equality, bukan >=
│
├─ 5. Sub-klasifikasi PA/PD → Dip vs Ready
│   └─ berdasarkan arah histogram SAAT preAkum/preDist true (>=/< , beda
│      operator dari hist_momentum di langkah 3 yang pakai strict >/<)
│
├─ 6. Failed mid hold (fakeout) — baca counter SATU BAR SEBELUMNYA
│   └─ smi baru cross MID, tapi bar sebelumnya counter arah lawan > 0
│
├─ 7. Cascade phase_label (= barStateTxt = barCol, prioritas berurutan,
│      urutan WAJIB persis — lihat tabel 2.3):
│   cross_up/down → OB → OS → PA dip/ready → PD dip/ready →
│   fail buy/sell → bias bawah/atas → netral
│
└─ 8. Simpan smi/smiEma/smiH bar ini jadi "prev" utk bar berikutnya
```

### Tree B — Alur Divergensi (terpisah, delay konfirmasi)

```
Tiap bar, cek pivot di SERIES SMI (bukan di harga)
│
├─ pivotlow(smi, divLbL, divLbR) confirm di bar = pivot_bar + divLbR
├─ pivothigh(smi, divLbL, divLbR) confirm di bar = pivot_bar + divLbR
│
├─ Begitu pivot confirm:
│   ├─ Ambil harga (low/high) DI BAR PIVOT (bukan bar confirm)
│   ├─ Bandingkan ke pivot low/high SEBELUMNYA:
│   │   ├─ jarak antar pivot dalam [divRangeMin, divRangeMax] bar?
│   │   ├─ Bullish: harga lower low, SMI higher low → tandai "bullish"
│   │   ├─ Hidden Bullish (kalau enabled): harga higher low, SMI lower low
│   │   ├─ Bearish: harga higher high, SMI lower high → tandai "bearish"
│   │   └─ Hidden Bearish (kalau enabled): harga lower high, SMI higher high
│   └─ UPDATE "pivot terakhir" SELALU jalan, TERLEPAS dari lolos-tidaknya
│       cek jarak di atas (baca baris Pine-nya: update di luar if barsGap)
│
└─ Event dicatat di BAR CONFIRM (pivot_bar + divLbR), bukan di bar pivot
   asli → ini yang mencegah lookahead bias
```

---

## 4. Glossary Istilah (Parameter & Filter)

| Istilah | Default | Dampak ON/OFF | Status Python |
|---|---|---|---|
| `lenK` (SMI %K) | 5 | Periode range high-low | ✅ replikasi aktif |
| `lenD` (SMI %D) | 3 | Periode double-EMA smoothing | ✅ replikasi aktif |
| `lenE` (SMI EMA) | 3 | Periode signal line | ✅ replikasi aktif |
| `smiOB` | 80 | Batas overbought | ✅ replikasi aktif |
| `smiMID` | 0 | Batas bias atas/bawah, trigger PA/PD | ✅ replikasi aktif |
| `smiOS` | -40 | Batas oversold | ✅ replikasi aktif |
| `akumCandles` | 2 | Jumlah candle di bawah MID sebelum PA trigger | ✅ replikasi aktif |
| `distCandles` | 2 | Jumlah candle di atas MID sebelum PD trigger | ✅ replikasi aktif |
| `showDiv` | true | Aktifkan divergence reguler | ✅ replikasi aktif |
| `showHiddenDiv` | **false** | Aktifkan hidden divergence (continuation) | ✅ replikasi aktif (default off) |
| `divLbL`/`divLbR` | 5/5 | Bar kiri/kanan konfirmasi pivot | ✅ replikasi aktif |
| `divRangeMin`/`Max` | 5/60 | Jarak minimum/maksimum antar pivot | ✅ replikasi aktif |
| `sMk` (Markers) | true | Marker cross 0/OB/OS di chart | 🎨 kosmetik, tidak gate — direplikasi sbg kolom `marker_*` tapi murni informational |
| `showRibbon` | true | Ribbon visual bertumpuk | 🎨 kosmetik murni, tidak direplikasi (tidak ada nilai analitis) |
| `showBarColor` | true | Warna candle ikut event (= `barCol`) | 🎨 kosmetik — **tidak nge-gate** `phase_label` (lihat bagian 5) |
| `showLbl` (PA/PD lines) | true | Garis vertikal saat PA/PD trigger | 🎨 kosmetik, tidak gate `pa_pd_state` |
| `showDash` | true | Dashboard di chart (= `barStateTxt`, dst) | 🎨 kosmetik, tidak gate kolom manapun |
| `bcTrans`, semua warna | - | Estetika murni | ❌ tidak relevan buat data |

---

## 5. Temuan Lapisan Visibility: Tidak Ada Gating

Beda penting dari FBF kemarin: di FBF, ada filter trend (Supertrend) yang defaultnya ON dan menyembunyikan wave dari chart — meskipun ternyata **tidak** mengubah apakah event BREAK sungguhan terjadi (jadi kosmetik juga, tapi butuh ditelusuri dulu buat mastiin).

Di SMI Pro v3, setelah ditelusuri baris-per-baris:
- `showBarColor` cuma nentuin apakah `barcolor()` dipanggil dengan warna atau `na`. Cascade prioritas warnanya (`barCol`) tetap dihitung independen di background — kalau `showBarColor` OFF, candle di chart jadi warna default polos, TAPI variabel `barCol` (dan logikanya) tetap jalan seperti biasa, cuma hasilnya tidak ditampilkan.
- `showLbl` cuma nentuin gambar garis vertikal PA/PD — tidak menyentuh `preAkum`/`preDist`/`paDip`/dst.
- `showDash` cuma nentuin tabel dashboard digambar atau tidak — semua variabel yang ditampilkan di situ tetap dihitung terus di background.

**Kesimpulan**: tidak ada elemen di indikator ini yang perlu ditambahkan sebagai "layer visibility" terpisah seperti di FBF. Semua kolom Python yang ada sudah representasi penuh dari apa yang *seharusnya* muncul di chart/dashboard kalau semua toggle dinyalakan (kondisi default) — termasuk kalau `showBarColor` di-OFF-kan di TradingView, kolom `phase_label` di Python tetap valid mewakili warna yang *seharusnya* muncul.

---

## 6. Gap yang Ditemukan & Patch v1.1

### Sumber Gap

Seperti dijelaskan di bagian 2.2 — ada **inkonsistensi kecil di source Pine itu sendiri** antara `sZone` vs `barStateTxt`/`barCol` soal batas OS:

```
sZone                = ... : smi > smiOS ? "Lower N" : "OS"        // OS kalau smi <= smiOS
barStateTxt / barCol = ... : smi < smiOS ? "OS Zone"/warna : ...   // OS kalau smi < smiOS (STRICT)
```

Beda persis di titik `smi == smiOS` (default -40).

Versi Python lama (`smi_pro_v3.py`, sebelum ada klasifikasi jelas seperti bagian 2 di atas) menurunkan `phase_label` dari `zn == "OS"` — yang berarti tanpa sadar ikut definisi `sZone`, **bukan** definisi asli `barStateTxt`/`barCol` yang seharusnya jadi acuan (sesuai fokus kamu ke bar color). Jadi di titik edge case itu, Python bisa keluar "OS Zone" padahal Pine aslinya (dan warna candle-nya) jatuh ke kondisi lain.

### Kenapa Ini Layak Dicatat (Bukan Diabaikan)

Sesuai prinsip yang sudah dipegang di project ini soal operator ambang (`==` vs `>=`, lihat `smi_pro.py` versi paling awal) — perbedaan strict vs non-strict di titik batas itu sengaja, bukan boleh digeneralisir "kurang lebih sama". Walau kemungkinan kejadian `smi` persis `-40.000000...` di data real sangat kecil (floating point), tetap dicatat sebagai gap resmi, bukan diam-diam dibiarkan. Apalagi sekarang jelas fokus kamu ke bar color — ini justru gap yang paling relevan buat diperbaiki.

### Fix di v1.1

`phase_label` sekarang cek `cur_smi < smi_os` **langsung** (strict), niru `barStateTxt`/`barCol` persis, bukan lewat variabel `zone` lagi. Kolom `zone` sendiri **tidak diubah** — itu tetap representasi `sZone` yang benar buat referensi kasar, cuma sudah tidak dipakai lagi sebagai basis `phase_label`.

Sisi OB **tidak** kena gap ini — `sZone` dan `barStateTxt`/`barCol` semuanya pakai `smi > smiOB` (strict, konsisten), jadi tidak perlu diubah.

File hasil patch: **`smi_pro_v3_v1_1.py`** (sudah dites jalan, sanity check pakai data sintetis lolos).

---

## 7. Tabel Dampak ON/OFF (Parameter yang Mengubah Hasil Analitis)

| Parameter | Kalau diubah dari default | Efek |
|---|---|---|
| `akum_candles` / `dist_candles` | naik | PA/PD butuh lebih banyak candle beruntun sebelum trigger — makin jarang tapi makin "matang" sinyalnya |
| `smi_mid` | digeser dari 0 | **HATI-HATI**: `zone` (Middle boundary) dan `signal` tetap pakai literal `0`, bukan ikut `smi_mid` — kalau `smi_mid` diubah, definisi "Upper N" vs "Middle" jadi tidak simetris dengan bias PA/PD. Ini quirk source asli, sudah direplikasi apa adanya (bukan dibetulkan) |
| `div_range_min`/`max` | diperlebar | divergence lebih longgar mendeteksi pivot yang jauh; makin sempit → makin ketat |
| `enable_hidden_div` | ON | Python juga akan mengisi `divergence_event` dengan `hidden_bullish`/`hidden_bearish` |

---

## 8. Skenario Jalur (Contoh Konkret)

**Skenario 1 — Cross menang lawan zona ekstrem**: kalau di satu bar SMI baru saja cross up EMA-nya **dan** SMI-nya sudah di atas OB (jarang tapi mungkin kalau histogram melonjak cepat), `phase_label` akan bilang **"Cross UP"**, bukan "OB Zone" — karena cross dicek duluan di cascade. Ini benar sesuai source, dan warna candle di chart juga akan cyan (bukan merah OB), konsisten.

**Skenario 2 — Failed Mid Hold vs PA/PD bentrok**: PA/PD dicek sebelum failed-mid di cascade. Jadi kalau di bar yang sama PA trigger (`preAkum` pas `bCnt==2`) sekaligus ada pola fakeout, yang menang PA/PD, bukan fail-mid. Fail-mid baru "kelihatan" di `phase_label` (dan warna candle) kalau tidak ada PA/PD aktif di bar itu.

**Skenario 3 — Edge case OS (yang jadi alasan patch v1.1)**: SMI turun pelan-pelan, di satu bar persis menyentuh -40.000... (`smiOS` default). `zone` = "OS" (kategori Zone di dashboard), tapi kalau tidak ada cross/PA/PD/fail-mid aktif di bar itu, `phase_label` — dan warna candle di chart — akan jatuh ke "Bias Bawah" (karena smi < smiMID tetap true), **bukan** "OS Zone". Ini contoh nyata kenapa `zone` dan `phase_label` bisa beda jawaban di 1 titik yang sama.

---

## 9. Status Akhir & To-Do

**Selesai:**
- [x] Klasifikasi 3 sumber definisi fase (Zone / Phase Text / Bar Color) + kamus istilah
- [x] Node tree alur utama + divergensi
- [x] Glossary lengkap parameter & filter
- [x] Cross-check baris-per-baris Pine vs Python
- [x] Cek lapisan visibility — hasil: tidak ada gating di indikator ini
- [x] 1 gap ditemukan (OS-zone edge case, Zone vs Phase/BarColor) → dipatch di `smi_pro_v3_v1_1.py`
- [x] Sanity check jalan pakai data sintetis, tidak ada error

**Belum/To-Do:**
- [ ] Validasi numerik ke data real TradingView — blocked, nunggu stage 2 (fetcher Binance)
- [ ] Validasi tie-break pivot (`_find_pivots`) kalau ketemu kasus nilai SMI identik dalam satu window — perilaku Pine yang PERSIS untuk kasus ini belum terdokumentasi jelas, WAJIB dicek manual pas data real sudah ada
- [ ] Kasus collision divergence (bullish & bearish confirm di bar yang sama persis) — saat ini bearish menimpa bullish, flag sebagai known limitation bukan bug, belum pernah diuji apakah kasusnya realistis muncul di data crypto

---

## 10. File Terkait

| File | Isi |
|---|---|
| `smi_pro_v3_v1_1.py` | Python replikasi SMI Pro v3, **versi terpatch** (pakai ini, bukan `smi_pro_v3.py` lama). `phase_label`-nya = acuan "Phase Label" kamu (setara bar color) |
| `smi_pro_v3.py` | Versi lama (v1.0) — masih ada gap OS-zone, disimpan sebagai riwayat, jangan dipakai lagi |
| `smi_pro_panduan_pine_vs_python.md` | Dokumen ini |
