# Stage 4b — Data Pendukung: Fee, Funding Rate, Liquidation Price, dan MMR

Dokumen ini pelengkap `stage_04_metrics_guide.md`. Fokusnya bukan cara baca metric, tapi **dari mana angka input metric itu didapat**, dan bagaimana menjaganya tetap akurat serta konsisten — karena beberapa angka ini (fee, funding, MMR) bisa berubah dari waktu ke waktu di sisi Binance, bukan angka tetap yang aman dihardcode selamanya.

Relevan terutama kalau strategi yang dites nanti melibatkan **leverage atau perpetual futures**. Kalau backtest murni spot tanpa leverage, bagian liquidation price dan MMR bisa dilewati — fee dan funding tetap relevan kalau posisi diinapkan di perpetual.

---

## 1. Trading Fee (Maker/Taker)

**Definisi**: biaya per transaksi. Maker (order nempel di orderbook, nunggu match) biasanya lebih murah dari taker (order langsung match seketika).

**Angka acuan per awal 2026** (tier reguler, belum VIP):
- Futures USDⓈ-M: maker 0.02%, taker 0.05%
- Spot: maker dan taker sama-sama 0.1%
- Diskon bayar pakai BNB: potongan 10% di futures, 25% di spot
- VIP tier menurunkan lebih jauh — VIP 9 bisa sampai 0% maker dan 0.017% taker di futures

**Kenapa jangan dihardcode permanen**: angka ini tergantung tier VIP akun (berdasarkan volume trading 30 hari) dan metode bayar fee. Dua akun beda tier bisa punya fee effective yang jauh berbeda untuk strategi identik.

**Cara dapetin data akurat dan konsisten**:
- Kalau backtest untuk strategi pribadi: cek tier fee aktual di akun sendiri (halaman Fee di Binance), pakai angka itu, bukan angka default dari artikel.
- Kalau belum ada akun/API key, angka tier reguler di atas cukup aman sebagai default awal — tapi **catat eksplisit di journal bahwa itu asumsi tier reguler**, bukan tier akun sungguhan.
- Fee tier bisa naik/turun kalau volume trading berubah — kalau backtest dipakai jangka panjang, cek ulang tier secara berkala, jangan asumsikan tier hari ini berlaku selamanya.

---

## 2. Funding Rate (Khusus Perpetual Futures)

**Definisi**: biaya periodik yang dipertukarkan antara posisi long dan short di perpetual futures, fungsinya menjaga harga perpetual tetap dekat dengan harga spot.

**Catatan penting yang sering salah diasumsikan**: dulu selalu setiap 8 jam, tapi sejak sekitar 2025 Binance bisa menerapkan interval berbeda per simbol — bisa 8 jam, 4 jam, bahkan 1 jam tergantung simbol dan kondisi (misalnya saat funding rate menyentuh batas cap/floor). **Jangan asumsikan semua simbol funding tiap 8 jam** — itu bisa bikin perhitungan annual funding drag meleset.

**Sumber data resmi**:
- `GET /fapi/v1/fundingRate` — histori funding rate per simbol, hasilnya berisi `fundingRate`, `fundingTime`, `markPrice` per periode. Endpoint publik, tidak butuh API key.
- `GET /fapi/v1/fundingInfo` — cek simbol mana yang punya interval funding custom (bukan default 8 jam).

**Dampak ke `metrics.py` saat ini**: fungsi `annual_fee_funding_drag` menerima `funding_pct_per_8h` sebagai **angka flat/konstan**. Ini simplifikasi yang oke untuk estimasi kasar di awal, tapi bukan representasi realita — funding rate aktual naik turun tiap periode, kadang positif kadang negatif. Untuk strategi yang akan benar-benar menahan posisi leverage dalam waktu lama, versi lebih akurat harus mengambil funding rate historis asli di tiap checkpoint yang dilewati selama posisi terbuka, dijumlahkan satu per satu — bukan dikalikan rata-rata konstan.

**Rekomendasi ke depan (masuk ke stage 2 data layer)**: tambahkan fetcher khusus funding rate history, simpan terpisah di `data/raw/funding/`, supaya nanti backtest engine bisa mencocokkan funding rate aktual di tiap timestamp selama sebuah trade berjalan.

---

## 3. Liquidation Price

**Kapan relevan**: hanya untuk simulasi leverage/perpetual. Spot tanpa leverage tidak punya liquidation price.

**Formula resmi Binance (cross margin, one-way mode)** cukup kompleks — melibatkan wallet balance, maintenance margin dan unrealized PnL dari posisi lain, MMR bertingkat, dan seterusnya. Rumus ini relevan kalau mensimulasikan akun dengan banyak posisi berbagi margin sekaligus.

**Formula isolated margin** (lebih relevan untuk backtest satu strategi berdiri sendiri), diturunkan dari rumus resmi dengan margin posisi lain diabaikan:

```
Long  : LiqPrice = (EntryPrice × PositionSize − Margin + MaintenanceAmount) / (PositionSize × (1 − MMR))
Short : LiqPrice = (EntryPrice × PositionSize + Margin − MaintenanceAmount) / (PositionSize × (1 + MMR))
```

**Versi simplifikasi** yang umum dipakai kalkulator pihak ketiga (asumsi bracket notional terendah, MaintenanceAmount diabaikan — cukup akurat untuk posisi kecil dengan leverage rendah-menengah):

```
Long  : LiqPrice ≈ EntryPrice × (1 − 1/Leverage + MMR)
Short : LiqPrice ≈ EntryPrice × (1 + 1/Leverage − MMR)
```

**Catatan akurasi**: versi simplifikasi cukup dekat selama notional posisi masih di bracket MMR paling rendah (biasanya posisi kecil-menengah, umum untuk retail). Begitu notional posisi cukup besar untuk masuk bracket MMR yang lebih tinggi, `MaintenanceAmount` (disebut `cum` di data Binance) tidak lagi bisa diabaikan, dan bracket yang sesuai harus dicari lebih dulu dari data notional aktual.

---

## 4. Maintenance Margin Rate (MMR) dan Leverage Bracket

**Definisi**: persentase minimum margin yang harus dipertahankan supaya posisi tidak dipaksa likuidasi. Nilainya bertingkat (bracket) berdasarkan notional posisi — makin besar posisi, makin tinggi MMR dan makin rendah leverage maksimum yang diizinkan Binance.

**Sumber data resmi dan akurat**: `GET /fapi/v1/leverageBracket` (endpoint signed, butuh API key). Hasilnya per simbol: daftar bracket berisi `notionalFloor`, `notionalCap`, `initialLeverage`, `maintMarginRatio`, dan `cum` (maintenance amount).

**Kenapa harus fetch dinamis, bukan disalin manual dari tabel di web**: Binance bisa menyesuaikan leverage maksimum dan MMR per bracket sewaktu-waktu, terutama saat volatilitas pasar ekstrem. Tabel yang di-screenshot atau disalin manual hari ini berpotensi sudah tidak akurat beberapa bulan kemudian. Simpan hasil fetch dengan timestamp, dan refresh berkala — misalnya setiap kali mulai sesi backtest baru yang melibatkan leverage.

---

## 5. Mode Akun yang Mempengaruhi Semua Rumus di Atas

- **One-way mode vs Hedge mode**: one-way hanya boleh satu arah posisi per simbol dalam satu waktu. Hedge mode membolehkan long dan short bersamaan di simbol yang sama. Ini mempengaruhi rumus liquidation (pakai variabel posisi gabungan vs posisi long/short terpisah).
- **Isolated vs Cross margin**: isolated mengunci margin per posisi — rumus liquidation lebih sederhana, risiko kerugian terbatas ke margin posisi itu saja. Cross margin memakai saldo wallet gabungan sebagai margin bersama semua posisi — rumus jauh lebih kompleks karena melibatkan maintenance margin dan unrealized PnL posisi-posisi lain sekaligus.

**Rekomendasi untuk backtest**: pakai asumsi **isolated margin + one-way mode** sebagai default. Ini yang paling umum dipakai trader retail, dan rumusnya paling straightforward untuk disimulasikan per strategi secara independen tanpa perlu memodelkan interaksi antar posisi. Simulasi cross margin dengan banyak posisi sekaligus adalah kompleksitas tambahan yang lebih tepat jadi modul terpisah di masa depan, bukan dicampur ke backtest engine strategi tunggal yang sedang dibangun sekarang.

---

## Ringkasan Sumber Data

| Kebutuhan | Sumber resmi | Butuh API key | Catatan |
|---|---|---|---|
| Fee maker/taker | Halaman Fee di akun Binance | Ya (untuk fee aktual akun) | Tier reguler bisa dipakai sebagai default awal, dicatat sebagai asumsi |
| Funding rate historis | `GET /fapi/v1/fundingRate` | Tidak (publik) | Interval bisa dinamis, jangan asumsikan selalu 8 jam |
| Info interval funding custom | `GET /fapi/v1/fundingInfo` | Tidak (publik) | Cek simbol yang berbeda dari default |
| MMR dan leverage bracket | `GET /fapi/v1/leverageBracket` | Ya | Jangan hardcode, fetch dan cache dengan timestamp |
| OHLCV harga | `GET /fapi/v1/klines` atau data.binance.vision | Tidak (publik) | Sudah dibahas di rencana stage 2 |

---

## Dampak Konkret ke Pekerjaan Selanjutnya

- **`metrics.py`**: fungsi `annual_fee_funding_drag` saat ini pakai `funding_pct_per_8h` flat — valid untuk estimasi kasar tahap awal. Untuk akurasi tinggi nanti, sebaiknya diganti menghitung funding cost langsung dari data historis `fundingRate` per checkpoint yang dilewati selama trade berjalan, bukan dikalikan rata-rata konstan. Ini catatan untuk revisi lanjutan, belum perlu dikerjakan sekarang.
- **Backtest engine (bagian eksekusi trade, belum dibangun)**: kalau nanti mau simulasikan leverage secara realistis, perlu fungsi cek likuidasi yang dipanggil tiap candle — kalau harga high/low candle menyentuh liquidation price, trade dianggap closed paksa di titik itu, bukan menunggu stop loss manual seperti pada spot.
- **Stage 2 (data layer)**: perlu ditambah fetcher funding rate history sebagai pelengkap fetcher OHLCV, disimpan terpisah di `data/raw/funding/`.
