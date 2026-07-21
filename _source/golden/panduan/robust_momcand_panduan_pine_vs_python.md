# Panduan Pine ↔ Python — Robust + MomCand Signal

> Dokumen hasil deep-dive review sesuai metodologi di `handoff_review_indikator.md`.
> Status: **selesai dibedah, TIDAK ditemukan gap** — beda dari FBF dan SMI Pro v3
> yang masing-masing ketemu 1 gap dan perlu patch. Indikator ini validasi lolos
> tanpa perubahan kode.

---

## 0. Ringkasan Eksekutif

| | |
|---|---|
| **File Pine** | `Robust + MomCand Signal.txt` (v6) |
| **File Python** | `robust_momcand.py` — **tidak perlu di-patch**, versi yang ada sudah benar |
| **Hasil cross-check** | Tidak ada gap. 3 keputusan scope yang sudah didokumentasikan di docstring (exclude HTF, skip CRT, hitung 3 mode sekaligus) — semua dikonfirmasi ulang dan benar |
| **Loop bar-by-bar?** | Tidak perlu — tidak ada state persisten antar-bar (beda dari SMI/FBF yang punya counter `var`) |
| **Validasi numerik ke data real** | Masih pending, nunggu stage 2 (fetcher Binance) — sama seperti indikator lain |

---

## 1. Node Tree Alur

Indikator ini punya 2 "mesin" independen yang ketemu di bagian akhir (Signal Generation) — beda dari FBF yang punya Tracker+Judge yang saling terkait erat.

```
ROBUST + MOMCAND SIGNAL
│
├─ MESIN 1: ROBUST LINES (trend direction, current TF)
│   │
│   ├─ 8 EMA dasar: e1(8) ... e8(200), semua dari close
│   │
│   ├─ f_robust() — MAD cross-sectional per grup EMA
│   │   ├─ rob_fast  = robust(e1,e2,e3,e4)        bobot 1.0/1.5/2.0/2.5
│   │   ├─ rob_main  = robust(e1..e8)              bobot 1.0/1.5/2.0/2.5/3.0/4.0/4.5/5.0
│   │   └─ rob_slow  = robust(e5,e6,e7,e8)        bobot 3.0/4.0/4.5/5.0
│   │
│   ├─ Arah per garis: close > garis = up, close < garis = down
│   │
│   ├─ Align Mode (pilih salah satu cara gabungkan 3 garis):
│   │   ├─ AND (semua harus align)
│   │   ├─ OR (salah satu cukup)
│   │   ├─ Priority FAST / MAIN / SLOW (garis prioritas menang kalau show-nya aktif,
│   │   │   fallback ke garis lain kalau prioritas di-off)
│   │   └─ → hasil: rob_trend_up / rob_trend_dn (awal)
│   │
│   └─ Stack Filter (opsional, default ON, syarat 3 show flag semua aktif)
│       ├─ Bullish stack: fast > main > slow (atau >= kalau equal diizinkan)
│       ├─ Bearish stack: fast < main < slow
│       └─ → rob_trend_up/dn di-AND dengan syarat stack ini
│
├─ [DIBUANG] HTF Robust Lines + HTF Cross Label
│   └─ Ditelusuri: 100% visual/informational, gak nyambung ke rob_trend_up/dn
│      atau ke sig_bull/sig_bear manapun. Lihat section 4.
│
├─ MESIN 2: MOMENTUM CANDLE (candle threshold, 1 dari 4 mode)
│   │
│   ├─ Fixed Pips    : body >= (min_pips × pip_size)
│   ├─ Dynamic ATR   : body >= ATR(len, smoothing) × multiplier
│   ├─ Smart Stats    : body >= rolling_median(body) + rolling_MAD(body) × dev_mult
│   │                    DAN wick_ratio <= max_wick
│   ├─ CRT (2-Candle) : [SKIP - keputusan eksplisit, lihat section 4]
│   │
│   └─ → mom_bull = pass_mode AND candle_bullish
│        mom_bear = pass_mode AND candle_bearish
│
└─ SIGNAL GENERATION (titik temu Mesin 1 + Mesin 2)
    │
    ├─ bull_raw = mom_bull, bear_raw = mom_bear   (titik awal)
    │
    ├─ [OPSIONAL, default OFF] Robust Direction Filter (rob_dir_on)
    │   ├─ Kalau trend NEUTRAL (gak up gak down) → bull_raw & bear_raw dipaksa false
    │   ├─ Mode "Only One Direction": bull_raw &= rob_trend_up, bear_raw &= rob_trend_dn
    │   └─ Mode "Both Direction (Reverse)": kalau trend_up → bear_raw dimatikan;
    │       kalau trend_dn → bull_raw dimatikan
    │       (CATATAN: 2 mode ini matematis identik — lihat section 5)
    │
    ├─ Side Filter (side_mode: Both / Buy Only / Sell Only)
    │
    └─ → sig_bull, sig_bear  (SINYAL FINAL)
```

---

## 2. Glossary — Parameter & Filter

| Nama Pine | Default | Dampak ON/OFF | Status Python |
|---|---|---|---|
| `rob_show_fast/main/slow` | true/true/true | Matiin salah satu = garis itu dikeluarkan dari align logic (bukan cuma disembunyikan visualnya) | ✅ aktif, ikut nentuin align sesuai Pine |
| `rob_align_mode` | "AND (semua harus align)" | Cara gabungkan arah 3 garis jadi 1 trend | ✅ aktif, 5 pilihan sama persis |
| `rob_stack_on` | true | Syarat tambahan: garis harus tersusun rapi fast>main>slow (atau sebaliknya). Butuh SEMUA 3 show flag aktif, kalau salah satu off maka filter ini otomatis gak berlaku walau `rob_stack_on`=true | ✅ aktif |
| `rob_stack_eq_ok` | false | Izinkan `>=`/`<=` (bukan strict `>`/`<`) di syarat stack | ✅ aktif |
| `htf_on` + section 2 semua | true (tapi efeknya nihil ke sinyal) | **Cuma visual** — plot garis HTF + label cross HTF. Gak nyentuh sinyal | ❌ dibuang total (keputusan eksplisit, benar) |
| `mom_mode` | "Smart Stats" | Pilih 1 dari 4 metode threshold candle | ✅ 3 mode aktif, 1 mode (CRT) skip |
| `fp_min_pips`, `fp_pip_size` | 20.0, 0.0001 | Threshold body candle mode Fixed Pips | ✅ aktif |
| `atr_len`, `atr_mult`, `atr_smooth` | 14, 1.5, "RMA" | Threshold body candle mode Dynamic ATR | ✅ aktif, 4 pilihan smoothing sama persis |
| `qt_look`, `qt_dev`, `qt_max_wick` | 200, 2.0, 0.30 | Threshold + filter wick mode Smart Stats | ✅ aktif |
| CRT params (7 input) | — | Deteksi pola 2-candle sweep/no-sweep | ❌ skip — keputusan eksplisit Zenlol, raise `NotImplementedError` kalau dipanggil |
| `side_mode` | "Both" | Filter akhir: tampilkan buy/sell/keduanya | ✅ aktif |
| `rob_dir_on` | **false** | Kalau ON, sinyal candle harus align sama trend Robust Lines | ✅ aktif |
| `rob_dir_mode` | "Only One Direction" | 2 sub-mode filter arah (matematis identik, lihat section 5) | ✅ aktif, 2-2nya direplikasi |
| `show_sig_lbl`, marker style/size/color, `dash_*` | — | Semua kosmetik murni (gambar marker/dashboard), gak nyentuh nilai sinyal | ❌ tidak direplikasi (memang gak perlu, gak ada di layer numerik) |

---

## 3. Dua "Keluaran Fase" — Beda Konsep, Bukan Duplikasi

Sesuai poin 2b metodologi: indikator ini punya 2 baris dashboard yang kelihatannya mirip tapi **memang secara sengaja berbeda konsep**, bukan kasus 1-konsep-2-definisi kayak SMI Pro v3:

| Nama Pine | Muncul di dashboard | Basis | Kolom Python |
|---|---|---|---|
| `rob_dir_txt` | Row "Rob Dir" | `rob_trend_up`/`rob_trend_dn` — trend garis MENTAH, SEBELUM ketemu momentum candle & filter | `rob_dir_text` |
| `sig_txt` | Row "Signal" | `sig_bull`/`sig_bear` — hasil AKHIR setelah momentum candle + (opsional) direction filter + side filter | `signal_text` |

Ini **bukan** kasus ambigu — `rob_dir_txt` menjawab "kemana arah trend garis robust saat ini", `sig_txt` menjawab "apakah ada sinyal entry sekarang". Dua pertanyaan yang memang beda, keduanya sudah ada sebagai kolom terpisah di Python. Tidak perlu tindakan lanjutan.

`htf_dir_txt` (row "HTF") sengaja tidak direplikasi karena bagian dari section HTF yang dibuang (murni visual, lihat section 4).

---

## 4. Elemen Visual yang Dicek — Klasifikasi Kosmetik vs Nge-gate

| Elemen | Ditelusuri sampai mana | Klasifikasi |
|---|---|---|
| HTF Robust Lines (plot garis) | Cuma dipakai `plot()` | Kosmetik |
| HTF Cross Labels (`f_push_htf_lbl`) | Cuma dipakai gambar `label.new()` | Kosmetik |
| `show_sig_lbl` | Gate `f_draw_marker()` doang, gak gate `sig_bull`/`sig_bear` | Kosmetik |
| `show_crt_type` | Cuma nambah suffix teks " T1"/" T2" di label marker | Kosmetik (lagipula CRT mode di-skip) |
| Dashboard (`dash_on`, semua row) | `barstate.islast` block, baca variabel yang udah jadi, gak nulis balik ke variabel manapun | Kosmetik |
| Marker style/size/color inputs | Cuma parameter gambar `label.new()` | Kosmetik |

**Kesimpulan**: **tidak ada elemen visual yang nge-gate** di indikator ini — beda dari FBF yang punya filter trend Supertrend (section 6) yang bener-bener nyembunyiin wave dari chart tapi event BREAK-nya sendiri tetap kejadian di balik layar. Di sini, semua yang "ON secara default" (`rob_show_*`, `rob_stack_on`) memang genuinely mempengaruhi perhitungan trend, bukan cuma tampilan — dan itu sudah benar direplikasi.

---

## 5. Observasi: `rob_dir_mode` Punya 2 Sub-mode yang Matematis Identik

Ditelusuri dari source:
- `bull_raw` dan `bear_raw` gak pernah `true` bersamaan (candle cuma bisa bull ATAU bear per bar, gak dua-duanya)
- Saat kondisi non-neutral, `rob_trend_up` dan `rob_trend_dn` saling eksklusif (praktis — lihat catatan edge case di bawah)

Konsekuensinya: `"not rob_trend_up"` ≈ `"rob_trend_dn"` di kondisi non-neutral, jadi cabang **"Only One Direction"** dan **"Both Direction (Reverse)"** ketemu hasil akhir yang sama.

**Edge case yang dicek manual**: kalau align mode = "OR (salah satu cukup)", secara teori `rob_trend_up` dan `rob_trend_dn` BISA true bersamaan (misal harga di antara 2 garis yang saling silang). Sudah ditelusuri baris-per-baris apa yang terjadi di kedua mode untuk edge case ini — hasilnya **tetap identik** (kedua sinyal ke-wipe bareng di kedua mode). Jadi observasi ini valid untuk semua kondisi, bukan cuma kasus umum.

**Ini bukan bug** — kemungkinan besar opsi redundant di source Pine asli (mungkin disiapkan untuk future-proofing atau simetri UI). `robust_momcand.py` tetap mereplikasi 2-2nya persis sesuai source (prinsip "cerminkan, jangan membetulkan source"), plus ada test otomatis di `if __name__ == "__main__"` yang **memverifikasi** kedua mode menghasilkan sinyal identik pada data sintetis — bagus untuk deteksi dini kalau suatu saat ada perubahan yang bikin asumsi ini gak berlaku lagi.

---

## 6. Skenario Jalur (Contoh Konkret)

**Skenario A — Setup paling sering dipakai (semua default)**
`rob_dir_on=false` → filter arah gak aktif sama sekali. `sig_bull = mom_bull`, `sig_bear = mom_bear` — sinyal murni dari Momentum Candle (default: Smart Stats), trend Robust Lines cuma informasi di dashboard, gak mempengaruhi entry.

**Skenario B — Trend filter aktif, momentum searah trend**
`rob_dir_on=true`, harga lagi `rob_trend_up=true`. Muncul `mom_bull=true` (candle momentum bullish) → lolos filter (`bull_raw AND rob_trend_up` = true) → `sig_bull=true`. Tapi kalau di bar yang sama `mom_bear=true` juga muncul (gak akan terjadi bareng karena 1 candle cuma bull atau bear, tapi hipotesis kalau ada logic lain) → `bear_raw AND rob_trend_dn` = `true AND false` = false, ke-filter.

**Skenario C — Kondisi neutral**
`rob_dir_on=true`, harga di antara garis-garis robust sehingga `rob_trend_up=false` DAN `rob_trend_dn=false` (neutral). Berapapun kuatnya momentum candle yang muncul, `bull_raw` dan `bear_raw` dipaksa `false` duluan sebelum sempat dicek `rob_dir_mode` apapun — **tidak ada sinyal sama sekali** selama trend neutral dan filter ini aktif.

**Skenario D — Stack filter menggagalkan trend yang "kelihatan" align**
Misal align mode "OR (salah satu cukup)" bikin `rob_trend_up=true` (karena harga di atas SALAH SATU garis), tapi urutan garisnya berantakan (bukan fast>main>slow). Kalau `rob_stack_on=true` (default), trend ini di-AND dengan syarat stack — kalau stack gagal, `rob_trend_up` jadi `false` lagi. Ini contoh kenapa 2 filter (align mode + stack) harus dicek DUA-DUANYA, gak cukup salah satu.

---

## 7. Status Akhir & To-Do

**Selesai dikonfirmasi (tidak perlu patch):**
- Node tree 2-mesin (Robust Lines + Momentum Candle) lengkap dipetakan
- Glossary semua parameter + default + dampak ON/OFF
- Cross-check baris-per-baris — 0 gap ditemukan
- Konfirmasi ulang 3 keputusan scope di docstring (exclude HTF, skip CRT, hitung 3 mode sekaligus) — semua benar dan konsisten dengan source
- Klasifikasi visual — dikonfirmasi TIDAK ADA elemen yang nge-gate (beda dari FBF)
- 2 keluaran "fase" (`rob_dir_text` vs `signal_text`) dikonfirmasi memang konsep berbeda, bukan duplikasi ambigu

**Belum/To-Do (sama seperti indikator lain):**
- [ ] Validasi numerik ke data real TradingView — blocked, nunggu stage 2 (fetcher Binance)
- [ ] Kalau mode **CRT (2-Candle)** suatu saat mau dipakai aktif: perlu sesi bedah terpisah dari nol (belum ada analisis sama sekali untuk mode ini)
- [ ] Kalau nanti ada perubahan yang bikin `rob_trend_up`/`rob_trend_dn` bisa true bersamaan lebih sering (misal ganti align mode default ke OR): jalankan ulang test `__main__` untuk mastiin observasi section 5 masih valid

---

## 8. Update ke File Referensi Lintas-Chat

Tambahan untuk tabel di `handoff_review_indikator.md` section 5:

| File | Isi |
|---|---|
| `robust_momcand.py` | **Tidak berubah** — sudah benar dari awal, tidak perlu versi `_v1_1` |
| `robust_momcand_panduan_pine_vs_python.md` | Dokumen ini — panduan lengkap Robust + MomCand Signal |

Indikator yang masih tersisa untuk dibedah: **RSI Pro Enhanced**, **EMA Ribbon Pro [Krypt v11]**. **ATR Percentage** kemungkinan besar gak butuh sesi sedalam ini (gak ada state persisten, source-nya sendiri cuma ~15 baris) — cukup dicek sekilas pas gilirannya nanti.
