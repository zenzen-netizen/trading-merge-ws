# Stage 1 — Struktur Folder Project

## Kenapa Struktur Ini Dibuat di Awal

Struktur folder ini dibuat sebelum ada satu baris kode strategi pun, karena rencana ke depan bukan cuma satu strategi — bakal ada banyak strategi, banyak pair, banyak timeframe, dan banyak kali revisi. Kalau struktur baru dirapikan setelah semuanya campur aduk, kerja beresinnya jauh lebih berat daripada susun rapi dari awal.

Prinsip utamanya: **pisahkan data mentah, kode, hasil, dan catatan** — empat hal ini punya siklus hidup berbeda. Data mentah jarang berubah. Kode sering direvisi. Hasil selalu baru tiap run. Catatan terus bertambah. Kalau dicampur dalam satu folder, salah satu dari empat itu pasti berantakan duluan.

## Komponen Folder

### `data/raw/`
Tempat OHLCV (open, high, low, close, volume) mentah hasil fetch dari Binance, apa adanya, belum diubah sama sekali. Satu file per kombinasi pair-timeframe.

Kenapa dipisah: folder ini berfungsi sebagai cache dan sumber tunggal kebenaran. Begitu data sudah di-fetch sekali, tidak perlu fetch ulang setiap mau backtest — tinggal baca dari sini. Kalau ada bug di tahap pengolahan data nanti, folder ini jadi titik pembanding "data asli sebelum diapa-apain".

Saran penamaan file: `PAIR_TIMEFRAME_tanggalmulai_tanggalselesai.csv` — misalnya `BTCUSDT_1h_20230101_20241231.csv`.

### `data/processed/`
Hasil olahan dari data raw — misalnya resample timeframe (ubah 1 menit jadi 15 menit), atau data yang sudah ditambah kolom indikator kalau butuh precompute.

Kenapa dipisah dari raw: folder ini boleh dihapus dan digenerate ulang kapan saja tanpa risiko kehilangan data asli. Raw tidak boleh pernah ditimpa; processed boleh dianggap sementara.

### `indicators/pine_source/`
Simpan file `.pine` asli dari TradingView di sini, apa adanya, sebelum direplikasi ke Python.

Kenapa penting: ini jadi bahan pembanding kalau suatu saat hasil replikasi Python meleset dari angka TradingView. Tanpa source asli tersimpan, susah melacak balik logika mana yang salah pindah.

### `indicators/python/`
Hasil replikasi indikator dari Pine ke Python — fungsi-fungsi seperti hitung RSI custom, moving average versi tertentu, dan sejenisnya.

Kenapa terpisah dari folder strategi: satu indikator bisa dipakai lebih dari satu strategi. Kalau ditaruh nempel di folder strategi tertentu, begitu strategi lain butuh indikator yang sama, jadinya copy-paste kode — dan itu bikin repot kalau nanti ada bug atau perlu update).

### `strategies/[nama_strategi]/`
Satu folder per strategi. Isinya: rule entry/exit, dan file konfigurasi parameter (angka-angka seperti periode RSI, threshold, dan sejenisnya).

Kenapa satu folder per strategi: rencana ke depan bakal ada banyak strategi berjalan paralel. Kalau semua rule ditumpuk dalam satu file besar, begitu strategi bertambah jadi 10-20, akan sangat sulit dilacak mana rule punya strategi mana.

### `backtest_engine/`
Logic inti yang sifatnya generic — dipakai oleh semua strategi tanpa terkecuali. Isinya: mesin eksekusi trade (baca data, cek kondisi, catat transaksi) dan metrics calculator (`metrics.py`, sudah selesai di stage 4).

Kenapa dipisah tegas dari strategi: kalau logic spesifik satu strategi menyelinap masuk ke sini, engine ini jadi tidak lagi generic — dan setiap strategi baru berisiko butuh modifikasi ulang mesin intinya. Itu jadi sumber bug berantai.

### `results/raw/`
Trade list mentah dan equity curve lengkap per run backtest — detail tiap transaksi, biasanya file panjang.

Kenapa perlu, meskipun sudah ada summary: kadang metric ringkas belum cukup untuk memahami kenapa strategi berperilaku tertentu. Folder ini memungkinkan drill-down ke level transaksi individual saat perlu investigasi lebih dalam.

### `results/summary/`
Output ringkas dari `metrics.py` — satu file per run, isi semua angka metric yang sudah dibahas (net profit, win rate, EV, dan seterusnya).

Kenapa dipisah dari raw: supaya bisa membandingkan banyak run sekaligus dengan cepat, tanpa harus membuka file trade list yang besar satu per satu.

### `journal/`
Catatan naratif — hipotesis di balik strategi, riwayat perubahan versi, dan guide tiap stage seperti file ini sendiri.

Fungsinya: mendokumentasikan "kenapa" di balik tiap keputusan, bukan cuma "apa" hasilnya. Angka metric saja tidak menjelaskan alasan sebuah strategi dibuat atau kenapa parameter tertentu dipilih — itu tugas journal.

### `sandbox/`
Tempat eksperimen bebas — coba kombinasi indikator/parameter tanpa komit ke proses formal.
Pakai data dan engine yang sama dengan sistem utama, tapi hasilnya tidak masuk `strategies/` atau `results/` resmi.

Isinya:
- `README.md` — aturan main sandbox
- `log.md` — ringkasan semua eksperimen (satu baris per eksperimen)
- `experiments/exp_NNN_nama/` — satu folder per eksperimen

Kalau hasil eksperimen menjanjikan → "naik kelas" ke `strategies/`, mulai siklus resmi 8 langkah.
Kalau tidak → dicatat ringkas di `log.md`, folder boleh dihapus.

### `notebooks/`
Tempat eksplorasi cepat, visualisasi ad hoc, dan uji coba sebelum sebuah logic matang dan dipindah jadi kode formal di `backtest_engine/` atau `strategies/`.

Kenapa dipisah: mencegah kode eksperimen tercampur dengan kode yang sudah dianggap stabil dan dipakai produksi.

## Insight Penting

Naming convention run wajib konsisten sejak awal — begitu jumlah run bertambah puluhan, format nama file yang tidak konsisten membuat folder `results/` sulit ditelusuri. Pola yang disarankan: `strategyname_PAIR_TF_daterange_v1_YYYYMMDD-HHMM`.
