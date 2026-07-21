# FBF (Fractal Break Filter v11.1) — Panduan Alur Pine vs Python

> Dokumen pegangan. Kalau lupa cara kerja FBF atau bingung bedanya Pine
> vs Python, baca ini duluan sebelum buka kode. Berlaku untuk
> `fbf_break_filter_v1_2.py`, mengacu ke source `Fractal Break Filter v11.1.txt`.

---

## 0. Mindset Dasar (Wajib Dipegang Baca Dokumen Ini)

**Chart TradingView = kebenaran setup.** Apa yang KETAMPIL di chart itu
yang jadi acuan waktu kalibrasi setup (case study), bukan apa yang
"kejadian di mesin" tapi gak pernah kelihatan.

Konsekuensi mindset ini: indikator ini punya **dua lapisan** yang harus
dipisah jelas.

| Lapisan | Ngapain | Nentuin |
|---|---|---|
| **Lapisan 1 — Mesin** | Tracker + Judge | APAKAH event BREAK/FAIL terjadi, secara matematis |
| **Lapisan 2 — Visibility** | Gating Supertrend/EMA | APAKAH event itu KETAMPIL di chart |

Event bisa aja "benar secara matematis" (Lapisan 1 bilang ya) tapi
"gak pernah ada" secara mindset kita (Lapisan 2 nyembunyiin). Python
`v1.2` sekarang punya dua-duanya — lihat kolom `visible_at_confirm` di
`events_df` buat nyaring mana yang beneran perlu dipakai acuan.

---

## 1. Glossary — Istilah yang Dipakai

| Istilah | Arti | Default | Status di Python |
|---|---|---|---|
| **Pivot / Fractal** | Titik tertinggi/terendah lokal, confirm setelah `right_bars` candle ke kanan kebentuk (delay wajib, anti-lookahead) | left=3, right=3 | Replikasi (`_find_pivots`) |
| **Leg A** | Titik awal wave (pivot low buat wave bull) | — | Replikasi |
| **Leg B** | Titik pivot high yang jadi level breakout | — | Replikasi |
| **Leg C** | Titik retracement setelah B, dikonfirmasi belakangan | — | Replikasi |
| **Tracker (Otak 1)** | Mesin yang bentuk wave A→B→C, satu slot aktif per sisi (bull/bear) | — | Replikasi (loop `tb_phase`/`tr_phase`) |
| **Judge (Otak 2)** | Mesin yang adili candidate ABC beku jadi BREAK/FAIL, sampai 8 slot paralel per sisi | — | Replikasi (`bull_cands`/`bear_cands`) |
| **Phase (tracker)** | 0 = idle (nunggu wave baru), 1 = forming (C masih tentatif) | — | Replikasi (`tb_phase`) |
| **Candidate** | Snapshot beku A/B/C yang udah lolos dari tracker, dikirim ke Judge | — | Replikasi (dict di `bull_cands`) |
| **Active (candidate)** | Candidate udah breakout level B, lagi ditracking persistence-nya | — | Replikasi (`c["active"]`) |
| **Persist** | Counter berapa bar berturut candidate bertahan di luar B + buffer ATR | reqN=1 (persistence filter off) | Replikasi (`c["persist"]`) |
| **BREAK** | Event candidate lolos SEMUA syarat confirm | — | Replikasi (`event_type="BREAK"`) |
| **FAIL** | Event candidate gagal bertahan (balik masuk B) sebelum confirm | — | Replikasi (`event_type="FAIL"`) |
| **Struct filter** | C harus higher-low (bull) / lower-high (bear) dibanding A | ON | Replikasi (`enable_struct_filter`) |
| **A2 dist filter** | Jarak A-B minimal `aDistMult × ATR` | ON, mult=1.0 | Replikasi (`enable_a_dist`) |
| **A3 lookback** | Override A jadi titik paling ekstrem N bar ke belakang, dihitung ULANG saat candidate aktif | OFF | Replikasi tapi dormant |
| **C1 fractal** | C wajib align sama pivot fractal lebih besar | OFF | Replikasi tapi dormant |
| **C2 fibo** | Retracement B→C harus di rentang 0.5–0.786 dari A→B | ON | Replikasi (`enable_fibo_bc`) |
| **Fibo box** | Kotak warna visual doang, penanda "C masuk zona fibo apa enggak" | ON tampil, tapi `hideWaveIfC2Invalid` OFF (gak gating apa pun) | TIDAK direplikasi (murni visual, gak ngefek) |
| **ATR buffer filter** | Breakout harus tembus B minimal `atrMult × ATR` | ON, mult=0.15 | Replikasi (`enable_atr_filter`) |
| **Persistence filter** | Candidate wajib tahan N bar berturut sebelum boleh confirm | OFF, N=2 | Replikasi tapi dormant (reqN=1 efektif) |
| **SMI filter** | Confirm butuh persetujuan SMI internal (instance terpisah dari indikator SMI Pro) | OFF | Replikasi tapi dormant |
| **No duplicate** | 1 level B cuma boleh confirm BREAK sekali | ON | Replikasi |
| **EMA trend filter** | Gate visibility berbasis close vs EMA slow | OFF | Replikasi (v1.2) tapi dormant |
| **Supertrend trend filter** | Gate visibility berbasis Supertrend Adaptive | **ON** ⚠️ | Replikasi (v1.2), **AKTIF** |
| **wasVisible / visible_at_birth** | Status visibility SAAT wave lahir (C lock) | — | Kolom baru v1.2 |
| **visible_at_confirm** | Status visibility SAAT event BREAK/FAIL terjadi | — | Kolom baru v1.2 |
| **BREAK↺** | Tag Pine buat BREAK yang lahir invisible tapi confirm setelah trend flip jadi visible | — | Diwakili kombinasi flag, bukan tag visual (Python gak punya chart) |

---

## 2. Node Tree — Lapisan 1a: Tracker (bentuk wave A-B-C)

Sisi bull. Sisi bear cerminan terbalik (pivot low↔high, A<B↔A>B, dst).

```
IDLE (phase=0)
│
├─ pivot high baru confirm (delay right_bars)
│  A = pivot low sebelum B (pakai A-fractal kalau enable_a_fractal ON)
│  syarat mulai: A < B, bar A lebih awal dari bar B
│
▼
WAVE FORMING (phase=1)
│  garis A→B, B→C(tentatif) — C terus update = low terendah sejak B
│
├─ close < A (kapan pun) ──► INVALIDATED, balik IDLE
│                             (candidate TIDAK dibuat)
│
└─ C terkunci, dipicu:
   • pivot low baru confirm setelah B, ATAU
   • close tembus di atas B
   │
   ├─ C ≤ A (gagal struct) ──► DISCARDED, balik IDLE
   │                            (candidate TIDAK dibuat)
   │
   └─ C > A (struct valid) ──► CONFIRMED WAVE
                                cap status visibility SAAT INI
                                (bull_wave_visible[i]) jadi "visible_at_birth"
                                → push candidate ke Judge
                                → tracker balik IDLE, cari wave baru
```

---

## 3. Node Tree — Lapisan 1b: Judge (candidate → BREAK/FAIL)

```
FROZEN (baru masuk array, belum aktif)
│
├─ close < A ──► DISCARDED (hilang dari array, gak pernah diadili)
│
└─ close > B + jarak ATR cukup ──► ACTIVE (persist=1)
   │  [kalau A3 lookback ON: A di-override di sini]
   │
   ▼
   ACTIVE
   │
   ├─ tiap bar: masih di atas B + jarak ATR?
   │  YA → persist+1
   │  TIDAK → FAIL
   │          catat visible_at_confirm = status visibility bar INI
   │          persist reset 0, active=false
   │          candidate TETAP di array (↻ bisa ACTIVE lagi kalau breakout ulang)
   │
   └─ tiap bar aktif, cek confirm (SEMUA harus lolos):
      persist≥syarat, SMI ok (opsional), struct ok, jarak A-B vs ATR,
      C-fractal align (opsional), fibo retracement 0.5–0.786
      │
      └─ lolos semua ──► BREAK
                          catat visible_at_confirm = status visibility bar INI
                          cek duplikat per level B
                          candidate dibuang (selesai)
```

---

## 4. Node Tree — Lapisan 2: Visibility Gating

```
Tiap bar, dihitung independen dari Lapisan 1:
│
├─ Supertrend Adaptive (period=10, mult=3.0, src=hl2)
│  → status: uptrend (1) / downtrend (-1)
│
├─ EMA trend filter (OFF default → selalu lolos kalau off)
│
└─ bull_wave_visible = EMA_ok AND Supertrend==uptrend
   bear_wave_visible = EMA_ok AND Supertrend==downtrend

Dipakai di DUA titik oleh Lapisan 1:
│
├─ saat WAVE CONFIRMED (C lock) → dicatat sebagai visible_at_birth
│
└─ saat event BREAK atau FAIL terjadi → dicatat sebagai visible_at_confirm
   (trend bisa udah beda dari saat wave lahir — makanya dicatat dua kali,
   bukan sekali)
```

---

## 5. Flow Gabungan — dari Harga Mentah sampai Event Tampil di Chart

```
Data harga (high/low/close)
│
├──────────────► Lapisan 2: hitung Supertrend trend tiap bar
│                 (independen, jalan terus tiap bar apa pun kondisi wave)
│
└──────────────► Lapisan 1a: Tracker
                  │
                  ├─ INVALIDATED / DISCARDED → selesai, tidak ada apa-apa
                  │
                  └─ CONFIRMED WAVE
                     │  ambil status Lapisan 2 SAAT INI → visible_at_birth
                     │
                     ▼
                     Lapisan 1b: Judge (candidate)
                     │
                     ├─ DISCARDED (close<A sebelum breakout) → selesai
                     │
                     └─ ACTIVE → loop FAIL/persist
                        │
                        ├─ FAIL → ambil status Lapisan 2 SAAT INI
                        │          → visible_at_confirm (untuk event FAIL)
                        │
                        └─ BREAK → ambil status Lapisan 2 SAAT INI
                                    → visible_at_confirm (untuk event BREAK)

Hasil akhir tiap event BREAK/FAIL: (visible_at_birth, visible_at_confirm)
→ dipakai nyaring "yang beneran tampil di TradingView" vs "yang cuma
  kejadian di mesin"
```

---

## 6. Semua Skenario Jalur yang Mungkin Terjadi

Kombinasi (visible_at_birth, visible_at_confirm) x (BREAK/FAIL) menghasilkan
beberapa jalur konkret. Ini daftar lengkapnya:

**A. Invalidated / Discarded di Tracker** — gak pernah jadi candidate,
gak pernah masuk events_df sama sekali. Paling sering terjadi, karena
mayoritas percobaan wave emang gagal duluan sebelum sempat breakout.

**B. Discarded di Judge** (close<A sebelum sempat breakout B) — candidate
sempat lahir (mungkin visible mungkin enggak), tapi gak pernah masuk
events_df juga, karena gak pernah aktif — ini juga gak tercatat sebagai
event (baik BREAK maupun FAIL).

**C. Visible dari lahir sampai confirm (kasus normal)** —
`visible_at_birth=True, visible_at_confirm=True`. Ini yang paling gampang
divalidasi manual ke chart TV, karena dari awal sampai akhir kelihatan
terus, gak ada perubahan trend di tengah jalan.

**D. Invisible dari lahir sampai confirm** —
`visible_at_birth=False, visible_at_confirm=False`. Event ini KEJADIAN
secara matematis tapi **TIDAK PERNAH KETAMPIL** di chart TradingView sama
sekali. Dengan mindset "chart = kebenaran", event ini harus DIABAIKAN
kalau tujuannya kalibrasi setup — walau ada di events_df.

**E. Lahir invisible, confirm jadi visible ("BREAK↺")** —
`visible_at_birth=False, visible_at_confirm=True`. Trend flip di tengah
proses candidate berjalan (dari lawan trend jadi searah). Di Pine, event
ini KETAMPIL tapi dengan tag khusus "BREAK↺" plus wave induknya digambar
ulang retroaktif. Di Python, wave induk gak digambar ulang (gak ada
chart), tapi kombinasi dua flag ini udah cukup buat identifikasi kasus
yang sama.

**F. Lahir visible, confirm jadi invisible (kebalikan E)** —
`visible_at_birth=True, visible_at_confirm=False`. Trend flip ke arah
sebaliknya — candidate awalnya kelihatan (wave-nya tergambar), tapi pas
akhirnya BREAK/FAIL beneran kejadian, trend udah berubah lawan arah,
jadi event itu **HILANG dari pandangan** padahal user sempat lihat
wave-nya waktu masih forming. Ini kasus paling gampang bikin bingung
pas kalibrasi manual (user inget lihat wave-nya, tapi break-nya gak
pernah nongol) — makanya penting kedua flag ini dicek, bukan cuma salah
satu.

**G. FAIL yang loop berkali-kali sebelum akhirnya BREAK atau discard
permanen** — satu candidate bisa gantian ACTIVE → FAIL → ACTIVE → FAIL
beberapa kali (tiap kali breakout ulang B) sebelum akhirnya salah satu:
lolos semua syarat jadi BREAK, atau harga jatuh balik ke bawah A dan
dibuang total. Tiap siklus FAIL tercatat sebagai baris event terpisah di
events_df (bukan cuma baris terakhir).

---

## 7. Tabel Dampak ON/OFF — Ringkas

| Filter | Kalau ON | Kalau OFF |
|---|---|---|
| `enable_struct_filter` | C wajib higher-low/lower-high vs A, banyak wave gagal duluan | semua wave lolos struct, lebih banyak candidate lahir |
| `enable_a_dist` | Wave dgn jarak A-B kecil dibuang | wave dekat pun lolos |
| `enable_fibo_bc` | C wajib retracement 0.5–0.786 dari A-B | retracement berapa pun lolos |
| `enable_atr_filter` | Breakout wajib tembus cukup jauh dari B | breakout tipis pun langsung aktif |
| `enable_persist_filter` | Candidate wajib tahan N bar dulu sebelum confirm | 1 bar langsung cukup buat confirm |
| `enable_smi_filter` | Confirm butuh SMI internal setuju arah | SMI diabaikan total |
| `enable_a_lookback` | A di-override jadi titik paling ekstrem pas breakout | A tetap dari pivot awal |
| `enable_c_fractal` | C wajib align pivot fractal lebih besar | C dari pivot biasa cukup |
| `enable_st_trend_filter` | **Gate visibility aktif** — banyak event matematis gak ketampil | semua event yang matematis kejadian juga ketampil |
| `enable_ema_trend_filter` | Gate tambahan berbasis EMA slow | tidak nge-gate apa pun |
| `no_duplicate` | 1 level B max 1x confirm | level B sama bisa confirm berkali-kali (jarang secara praktik) |

---

## 8. Cara Pakai buat Kalibrasi Setup (Case Study)

Sesuai `00_roadmap.md` langkah 3 (kalibrasi setup via studi kasus riil):

```python
result = calculate_fbf(df, ...)  # default = persis Pine
events = result["events"]

# INI yang jadi acuan diskusi kalibrasi setup — persis apa yang
# kelihatan di TradingView pada window waktu yang sama:
events_visible = events[events["visible_at_confirm"]]

# kalau mau bandingkan "kenapa event ini gak kepake di kalibrasi
# padahal ada di data" — cek events yang invisible:
events_hidden = events[~events["visible_at_confirm"]]
```

Saat nunjukin window waktu ke AI buat identifikasi event (langkah 3
alur operasional), **selalu filter ke `events_visible` dulu** — biar AI
gak salah "lihat" event yang sebenarnya gak pernah tampil ke user di
chart aslinya.

---

## 9. Status Replikasi — Ringkasan Akhir

| Bagian | Status |
|---|---|
| Tracker (wave A-B-C) | ✅ Replikasi persis, tervalidasi logic |
| Judge (BREAK/FAIL + semua filter Grup A) | ✅ Replikasi persis, tervalidasi logic |
| Fibo retracement (angka) | ✅ Replikasi persis |
| Fibo box (visual) | ❌ Sengaja dibuang, murni kosmetik nol pengaruh |
| Supertrend gating (Lapisan 2) | ✅ Replikasi v1.2 |
| EMA gating (Lapisan 2) | ✅ Replikasi v1.2, dormant (default off) |
| Tag "BREAK↺" | ⚠️ Diwakili flag, bukan visual redraw (Python gak punya chart) |
| HTF section, warna, label, fade-lookback | ❌ Sengaja dibuang, murni kosmetik |
| A3 lookback edge-case (NaN vs clip di awal data) | ⚠️ Ada selisih kecil, flag buat dicek pas validasi data real |

**Belum divalidasi ke data real TradingView** — nunggu stage 2 (fetcher
Binance) selesai dibangun. Begitu ada data real, checklist validasi di
akhir file `fbf_break_filter_v1_2.py` wajib dijalankan sebelum dipakai
strategi resmi.
