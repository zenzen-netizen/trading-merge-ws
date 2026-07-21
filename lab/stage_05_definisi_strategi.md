# Stage 5 — Panduan Definisi Strategi (Skema & Format Teknis)

Status: panduan siap, skema belum diimplementasikan sebagai kode.

---

## Penting: Beda dengan Alur Operasional, Tapi Nyambung Erat

Sebelum masuk isi, perlu diluruskan dulu supaya tidak tertukar dengan yang sudah dibahas di `journal/00_roadmap.md` bagian "Alur Kerja Operasional".

**Catatan penomoran**: build-stage 3 ("Replikasi indikator") dan langkah ke-3 di siklus operasional ("Kalibrasi setup via studi kasus riil") adalah dua hal berbeda yang kebetulan sama-sama bernomor 3 — karena keduanya berasal dari tree yang berbeda (tree pembangunan sistem vs tree siklus pemakaian). Kalau merujuk salah satu, sebaiknya disebut eksplisit "build-stage 3" atau "langkah operasional 3" supaya tidak ambigu.

**Dua hal yang berbeda lapisan**:

- **Langkah 2–4 di siklus operasional** (Indikator siap → Kalibrasi setup → Rule strategi) adalah **metode/proses** — cara lu dan AI, tiap kali ada ide strategi baru, sampai ke pemahaman rule yang benar dan tidak ambigu. Ini soal *bagaimana cara berpikir dan berkomunikasi* untuk merumuskan setup.
- **Stage 5 di build roadmap** (dokumen ini) adalah **infrastruktur/format teknis** — skema kode yang dibangun **sekali**, supaya hasil dari proses kalibrasi (kesimpulan aturan final dari case study) punya struktur baku untuk dituliskan jadi kode yang bisa dijalankan backtest engine, strategi apa pun bentuknya.

Analoginya: langkah operasional itu cara merumuskan resep. Stage 5 ini bikin **format kartu resep standar** — kolom apa saja yang wajib diisi, strukturnya seperti apa — supaya "dapur" (backtest engine, stage 4) bisa memasak resep apa pun tanpa perlu diubah tiap kali resepnya beda.

---

## Yang Perlu Dibangun di Stage 5

### 1. Struktur File di `strategies/[nama_strategi]/`

Skema yang disarankan, tiap strategi punya isi seragam:

- **`config`** (parameter) — semua angka yang bisa diubah-ubah: periode indikator, threshold, risk per trade, mode stop loss/take profit, dsb. Dipisah dari logic supaya tuning parameter (langkah 4a di alur operasional) tidak perlu ubah kode, cukup ubah angka di sini.
- **`rules`** (logic) — fungsi yang menentukan sinyal entry dan exit, ditulis mengacu langsung ke kesimpulan aturan final dari case study yang relevan (bukan ditulis ulang dari ingatan/interpretasi baru).
- **`metadata`** — hipotesis strategi (dari langkah 1 alur operasional), dan link eksplisit ke versi case study yang jadi acuan (misalnya "mengacu ke `case_studies/case_v3.md`") — supaya kalau nanti aturan berubah karena case study baru, jelas kode mana yang harus diupdate.

### 2. Interface Kontrak ke Backtest Engine

Ini bagian paling penting secara teknis: backtest engine (stage 4) harus bisa menjalankan **strategi apa pun** tanpa perlu tahu detail masing-masing strategi. Supaya itu bisa terjadi, tiap strategi wajib mengikuti kontrak yang sama:

- **Input yang diterima**: tabel data yang sudah mengandung kolom-kolom hasil replikasi indikator (termasuk layer fase/state dari stage 3 — kolom kategori seperti zone, cross event, teks fase gabungan).
- **Output yang dihasilkan**: penanda sinyal entry dan exit dalam bentuk yang konsisten (misalnya: true/false per baris data, menandakan sinyal aktif atau tidak di titik itu).

Selama tiap strategi mengikuti kontrak input-output yang sama, backtest engine tidak perlu tahu strategi tersebut pakai indikator apa atau logic seperti apa di dalamnya — dia cukup panggil fungsi sesuai kontrak, dapat sinyal, lalu proses eksekusi trade seperti biasa. Ini yang bikin sistem bisa menampung "bukan cuma satu metode trading saja" seperti yang direncanakan dari awal, tanpa backtest engine harus diubah tiap kali ada strategi baru.

### 3. Konvensi Parameter Risk yang Konsisten

Supaya `metrics.py` bisa menghitung `risk_amount` per trade secara konsisten lintas strategi (dibutuhkan untuk expectancy dalam R, EV per trade, dst — lihat `stage_04_metrics_guide.md`), semua strategi sebaiknya mendefinisikan risk dengan cara yang sama: persentase risk per trade dari modal, dan metode penentuan stop loss (jarak tetap, berbasis ATR, berbasis structure, dsb) — supaya `risk_amount` bisa dihitung otomatis dari config tanpa strategi harus menghitungnya sendiri-sendiri dengan cara berbeda-beda.

### 4. Versi Strategi

Mengikuti pola yang sudah dipakai di case study (`case_v1`, `case_v2`, dst), strategi yang direvisi (tuning parameter, perubahan rule karena case study baru) sebaiknya juga diberi penanda versi yang konsisten — supaya hasil backtest di `results/` jelas merujuk ke versi strategi yang mana, dan riwayat perubahan bisa ditelusuri balik ke journal.

---

## Alur Keterkaitan Lengkap (Biar Kelihatan Jahitannya)

```
[Alur Operasional]                          [Build Stage terkait]
Langkah 1 Hipotesis strategi        ─────►  (ditulis manual ke journal, tidak butuh skema khusus)
Langkah 2 Indikator siap            ─────►  Output-nya harus ikut format stage 3
                                             (kolom numerik + kolom fase/state)
Langkah 3 Kalibrasi setup           ─────►  Hasilnya: kesimpulan aturan final per
(studi kasus riil)                          versi, disimpan di case_studies/
Langkah 4 Rule strategi             ─────►  DI SINI stage 5 dipakai — kesimpulan
                                             aturan final dituliskan mengikuti skema
                                             config + rules + metadata di atas,
                                             yang lalu dipanggil backtest engine
                                             lewat interface kontrak yang sama
                                             untuk semua strategi
```

---

## Checklist Stage 5

- [ ] Skema file `config` / `rules` / `metadata` per strategi disepakati dan didokumentasikan
- [ ] Interface kontrak input-output ke backtest engine didefinisikan jelas, tidak berubah-ubah per strategi
- [ ] Konvensi parameter risk (risk per trade %, metode stop loss) seragam lintas strategi
- [ ] Skema versi strategi konsisten dengan konvensi versi case study yang sudah ada
- [ ] Metadata strategi wajib merujuk eksplisit ke versi case study yang jadi acuan pembuatan rule
