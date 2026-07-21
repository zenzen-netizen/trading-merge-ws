# Panduan Pine ↔ Python — RSI Pro Enhanced

> Dibuat mengikuti metodologi `handoff_review_indikator.md`. Beda dari sesi
> FBF/SMI sebelumnya: untuk indikator ini **belum ada file Python** saat
> sesi dimulai, jadi `rsi_pro_enhanced.py` dibuat dari nol di sesi ini juga
> — bukan patch dari versi lama. Gotcha di bawah sudah langsung dimasukkan
> ke kode sejak awal (tidak perlu bump versi v1→v2), tapi tetap dijabarkan
> lengkap di sini karena itu esensi dari proses review-nya.

Status stage 2 (fetcher Binance): **belum dibangun**. Jadi review ini masih
level **cross-check logic Pine vs Python** (baca kode), bukan validasi
numerik ke data real. Itu tercatat eksplisit sebagai to-do di bagian akhir.

---

## 1. Node Tree Alur (Teks)

RSI Pro Enhanced **tidak punya state-machine kompleks** seperti FBF (gak
ada wave A-B-C, gak ada multi-slot candidate). State persisten cuma dua:
counter PA/PD (`bCnt`/`aCnt`) dan tracking bar-sejak-cross (`sLB`). Alurnya
linear per-bar:

```
Tiap bar:
│
├─ 1. Hitung RSI (Wilder RMA dari up/down)
│
├─ 2. Kalau enableMA: hitung rsiMA (sesuai maType) + rsiH = rsi - rsiMA
│      Kalau maType="None": rsiH = 0 (konstan), sAb = true (hardcode)
│
├─ 3. Zone (cascade independen, cuma butuh rsi valid)
│      OB > rsiMID(40) > 50(literal) > rsiOS(30) > OS
│
├─ 4. Markers (6 event pulse, independen dari MA)
│      cUM/cDM (cross 50) | cUO/cDB (masuk/keluar OB) | cDO/cUS (masuk/keluar OS)
│
├─ 5. PA/PD counter (state persisten, independen dari MA)
│      rsi < rsiMID(40) → bCnt++ | rsi > rsiMID(40) → aCnt++
│      preAkum = bCnt==akumCandles | preDist = aCnt==distCandles (pulse sekali tembak)
│
├─ 6. [Butuh MA valid] Histogram momentum (AU/AD/BD/BU, strict rsiH>0/<=0)
│
├─ 7. [Butuh MA valid] Cross event (rsi vs rsiMA) + bars-since-cross
│
├─ 8. [Butuh MA valid] Signal (cascade independen dari #3-#7!)
│      STR SELL/STR BUY (pakai rsiOB/rsiOS) > BUY/SELL (pakai sAb + 50-literal) > NEUTRAL
│
└─ 9. [Independen, delay konfirmasi] Divergence
       Pivot di SERIES RSI (bukan harga), confirm = pivot_bar + lbR bar kemudian
```

**Poin kunci**: langkah 3, 5, 6-8, dan 9 **TIDAK saling memberi tahu**.
Tidak ada satu titik pun di source yang menggabungkan Zone + Hist + PA/PD +
Divergence jadi satu kesimpulan tunggal (lihat Bagian 2 di bawah).

---

## 2. Klasifikasi Definisi Fase — Kenapa Bagian Ini Wajib Ada

Sesuai poin 2b metodologi: indikator ini punya **beberapa keluaran yang
sama-sama "kelihatan seperti status saat ini"** (Zone, vs-MA, Hist, Signal,
PA/PD, Divergence) — harus dipetakan dulu sebelum diasumsikan konsisten
satu sama lain.

### 2a. Temuan Utama: Dua "Titik Tengah" yang Berbeda

| Elemen | Pakai `rsiMID` (default 40)? | Pakai literal `50`? |
|---|---|---|
| Zone — cabang "Upper N" / batas atas "Middle" | ✅ | — |
| Zone — cabang "Middle" itu sendiri | — | ✅ (`rsi > 50`) |
| PA/PD counter (`bCnt`/`aCnt`) | ✅ (satu-satunya pemakai murni) | — |
| Signal — cabang BUY/SELL | — | ✅ (`rsi > 50` / `rsi < 50`) |
| Marker `cUM`/`cDM` (cross tengah) | — | ✅ (`ta.crossover(rsi, 50)`) |

**Konsekuensi konkret** (dibuktikan lewat sanity check kode, lihat Bagian 6):
dengan `rsiMID` default 40 (< 50), cabang cascade `sZone > 50 ? "Middle"`
**tidak pernah bisa tercapai** — begitu `rsi > rsiMID(40)` sudah `true` di
cabang sebelumnya, cascade if-elif langsung jatuh ke `"Upper N"`. Cabang
"Middle" hanya bisa dicek kalau `rsi <= 40`, yang otomatis membuat
`rsi > 50` mustahil di saat bersamaan. **Dead branch di source Pine asli**,
bukan bug Python — dan baru "hidup" kalau user mengubah `rsiMID` jadi > 50.

Ini persis pola yang sama seperti temuan Zone-vs-Phase di SMI Pro v3
(inkonsistensi strict/non-strict antar keluaran fase, ADA DI SOURCE PINE
ITU SENDIRI) — bedanya di sini bukan soal strict vs non-strict operator,
tapi soal **dua parameter yang namanya beda tapi kelihatannya sama-sama
"titik tengah"**.

### 2b. Tidak Ada Cascade Gabungan (Beda dari SMI Pro v3 / FBF)

| | SMI Pro v3 | FBF | RSI Pro Enhanced |
|---|---|---|---|
| Ada 1 kolom teks gabungan (cascade prioritas semua state)? | ✅ `barStateTxt` | ✅ (event log BREAK, walau beda bentuk) | ❌ **Tidak ada** |
| Dipakai buat `barcolor()` candle? | ✅ | — (overlay tapi gak barcolor candle) | ❌ Tidak ada `barcolor()` sama sekali |
| Signal paling "final" | `barStateTxt`/`barCol` | Event BREAK | `sSig` — tapi cakupannya SEMPIT |

`sSig` ("Signal") adalah elemen yang paling dekat ke "kesimpulan", TAPI
cascade-nya **hanya** memakai `rsiOB`/`rsiOS` + `sAb` (vs-MA) + literal 50.
Histogram momentum, cross event, PA/PD, dan divergence **semuanya di luar**
cascade Signal — mereka baris dashboard yang berdiri sendiri-sendiri, tidak
pernah ikut menentukan `sSig`. Kalau nanti dipakai buat kalibrasi setup
(case study), jangan asumsikan "Signal = BUY" berarti PA/PD atau divergence
juga sedang aktif — itu dua hal yang independen.

### 2c. Kamus Istilah (Pine ↔ Python)

| Nama Pine | Kolom Python | Kondisi Pemicu Ringkas |
|---|---|---|
| `rsi` | `rsi` | Wilder RSI, `rsiLen` default **5** (bukan 14!) |
| `rsiMA` | `rsi_ma` | MA dari `rsi`, sesuai `maType` |
| `rsiH` | `rsi_hist` | `rsi - rsiMA` (0 kalau MA off) |
| `sZone` | `zone` | Cascade OB/Upper N/Middle/Lower N/OS |
| `sAb` | (dipakai internal `above`) → `vs_ma` | `rsi >= rsiMA` (hardcode true kalau MA off) |
| `sHAU/sHAD/sHBD/sHBU` | `hist_momentum` | Kombinasi arah histogram + `rsiH > 0` / `<= 0` (strict) |
| `sHSt` | `hist_state_label` | Exp Bull / Shr Bull / Exp Bear / Shr Bear / Neutral |
| `sCr` | `cross_event` (+ arah direkonstruksi) | `ta.cross(rsi, rsiMA)` |
| `sBA` | `bars_since_cross` | Jarak bar dari cross terakhir |
| `bCnt`/`aCnt` | `b_cnt`/`a_cnt` | Counter persisten vs `rsiMID` |
| `preAkum`/`preDist` | `pa_pd_state` | Exact equality (`==`), pulse sekali tembak |
| `paPdTxt` | `pa_pd_progress_text` | Progress text dashboard |
| `sSig` | `signal` | Cascade STR SELL/STR BUY/BUY/SELL/NEUTRAL |
| `sStrVal` | `signal_strength` | 90/70/30 (ASCII hash-bar `sStrBar` **sengaja tidak direplikasi** — murni kosmetik) |
| `cUM/cDM/cUO/cDO/cDB/cUS` | `marker_cross_mid_up/down`, `marker_enter_ob/os`, `marker_exit_ob/os` | 6 event pulse independen |
| `bullCond`/`bearCond` | `divergence_event` | Regular divergence saja — **tidak ada Hidden Divergence** di indikator ini |

---

## 3. Cross-Check Baris-per-Baris — Temuan

| # | Temuan | Klasifikasi | Status Python |
|---|---|---|---|
| 1 | `rsiMID`(40) vs literal `50` — dua konsep "tengah" berbeda | Gotcha logic, ada di source asli | ✅ Direplikasi persis (lihat komentar `# literal 50` di kode) |
| 2 | Zona "Middle" dead-branch di default | Konsekuensi dari #1 | ✅ Direplikasi apa adanya, dicek lewat sanity test `rsi_mid=60` |
| 3 | `maType="None"` tetap memengaruhi `sSig` lewat `sAb` hardcode true | Gotcha logic | ✅ Direplikasi — signal gak pernah SELL/STR SELL kalau MA off |
| 4 | Flat market (`up==0` dan `down==0`) → RSI=100, bukan 50 | Urutan prioritas ternary | ✅ Cek `down==0` duluan, sesuai source |
| 5 | Tidak ada cascade gabungan / barcolor | Struktural (poin 2b) | ✅ Tidak dipaksakan — setiap kolom fase berdiri sendiri sesuai source |
| 6 | `rsiLen` default 5 (bukan 14) | Default parameter | ✅ Default Python disamakan persis |
| 7 | Elemen visual (`sMk`, `showLbl`, `showHist`, ribbon, dashboard) | Visibility layer | ✅ Diklasifikasi murni kosmetik — TIDAK ada satupun yang nge-gate sinyal (beda dari FBF Supertrend filter) |
| 8 | `sStrBar` (ASCII progress bar teks) | Kosmetik | ❌ Sengaja tidak direplikasi (nilai `signal_strength` numeriknya tetap ada) |
| 9 | Divergence pakai `ta.barssince(plFound[1])` gaya implementasi beda dari SMI (manual last-pivot-bar tracking) | Implementasi, bukan gotcha logic | ✅ Fungsional sama — delay konfirmasi `divLbR` bar tetap terjaga |

**Tidak ditemukan elemen visual yang nge-gate sinyal** (beda dari kasus FBF
di mana filter trend Supertrend, default ON, menyembunyikan mayoritas event
BREAK dari chart). Lapisan Visibility indikator ini praktis kosong — semua
toggle murni soal tampilan render, tidak mengubah nilai output numerik atau
kategori state apa pun.

---

## 4. Skenario Jalur (Kombinasi State yang Perlu Dipahami)

1. **Signal BUY tanpa histogram bullish** — mungkin terjadi, karena
   `sSig` cascade-nya independen dari `hist_momentum`. Contoh: `rsi=55`,
   `above=true`, tapi histogram baru saja mulai turun (`above_down`) →
   `signal="BUY"` DAN `hist_momentum="above_down"` bersamaan. Jangan
   asumsikan Signal BUY = momentum histogram juga menguat.

2. **PA/PD pulse tanpa Signal berubah** — `preAkum`/`preDist` cuma
   bergantung pada counter berturut-turut vs `rsiMID`(40), sama sekali
   tidak menyentuh `sSig`. Bisa saja `pa_pd_state="pre_akum"` muncul di
   tengah `signal="NEUTRAL"` yang jalan terus tanpa berubah.

3. **Divergence event confirm, tapi Signal masih NEUTRAL** — karena delay
   konfirmasi divergence (`divLbR`=5 bar), event divergence baru "terlihat"
   Python beberapa bar setelah titik pivot aslinya — sangat mungkin di bar
   konfirmasi itu `signal` sudah balik NEUTRAL atau malah berlawanan arah.

4. **Zona "Middle" hanya realistis kalau user override `rsiMID` > 50** —
   kalau kalibrasi setup nanti melibatkan "Zone Middle", pastikan dulu
   parameter `rsi_mid` yang dipakai, karena dengan default project ini
   (40) zona itu **tidak akan pernah muncul** di data manapun.

5. **`maType="None"` — Signal jadi bias struktural** — kalau strategi nanti
   sengaja mematikan MA (misal biar RSI "murni"), sadari bahwa `sSig` jadi
   TIDAK PERNAH mengeluarkan SELL/STR SELL, bukan karena market selalu
   bullish, tapi karena `sAb` di-hardcode true di source Pine-nya sendiri.

---

## 5. Tabel Dampak ON/OFF Parameter Utama

| Parameter | Default | Dampak kalau diubah |
|---|---|---|
| `rsi_len` | 5 | RSI lebih sensitif (kecil) / lebih smooth (besar). Default 5 jauh lebih cepat dari RSI(14) konvensional. |
| `ma_type` | "EMA" | "None" → matikan histogram/cross/vs-MA secara efektif, TAPI signal tetap bias ke BUY-side (gotcha #3). "VWMA" butuh kolom volume. |
| `ma_len` | 14 | Panjang smoothing MA sinyal. |
| `rsi_mid` | 40 | HANYA pengaruh ke PA/PD counter. Kalau > 50, zona "Middle" jadi reachable (gotcha #1/#2). |
| `rsi_ob` / `rsi_os` | 80 / 30 | Threshold Zone, Signal (STR BUY/SELL), dan marker enter/exit OB-OS. |
| `akum_candles` / `dist_candles` | 2 / 2 | Jumlah candle berturut-turut di bawah/atas `rsi_mid` sebelum PA/PD pulse terpicu (exact equality, sekali tembak). |
| `calc_div` | True | Matikan seluruh layer divergensi kalau False. |
| `div_left` / `div_right` | 5 / 5 | Delay konfirmasi pivot makin besar kalau `div_right` dinaikkan. |
| `div_range_lower` / `div_range_upper` | 5 / 60 | Jarak minimum/maksimum antar pivot yang dianggap valid buat divergence. |

---

## 6. Bukti Sanity Check (Data Sintetis)

Dijalankan `rsi_pro_enhanced.py` langsung (`__main__` block) — semua
prediksi dari analisis gotcha di atas **terkonfirmasi**:

- Default (`rsi_mid=40`): distribusi `zone` **tidak mengandung "Middle"
  sama sekali** (OB/Upper N/Lower N/OS/warmup saja).
- `rsi_mid=60`: "Middle" **muncul** di distribusi zone (51 dari 300 bar).
- `ma_type="None"`: distribusi `signal` **hanya** berisi BUY/STR BUY/NEUTRAL
  — tidak ada satupun SELL/STR SELL, dan `vs_ma` cuma berisi "N/A"/"warmup".
- `ma_type="SMA + BB"`: `bb_upper`/`bb_lower` terisi dan melebar-menyempit
  wajar mengikuti `rsi_ma`.
- `ma_type="VWMA"` tanpa kolom `volume` → `ValueError` jelas, fail fast
  (bukan silent wrong result).

Catatan: sanity check ini pakai data sintetis (random walk), **bukan**
validasi numerik ke TradingView asli — cuma memastikan logic jalan dan
gotcha yang dianalisis dari kode memang berperilaku seperti prediksi.

---

## 7. Status Akhir & To-Do

**Selesai di sesi ini:**
- Node tree alur (per-bar, linear, tanpa state-machine kompleks)
- Klasifikasi >1 keluaran fase (Zone / vs-MA / Hist / Signal / PA-PD /
  Divergence) — ketemu gotcha struktural (dua "titik tengah" berbeda,
  zona Middle dead-branch di default) + kamus istilah lengkap
- Cross-check baris-per-baris Pine vs Python — 9 temuan (lihat Bagian 3),
  semuanya sudah masuk ke kode `rsi_pro_enhanced.py` sejak awal ditulis
- Klasifikasi lapisan visibility: **kosong/tidak ada gating signifikan**
- Sanity check kode jalan + 4 skenario pembuktian gotcha via data sintetis

**Belum/To-Do:**
- [ ] Validasi numerik ke data real TradingView — blocked, nunggu stage 2
      (fetcher Binance)
- [ ] Validasi tie-break pivot (`_find_pivots`) untuk kasus nilai RSI
      identik dalam satu window — sama disclaimer dengan smi_pro_v3.py
- [ ] Kalau `ma_type="SMA + BB"` dipakai nyata: validasi `ddof=0`
      (population stdev) beneran cocok dengan `ta.stdev()` Pine — asumsi
      diambil dari konvensi yang sudah dipakai di `atr_percentage.py`,
      belum di-cross-check numerik langsung untuk indikator ini
- [ ] Kalau nanti mau eksperimen `rsi_mid` > 50 di strategi real: perlu
      dipikirkan ulang apakah itu memang niat desain awal indikator, atau
      cuma efek samping yang belum kepikiran pembuat source Pine-nya
