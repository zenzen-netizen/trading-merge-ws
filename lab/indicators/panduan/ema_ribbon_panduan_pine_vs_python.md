# Panduan Pine vs Python — EMA Ribbon Pro [Krypt v11 - High Contrast]

> Dibuat mengikuti metodologi `handoff_review_indikator.md`. File Python
> yang direview: `ema_ribbon_krypt_v11.py` (baru dibuat sesi ini, karena
> sebelumnya belum ada versi Python-nya — beda dari FBF/SMI yang sudah
> ada draft Python duluan).

---

## 0. Ringkasan Temuan Utama (TL;DR)

Indikator ini **beda karakter** dari FBF & SMI Pro v3 yang sudah direview
lebih dulu:

1. **Gotcha visibility-nya BUKAN soal elemen ke-gate** (seperti Supertrend
   filter di FBF). Gotcha di sini: dashboard (tempat `trend_label` dan
   turunannya muncul) **cuma digambar di bar terakhir/live**
   (`barstate.islast`), TIDAK PERNAH ada rekam jejak historis di chart —
   beda total dari SMI Pro yang punya `barcolor()` per-bar. Konsekuensi:
   "chart = kebenaran setup" jadi sulit diterapkan apa adanya untuk
   indikator ini, karena chart-nya sendiri gak nyimpen histori fase.
2. **8 sinyal alert (`alertcondition`) 100% independen dari dashboard** —
   dihitung dari angka mentah, gak peduli `trend_method` yang dipilih
   atau `showDashboard` on/off. Ini "sumber kebenaran" yang lebih aman
   dipakai untuk kalibrasi setup dibanding `trend_label`.
3. Ditemukan **1 bug murni di sisi Python** (bukan gap replikasi Pine) —
   sudah diperbaiki sebelum handoff ini ditulis, lihat bagian 4b.
4. **Tidak ditemukan** inkonsistensi strict `<` vs non-strict `<=` antar
   keluaran fase seperti kasus SMI Pro v3 — semua threshold di indikator
   ini konsisten non-strict (`>=`/`<=`).

---

## 1. Node Tree (Text)

### Tree A — Kalkulasi Ribbon (12 MA)

```
getMA(source, length, maType) per 1 dari 12 length (len1..len12)
│
├─ maType == "KAMA" → jalur TERPISAH (kamaCalc, rekursif, var-per-length)
│   direction = |src[i] - src[i-length]|
│   noise     = sum(|src[t]-src[t-1]|) selama `length` bar terakhir
│   er        = direction/noise (0 kalau noise==0)
│   sc        = (er*(fastSC-slowSC)+slowSC)^2      [fastSC=2/3, slowSC=2/31]
│   kama[i]   = na(kama[i-1]) ? src[i] : kama[i-1] + sc*(src[i]-kama[i-1])
│
└─ maType != "KAMA" → getMA() switch
    ├─ SMA        → rolling mean
    ├─ EMA        → ewm (DEFAULT)
    ├─ WMA        → weighted rolling
    ├─ RMA        → Wilder smoothing (seed = SMA length bar pertama)
    ├─ HMA        → wma(2*wma(src,half) - wma(src,length), sqrt(length))
    ├─ DEMA       → 2*ema - ema(ema)
    ├─ TEMA       → 3*ema1 - 3*ema2 + ema3
    └─ (gak dikenali) → FALLBACK EKSPLISIT ke EMA (ada di source Pine,
                         bukan interpretasi Python)

Output: ma1..ma8 (short ribbon, len 20-55), ma9..ma12 (long ribbon, len 100-365)
```

### Tree B — Deviation & Volatilitas (self-calibrating)

```
rawDev = useMAD ? mad_1tahap(src, devPeriod) : stdev(src, devPeriod, ddof=0*)
dev    = rawDev * mult
devPct = dev/close * 100        atrPct = atr(14)/close * 100
│
├─ normLen = max(2, devPeriod*2)
├─ devPctAvg = SMA(devPct, normLen)   atrPctAvg = SMA(atrPct, normLen)
├─ devRatio = devPct/devPctAvg        atrRatio = atrPct/atrPctAvg
└─ vol_label: ratio<0.7 → RENDAH | ratio>1.3 → TINGGI | else NORMAL

(*) ddof=0 = ASUMSI belum tervalidasi, sama seperti pending item di
    atr_percentage.py — lihat bagian 6 (To-Do).

ATR SL: long_sl = close - ATR(14)*multATR ; short_sl = close + ATR(14)*multATR
```

### Tree C — `getTrend()` (SUMBER `trend_label`, cascade prioritas)

```
getTrend()
│
├─ [CEK PALING PERTAMA, SEBELUM trend_method APA PUN]
│   IF useATRFilter AND NOT isTrending(ATR(14) > SMA(ATR(14),20)):
│       → "Ranging ↔"   (override total, gak peduli trend_method)
│
└─ ELSE, cabang sesuai trend_method yang dipilih:
    │
    ├─ "MA200 Cross" (2 state, BINARY, gak ada Choppy)
    │   close >= ma10 → "Bullish ▲"  |  else → "Bearish ▼"
    │
    ├─ "Ribbon Divergence" (7 state, DEFAULT method)
    │   divPct = (ma1 - ma12) / ma12 * 100        ← titik-ke-titik,
    │   overextThresh = divBullStrong * divOverextMult   BUKAN rata2 ribbon!
    │   divPct >= overextThresh      → "OverExt ▲▲▲"
    │   divPct >= divBullStrong      → "Strong Bull ▲▲"
    │   divPct >= divBullWeak        → "Bull ▲"
    │   divPct <= -overextThresh     → "OverExt ▼▼▼"
    │   divPct <= -divBullStrong     → "Strong Bear ▼▼"
    │   divPct <= -divBullWeak       → "Bear ▼"
    │   else                         → "Choppy ↔"
    │
    ├─ "Short vs Long Ribbon" (2 state, BINARY, gak ada Choppy)
    │   avgShort = rata2(ma1..ma8) ; avgLong = rata2(ma9..ma12)
    │   avgShort >= avgLong → "Bullish ▲"  |  else → "Bearish ▼"
    │
    └─ "Ribbon Alignment" (3 state)
        isAlignedBull = ma1>ma2>ma3>...>ma8  (strict >, gak ada eq-ok toggle)
        isAlignedBull → "Strong Bull ▲▲"
        isAlignedBear → "Strong Bear ▼▼"
        else          → "Choppy ↔"
```

### Tree D — `getVerdict()` (turunan dari `trend_label`, dashboard-only)

```
getVerdict(trend_label, strengthCount, longStrCount, ribbonStrength)
│
├─ "OverExt ▲▲▲"                              → PARABOLIC - TRAIL SL
├─ "OverExt ▼▼▼"                              → CAPITULATE - WAIT
├─ trend_label in {Strong Bull▲▲, Bull▲, Bullish▲}
│   ├─ strengthCount>=6 AND longStrCount>=3   → STRONG BUY
│   ├─ strengthCount>=6 AND longStrCount<3    → HOLD - MACRO LEMAH
│   └─ else                                   → BUY DIP - TUNGGU
├─ trend_label in {Strong Bear▼▼, Bear▼, Bearish▼}
│   ├─ ribbonStrength>=75                     → AVOID - RETEST
│   └─ else                                   → SELL / SHORT
├─ trend_label in {Choppy↔, Ranging↔}         → WAIT - NO TRADE
└─ else (fallback)                            → WAIT
```

### Tree E — Context Label (dashboard-only, independen dari getVerdict)

```
short_str_ctx (butuh isBullContext/isBearContext dari trend_label):
  isBullContext = trend_label in {Bull▲, Strong Bull▲▲, OverExt▲▲▲, Bullish▲}
  isBearContext = trend_label in {Bear▼, Strong Bear▼▼, OverExt▼▼▼, Bearish▼}
  ├─ bull context: ribbonStrength>=87.5→MOMENTUM | >=50→PULLBACK? | else→LEMAH
  ├─ bear context: ribbonStrength>=75→RETEST!   | >=50→BOUNCE?   | else→KONFIRM
  └─ neither                                     → SIDEWAYS

long_str_ctx_label (murni dari longStrCount, TIDAK peduli trend_method):
  4→MACRO BULL | 3→ABOVE 3/4 | 2→MIXED | 1→NEARLY BEAR | 0→MACRO BEAR
```

### Tree F — Event/Alert (8 `alertcondition`, INDEPENDEN dari Tree C/D/E)

```
1. Break Upper Band 1  : crossover(close, ma1+dev)
2. Break Lower Band 1  : crossunder(close, ma1-dev)
3. Cross Above MA200   : crossover(close, ma10)
4. Cross Below MA200   : crossunder(close, ma10)
5. Ribbon Aligned Bull : isAlignedBull AND NOT isAlignedBull[1]   (transisi!)
6. Ribbon Aligned Bear : isAlignedBear AND NOT isAlignedBear[1]   (transisi!)
7. Div Overext Bull    : divPct>=overextThresh AND divPct[1]<overextThresh
8. Div Overext Bear    : divPct<=-overextThresh AND divPct[1]>-overextThresh

Semua dihitung dari variabel numerik mentah - GAK ADA satupun yang baca
trend_label/dashboard. Aman dipakai walau showDashboard=False atau
trend_method apa pun.
```

---

## 2. Glossary — Parameter, Default, Dampak ON/OFF, Status Python

| Parameter Pine | Default | Dampak kalau diubah | Status Python |
|---|---|---|---|
| `src` | close | Sumber harga semua MA | ✅ `src_col` |
| `maType` | EMA | Ganti rumus SEMUA 12 MA sekaligus | ✅ `ma_type`, 8 varian + fallback EMA |
| `len1..len8` | 20,25,30,35,40,45,50,55 | Short ribbon | ✅ |
| `len9..len12` | 100,200,300,365 | Long ribbon (dipakai divPct & avgLong) | ✅ |
| `showLongMA` | true | **MURNI toggle plot** — ma9-12 & divPct TETAP dihitung walau OFF | ⚠️ sengaja TIDAK ada parameter ini di Python (lihat catatan di bawah tabel) |
| `showDeviationBands` | **false** | **MURNI toggle plot** — `dev` tetap dihitung, dipakai alert #1/#2 walau band gak ditampilkan | ⚠️ sengaja TIDAK ada parameter (kolom band selalu dihitung) |
| `mult` | 1.0 | Lebar deviation band | ✅ |
| `devPeriod` | 20 | Window MAD/stdev + basis `normLen` | ✅ |
| `useMAD` | true | MAD 1-tahap vs stdev(ddof=0*) | ✅ |
| `showATRSL` | true | **MURNI toggle plot** | ⚠️ sengaja tidak ada parameter |
| `multATR` | 1.5 | Jarak SL dari harga | ✅ |
| `trendMethod` | Ribbon Divergence | Pilih 1 dari 4 cabang Tree C | ✅ `trend_method` |
| `divBullStrong` | 3.0 | Threshold Strong Bull/Bear + basis overextThresh | ✅ |
| `divBullWeak` | 1.0 | Threshold Bull/Bear biasa | ✅ |
| `divOverextMult` | 5.0 | Pengali overextThresh | ✅ |
| `useATRFilter` | **false** | Override SEMUA trend_method jadi "Ranging" saat ATR gak trending | ✅ `use_atr_filter` |
| `showDashboard` | **false** | Gerbang tampil SELURUH Tree D/E (bukan Tree C — trend_label tetap dihitung internal walau dashboard mati) | ⚠️ N/A di Python (semua kolom fase selalu dihitung — lihat bagian 0 & 4a) |

**Kenapa `showLongMA`/`showDeviationBands`/`showATRSL`/`showDashboard` gak
jadi parameter Python:** sudah ditelusuri baris-per-baris — keempatnya
di source Pine **cuma gate PLOTTING**, nilai di baliknya selalu
dihitung tanpa syarat. Konsisten dengan prinsip "jangan gate hitungan
demi tampilan" yang sudah dipakai di FBF/SMI. `showDashboard` beda
sedikit — dia gate SELURUH TABLE (Tree D & E sepenuhnya, termasuk
`trend_label` yang notabene dihitung di Tree C terpisah dari tabel) —
tapi karena `getTrend()` fungsinya dipanggil TANPA syarat showDashboard
(dipanggil di baris global, bukan di dalam blok `if showDashboard`),
`trend_label` (Tree C) tetap valid dihitung Python walau showDashboard
mati. Yang benar-benar gak pernah muncul di TV kalau showDashboard OFF
adalah TAMPILANNYA saja.

---

## 3. Klasifikasi Definisi Fase (Wajib — Indikator Ini Punya >1 Keluaran Fase)

Ditemukan **5 keluaran fase berbeda** yang harus dibedakan tegas
(langkah 2b metodologi):

| Keluaran | Muncul di chart? | Jumlah kategori | Bergantung ke | Independen trend_method? |
|---|---|---|---|---|
| `trend_label` | Dashboard row "Trend", **HANYA bar terakhir** | 2-7 tergantung method | `trend_method` | Tidak (ini output-nya) |
| `verdict_label` | Dashboard row "VERDICT", **HANYA bar terakhir** | ~7 | `trend_label` + strength counts | Tidak langsung |
| `short_str_ctx` | Dashboard row "Short Str" (suffix teks), **HANYA bar terakhir** | 7 | `trend_label` (bull/bear context) + ribbonStrength | Tidak langsung |
| `long_str_ctx_label` | Dashboard row "Long Str" (suffix teks), **HANYA bar terakhir** | 5 | `longStrCount` SAJA | **Ya**, gak peduli trend_method |
| 8 kolom `*_event` | **TIDAK PERNAH** lewat dashboard — lewat `alertcondition` (bisa jadi log alert kalau di-set di TV) | boolean per event | Variabel numerik mentah | **Ya**, 100% independen |

**Kamus istilah (Pine ↔ Python ↔ kondisi pemicu):**

| Pine | Python | Kondisi Pemicu |
|---|---|---|
| `divPct` | `div_pct` | `(ma1-ma12)/ma12*100` — **titik ma1 vs ma12**, BUKAN `avgShort` vs `avgLong` |
| `overextThresh` | `overext_thresh` | `divBullStrong * divOverextMult` |
| `avgShort`/`avgLong` | `avg_short`/`avg_long` | Rata-rata 8 MA pendek / 4 MA panjang — dipakai method "Short vs Long Ribbon" SAJA, beda dari `divPct` |
| `ribbonStrength` | `ribbon_strength` | `%` dari 8 MA pendek yang di bawah `close` |
| `longStrCount` | `long_str_count` | Jumlah (0-4) dari 4 MA panjang yang di bawah `close` |
| `isAlignedBull/Bear` | `is_aligned_bull/bear` | Strict `>`/`<` berurutan ma1..ma8, TANPA opsi eq-ok (beda dari `Robust+MomCand` yang punya `rob_stack_eq_ok`) |

**Titik ambang strict vs non-strict:** dicek semua — **konsisten
non-strict (`>=`/`<=`)** di seluruh cascade Tree C, Tree D, Tree E.
Tidak ditemukan inkonsistensi strict/non-strict antar keluaran fase
seperti kasus SMI Pro v3 (`sZone` vs `barStateTxt` beda di titik OS).
Satu-satunya operator strict murni ada di `isAlignedBull/Bear`
(`>`/`<`, bukan `>=`/`<=`) — tapi ini KONSISTEN dipakai di semua tempat
yang merujuknya (Tree C method "Ribbon Alignment" DAN Tree F event
#5/#6), jadi bukan inkonsistensi, cuma catatan desain.

---

## 4. Cross-Check Baris-per-Baris — Temuan

### 4a. Gap Kelas "Visibility" (bukan gate, tapi *scope tampilan*)

Beda dari FBF (elemen ke-gate hilang dari chart) atau SMI (dua sumber
fase beda definisi) — gap di sini adalah **`trend_label` dkk cuma
pernah tampil untuk bar TERAKHIR/live**, gak pernah untuk histori.
Ini BUKAN bug replikasi (Python **benar** menghitung untuk semua bar,
karena itu perlu untuk backtest), tapi WAJIB didokumentasikan supaya
saat validasi manual ke TV nanti, caranya beda dari SMI/FBF: harus
scrub replay bar-by-bar (mahal), bukan sekadar screenshot chart hari
ini. Lihat To-Do di bagian 6.

### 4b. Bug Python (ditemukan & diperbaiki sebelum handoff ini)

Implementasi awal `ribbon_aligned_bull/bear_event` salah — nyala di
**setiap** bar yang `is_aligned_bull`, bukan cuma di bar transisinya.
Root cause: `pandas.Series.shift(1)` pada kolom `bool` mengubah dtype
jadi `object` (karena bar pertama jadi `NaN`), dan operator `~` pada
dtype `object` men-invert nilai `bool` Python secara bitwise
(`~True == -2`, `~False == -1` — **dua-duanya truthy!**), bukan
logical negate. Sudah diperbaiki dengan `.astype(bool)` eksplisit
setelah `.fillna(False)`. Sanity check sebelum-sesudah:

| | Sebelum fix | Sesudah fix |
|---|---|---|
| `ribbon_aligned_bull_event` (data sintetis 500 bar) | 297 True (≈ semua bar aligned) | 7 True (transisi asli) |
| `ribbon_aligned_bear_event` | 95 True | 4 True |

Ini bug murni sisi Python/pandas, bukan gap pemahaman Pine — dicatat
di sini karena termasuk "cross-check" yang relevan untuk siapa pun
yang nanti modifikasi file ini lebih lanjut.

### 4c. Elemen yang DICEK dan TERKONFIRMASI AMAN (tidak perlu patch)

- Urutan cascade `useATRFilter` di paling atas `getTrend()`, sebelum
  cabang `trend_method` manapun — direplikasi persis urutannya.
- `divPct`/`overextThresh` dihitung tanpa syarat `showLongMA` — event
  #7/#8 tetap valid walau ma9-12 gak ditampilkan di TV.
- Tidak ada elemen HTF/Supertrend/EMA-trend-visual-gate seperti di
  FBF — indikator ini gak punya mekanisme sembunyikan wave/garis
  berdasarkan tren, jadi kelas gotcha itu **tidak berlaku** di sini.
- `getMA()` fallback eksplisit ke EMA — dicek benar ada di source
  Pine (komentar "FIX" eksplisit), bukan asumsi Python.
- KAMA per-length independen (`kama1_v`..`kama12_v` beda `var` state
  masing-masing) — direplikasi dengan cara panggil `_kama()` 12 kali
  terpisah, bukan 1 fungsi dipakai ulang dengan state ke-share (yang
  akan jadi bug kalau salah implementasi).

---

## 5. Skenario Jalur (Contoh Konkret)

**Skenario 1 — "Sinyal tampak tapi label sesat":** `useATRFilter=True`,
market lagi sideways rendah-volatilitas (ATR di bawah SMA(ATR,20)),
tapi kebetulan `avgShort >= avgLong` sudah terjadi (Short vs Long
Ribbon method akan bilang "Bullish ▲" kalau method ini aktif). Karena
`useATRFilter` override paling awal, `trend_label` yang keluar tetap
**"Ranging ↔"**, BUKAN "Bullish ▲" — walau kondisi ribbon aslinya
sudah bullish. Trader yang cuma baca `verdict_label` ("WAIT - NO
TRADE") bisa melewatkan bahwa `avgShort>=avgLong` sebenarnya sudah
terjadi (info itu ada di kolom `avg_short`/`avg_long`, cuma gak
tercermin di `trend_label` versi ter-override ini).

**Skenario 2 — "Event nyala, dashboard diam":** `showDashboard=False`
di TV (default!). `close` baru saja crossover `ma10` (MA200 versi
default EMA200). Event #3 (`cross_above_ma200_event`) valid TRUE di
Python & alert Pine tetap bisa trigger (kalau di-set), TAPI di chart
TV **gak ada elemen visual apa pun** yang berubah untuk menandai ini
(gak ada plotshape khusus buat event ini) — kecuali user
nyalain dashboard atau tahu dari alert log. Konsekuensi praktis:
kalibrasi setup untuk sinyal berbasis MA200 cross HARUS mengandalkan
kolom event Python / alert log, TIDAK BISA murni visual dari candle
chart historis.

**Skenario 3 — "Dua sumber divergence, dua makna beda":**
`trend_method="Short vs Long Ribbon"` dipilih di TV. `divPct`
(berbasis ma1 vs ma12) tetap dihitung terus di background, dan event
#7/#8 (div overext) tetap bisa trigger — TAPI `trend_label` yang
kelihatan di dashboard TIDAK mencerminkan `divPct` sama sekali (dia
pakai `avgShort` vs `avgLong`). Kalau nanti mau bikin rule setup yang
menggabungkan "trend method apa pun + div overext event", jangan
asumsikan keduanya "satu bahasa" — `divPct` independen sepenuhnya
dari `trend_method` yang lagi aktif.

---

## 6. Status Replikasi & To-Do

**Sudah dikerjakan (sesi ini):**
- [x] Kode Python `ema_ribbon_krypt_v11.py` — 12 MA (8 tipe termasuk
      KAMA rekursif), deviation bands, ATR SL, normalisasi volatilitas
      self-calibrating, 4 `trend_method`, `verdict_label`, 2 context
      label, 8 event/alert.
- [x] Sanity check jalan tanpa error untuk 8 `ma_type` × 4 `trend_method`
      (data sintetis).
- [x] 1 bug ditemukan & diperbaiki (shift-bool dtype object, lihat 4b).
- [x] Node tree (6 tree terpisah, Tree A-F).
- [x] Glossary + tabel dampak ON/OFF.
- [x] Klasifikasi 5-sumber-fase + kamus istilah (langkah 2b).
- [x] Cross-check baris-per-baris (4a-4c).
- [x] 3 skenario jalur konkret.

**Belum/To-Do (pending, konsisten dengan status stage 2):**
- [ ] **Validasi numerik ke data real TradingView — BLOCKED**, nunggu
      stage 2 (fetcher Binance).
- [ ] **Validasi `trend_label`/`verdict_label`/context label PERLU
      METODE BEDA** dari SMI/FBF: karena TV cuma nampilin dashboard
      untuk bar live, validasi historis WAJIB pakai replay/scrub
      manual bar-by-bar di TradingView (bukan screenshot kondisi
      sekarang) — dicatat eksplisit di sini supaya gak lupa pas mulai
      validasi nanti.
- [ ] Validasi asumsi `stdev(ddof=0)` kalau `useMAD=False` dipakai —
      sama seperti pending item `atr_percentage.py`, belum
      dicross-check numerik lawan Pine.
- [ ] KAMA butuh sample validasi ekstra hati-hati (paling rawan
      salah index karena rekursif dgn `sc` dinamis) — kalau memang
      berencana pakai `maType="KAMA"` untuk setup nyata.
- [ ] Event (Tree F) paling gampang divalidasi duluan (independen
      dashboard) — prioritaskan ini di sesi validasi numerik nanti
      sebelum masuk ke trend_label yang lebih ribet cara ceknya.
- [ ] Sample check ke-4 `trend_method` satu-satu lawan TV (khususnya
      titik transisi antar kategori Ribbon Divergence yang 7 state),
      dan sample `useATRFilter=True` eksplisit (Skenario 1 di atas).

---

## 7. File yang Dihasilkan Sesi Ini

| File | Isi |
|---|---|
| `ema_ribbon_krypt_v11.py` | Python replikasi EMA Ribbon Pro Krypt v11 — kode BARU, sebelumnya belum ada versi Python |
| `ema_ribbon_panduan_pine_vs_python.md` | Dokumen ini |

**Update ke `handoff_review_indikator.md`:** tabel di bagian 5
handoff sebaiknya ditambah baris untuk 2 file ini, dan status
"belum dibedah" untuk EMA Ribbon Pro [Krypt v11] dipindah ke daftar
"sudah selesai deep-dive", supaya konsisten dengan aturan sinkronisasi
dokumen (mirip aturan update `00_index_guide.md`/`00_roadmap.md`).
Indikator yang masih tersisa: RSI Pro Enhanced (belum ada Python sama
sekali, sama seperti kasus ini tadi), Robust + MomCand Signal (sudah
ada draft tapi belum deep-dive), ATR Percentage (sudah ada draft,
kemungkinan gak butuh deep-dive selengkap ini karena gak ada state
persisten/dashboard-only-display).
