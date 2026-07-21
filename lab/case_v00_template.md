# Case Study Kalibrasi Setup — Template

Copy file ini jadi `case_v1.md`, `case_v2.md`, dst di dalam `strategies/[nama_strategi]/case_studies/`. Tiap kasus baru dianggap **versi baru dari pemahaman setup**, bukan sekadar contoh lepas — karena tiap kasus berpotensi mengoreksi atau memperjelas aturan yang sudah disepakati di versi sebelumnya.

**Penamaan file**: `case_v{N}.md`, angka naik terus tiap ada kasus baru (v1, v2, v3, ...). Jangan pakai nomor urut acak atau tanggal — versi ini juga jadi penanda urutan belajar, semakin tinggi angkanya semakin baru dan semakin mendekati pemahaman final.

**Wajib update** `case_studies/00_case_tree.md` setiap selesai bikin case baru — itu tracker yang rangkum semua versi sekaligus, biar enggak perlu buka satu-satu file buat tau perkembangan terakhir.

---

## Versi
`v{N}` — isi angka versi sesuai nama file

## Pair & Timeframe
Contoh: BTCUSDT, 1h

## Window Waktu
Dari `[tanggal mulai]` sampai `[tanggal selesai]`

## Kondisi Indikator yang Teridentifikasi
Isi state/nilai tiap indikator yang relevan di window ini. Contoh:
- RSI(14): turun ke 28 pada candle jam 14:00, mulai naik lagi jam 16:00
- MA(50) vs MA(200): golden cross terjadi jam 15:00
- Volume: spike 2x rata-rata pada candle entry kandidat

## Event yang Dianggap Sinyal Valid
Jelaskan persis kombinasi kondisi mana yang dianggap entry/exit valid, dan di candle mana persisnya sinyal itu dianggap "terjadi".

## Near-Miss — Terlihat Mirip Tapi BUKAN Sinyal Valid
Ini bagian penting untuk membatasi ambiguitas. Kalau ada kejadian di window yang sekilas mirip tapi tidak dianggap sinyal (misalnya RSI sempat oversold tapi tanpa konfirmasi MA cross), catat di sini beserta alasan kenapa itu bukan sinyal.

## Koreksi dari User
Kalau interpretasi awal AI terhadap window ini meleset, catat di sini apa yang salah dan bagaimana koreksinya. Kalau interpretasi awal sudah benar, tulis "Tidak ada koreksi — interpretasi awal sudah sesuai".

## Apa yang Berubah dari Versi Sebelumnya
Kalau ini bukan `v1`, jelaskan singkat apa yang beda dari kesimpulan versi sebelumnya — ditambah pengecualian baru, dipersempit, atau malah dikoreksi total. Kalau `v1`, tulis "Versi awal, belum ada pembanding".

## Kesimpulan Aturan Final dari Kasus Ini
Rangkum jadi kalimat aturan yang jelas dan tidak ambigu, siap diterjemahkan ke kode di step "Rule strategi". Contoh: "Entry long ketika RSI(14) menyentuh di bawah 30 DAN candle berikutnya close di atas MA(50), dengan volume candle entry minimal 1.5x rata-rata 20 candle terakhir."
