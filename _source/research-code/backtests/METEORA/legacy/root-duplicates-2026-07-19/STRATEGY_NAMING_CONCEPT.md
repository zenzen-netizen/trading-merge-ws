# Strategy Naming & Folder Concept — Meteora Reclaim Workflow

Tujuan:
- merapikan semua artefak backtest sampai payload Meridian,
- kasih nama strategi/metode yang bisa dipakai jangka panjang,
- bikin struktur yang scalable kalau nanti ada backtest lain.

PENTING:
- ini baru konsep,
- belum pindah file apa pun,
- belum rename folder apa pun.

## 1. Prinsip naming

Nama ideal menurut kebutuhanmu:
- tidak terlalu panjang
- gampang diingat
- cukup netral untuk backtest, thesis, playbook, payload
- tidak terlalu nempel ke satu indikator teknis mentah
- masih cocok kalau nanti hidup sebagai `strategy family`

Jadi sebaiknya nama jangan model:
- `rsi-fractal-supertrend-smi-5m-reclaim`
- kepanjangan
- terlalu teknis
- susah dipakai sebagai folder induk

Lebih bagus:
- nama family / metode
- indikator detail turun ke subfile

## 2. Arah identitas strategi ini

Dari semua file sekarang, karakter strategi ini paling kuat:
- bullish reclaim
- continuation-oriented
- pool quality first
- 5m timing + 15m context
- spot-first deployment
- BE1-style protection

Jadi nama sebaiknya memantulkan:
- reclaim
- continuation
- thrust / spring / pulse / lift
- tidak terlalu meme
- tidak terlalu generic

## 3. Kandidat nama terbaik

## Opsi A — Reclaim

Kelebihan:
- paling jujur ke thesis
- pendek
- jelas
- gampang dipakai di nama file

Kekurangan:
- agak generik
- kurang punya identitas khas kalau nanti family strategi banyak

Contoh:
- `reclaim`
- `meteora-reclaim`

## Opsi B — SolReclaim

Kelebihan:
- langsung nyambung SOL pair thesis
- tetap pendek
- enak dibaca

Kekurangan:
- terlalu sempit kalau nanti dipakai di non-SOL pair

## Opsi C — Reclaim5

Kelebihan:
- pendek
- ada identitas timeframe utama

Kekurangan:
- terlalu nempel ke 5m
- kalau nanti logic evolve, nama jadi sempit

## Opsi D — Spring

Kelebihan:
- catchy
- ngasih rasa pullback lalu pantul
- pendek banget

Kekurangan:
- terlalu abstrak
- tanpa konteks agak susah ditebak

## Opsi E — UpSpring

Kelebihan:
- lebih jelas bullish reclaim
- tetap pendek
- gampang diingat

Kekurangan:
- sedikit lebih branding-style

## Opsi F — FluxLift

Kelebihan:
- modern
- terasa systematic
- cukup unik

Kekurangan:
- agak jauh dari bahasa thesis asli
- butuh adaptasi biar nempel di kepala

## Opsi G — ReboundX

Kelebihan:
- gampang diingat
- terkesan strategi aktif

Kekurangan:
- agak generik trading-bro
- kurang elegan buat folder riset jangka panjang

## Opsi H — Lift

Kelebihan:
- super pendek
- gampang dipakai

Kekurangan:
- terlalu umum
- kurang spesifik

## 4. Rekomendasi utama

Kalau cari nama paling waras, bersih, tahan lama:

### Pilihan terbaik 1 — `Reclaim`
Kenapa:
- paling dekat dengan thesis sebenarnya
- netral
- mudah jadi parent folder
- mudah diperluas jadi family

Contoh family:
- `reclaim/rsi-fractal-v1`
- `reclaim/smi-confirm-v1`
- `reclaim/dual-side-exp`

### Pilihan terbaik 2 — `UpSpring`
Kenapa:
- lebih punya identitas
- masih pendek
- tetap membawa rasa pullback lalu naik lagi
- lebih enak kalau kamu mau terasa seperti nama metode, bukan label teknis mentah

Contoh family:
- `upspring/core`
- `upspring/meridian`
- `upspring/payloads`

### Pilihan terbaik 3 — `SolSpring`
Kenapa:
- mudah diingat
- ada flavor SOL pair
- catchy

Risiko:
- nanti sempit kalau family meluas ke non-SOL

## 5. Rekomendasi final dariku

Kalau mau paling aman dan matang:
- nama metode induk: `Reclaim`
- nama lebih branded opsional: `UpSpring`

Cara pilih:
- kalau mau serius-riset, bersih, tahan lama: `Reclaim`
- kalau mau lebih memorable dan punya identitas: `UpSpring`

Kalau disuruh pilih satu sekarang:
- aku condong ke `UpSpring`

Alasannya:
- lebih khas dari `Reclaim`
- tetap pendek
- tetap nyambung ke pullback lalu continuation
- enak buat nama folder, file, setup, payload

## 6. Konsep struktur folder

Sekarang file masih numpuk di `METEORA/`.
Kalau pakai family strategy, lebih rapi begini:

```text
backtests/METEORA/
  strategies/
    upspring/
      01-research/
        pool-discovery/
        backtests/
        raw-reports/
      02-thesis/
        setup-deployment-notes.md
        meridian-preset-thesis.md
      03-operator/
        operator-playbook.md
        operator-playbook-compact.md
      04-meridian/
        config-draft.md
        promptnotes-final.md
        profile-mapping.md
        ready-to-apply-jsons.md
      05-payloads/
        ready-load-profiles/
          meteora-baseline.user-config.json
          meteora-dualside-exp.user-config.json
          meteora-manual-sandbox.user-config.json
          README.md
```

## 7. Kenapa struktur ini bagus

Karena pisah jelas:
- research mentah
- thesis
- operator doctrine
- Meridian translation
- payload final

Jadi nanti kalau ada strategi lain, tinggal paralel:

```text
backtests/METEORA/strategies/
  upspring/
  dipforge/
  trendvault/
```

Tanpa bikin semua file campur satu lantai.

## 8. Naming style file kalau pakai nama metode

Kalau pakai `UpSpring`, file bisa jadi begini:
- `UPSPRING_SETUP_NOTES.md`
- `UPSPRING_MERIDIAN_THESIS.md`
- `UPSPRING_OPERATOR_PLAYBOOK.md`
- `UPSPRING_READY_TO_APPLY_JSONS.md`

Atau lebih rapi lagi folder-based, jadi nama file pendek saja:
- `setup-notes.md`
- `meridian-thesis.md`
- `operator-playbook.md`
- `ready-to-apply-jsons.md`

Aku lebih suka folder-based + nama file pendek.
Karena:
- folder sudah bawa identitas strategi
- file lebih gampang dibaca
- tidak redundant

## 9. Konsep jangka panjang

Kalau nanti ada indikator lain, jangan taruh di level sama sebagai file liar.
Taruh sebagai strategy sibling.

Contoh:
- `upspring` = reclaim continuation family
- `dipforge` = dip accumulation family
- `trendvault` = trend quality / higher-timeframe family

Jadi framework-mu jadi:
- satu folder per strategy family
- di dalamnya lengkap dari research sampai payload

## 10. Bottom line

Usulan konsep terbaik:
- parent architecture: strategy family based
- nama metode terbaik: `UpSpring`
- nama alternatif aman: `Reclaim`

Kalau mau paling clean:
- metode = `UpSpring`
- semua file riset sampai payload masuk ke satu dir khusus strategy itu
- nanti strategi lain tinggal bikin sibling dir baru
