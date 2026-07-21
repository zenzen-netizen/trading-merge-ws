# Meteora Setup Deployment Notes

Tujuan note ini:
- merangkum semua sample + metric backtest yang sudah kita kumpulkan,
- lalu merumuskan versi setup yang PALING MASUK AKAL kalau nanti dipakai
  untuk deploy pool di Meteora,
- baik untuk bot Meridian maupun untuk eksekusi manual.

Ini bukan file backtest baru.
Ini adalah note / thesis / deployment view yang ditarik dari hasil backtest
chart-based yang sudah ada.

## 1. Sumber data yang dipakai

Backtest source utama:
- `backtests/METEORA/POOL_DISCOVERY/top20_sol_30m_fee_tvl_age15h.json`
- `backtests/METEORA/POOL_DISCOVERY/rsi_fractal_backtest_mhermes_be/summary.csv`
- `backtests/METEORA/POOL_DISCOVERY/rsi_fractal_backtest_mhermes_be/report.md`
- `backtests/METEORA/POOL_DISCOVERY/rsi_fractal_backtest_mhermes_be/full_report.md`

Setup chart yang diuji:
- trend bullish: Supertrend up + close di atas EMA50 atau EMA200
- trigger: RSI(2) > 90
- confirm: upper fractal(3) confirm
- entry: next candle open setelah fractal confirm
- TP baseline: kembali ke fractal high
- SL:
  - O1 = -50%
  - O2 = 2x jarak close confirm ke garis Supertrend
- exit variants:
  - `BE1`
  - `BE50`
  - `BE75`
  - `TP_FRACTAL`

## 2. Caveat besar — ini BUKAN simulasi LP PnL penuh

Yang sudah kita backtest sekarang adalah:
- timing entry,
- struktur SL,
- recovery behavior,
- reclaim ke fractal high,
- dan karakter trade setelah trigger.

Yang BELUM benar-benar disimulasikan penuh di note ini:
- fee accrual DLMM real,
- IL / inventory drift real,
- efek distribusi bin terhadap PnL live,
- perbedaan real antara `spot / bid_ask / curve` di hasil uang live.

Jadi note ini harus dibaca seperti ini:
- chart backtest = alat untuk pilih TIMING + karakter setup,
- lalu dipetakan ke gaya deploy LP yang paling nyambung,
- BUKAN dianggap sudah membuktikan profit final LP strategy.

## 3. Ringkasan temuan paling penting dari data sekarang

### 3.1 Exit behavior

Global recovery stats dari sample 20 pool:
- `BE1`: 305 / 472 = `64.6%`
- `BE50`: 37 / 472 = `7.8%`
- `BE75`: 17 / 472 = `3.6%`

Deep recovery stats:
- `Deep50`: 37 / 227 = `16.3%`
- `Deep75`: 17 / 209 = `8.1%`

Makna praktis:
- mayoritas recovery yang benar-benar sering terjadi itu recovery CEPAT / dangkal,
  bukan recovery yang nunggu dijilat sangat dalam dulu.
- edge terbesar setup ini bukan “tahan drawdown dalam lalu balik”,
  tapi “kena noise / pullback ringan lalu pulih cepat”.

### 3.2 Winner mode frequency

Kalau dilihat dari `best mode per family (pool + tf + SL)`:
- `BE1` menang `60 / 102` family best
- `BE50` menang `21 / 102`
- `BE75` menang `11 / 102`
- `TP_FRACTAL` menang `10 / 102`

Makna:
- secara breadth / coverage, `BE1` adalah mode paling robust.
- `BE50` dan `BE75` bukan mode default yang bagus untuk semua kasus,
  tapi bisa berguna untuk subset tertentu.
- `TP_FRACTAL` murni menang di sedikit family, tapi saat menang kadang menang bagus.

### 3.3 Timeframe character

Berdasarkan `best row per family`:
- `1m`: 34 family, 16 positif, median best `0.000`
- `5m`: 34 family, 15 positif, median best `-0.065`
- `15m`: 34 family, 11 positif, median best `0.000`

Makna:
- `1m` punya tail winner besar, tapi karakter paling liar / fragile.
- `5m` paling balance: breadth positif paling banyak dan median best juga paling sehat.
- `15m` lebih bersih untuk confirmation, tapi sebagai engine utama belum sekuat 5m.

Kesimpulan TF:
- `5m` = kandidat utama untuk deployment mindset
- `15m` = candidate confirmation layer
- `1m` = opportunistic / manual / high noise only

### 3.4 SL behavior

Stat family-best per SL:
- `O1_SL50`: 24 / 51 family best positif
- `O2_ST2X`: 18 / 51 family best positif

Tapi head-to-head winner count:
- overall: `O1` menang 22, `O2` menang 21, tie 8
- khusus `5m`: `O2` menang 10, `O1` menang 6, tie 1

Makna:
- `O1` lebih stabil secara breadth dan lebih mudah jadi mode konservatif.
- `O2` lebih selective, tapi saat cocok bisa memberi payoff lebih besar.
- untuk `5m`, justru `O2` lebih sering unggul head-to-head.

## 4. Pembacaan karakter setup ini

Dari semua metric yang kita kumpulkan, setup ini terlihat seperti:

1. setup bullish-reclaim / recovery,
   bukan setup “buy deep collapse lalu nunggu miracle reversal”.

2. edge utamanya muncul saat:
   - trend besar masih bullish,
   - ada pullback / cooldown kecil setelah kondisi panas,
   - lalu harga punya ruang reclaim ke area fractal high.

3. setup ini cenderung lebih cocok untuk:
   - recovery cepat,
   - reclaim terukur,
   - invalidasi cepat kalau reclaim gagal.

4. karena `BE1` dominan,
   maka pasar yang cocok adalah pasar yang:
   - masih punya bid kuat,
   - sering fake-dip,
   - tapi cepat dipantulkan.

Jadi secara mental model:
- ini lebih dekat ke `timing a bullish continuation reclaim`
- daripada `timing a deep bargain accumulation`

## 5. Kontemplasi strategy LP: spot vs bid_ask vs curve

## 5.1 Bid-ask

Kelebihan:
- cocok kalau tujuan utama adalah buy-lower-on-dip,
- bagus saat kita ingin single-sided SOL di bawah,
- bisa masuk akal kalau thesis utama = chop / mean reversion bawah + fee capture.

Kelemahan terhadap setup ini:
- setup chart kita target utamanya reclaim ke atas / kembali ke fractal high,
- sedangkan bid_ask cenderung membiarkan upside di atas range kurang tercapture,
- terutama kalau range sangat condong ke bawah dan `bins_above` sempit / nol.

Interpretasi:
- bid_ask masuk akal kalau kita pakai setup ini hanya sebagai “timing beli ketika dip”
  tapi BUKAN ketika objective utamanya benar-benar menangkap reclaim ke atas.

## 5.2 Spot

Catatan penting dari referensi SDK:
- Spot di Meteora BUKAN berarti semua SOL numpuk di satu bin.
- Spot justru distribusinya even across bins pada range yang dipilih.

Kenapa spot terasa cocok untuk setup ini:
- setup chart kita punya bias reclaim upward,
- spot lebih netral dan lebih gampang dipakai sebagai ekspresi “ikut recovery”
  daripada bid_ask yang terlalu berat ke bawah,
- untuk bot maupun manual, spot juga lebih mudah dijelaskan dan dioperasikan.

Interpretasi:
- kalau setup chart ini dipakai sebagai PRIMARY timing layer,
  `spot` terasa paling natural sebagai baseline deployment strategy.

## 5.3 Curve

Curve secara konsep bisa jadi jembatan antara:
- tidak seberat bid_ask,
- tapi tidak senetral spot juga,
- cocok kalau kita ingin distribution yang lebih shaped.

Masalahnya di konteks data kita sekarang:
- kita belum punya validasi live / paper khusus curve untuk setup ini,
- chart backtest kita belum membuktikan curve lebih unggul dari spot,
- jadi curve masih masuk kategori secondary exploration, bukan default thesis.

## 5.4 Kesimpulan strategy LP

Kalau mindset-nya:
“setup chart ini akan dipakai sebagai real deploy filter untuk Meridian + manual”

maka urutan yang paling masuk akal menurut data saat ini adalah:

1. `spot` = pilihan utama
2. `curve` = pilihan eksperimen lanjutan
3. `bid_ask` = conditional use only

Dengan kata lain:
- kalau objective = tangkap reclaim / recovery move,
  jangan jadikan `bid_ask` sebagai default utama.
- `bid_ask` lebih cocok dipakai kalau kita sengaja ingin memonetisasi dip / chop / fee,
  bukan saat thesis utamanya reclaim ke atas.

## 6. Rumusan setup yang paling masuk akal

## 6.1 Versi “default paling waras” untuk live thinking

Kalau aku harus merumuskan satu versi paling masuk akal dari data sekarang:

- TF utama: `5m`
- TF konfirmasi: `15m`
- SL utama: `O2_ST2X`
- exit governance utama: `BE1`
- LP strategy thesis utama: `spot`

Kenapa kombinasi ini:
- `5m` paling balance dari sisi breadth + median best
- `15m` bisa dipakai buat buang sinyal yang terlalu noise
- `O2` lebih nyambung dengan struktur trend / supertrend, terutama di 5m
- `BE1` adalah exit mode yang paling robust across family
- `spot` paling cocok dengan thesis reclaim ke atas

## 6.2 Versi konservatif untuk bot autonomous

Kalau prioritasnya safety / robustness buat Meridian:
- TF utama: `5m`
- filter tambahan: pastikan trend lebih besar tetap sehat
- SL: mulai dari `O1_SL50` kalau ingin breadth lebih aman
- exit: `BE1`
- strategy: `spot`

Mindset:
- bot jangan dipaksa cari homerun,
- bot cukup fokus ke reclaim cepat + cut ambiguity cepat,
- biarkan upside besar jadi bonus, bukan requirement.

## 6.3 Versi agresif / manual discretionary

Kalau untuk manual execution:
- TF utama tetap `5m`
- `15m` dipakai sebagai context filter
- SL boleh naik ke `O2_ST2X`
- mode exit bisa dibedakan:
  - `BE1` untuk pool mediocre / noisy
  - `BE50` untuk pool yang kualitasnya sangat kuat dan masih mau diberi ruang
- strategy bisa mulai dari `spot`, lalu test `curve`

Mindset:
- manual trader bisa lebih pilih-pilih pool,
- jadi boleh menahan sedikit lebih lama pada nama yang benar-benar berkualitas,
- tapi jangan menggeneralisasi itu ke semua pool seperti bot.

## 7. Rumusan yang kusarankan untuk Meridian bot

Kalau setup ini mau dijalankan di bot Meridian, aku sarankan setup ini diposisikan sebagai:

- `timing overlay`, bukan satu-satunya selector pool

Artinya:
1. screening kualitas pool tetap penting:
   - liquidity quality
   - holders
   - fee/TVL
   - organic behavior
   - launchpad / token hygiene

2. setup RSI + fractal ini dipakai untuk:
   - mengatur kapan masuk,
   - bukan memaksa semua pool bagus otomatis jadi deploy.

3. untuk implementasi mindset di bot:
   - lebih baik `strategyLock = spot`
     ATAU
   - `strategyLock = default`, tapi promptNotes / lesson mengarahkan bahwa
     setup ini prefer `spot/curve`, dan `bid_ask` hanya dipakai bila thesis pool-nya
     lebih ke dip-accumulation + fee capture.

## 8. Rumusan yang kusarankan untuk manual execution

Untuk manual, aku akan pakai framework ini:

### A. Pool selection
- pilih pool yang memang lolos quality filter dulu
- hindari pool yang terlalu chaos / terlalu tipis hanya karena sinyal chart muncul

### B. Timing
- fokus `5m`
- cek `15m` supaya tidak melawan struktur lebih besar

### C. Deployment style
- default mulai `spot`
- kalau mau eksperimen kedua: `curve`
- jangan jadikan `bid_ask` sebagai first reflex untuk setup ini

### D. Exit mindset
- baseline pakai `BE1`
- pindah ke `BE50` hanya kalau conviction pool sangat tinggi
- `BE75` jangan dijadikan default; terlalu niche dari data sekarang

## 9. Final thesis — jawaban paling singkat

Kalau ditanya:
“dari semua sample dan metric yang kita punya, combo metric + setup rule + TF + style deploy apa yang paling masuk akal buat dipakai di Meteora, baik di Meridian maupun manual?”

jawabanku saat ini:

### Thesis utama
- pakai setup ini sebagai `bullish reclaim timing filter`
- bukan sebagai deep-value accumulation filter

### Combo utama
- TF utama: `5m`
- TF pendamping: `15m`
- SL utama: `O2_ST2X`
- fail-safe exit utama: `BE1`

### Style deploy utama
- `spot` paling masuk akal sebagai default
- `curve` boleh jadi eksperimen kedua
- `bid_ask` jangan jadi default utama untuk setup ini

### Deployment split
- bot Meridian: lebih konservatif, gunakan setup ini sebagai timing overlay
- manual: boleh lebih discretionary, dan boleh kasih ruang `BE50` pada pool terbaik

## 10. What I would do next

Urutan eksperimen lanjutan yang paling bernilai:

1. paper / sim khusus `spot` vs `bid_ask` vs `curve`
   pada subset pool yang sama
2. khusus `5m`, bandingkan live behavior:
   - `O1 + BE1 + spot`
   - `O2 + BE1 + spot`
3. cek apakah `15m confirm` benar-benar meningkatkan kualitas deploy
4. buat preset Meridian khusus setup ini:
   - conservative bot version
   - manual discretionary version

## 11. Setting umum yang lebih spesifik

Bagian ini menutup kekurangan note versi awal: bukan cuma `spot vs bid_ask`,
tapi setting umum apa yang paling masuk akal dipasang.

### 11.1 Baseline utama yang kusarankan

Kalau thesis ini mau dipakai sekarang sebagai baseline paling waras:

- `solMode = true`
- `strategy = spot`
- `strategyLock = spot`
- `dualSideEnabled = false`
- `minBinsBelow = 35`
- `maxBinsBelow = 52`
- `defaultBinsBelow = 52`
- TF engine = `5m`
- TF confirm = `15m`
- chart thesis = `O2_ST2X + BE1`

Makna setting ini:
- `solMode=true` → fokus ke pool SOL-pair, selaras dengan sample yang kita uji
- `strategy=spot` + `strategyLock=spot` → jangan biarkan deploy expression drift
  ke thesis lain dulu
- `dualSideEnabled=false` → baseline awal tetap single-side SOL, karena data kita
  baru kuat di timing reclaim, belum kuat di distribusi LP dua sisi
- `35–52 bins below` → tetap di band kontrol Meridian yang sekarang, jangan terlalu
  lebar dulu karena kita belum membuktikan widening range otomatis memperbaiki edge

### 11.2 Kenapa bukan dual-side dulu sebagai default

Walau secara narasi reclaim ke atas itu terlihat “menggoda” untuk dual-side,
aku belum mau menjadikannya default karena:

1. backtest kita masih chart-timing, belum full LP PnL
2. dual-side di code path Meridian masih sifatnya eksperimen / config-gated OFF
3. begitu kita bikin dual-side default, kita sekaligus mengubah:
   - ekspresi inventory
   - inventory drift
   - fee vs upside capture trade-off
   - behavior close / management

Jadi default yang paling disiplin tetap:
- `single-side SOL`
- `spot locked`
- `BE1`

### 11.3 Kalau MAU eksperimen dual-side, setting yang paling masuk akal apa?

Kalau mau eksperimen dual-side, aku sarankan JANGAN langsung besar.
Mulai dari sleeve kecil.

Preset eksperimen yang paling masuk akal:
- `solMode = true`
- `strategy = spot`
- `strategyLock = spot`
- `dualSideEnabled = true`
- `dualSideTokenPct = 10`
- `dualSideUpsidePct = 10 sampai 15`
- `dualSideStrategy = spot`
- `minBinsBelow = 35`
- `maxBinsBelow = 52`
- `defaultBinsBelow = 52`

Kenapa begitu:
- `dualSideTokenPct=10` → cukup kecil untuk jadi upside sleeve, belum terlalu agresif
- `dualSideUpsidePct=10–15` → cukup dekat untuk menangkap reclaim, belum terlalu jauh
- `dualSideStrategy=spot` → tetap netral / selaras dengan thesis reclaim utama,
  tidak langsung condong ke distribusi yang terlalu “dip-play”

Kalau suatu hari mau test versi lebih agresif, baru naikkan bertahap:
- token sleeve `10 -> 15%`
- upside band `10 -> 15 -> 20%`

Tapi bukan default pertama.

### 11.4 Kapan bid_ask baru layak jadi setting umum?

`bid_ask` baru layak dijadikan setting umum kalau thesis operasional berubah jadi:
- kita sengaja mau membeli penurunan,
- kita rela upside capture kurang penuh,
- fee-chop lebih penting daripada reclaim-upside.

Jadi kalau setup yang sedang dipakai tetap setup RSI/fractal reclaim ini,
aku TIDAK sarankan setting umum utamanya menjadi:
- `strategy=bid_ask`
- apalagi `strategyLock=bid_ask`

### 11.5 Catatan implementasi Meridian yang penting

- di codebase utama / produksi, baseline paling aman dibaca sebagai
  `spot locked + single-side SOL`
- dual-side lebih cocok dianggap sebagai preset eksperimen profile terpisah,
  bukan preset produksi pertama
- kalau dual-side mau dinyalakan, lebih baik diuji di profile / instance terpisah
  supaya hasil learning / lessons tidak tercampur langsung dengan baseline utama

## 12. Bottom line

Kalau harus pilih satu arah paling waras sekarang:

- `solMode = true`
- `strategy = spot`
- `strategyLock = spot`
- `dualSideEnabled = false`
- `minBinsBelow = 35`
- `maxBinsBelow = 52`
- `defaultBinsBelow = 52`
- `5m + 15m confirm`
- `O2_ST2X`
- `BE1`
- gunakan sebagai timing overlay di atas screening pool yang tetap ketat

Dan kalau harus pilih satu warning paling penting:

- jangan terlalu cepat menyimpulkan bahwa karena chart setup ini bagus,
  maka `bid_ask` atau `dual-side` otomatis jadi style deploy terbaik.
- dari struktur edge yang kita lihat, setup ini justru lebih terasa cocok untuk
  menangkap reclaim / recovery move, jadi `spot` single-side lebih natural
  sebagai baseline pertama.
