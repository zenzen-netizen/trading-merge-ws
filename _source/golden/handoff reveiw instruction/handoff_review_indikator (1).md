# Handoff — Deep-Dive Review Indikator (Pine ↔ Python)

> Dokumen ini dibawa ke chat baru tiap mau bedah 1 indikator. Lampirkan
> file ini + source `.pine`/`.txt` + `.py` indikator yang mau dibahas.
> Chat baru otomatis punya konteks metodologi, mindset, dan tahu harus
> ngapain tanpa perlu dijelasin ulang dari nol.

---

## 0. Konteks Project (Anchor — Baca Dulu Kalau Belum)

Project ini bagian dari sistem backtest multi-strategi (`00_roadmap.md`
di project knowledge). Sesi review indikator per-indikator ini masuk ke
**build-stage 3** (`stage_03_replikasi_indikator.md`) — validasi replikasi
Pine→Python, khususnya layer fase/state, sebelum indikator dipakai bahan
strategi resmi. Playbook eksekusi teknis ada di
`00_playbook_eksekusi_ai_agent.md` langkah 2.

**Status stage 2 (fetcher Binance): belum dibangun.** Artinya semua
review di sesi-sesi ini masih level **cross-check logic Pine vs Python**
(baca kode, bukan baca angka), BUKAN validasi numerik ke data real. Itu
nunggu stage 2 kelar.

---

## 1. Mindset Wajib (Berlaku ke Semua Indikator)

**Chart TradingView = kebenaran setup.** Yang jadi acuan kalibrasi setup
nanti adalah apa yang KETAMPIL di chart, bukan apa yang "kejadian di
mesin" doang. Konsekuensinya, tiap indikator perlu dicek dua lapisan:

- **Lapisan Mesin** — logic yang nentuin APAKAH suatu kondisi/event
  terjadi secara matematis (angka, counter, threshold).
- **Lapisan Visibility** — ada gak elemen yang nentuin APAKAH sesuatu
  KETAMPIL di chart, terpisah dari apakah dia "terjadi". Ini yang paling
  gampang kelewat kalau cuma baca sekilas, karena kelihatannya "cuma
  soal warna/toggle tampilan" padahal bisa nge-gate signifikan (contoh
  nyata: filter trend Supertrend di FBF, default ON, ngefilter mayoritas
  event).

**Default value Pine = default value Python.** Semua parameter Python
harus punya default persis sama dengan input Pine aslinya — ini bukan
opsional, karena "setup yang user pakai" itu ya defaultnya, kecuali user
eksplisit bilang dia ubah sesuatu.

**Waspada indikator yang punya LEBIH DARI SATU representasi "fase"
sekaligus.** Ditemukan di sesi SMI Pro v3: satu indikator bisa punya
beberapa keluaran yang sama-sama kelihatan seperti "kasih tau kondisi
saat ini", tapi definisinya TIDAK OTOMATIS identik satu sama lain —
misalnya baris teks di dashboard ("Zone") vs baris teks lain di
dashboard ("Phase") vs warna candle di chart itu sendiri. Kadang dua
di antaranya ternyata cascade yang sama persis (cuma beda bentuk
output — teks vs warna), tapi yang ketiga punya threshold/logic
sedikit beda (termasuk beda strict `<` vs non-strict `<=` di satu
titik batas). Kalau ini kelewat, replikasi Python bisa nurunin
"fase" dari sumber yang salah tanpa sadar — jangan asumsikan "yang
namanya mirip pasti sama persis", WAJIB ditelusuri baris kodenya.
Lihat langkah 2b dan contoh konkret di bagian 3.

---

## 2. Metodologi Review (Urutan Kerja, Reusable)

1. **Baca source Pine + Python side by side.** Jangan asumsi dari nama
   variabel — telusuri tiap baris logic yang related.
2. **Bikin glossary istilah** — tiap fase/state/filter yang dipakai
   indikator, plus: default value, dampak ON/OFF, status di Python
   (replikasi aktif / replikasi tapi dormant / sengaja dibuang).

   **2b. Kalau indikator punya lebih dari satu "keluaran fase"**
   (baris dashboard berbeda, warna bar, label plot, dst) — jangan
   langsung anggap semuanya identik. Petakan dulu SATU-SATU: nama
   variabel Pine-nya, di mana dia muncul di chart, berapa kategori,
   dan urutan cascade-nya kalau ada. Baru setelah dipetakan, cek
   apakah dua atau lebih di antaranya benar-benar cascade yang sama
   (kalau sama, boleh diwakili SATU kolom Python + didokumentasikan
   eksplisit "X = Y, sudah dicek identik") atau ternyata beda
   (kalau beda, WAJIB jadi kolom terpisah di Python, jangan digabung
   demi kesederhanaan). Tandai juga titik ambang mana yang strict
   (`<`/`>`) vs non-strict (`<=`/`>=`) di tiap keluaran — inkonsistensi
   strict vs non-strict antar-keluaran DI SOURCE PINE ITU SENDIRI
   pernah ketemu (lihat SMI Pro v3 di bagian 3), bukan cuma soal
   Python salah baca.
3. **Bikin node tree teks** (bukan cuma diagram visual, biar ringan &
   gampang di-copy) buat tiap mesin/state-machine yang ada di indikator.
   Pisah tree per "otak"/"lapisan" kalau indikatornya kompleks (contoh
   FBF: Tracker vs Judge vs Visibility — 3 tree terpisah, baru digabung
   di 1 flow besar).
4. **Cross-check baris-per-baris** — cari SEMUA elemen yang exist di
   Pine tapi mungkin kelewat di Python: state persisten antar-bar,
   operator ambang (`==` vs `>=`), urutan cascade if-elif, filter yang
   defaultnya ON (paling gampang kelewat karena orang cenderung fokus ke
   yang OFF-dijelasin-di-tooltip), dan terutama elemen VISUAL yang
   ternyata NGE-GATE (bukan cuma kosmetik).
5. **Klasifikasi tiap elemen visual** yang ketemu: murni kosmetik (aman
   dibuang) vs nge-gate visibility (WAJIB direplikasi kalau mau
   mindset "chart=kebenaran" konsisten).
6. **Kalau ketemu gap nyata** (elemen nge-gate yang belum direplikasi,
   ATAU keluaran fase yang ternyata beda definisi seperti poin 2b):
   patch Python-nya. Bump versi filename (`_v1_2`, dst) biar jelas beda
   dari yang lama. Jangan overwrite file lama diam-diam.
7. **Jabarkan semua skenario jalur** yang mungkin terjadi dari kombinasi
   state — termasuk kasus counter-intuitive (kayak FBF skenario F: wave
   sempat kelihatan pas forming, tapi break-nya malah hilang dari chart
   karena trend keburu flip balik pas mau confirm; atau kayak SMI Pro
   v3: dua keluaran fase beda jawaban persis di satu titik ambang).
8. **Compile jadi 1 dokumen "buku panduan"** — glossary + node tree +
   skenario + tabel dampak ON/OFF + status replikasi akhir. WAJIB ada
   section terpisah "Klasifikasi Definisi Fase" kalau langkah 2b nemuin
   lebih dari satu keluaran fase, lengkap dengan tabel kamus istilah
   (nama Pine ↔ nama Python ↔ kondisi pemicu) — ini yang jadi istilah
   resmi buat dikomunikasikan ke AI coding agent nanti pas kalibrasi
   setup. Ini yang jadi pegangan kalau lupa cara kerja indikatornya
   nanti.
9. **Validasi numerik ke data real TETAP PENDING** sampai stage 2 kelar
   — dicatat eksplisit di dokumen sebagai to-do, bukan dianggap selesai.

---

## 3. Status Sesi Sebelumnya

### FBF (Fractal Break Filter v11.1) — Selesai

**Selesai dikerjakan:**
- Node tree Tracker (wave A-B-C) + Judge (candidate→BREAK/FAIL)
- Cross-check baris-per-baris Pine vs Python — ketemu 1 gap nyata
  (visibility gating Supertrend, default ON, belum direplikasi) + 1
  selisih kecil (A3 lookback edge-case NaN vs clip di awal data)
- Patch `fbf_break_filter_v1_2.py` — nambah layer visibility
  (`st_trend`, `bull_wave_visible`, `bear_wave_visible` di bars;
  `visible_at_birth`, `visible_at_confirm` di events), tanpa ubah
  logic Tracker/Judge yang udah tervalidasi
- Dokumen panduan lengkap: `fbf_panduan_pine_vs_python.md` (glossary,
  4 node tree, 7 skenario jalur, tabel ON/OFF, status akhir)

**Belum/To-Do:**
- [ ] Validasi numerik ke data real TradingView — blocked, nunggu
      stage 2 (fetcher Binance)
- [ ] Kalau A3 lookback (`enable_a_lookback`) nanti dipakai aktif: cek
      manual titik-titik dekat awal dataset (selisih NaN vs clip)
- [ ] Kalau `enable_smi_filter`/`enable_c_fractal` nanti diaktifkan:
      belum ada review mendalam ke filter itu (masih dormant, cuma
      dicek eksis di kode, belum dibedah skenarionya)

### SMI Pro Enhanced v3 — Selesai

**Selesai dikerjakan:**
- Node tree alur utama (per-bar) + tree divergensi terpisah
- Glossary lengkap parameter & filter, termasuk klasifikasi kosmetik
  vs bukan
- Cross-check baris-per-baris Pine vs Python — ketemu **1 gap kelas
  "poin 2b metodologi"**: indikator ini punya 3 keluaran fase berbeda
  sekaligus —
  - `sZone` ("Zone" di dashboard, 5 kategori sederhana),
  - `barStateTxt` ("Phase" di dashboard, cascade 13 kategori),
  - `barCol` (warna candle di chart, ternyata cascade IDENTIK dengan
    `barStateTxt` — cuma beda bentuk output).

  `sZone` vs `barStateTxt`/`barCol` beda strict-operator di titik batas
  OS (`smi <= smiOS` vs `smi < smiOS`) — inkonsistensi ini ADA DI
  SOURCE PINE ITU SENDIRI, bukan salah baca Python. Python versi lama
  tanpa sadar nurunin kolom fase-nya dari `sZone`, bukan dari
  `barStateTxt`/`barCol` yang seharusnya jadi acuan utama (chart =
  warna candle = kebenaran).
- Patch `smi_pro_v3_v1_1.py` — `phase_label` sekarang independen dari
  `zone`, cek threshold langsung niru `barStateTxt`/`barCol` persis
- Dokumen panduan lengkap: `smi_pro_panduan_pine_vs_python.md`
  (glossary, 2 node tree, section klasifikasi 3-sumber-fase + kamus
  istilah, tabel ON/OFF, status akhir)

**Belum/To-Do:**
- [ ] Validasi numerik ke data real TradingView — blocked, nunggu
      stage 2 (fetcher Binance)
- [ ] Validasi tie-break pivot (`_find_pivots`) kalau ketemu kasus
      nilai SMI identik dalam satu window — perilaku Pine yang PERSIS
      untuk kasus ini belum terdokumentasi jelas
- [ ] Kasus collision divergence (bullish & bearish confirm di bar yang
      sama persis) — saat ini bearish menimpa bullish, flag sebagai
      known limitation bukan bug, belum diuji apakah realistis muncul
      di data crypto

---

## 4. Template Pembuka Chat Baru — Indikator Selanjutnya

Copy blok di bawah, ganti `[NAMA_INDIKATOR]`, tempel jadi pesan pertama
di chat baru bareng lampiran file ini + source Pine (.txt) + Python (.py)
indikator yang dimaksud:

```
Lanjut review indikator [NAMA_INDIKATOR] — Pine vs Python.
File terlampir: handoff ini, source Pine (.txt), source Python (.py).

Ikuti metodologi & mindset di bagian 1-2 handoff ini. Mulai dari:
1. Node tree alur (text, bukan cuma diagram)
2. Glossary istilah/fase/filter + default + dampak ON/OFF + status Python
   (termasuk poin 2b: kalau ada >1 keluaran fase, petakan & bandingkan
   dulu sebelum asumsi identik)
3. Cross-check Pine vs Python cari gap (terutama elemen visual yang
   ternyata nge-gate, bukan cuma kosmetik, DAN inkonsistensi antar
   keluaran fase kalau ada lebih dari satu)
4. Kalau ada gap: patch + versionkan filename
5. Compile jadi 1 buku panduan .md kayak
   smi_pro_panduan_pine_vs_python.md / fbf_panduan_pine_vs_python.md
   (kalau ada >1 keluaran fase, wajib ada section klasifikasi + kamus
   istilah, contoh formatnya ada di smi_pro_panduan_pine_vs_python.md
   section 2)
```

---

## 5. File yang Udah Dihasilkan (Referensi Lintas-Chat)

| File | Isi |
|---|---|
| `fbf_break_filter_v1_2.py` | Python replikasi FBF, sudah termasuk layer visibility |
| `fbf_panduan_pine_vs_python.md` | Buku panduan lengkap FBF |
| `smi_pro_v3_v1_1.py` | Python replikasi SMI Pro v3, versi terpatch — pakai ini, bukan `smi_pro_v3.py` lama |
| `smi_pro_v3.py` | Versi lama SMI (v1.0) — masih ada gap Zone-vs-Phase di titik OS, disimpan sebagai riwayat saja |
| `smi_pro_panduan_pine_vs_python.md` | Buku panduan lengkap SMI Pro v3, termasuk section klasifikasi 3-sumber-fase (contoh rujukan kalau nemu kasus serupa di indikator lain) |

**Catatan:** FBF dan SMI Pro v3 sudah lewat deep-dive lengkap (node tree,
glossary, cross-check baris-per-baris, dokumen panduan terpisah).
Indikator berikutnya yang belum dibedah: RSI Pro Enhanced, EMA Ribbon Pro
[Krypt v11], Robust + MomCand Signal (sudah ada draft Python-nya,
`robust_momcand.py`, tapi belum deep-dive sedalam FBF/SMI), ATR Percentage
(sudah ada `atr_percentage.py`, indikator paling sederhana — kemungkinan
gak butuh deep-dive selengkap yang lain karena gak ada state persisten).
