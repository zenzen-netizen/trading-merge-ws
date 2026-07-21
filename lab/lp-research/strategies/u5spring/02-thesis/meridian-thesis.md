# Meridian Preset Thesis — Meteora RSI/Fractal Deployment Blueprint

Tujuan file ini:
- menerjemahkan hasil backtest chart-based yang sudah kita kumpulkan
  menjadi thesis operasional untuk Meridian,
- menyesuaikan rekomendasi dengan workflow asli Meridian
  (`screening -> candidate filtering -> deploy decision -> management -> learning`),
- dan memberi 2 jalur pakai:
  1. autonomous bot preset
  2. manual / semi-manual preset

File ini sengaja lebih operasional daripada
`METEORA_SETUP_DEPLOYMENT_NOTES.md`.

Bacanya seperti ini:
- `METEORA_SETUP_DEPLOYMENT_NOTES.md` = thesis konseptual
- `MERIDIAN_PRESET_THESIS.md` = cara menaruh thesis itu ke workflow Meridian

## 1. Source of truth yang dipakai

Data dan report yang jadi dasar:
- `POOL_DISCOVERY/top20_sol_30m_fee_tvl_age15h.json`
- `POOL_DISCOVERY/rsi_fractal_backtest_mhermes_be/summary.csv`
- `POOL_DISCOVERY/rsi_fractal_backtest_mhermes_be/full_report.md`
- `METEORA_SETUP_DEPLOYMENT_NOTES.md`

Ringkasan angka kunci dari data:
- sample pool: `20`
- strategy rows: `408`
- family best mode overall:
  - `BE1 = 60`
  - `BE50 = 21`
  - `BE75 = 11`
  - `TP_FRACTAL = 10`
- global recovery:
  - `BE1 = 424/663 = 64.0%`
  - `BE50 = 99/663 = 14.9%`
  - `BE75 = 37/663 = 5.6%`
- deep recovery:
  - `Deep50 = 99/344 = 28.8%`
  - `Deep75 = 37/305 = 12.1%`

Per TF best-family character:
- `1m`: 34 family, 16 positif, median best `0.000`
- `5m`: 34 family, 15 positif, median best `-0.065`
- `15m`: 34 family, 11 positif, median best `0.000`

SL head-to-head:
- total: `O1_SL50` menang `22`, `O2_ST2X` menang `21`, tie `8`
- khusus `5m`: `O2` menang `10`, `O1` menang `6`, tie `1`

## 2. Thesis inti sebelum masuk ke Meridian workflow

Kalau diperas jadi satu kalimat:

`Setup ini paling masuk akal dipakai sebagai bullish reclaim timing overlay,
 bukan sebagai deep-value dip accumulation engine.`

Artinya:
- setup ini tidak bilang “asal ada diskon, LP saja”
- setup ini bilang “kalau pool-nya memang sehat dan struktur trend-nya masih hidup,
  masuk setelah reclaim timing muncul”

Implikasi langsung:
- jangan pakai setup ini sebagai pengganti screening pool quality
- pakai setup ini sebagai lapisan timing di atas screening yang tetap ketat

## 3. Bagaimana ini nyambung ke workflow asli Meridian

Meridian secara arsitektur kerja di siklus seperti ini:

1. screening cycle cari candidate
2. hard filter + soft recon terhadap candidate
3. LLM memutuskan deploy atau no-deploy
4. position masuk ke management cycle
5. hasil close masuk ke learning system
   - evolve thresholds
   - darwin signal weights
   - lessons text
   - time/narrative profile

Supaya setup RSI/Fractal ini tidak “salah tempat”, kita harus menaruhnya begini:

### Layer A — pool quality layer
Dikerjakan oleh Meridian screening:
- fee/TVL
- organic quality
- holders
- launchpad / hygiene
- liquidity sanity
- narrative / smart-wallet / memory layer

### Layer B — timing layer
Dikerjakan oleh setup backtest ini:
- bullish trend masih valid
- RSI(2) > 90
- upper fractal confirm
- entry on next open
- manage reclaim failure / reclaim success via BE + SL logic

### Layer C — deployment expression layer
Dikerjakan oleh strategy choice:
- `spot`
- `curve`
- `bid_ask`

### Layer D — management / escape layer
Dikerjakan oleh Meridian management cycle:
- stop-loss behavior
- break-even governance
- close jika thesis gagal
- claim / range management bila perlu

Kesalahan yang harus dihindari:
- pakai timing layer untuk menggantikan quality layer
- pakai style LP tertentu (`bid_ask`) seolah-olah pasti benar hanya karena chart timing-nya bagus

## 4. Rumusan placement setup ini di Meridian

## 4.1 Posisi setup ini di screening cycle

Setup ini paling tepat diletakkan sebagai:
- `entry timing preference`
- bukan `global hard gate untuk semua candidate`

Kenapa:
- screening Meridian sudah punya sistem sendiri untuk menyeleksi pool sehat
- backtest kita belum menguji full LP PnL live
- jadi paling aman setup ini dipakai untuk memilih KAPAN masuk,
  bukan memaksa SEMUA pool yang lolos screening harus auto-deploy

### Rekomendasi operasional
Gunakan setup ini untuk menaikkan conviction saat:
- pool quality sudah lolos
- trend context tidak rusak
- reclaim timing muncul

Gunakan setup ini untuk MENURUNKAN conviction / no-deploy saat:
- pool lolos screening tapi setup timing belum muncul
- RSI/fractal muncul tapi pool quality jelek / chaotic / tipis

## 4.2 Posisi setup ini di management cycle

Data kita bilang:
- `BE1` paling robust secara coverage
- recovery dalam (`BE50`, `BE75`) itu lebih niche

Jadi untuk Meridian management workflow:
- `BE1` paling cocok sebagai base defensive behavior
- `BE50` bukan baseline universal — lebih cocok sebagai exception path
- `BE75` terlalu sempit untuk dijadikan default bot logic

Artinya untuk bot:
- default harus “cut ambiguity cepat”
- jangan terlalu berharap comeback dari drawdown dalam

## 4.3 Posisi setup ini di learning system Meridian

Meridian punya 4 learning path:
- auto-evolve threshold
- darwin signal weights
- lessons text
- time/narrative profile

Setup ini paling nyambung ke learning system sebagai berikut:

1. auto-evolve threshold tetap jalan normal
   - jangan dicampur dengan logic chart ini dulu
2. darwin bisa dipakai untuk mengamati sinyal pool mana yang paling sering
   selaras dengan setup reclaim ini
3. lessons text bisa dipakai untuk menulis rule seperti:
   - “no smart wallet = soft negative only”
   - “reclaim timing lebih bagus pada pool quality tinggi”
4. time/narrative profile bisa membantu menyaring kapan setup reclaim ini
   lebih sering bekerja

Kesimpulan:
- thesis ini compatible dengan learning system Meridian,
- tapi belum sebaiknya di-hardcode terlalu agresif ke core engine.

## 5. Preset utama yang kusarankan

## 5.1 Preset A — Autonomous Conservative

Ini preset kalau targetnya:
- bot jalan sendiri,
- prioritas robustness,
- lebih penting menghindari deploy jelek daripada memburu winner besar.

### Thesis
- pool quality tetap nomor 1
- timing chart jadi overlay
- reclaim cepat lebih penting daripada nunggu drawdown dalam pulih

### Rekomendasi setup
- TF utama: `5m`
- TF pendamping: `15m`
- SL utama: `O1_SL50` atau `O2_ST2X` tergantung toleransi
- exit default: `BE1`
- LP strategy default: `spot`
- strategyLock: `spot`

### Kenapa begini
- `5m` paling balance di data sekarang
- `15m` membantu buang noise
- `BE1` paling robust di breadth
- `spot` paling nyambung dengan thesis reclaim
- strategyLock ke `spot` menjaga bot tidak drift ke ekspresi deploy yang salah

### Kapan pakai O1 vs O2 di preset A
- pakai `O1_SL50` kalau ingin baseline bot lebih stabil / simpel
- pakai `O2_ST2X` kalau sudah yakin screening pool quality cukup bagus
  dan mau memberi struktur SL yang lebih “trend-aware”

### Final recommendation untuk preset A
Kalau disuruh pilih SATU baseline bot sekarang:
- `5m + 15m confirm`
- `O2_ST2X`
- `BE1`
- `spot locked`

Tapi kalau mau start lebih aman dulu:
- mulai dari `O1_SL50 + BE1 + spot locked`
- lalu naik ke `O2_ST2X` setelah punya observasi live yang cukup

## 5.2 Preset B — Autonomous Balanced / Adaptive

Ini preset kalau targetnya:
- bot tetap autonomous,
- tapi kita mau kasih ruang sedikit buat upside,
- tanpa langsung masuk ke mode liar.

### Thesis
- tetap pakai setup ini sebagai timing overlay
- tetap prefer `spot`
- tapi jangan terlalu kaku jika subset pool tertentu lebih cocok diberi ruang

### Rekomendasi setup
- TF utama: `5m`
- TF pendamping: `15m`
- SL utama: `O2_ST2X`
- exit default: `BE1`
- optional alt path: `BE50` hanya untuk candidate conviction tinggi
- LP strategy: `spot` default, `curve` experimental, `bid_ask` conditional only
- strategyLock:
  - opsi 1: tetap `spot`
  - opsi 2: `default`, tapi promptNotes / lessons steer ke `spot-first`

### Rule operasional
Kalau strategyLock dibuka (`default`):
- `spot` = base case
- `curve` = hanya jika ingin ekspresi range yang lebih shaped
- `bid_ask` = hanya bila thesis pool lebih ke dip-accumulation / fee-chop,
  BUKAN reclaim-upside capture

### Kelebihan preset B
- lebih cocok untuk sesi eksperimen terarah
- bisa mengecek apakah `curve` memberi live benefit
- tidak terlalu menyimpang dari thesis utama

### Kelemahan preset B
- lebih mudah drift
- lebih susah diaudit
- lebih berisiko kalau prompt/LLM mulai terlalu kreatif

## 5.3 Preset C — Manual / Semi-Manual Discretionary

Ini preset kalau targetnya:
- operator manusia tetap lihat candidate,
- manual approve atau semi-manual pick,
- ingin memanfaatkan setup ini sebagai thesis yang lebih tajam.

### Thesis
- manusia bisa lebih selektif daripada bot
- jadi boleh memakai ruang tambahan pada pool terbaik

### Rekomendasi setup
- TF utama: `5m`
- TF konfirmasi: `15m`
- optional `1m` hanya untuk micro-entry refinement,
  bukan engine utama
- SL utama: `O2_ST2X`
- exit baseline: `BE1`
- exception mode: `BE50` untuk pool terbaik dengan conviction tinggi
- LP style utama: `spot`
- LP style eksperimen: `curve`
- `bid_ask` hanya jika operator sengaja mau play dip-accumulation thesis

### Rule manual yang paling masuk akal
- kalau pool kualitas sedang / noisy -> `BE1`
- kalau pool kualitas tinggi / structure sangat clean -> boleh pertimbangkan `BE50`
- `BE75` jangan jadi standar; gunakan hanya sebagai test niche

## 6. TF thesis yang paling operasional

## 6.1 5m = base engine

Kenapa 5m jadi base engine:
- family positif paling banyak (`11`)
- median best family paling sehat (`+0.300`)
- tidak se-noisy 1m
- tidak se-lambat 15m

Operational meaning:
- 5m adalah tempat terbaik untuk decision engine Meridian
- kalau nanti ada satu preset inti, mulai dari sini

## 6.2 15m = context / confirmation

15m bukan engine utama,
namun bagus sebagai:
- context trend filter
- sanity check bahwa 5m signal tidak melawan struktur lebih besar

Operational meaning:
- pakai 15m untuk menurunkan false enthusiasm,
  bukan untuk menunggu sinyal utama sendirian

## 6.3 1m = tactical only

1m punya beberapa top winner besar,
namun median family masih negatif dan noise tinggi.

Operational meaning:
- jangan pakai 1m sebagai default bot engine
- 1m hanya cocok untuk:
  - tactical refinement
  - manual scalp-style context
  - subset pool sangat liquid / sangat aktif

## 7. Exit thesis yang paling operasional

## 7.1 Default exit = BE1

Ini kesimpulan paling tegas dari data.

Kenapa:
- menang `38/58` family best
- global recovery `64.6%`
- paling cocok untuk karakter setup reclaim cepat

Interpretasi operasional:
- setup ini tidak boleh dibangun dengan asumsi kita akan sering diselamatkan
  oleh recovery dalam
- justru performa terbaik muncul saat ambiguity dipotong cepat

## 7.2 BE50 = selective extension, bukan default

Kenapa masih penting:
- dia tetap menang `13/58` family best
- pada subset tertentu dia bisa menang bagus
- deep50 recovery rate `16.3%` masih punya makna

Operational use:
- aktifkan hanya jika conviction kandidat sangat tinggi
- lebih cocok untuk manual atau semi-manual daripada bot mass deployment

## 7.3 BE75 = niche only

Data bilang jelas:
- family wins sangat sedikit
- global recovery rate sangat rendah

Operational use:
- jangan jadikan preset default
- pakai hanya sebagai eksperimen / diagnosis

## 7.4 TP_FRACTAL = reference mode, bukan default base

TP_FRACTAL penting sebagai pembanding,
karena dia menunjukkan bagaimana setup behave kalau reclaim dibiarkan bekerja.

Tapi sebagai default Meridian preset:
- dia terlalu lemah breadth-nya
- terlalu sering kalah dari BE1 dalam robustness

## 8. LP strategy thesis yang paling operasional

## 8.1 Kenapa spot harus jadi default utama

Dari sisi thesis:
- setup ini ingin ikut reclaim move
- spot paling netral untuk mengekspresikan reclaim
- lebih sedikit konflik dengan target upside dibanding bid_ask

Dari sisi workflow Meridian:
- lebih gampang diaudit
- lebih gampang dijelaskan ke operator
- lebih gampang dijadikan baseline paper/live comparison

Jadi:
- kalau harus pilih satu strategyLock sekarang,
  aku pilih `spot`

## 8.2 Kapan curve layak dicoba

Curve layak dicoba kalau:
- kita sudah punya baseline `spot`
- kita ingin lihat apakah shaped distribution memberi hasil LP live lebih baik
- kita sengaja melakukan paper/live A-B test

Bukan untuk default awal.

## 8.3 Kapan bid_ask boleh dipakai

Bid_ask hanya masuk akal kalau thesis entry berubah menjadi:
- kita ingin monetize dip,
- kita rela menangkap lebih sedikit upside,
- kita fokus ke fee-chop / mean-reverting lower-zone behavior.

Artinya:
- bid_ask itu conditional
- bukan expression default dari setup RSI/fractal reclaim ini

## 9. Rekomendasi operasional untuk bot Meridian

Kalau aku yang harus merumuskan deployment policy untuk Meridian sekarang,
aku akan tulis seperti ini:

### Policy 1 — screening tetap ketat
Jangan longgarkan screening quality hanya karena setup timing ini terlihat menarik.

### Policy 2 — timing setup adalah overlay
Candidate sehat dulu, baru timing dipakai untuk naikkan conviction.

### Policy 3 — default style = spot
Lock `spot` dulu sampai ada bukti live yang kuat bahwa `curve` atau `bid_ask`
lebih cocok.

### Policy 4 — default exit = BE1
Kalau recovery cepat tidak datang, jangan terlalu lama berharap.

### Policy 5 — 5m is the engine, 15m is the judge
Decision utama lahir di 5m,
15m hanya mengkonfirmasi apakah sinyal itu sehat.

### Policy 6 — 1m jangan dijadikan default autonomous loop
Gunakan 1m hanya kalau ada alasan khusus.

## 10. Rekomendasi operasional untuk manual workflow

Kalau operator mau menjalankan setup ini manual / semi-manual,
aku sarankan flow seperti ini:

1. buka candidate list hasil screening Meridian
2. buang pool quality jelek lebih dulu
3. lihat `5m` sebagai chart utama
4. cek `15m` untuk context
5. deploy default via `spot`
6. pakai `BE1` sebagai baseline
7. hanya pada kandidat premium:
   - boleh pertimbangkan `BE50`
   - boleh eksperimen `curve`

Manual checklist singkat:
- apakah pool sehat secara quality?
- apakah 15m tidak rusak?
- apakah 5m memberi reclaim timing yang clean?
- apakah ini kandidat biasa atau kandidat premium?
- kalau biasa -> `spot + BE1`
- kalau premium -> boleh `spot/curve + BE50`

## 11. Preset matrix yang kusarankan

### Preset matrix ringkas

| Use case | TF utama | TF confirm | SL | Exit | Strategy | Notes |
|---|---|---|---|---|---|---|
| Bot conservative | 5m | 15m | O1 atau O2 | BE1 | spot locked | default paling aman |
| Bot balanced | 5m | 15m | O2 | BE1 | spot default | curve experimental only |
| Manual standard | 5m | 15m | O2 | BE1 | spot | baseline operator |
| Manual premium candidate | 5m | 15m | O2 | BE50 | spot / curve | only selective |
| Experimental dip-fee thesis | 5m | 15m | O2 | conditional | bid_ask | bukan default reclaim play |

## 12. Setting umum yang lebih spesifik

Bagian ini khusus menjawab pertanyaan “oke, tapi setting umum strat-nya apa?”
Bukan cuma arah konsep, tapi field konfigurasi yang lebih konkret.

### 12.1 Baseline produksi yang paling kusarankan

Kalau setup ini mau ditaruh ke workflow Meridian produksi sekarang,
aku paling merekomendasikan baseline ini:

- `solMode = true`
- `strategy = spot`
- `strategyLock = spot`
- `dualSideEnabled = false`
- `minBinsBelow = 35`
- `maxBinsBelow = 52`
- `defaultBinsBelow = 52`
- timing engine = `5m`
- context confirm = `15m`
- chart risk logic = `O2_ST2X + BE1`

Ini artinya secara operasional:
- pair focus tetap SOL-pair
- deploy expression jangan dibiarkan drift
- default inventory tetap single-side SOL
- width tetap di band yang sekarang dipakai Meridian, jangan dilebarkan dulu

### 12.2 Kenapa baseline produksinya single-side dulu

Alasan utama:
- hasil backtest kita kuat di `timing reclaim`, bukan di `inventory engineering`
- dual-side mengubah struktur inventory, bukan cuma entry timing
- jadi terlalu prematur kalau langsung dijadikan preset produksi utama

Karena itu baseline produksi yang paling disiplin adalah:
- `spot locked`
- `single-side SOL`
- `BE1`

### 12.3 Kalau mau eksperimen dual-side, preset apa yang paling masuk akal?

Kalau mau eksperimen dual-side, jangan mulai besar.
Mulai dari sleeve token kecil.

Preset eksperimen yang paling masuk akal menurutku:
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

Cara baca preset ini:
- `90%` modal tetap berperan seperti baseline bawah
- `10%` dipakai sebagai token sleeve kecil di sisi atas
- targetnya bukan mengubah thesis utama,
  tapi memberi sedikit alat untuk ikut reclaim-upside

Kenapa angka ini yang kupilih:
- `10%` cukup kecil untuk eksplorasi aman
- `10–15% upside` cukup dekat untuk relevance reclaim,
  belum terlalu jauh sampai jadi “hiasan” doang
- `dualSideStrategy=spot` lebih selaras dengan thesis reclaim,
  tidak langsung mendorong ekspresi yang terlalu berat ke dip-play

### 12.4 Kapan bid_ask baru layak dipakai sebagai preset umum?

Hanya ketika thesis-nya berubah jadi:
- buy the dip / bawahannya,
- rela mengorbankan sebagian upside capture,
- fee-chop lebih penting daripada reclaim move.

Kalau thesis yang dipakai masih thesis RSI/fractal reclaim ini,
aku tidak sarankan preset umum utamanya menjadi:
- `strategy=bid_ask`
- `strategyLock=bid_ask`

### 12.5 Rekomendasi pemisahan profile / instance

Karena dual-side itu mengubah ekspresi deploy,
aku sarankan struktur operasional seperti ini:

- profile / instance A = baseline produksi
  - `spot locked`
  - `dualSideEnabled=false`
- profile / instance B = eksperimen
  - `spot locked`
  - `dualSideEnabled=true`
  - `dualSideTokenPct=10`
  - `dualSideUpsidePct=10–15`

Kenapa dipisah:
- learning / lessons tidak tercampur langsung
- lebih gampang audit performa
- lebih gampang rollback bila eksperimen jelek

## 13. Final recommendation — satu preset utama

Kalau user tanya:
“oke, jadi preset Meridian paling masuk akal sekarang apa?”

jawabanku:

### Preset utama
- `solMode = true`
- `strategy = spot`
- `strategyLock = spot`
- `dualSideEnabled = false`
- `minBinsBelow = 35`
- `maxBinsBelow = 52`
- `defaultBinsBelow = 52`
- TF engine: `5m`
- TF context: `15m`
- SL: `O2_ST2X`
- exit governance: `BE1`
- role setup: timing overlay di atas screening pool yang tetap ketat

### Alasan singkat
- `5m` paling balance
- `O2` lebih sering menang head-to-head terutama di 5m
- `BE1` paling robust secara coverage
- `spot` paling cocok dengan thesis reclaim-upside
- paling nyambung dengan workflow asli Meridian

## 14. Aturan paling penting

Kalau cuma boleh menulis SATU prinsip:

`Jangan pakai setup ini untuk memaksa semua pool bagus menjadi deploy;
 pakai setup ini untuk memilih timing reclaim terbaik pada pool yang memang
 sudah lolos quality screening Meridian.`

## 15. Next practical steps

Urutan implementasi yang paling masuk akal:

1. pakai preset `solMode=true + spot locked + single-side + 5m + 15m + O2 + BE1`
2. jalankan paper / guarded live
3. bandingkan dengan baseline Meridian biasa
4. kalau hasil stabil, baru uji:
   - `curve`
   - `BE50` pada candidate premium
   - `dualSideEnabled=true` di profile eksperimen terpisah
5. simpan lesson operator ke Meridian profile yang relevan
   supaya thesis ini ikut terbaca di siklus berikutnya

## 16. Bottom line

Untuk sekarang, versi paling operasional dan paling sinkron dengan workflow Meridian adalah:

- screening tetap ketat
- timing pakai setup reclaim ini
- `solMode = true`
- `strategy = spot`
- `strategyLock = spot`
- `dualSideEnabled = false`
- `minBinsBelow = 35`
- `maxBinsBelow = 52`
- `defaultBinsBelow = 52`
- engine di `5m`
- confirm di `15m`
- `O2_ST2X`
- `BE1`
- deploy via `spot`
- `curve` sebagai eksperimen berikutnya
- `bid_ask` hanya dipakai kalau thesis-nya memang berubah menjadi dip/fee capture play
- `dual-side` hanya dipakai sebagai eksperimen profile terpisah, mulai dari token sleeve kecil (`10%`) dan upside band `10–15%`
