# Stage 2 — Panduan Logika Waktu: Candle Binance vs WIB

Dokumen ini bukan kode fetcher-nya (itu belum dibuat, sengaja diserahkan ke AI agent lain untuk implementasi). Ini adalah **spesifikasi logika waktu** yang wajib dipatuhi siapa pun yang membangun fetcher-nya nanti — supaya tidak ada bug offset jam yang sering luput karena kelihatannya sepele.

Status stage 2: **panduan logika siap, kode fetcher belum dibangun.**

---

## Prinsip Inti: Simpan UTC, Tampilkan WIB

Binance selalu mengembalikan timestamp dalam **UTC** (epoch milliseconds), tidak peduli dari mana request datang. Aturan yang wajib dipegang di seluruh project:

- **Data mentah di `data/raw/` selalu disimpan dalam UTC** — jangan pernah dikonversi ke WIB sebelum disimpan.
- **Konversi ke WIB hanya dilakukan saat menampilkan ke manusia** (journal, laporan, dashboard) — bukan untuk komputasi internal.

Alasan: kalau data mentah sudah dikonversi ke WIB duluan, gampang muncul bug tumpang tindih atau celah antar candle begitu logic makin kompleks (multi timeframe, resample, dsb). UTC itu satu sumber kebenaran waktu yang tidak ambigu.

---

## Struktur Candle dari Binance

Satu candle (kline) dari Binance API punya dua timestamp penting:

- **`openTime`** — waktu candle mulai terbentuk (UTC, epoch ms)
- **`closeTime`** — hampir mustahil ini persis di awal candle berikutnya. Secara teknis, `closeTime = openTime + durasi_interval − 1 milidetik`. Jadi candle 1 jam yang open jam `07:00:00.000` UTC, close-nya di `07:59:59.999` UTC — bukan `08:00:00.000`.

**Kenapa ini penting**: candle berikutnya open persis 1 milidetik setelah candle sebelumnya close. Tidak ada celah, tidak ada tumpang tindih — tapi kalau logic fetcher salah asumsi (misalnya menyamakan `closeTime` dengan `openTime` candle berikutnya lalu dibulatkan), bisa muncul bug off-by-one-millisecond yang sebenarnya sepele tapi bikin bingung saat debug.

**Candle yang belum closed**: kalau fetcher menarik data "sampai sekarang", candle paling akhir dalam hasil kadang masih **sedang terbentuk** (belum closed). Untuk backtest historis, candle yang belum closed **wajib dibuang** — jangan dianggap data final. Cara ceknya: bandingkan `closeTime` candle dengan waktu server saat ini; kalau `closeTime` candle masih di masa depan (relatif ke waktu fetch), candle itu belum closed.

---

## Kenapa Boundary Candle Tidak Selalu "Rapi" di Jam WIB

Ini bagian yang paling sering bikin salah paham. Semua candle Binance **selalu berpatokan ke tengah malam UTC (00:00 UTC)**, bukan ke tengah malam WIB. Karena WIB itu UTC+7, pergeseran 7 jam ini bikin sebagian besar timeframe **tidak** jatuh di jam-jam bulat WIB yang orang biasanya bayangkan.

**Aturan umum**: candle timeframe `T` jam akan terasa "rapi" di WIB (mulai dari 00:00 WIB) hanya kalau 7 habis dibagi `T`. Karena 7 itu bilangan prima, praktis cuma timeframe **1 jam** yang selalu terasa rapi. Timeframe **4 jam, 1 hari, 1 minggu** — yang justru paling relevan untuk swing/trend following (gaya yang kita bahas paling masuk akal secara EV) — semuanya punya boundary WIB yang "ganjil" dibanding ekspektasi umum.

### Tabel Boundary untuk Timeframe yang Paling Relevan

| Timeframe | Boundary buka di UTC | Boundary buka di WIB (UTC+7) |
|---|---|---|
| 1 jam | Setiap jam bulat UTC (00, 01, 02, ...) | Setiap jam bulat WIB juga (karena 1 habis membagi 7) |
| 4 jam | 00, 04, 08, 12, 16, 20 UTC | **07, 11, 15, 19, 23, 03** WIB — bukan 00/04/08/12/16/20 seperti dugaan umum |
| 1 hari | 00:00 UTC | **07:00 WIB** — candle harian "mulai" jam 7 pagi WIB, bukan tengah malam WIB |
| 1 minggu | Senin 00:00 UTC | **Senin 07:00 WIB** |

**Yang paling gampang salah kaprah**: candle harian (1D) itu bukan jam 00:00–23:59 WIB seperti asumsi umum orang Indonesia. Candle harian Binance sebenarnya jam **07:00 WIB hari ini sampai 06:59:59 WIB hari berikutnya**. Kalau strategi nanti pakai candle harian dan analisis "kejadian per hari" dilakukan dengan asumsi hari mulai jam 00:00 WIB, hasil backtest akan salah — offset 7 jam, bisa menggeser sinyal ke hari yang salah.

---

## Contoh Konkret Cara Baca

Misalnya sekarang jam **14:23 WIB**. Konversi dulu ke UTC: `14:23 − 7 jam = 07:23 UTC`.

**Candle 1 jam yang sedang berjalan**:
- Buka: `07:00 UTC` = `14:00 WIB`
- Close: `07:59:59.999 UTC` = `14:59:59.999 WIB`
- Candle berikutnya buka jam `15:00 WIB`

**Candle 4 jam yang sedang berjalan**:
- `07:23 UTC` masuk ke bracket `04:00–08:00 UTC`
- Buka: `04:00 UTC` = `11:00 WIB`
- Close: `07:59:59.999 UTC` = `14:59:59.999 WIB`
- Candle berikutnya buka jam `15:00 WIB` (UTC `08:00`)

**Candle harian yang sedang berjalan**:
- Buka: `00:00 UTC` (hari yang sama) = `07:00 WIB`
- Close: `23:59:59.999 UTC` (hari yang sama) = `06:59:59.999 WIB` **hari berikutnya**
- Candle berikutnya buka jam `07:00 WIB` besok

Logika umum yang bisa dipakai fetcher/engine untuk hitung ini secara otomatis:

```
utc_time = wib_time − 7 jam
candle_open_utc = floor(utc_time ke kelipatan interval, dihitung dari UTC 00:00)
candle_close_utc = candle_open_utc + interval − 1 milidetik
# untuk ditampilkan ke user:
candle_open_wib = candle_open_utc + 7 jam
candle_close_wib = candle_close_utc + 7 jam
```

---

## Rekomendasi Struktur Penyimpanan

Di `data/raw/`, simpan kolom timestamp dalam UTC sebagai sumber kebenaran (`open_time_utc`, `close_time_utc`). Kalau butuh tampilan WIB untuk journal atau laporan, tambahkan kolom turunan (`open_time_wib`) yang dihitung sekali saat load data — bukan menyimpan ulang raw data dalam WIB.

## Checklist untuk AI Agent yang Membangun Fetcher

- [ ] Semua timestamp yang disimpan ke `data/raw/` dalam UTC, bukan WIB
- [ ] Candle yang `closeTime`-nya masih di masa depan (belum closed) dibuang dari data historis
- [ ] Tidak ada asumsi bahwa candle harian mulai jam 00:00 WIB — gunakan tabel boundary di atas
- [ ] Konversi ke WIB hanya terjadi di layer tampilan/journal, bukan di logika inti fetcher atau backtest engine
- [ ] Kalau fetch multi-timeframe (1h dan 4h sekaligus, misalnya), pastikan boundary masing-masing dihitung independen sesuai tabel — jangan asumsikan keduanya align di jam WIB yang sama
