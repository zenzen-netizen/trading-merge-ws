# Stage 3 — Panduan Replikasi Indikator (Pine Script → Python)

Status: **panduan logika siap, kode replikasi belum dibangun** (menunggu indikator final dipilih + implementasi oleh AI agent lain).

---

## Tujuan Replikasi: Bukan Cuma Angka, Tapi Juga Fase/State

Prinsip inti yang harus dipegang: replikasi Python **wajib mencerminkan data DAN visual yang dilihat di TradingView**, bukan cuma nilai numerik mentahnya. Ini bukan soal kerapian — ini soal supaya validasi dan komunikasi jadi gampang.

Ada dua layer yang harus direplikasi:

1. **Layer numerik** — deret angka hasil hitungan (contoh: nilai SMI, SMI EMA, histogram). Ini fondasi, harus akurat duluan.
2. **Layer fase/state** — kategori atau label yang diturunkan dari angka tadi (contoh: Zone OB/OS/Middle, Cross UP/DOWN, PA/PD Dip/Ready, Failed MID Hold, teks Phase gabungan). **Ini yang paling krusial** untuk proses kalibrasi setup (case study, step 3 di alur kerja) — karena inilah bahasa yang dipakai untuk "identifikasi event" secara visual, bukan angka mentah seperti `smi=45.2`.

### Kenapa Layer Fase Ini Krusial buat Validasi

- Kalau replikasi cuma fokus ke angka mentah, validasi jadi lambat — harus hitung manual tiap kali mau tahu "ini udah masuk OB zone belum" atau "ini PA Ready atau masih Dip".
- Kalau state/fase Python cocok dengan yang tampil di chart (warna bar, teks dashboard), validasi jadi sesimpel: buka candle tanggal tertentu di TradingView, baca warna bar atau teks dashboard, bandingkan dengan output Python di timestamp yang sama — tinggal cocokkan label, bukan itung ulang.
- Layer fase ini juga yang bakal dipakai **langsung** di proses kalibrasi setup nanti. Waktu ngomong soal setup, kemungkinan besar bahasa yang dipakai itu "PA Ready", "Cross Up", "OB Zone" — bukan "smi sekian, smiEma sekian". Jadi layer fase ini bukan cuma output sampingan, tapi literally bahasa komunikasi utama antara lu dan AI soal setup.

---

## Contoh Konkret: Bedah "TOP SMI Pro Enhanced v3"

Pakai script referensi yang sudah dikasih untuk ilustrasi konkret pola-pola yang perlu diperhatikan.

### Layer Numerik

- **SMI (Stochastic Momentum Index)**: dihitung dari `rel` (jarak close ke titik tengah range high-low) dan `rng` (lebar range), keduanya di-smooth pakai **double EMA** (`emaEma` — EMA dari EMA, bukan EMA biasa), lalu diskalakan.
- **SMI EMA**: signal line, EMA sederhana dari nilai SMI.
- **SMI Histogram**: selisih SMI dikurangi SMI EMA.

**Gotcha teknis di layer ini**:
- `emaEma()` adalah EMA dari EMA — kalau direplikasi jadi EMA tunggal, hasilnya beda cukup jauh, bukan sekadar selisih kecil.
- `ta.highest(lenK)` dan `ta.lowest(lenK)` tanpa argumen source eksplisit otomatis memakai `high` dan `low` bawaan Pine — bukan `close`. Default implisit seperti ini gampang kelewat kalau enggak familiar dengan behavior Pine Script.
- Warm-up period: karena ada EMA di dalam EMA, butuh kira-kira dua kali periode seeding sebelum nilai stabil — beberapa bar pertama di awal data belum representatif dan sebaiknya tidak dipakai untuk validasi.

### Layer Fase/State — Bagian yang Paling Sering Kelewat

**1. Klasifikasi momentum histogram (4 kategori)**
`Above-Up`, `Above-Down`, `Below-Down`, `Below-Up` — kombinasi posisi SMI relatif ke SMI EMA (di atas/bawah) dengan arah histogram (naik/turun dibanding bar sebelumnya). Empat kategori ini saling eksklusif dan harus direplikasi sebagai empat kondisi eksplisit, bukan disederhanakan jadi dua (misalnya cuma "bullish/bearish").

**2. Counter PA/PD — pakai kesetaraan persis (`==`), bukan `>=`**
Pola aslinya: sebuah flag jadi `true` cuma ketika counter **persis sama** dengan angka threshold — bukan "sudah mencapai atau lebih". Konsekuensinya, flag ini nyala di **satu candle spesifik saja** (event sekali tembak/pulse), bukan tetap menyala selama counter masih di atas threshold. Kalau direplikasi pakai kondisi "lebih besar sama dengan", event ini akan menyala berkali-kali padahal seharusnya cuma sekali — sinyal yang dihasilkan jadi beda drastis dari maksud aslinya.

**3. Sub-klasifikasi Dip vs Ready**
Event dasar tadi dipecah lagi jadi dua sub-state tergantung arah histogram saat event terjadi (histogram masih melemah = "Dip", histogram mulai menguat = "Ready"). Urutan evaluasi ini penting dijaga: cek event dasar dulu, baru cek arah histogram — bukan dibalik urutannya.

**4. Fakeout/failed-hold detector**
Pola ini membandingkan state SAAT INI dengan state **satu bar sebelumnya** (bukan bar sekarang) untuk mendeteksi kondisi "sempat menuju satu arah tapi gagal bertahan, balik lagi". Referensi antar-bar seperti ini gampang salah kalau proses candle di Python tidak dijaga urut per-bar secara berurutan — kalau logic ditulis secara vectorized tanpa hati-hati, berisiko "melihat" data dari bar yang belum semestinya diketahui pada titik itu (lookahead bias).

**5. Cascade prioritas warna/state — urutan if-elif krusial**
Penentuan state final mengikuti rangkaian pengecekan berurutan: cross duluan, baru OB/OS zone, baru PA/PD, baru fakeout, baru kondisi background biasa. Kalau di satu candle kebetulan beberapa kondisi sama-sama terpenuhi, yang menang adalah kondisi yang urutannya paling atas — **bukan digabung, bukan diambil yang "lebih penting" menurut interpretasi lain.** Replikasi Python wajib menjaga urutan if-elif ini persis sama, bukan mengecek semua kondisi secara independen lalu bingung menentukan mana yang berlaku kalau ada lebih dari satu yang benar.

**6. Teks fase gabungan (dashboard)**
Ini representasi akhir dari seluruh state di atas, ditampilkan sebagai satu baris teks di dashboard chart. Ini target validasi paling praktis — cukup buat satu kolom setara di output Python, lalu dicocokkan langsung ke teks yang tampil di dashboard chart pada candle yang sama.

---

## Rekomendasi Struktur Output Replikasi

Supaya gampang divalidasi dan langsung siap dipakai di proses kalibrasi setup (case study), output dari fungsi indikator sebaiknya berupa tabel dengan kolom-kolom eksplisit seperti ini — bukan cuma satu kolom angka:

| Kolom | Isi | Analog di Pine (contoh SMI) |
|---|---|---|
| Nilai numerik mentah | Nilai indikator, signal line, histogram | `smi`, `smiEma`, `smiH` |
| Kategori momentum histogram | above_up / above_down / below_down / below_up | `sHAU/sHAD/sHBD/sHBU` |
| Kategori zone | OB / Upper / Middle / Lower / OS | `sZone` |
| Event cross | none / cross_up / cross_down (cuma true di bar event terjadi) | `sCU`/`sCD` |
| State event khusus | none / dip / ready / fakeout, dst | `paDip/paReady/pdDip/pdReady`, `failedMIDHold` |
| Teks fase gabungan | Representasi final semua state di atas | `barStateTxt` |

Kolom teks fase gabungan inilah yang paling sering dipakai untuk komunikasi ("di tanggal segini fase-nya apa?") dan paling gampang divalidasi langsung lawan tampilan visual chart — tanpa perlu hitung manual satu-satu.

---

## Sinyal Berbasis Pivot (Divergence, dst) — Kategori Terpisah, Ada Delay

Sinyal yang butuh titik pivot (misalnya divergence) perlu beberapa bar **setelah** titik pivot untuk bisa dikonfirmasi sebagai pivot valid — bukan cuma bar sebelum. Konsekuensinya, sinyal jenis ini terdeteksi dengan **delay**: baru "muncul" beberapa bar setelah titik kejadian sebenarnya. Kalau sinyal berbasis pivot dipakai sebagai bagian setup, backtest engine harus mensimulasikan delay konfirmasi ini dengan benar — sinyal tidak boleh dianggap terjadi persis di bar pivot, karena itu artinya sistem "tahu" sesuatu sebelum waktunya (lookahead bias).

---

## Checklist Replikasi

- [ ] Layer numerik: source price yang dipakai benar (high/low/close sesuai aslinya), metode smoothing benar (kalau double smoothing, jangan disederhanakan jadi single)
- [ ] Layer fase: semua kategori/state direplikasi eksplisit sebagai kolom terpisah, bukan dihitung ulang manual tiap kali dibutuhkan
- [ ] Kesetaraan persis (`==`) dan kondisi ambang (`>=`) dijaga sesuai logic asli — jangan digeneralisasi asal mirip
- [ ] Referensi antar-bar (state bar sebelumnya) diproses berurutan per-bar, bukan vectorized yang berisiko lookahead
- [ ] Urutan prioritas (if-elif berurutan) direplikasi persis urutannya, bukan dicek independen semua sekaligus
- [ ] Sinyal berbasis pivot disimulasikan dengan delay konfirmasi yang sesuai, bukan seolah muncul real-time di titik pivot
- [ ] Ada kolom teks fase gabungan sebagai target validasi visual utama
- [ ] Validasi dilakukan di DUA layer: cocokkan angka mentah DAN cocokkan teks fase ke tampilan chart asli, di beberapa candle sampel dari kondisi market yang berbeda-beda (trending, sideways, volatile)

---

## Keterkaitan ke Stage Lain

- **Ke stage 2 (data & waktu)**: validasi numerik dan fase harus dilakukan pada candle yang boundary waktunya sudah dipastikan benar (lihat `stage_02_data_dan_waktu.md`) — kalau boundary candle salah, validasi indikator ikut salah walau logic replikasi-nya sendiri sudah benar.
- **Ke proses kalibrasi setup (case study)**: kolom teks fase gabungan inilah yang bakal jadi bahan utama diskusi di tiap case study — mempercepat proses karena tinggal rujuk label yang sama seperti yang terlihat di chart, bukan angka mentah.
