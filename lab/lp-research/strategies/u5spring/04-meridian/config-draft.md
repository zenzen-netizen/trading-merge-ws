# Meridian Config Draft — Meteora Reclaim Setup

Tujuan file ini:
- memberi draft config yang benar-benar bisa langsung dipakai sebagai acuan,
- menerjemahkan thesis dari:
  - `METEORA_SETUP_DEPLOYMENT_NOTES.md`
  - `MERIDIAN_PRESET_THESIS.md`
- menjadi preset yang lebih praktis untuk Meridian.

PENTING:
- ini masih draft operasional / policy note,
- bukan berarti semua key harus langsung diubah sekaligus,
- dan file ini sengaja memisahkan:
  1. preset produksi baseline
  2. preset eksperimen dual-side
  3. preset manual / semi-manual

## 1. Prinsip utama sebelum config

Setup ini dibaca sebagai:
- `bullish reclaim timing overlay`
- bukan `deep value accumulation engine`

Jadi config draft ini dibangun dengan 3 prinsip:
- screening pool quality tetap ketat
- timing entry pakai reclaim setup
- deploy expression jangan terlalu kreatif dulu

Artinya:
- baseline utama = `spot`
- baseline inventory = `single-side SOL`
- baseline protection = `BE1`
- `dual-side` = eksperimen, bukan default awal
- `bid_ask` = hanya kalau thesis sengaja digeser ke dip/fee capture

## 2. Preset A — Produksi baseline (paling direkomendasikan)

Ini preset yang paling “langsung pakai” menurutku sekarang.

### A1. Use case
- untuk bot Meridian utama
- untuk guarded live / paper baseline
- untuk profile yang mau dijadikan pembanding utama

### A2. Draft setting inti

```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": false,
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "activeSetup": "meteora-reclaim-baseline"
}
```

### A3. Draft setting workflow / timing thesis

```json
{
  "timeframe": "5m",
  "screeningIntervalMin": 30,
  "managementIntervalMin": 10,
  "adaptiveScreening": true
}
```

Catatan:
- `5m` = engine utama
- `15m` di thesis ini dipakai sebagai context / confirm,
  bukan berarti harus jadi `timeframe` screening utama bot
- kalau nanti mau dibuat lebih literal di sistem, 15m lebih cocok masuk ke logic
  confirm layer / promptNotes / operator checklist, bukan mengganti engine 5m

### A4. Draft setting size / risk baseline

Ini bukan hasil backtest murni, tapi guard operasional yang masuk akal.
Angka exact size tetap boleh disesuaikan ke wallet dan risk budget.

```json
{
  "maxPositions": 2,
  "deployAmountSol": 0.05,
  "positionSizePct": 0.20,
  "maxDeployAmount": 0.10,
  "gasReserve": 0.03,
  "minSolToOpen": 0.12,
  "rentPerPositionSol": 0.057
}
```

Cara baca:
- ini draft konservatif
- cocok untuk mulai observasi baseline dulu
- kalau wallet besar, `deployAmountSol` dan `maxDeployAmount` bisa dinaikkan,
  tapi struktur thesis-nya jangan berubah dulu

### A5. Draft policy exit / management

Backtest kita paling kuat di `BE1`.
Karena Meridian config sekarang tidak memakai field literal `BE1` seperti file backtest,
maka ini harus dibaca sebagai POLICY, bukan copy-paste key final.

Policy yang kusarankan:
- jika reclaim cepat gagal, cut ambiguity cepat
- jangan bangun preset awal dengan asumsi recovery dalam
- baseline mental model management = `BE1 behavior`

Operational translation:
- trailing / dynamic exit jangan dibuat terlalu longgar
- jangan terlalu cepat memberi ruang ke drawdown dalam
- kalau nanti ada preset management khusus untuk setup ini,
  arahnya harus mendekati `BE1`, bukan `BE50/BE75`

### A6. Kesimpulan Preset A

Kalau cuma boleh pilih satu preset buat mulai jalan:
- `solMode=true`
- `strategy=spot`
- `strategyLock=spot`
- `dualSideEnabled=false`
- `35/52/52 bins`
- engine `5m`
- policy exit = `BE1 style`

Itu preset baseline paling waras.

## 3. Preset B — Eksperimen dual-side (profile terpisah)

Ini preset buat menjawab rasa penasaran:
- “gimana kalau reclaim setup ini dikasih upside sleeve?”

Tapi ini BUKAN preset produksi pertama.

### B1. Use case
- profile eksperimen terpisah
- paper / guarded live kecil
- pembanding terhadap baseline single-side

### B2. Draft setting inti

```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": true,
  "dualSideTokenPct": 10,
  "dualSideUpsidePct": 12,
  "dualSideStrategy": "spot",
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "activeSetup": "meteora-reclaim-dualside-exp"
}
```

### B3. Kenapa angka ini
- `dualSideTokenPct=10`
  - kecil
  - cukup untuk jadi sleeve
  - tidak terlalu merusak baseline behavior
- `dualSideUpsidePct=12`
  - di tengah range saran 10–15
  - cukup dekat untuk tetap relevan dengan reclaim move
- `dualSideStrategy=spot`
  - lebih netral
  - lebih dekat ke thesis reclaim
  - jangan langsung didorong ke distribusi yang terlalu dip-oriented

### B4. Jangan langsung pakai angka besar

Yang TIDAK kusarankan sebagai first test:
- `dualSideTokenPct = 20` atau lebih
- `dualSideUpsidePct = 25+`
- `dualSideStrategy = bid_ask`

Kenapa:
- terlalu banyak moving parts berubah sekaligus
- susah audit apa yang benar-benar membantu
- berisiko membuat eksperimen tidak comparable dengan baseline

### B5. Cara scale eksperimen kalau hasil awal bagus

Urutan scale yang disiplin:
1. mulai `10% / 12%`
2. kalau stabil, naik ke `12–15% / 12–15%`
3. baru setelah itu pikirkan:
   - `dualSideStrategy`
   - atau perubahan sleeve lebih besar

### B6. Kesimpulan Preset B

Preset dual-side yang paling masuk akal untuk test awal:
- `spot locked`
- `dualSideEnabled=true`
- `dualSideTokenPct=10`
- `dualSideUpsidePct=12`
- `dualSideStrategy=spot`

## 4. Preset C — Manual / semi-manual operator preset

Ini bukan murni config file,
lebih tepat sebagai operator guideline yang konsisten dengan thesis.

### C1. Use case
- operator lihat candidate satu-satu
- operator bisa pilih conviction pool
- operator bisa bedakan candidate biasa vs premium

### C2. Draft setting umum

```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": false,
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "activeSetup": "meteora-reclaim-manual"
}
```

### C3. Policy manual
- candidate biasa:
  - `spot`
  - single-side
  - `BE1 style`
- candidate premium:
  - `spot`
  - optional `curve`
  - boleh diberi ruang mirip `BE50 style`
- `bid_ask`:
  - hanya kalau operator memang sengaja ganti thesis menjadi dip/fee-capture play

### C4. Manual checklist singkat
- pool quality sehat?
- 15m context tidak rusak?
- 5m reclaim timing clean?
- ini kandidat biasa atau premium?
- kalau biasa -> baseline preset
- kalau premium -> boleh tambah ruang, tapi jangan ubah terlalu banyak variabel sekaligus

## 5. Draft promptNotes / operator notes

Karena Meridian workflow banyak ditentukan prompt + learning,
berikut draft note yang konsisten dengan thesis ini.

### 5.1 Draft promptNotes untuk baseline

```json
{
  "promptNotes": {
    "screener": [
      "Treat this setup as a bullish reclaim timing overlay, not a deep dip-buying system.",
      "Prefer clean reclaim timing on already healthy SOL pools.",
      "Default deploy expression is spot and single-side SOL unless there is a very strong reason otherwise.",
      "Do not force a deploy just because chart timing appears; pool quality still wins."
    ],
    "manager": [
      "Manage this setup with fast ambiguity-cutting behavior closer to BE1 than deep recovery tolerance.",
      "Do not assume deep drawdowns will recover; protect capital first."
    ],
    "general": []
  }
}
```

### 5.2 Draft lesson untuk profile eksperimen dual-side

Kalau dual-side diuji di profile terpisah, operator note yang cocok:
- dual-side is an upside sleeve experiment, not a new default thesis
- keep token sleeve small
- compare against spot-single-side baseline, not against random discretionary trades

## 6. Setting yang jangan diubah dulu

Supaya eksperimen tetap bersih, untuk fase awal aku sarankan JANGAN dulu mengubah terlalu banyak hal ini bersamaan:
- `strategyLock`
- `dualSideEnabled`
- `dualSideTokenPct`
- `dualSideUpsidePct`
- `minBinsBelow/maxBinsBelow`
- sizing besar
- screening looseness besar-besaran

Kenapa:
- nanti hasilnya tidak bisa diatribusikan
- kita tidak tahu perubahan mana yang actually membantu

## 7. Field-by-field quick recommendation

| Key | Baseline | Eksperimen dual-side | Catatan |
|---|---|---|---|
| `solMode` | `true` | `true` | selaras dengan sample backtest |
| `strategy` | `spot` | `spot` | baseline reclaim thesis |
| `strategyLock` | `spot` | `spot` | jangan drift dulu |
| `dualSideEnabled` | `false` | `true` | ON hanya di profile eksperimen |
| `dualSideTokenPct` | n/a | `10` | mulai kecil |
| `dualSideUpsidePct` | n/a | `12` | midpoint 10–15 |
| `dualSideStrategy` | n/a | `spot` | jangan bid_ask dulu |
| `minBinsBelow` | `35` | `35` | tetap ikut guard Meridian |
| `maxBinsBelow` | `52` | `52` | jangan dilebarkan dulu |
| `defaultBinsBelow` | `52` | `52` | baseline width tetap |
| `timeframe` | `5m` | `5m` | engine utama |
| confirm context | `15m` | `15m` | lebih cocok jadi policy/overlay |
| exit mindset | `BE1 style` | `BE1 style` | baseline protection |

## 8. Rekomendasi profile layout

Kalau mau rapih dan gampang audit:

### Profile 1 — production baseline
- spot
- single-side
- reclaim overlay
- BE1-style management

### Profile 2 — dual-side experiment
- spot locked
- dual-side ON
- 10% token sleeve
- 12% upside sleeve

### Profile 3 — optional manual sandbox
- untuk operator discretionary
- boleh test curve / BE50-style handling
- bukan untuk dijadikan basis learning produksi langsung

## 9. Bottom line

Kalau kamu ingin satu draft yang paling langsung pakai sekarang:

### Draft utama
```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": false,
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "timeframe": "5m"
}
```

### Draft eksperimen dual-side
```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": true,
  "dualSideTokenPct": 10,
  "dualSideUpsidePct": 12,
  "dualSideStrategy": "spot",
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "timeframe": "5m"
}
```

Kalau harus pilih SATU arah sekarang:
- mulai dari baseline single-side spot dulu
- jangan dual-side dulu sebagai preset produksi
- kalau mau uji dual-side, uji di profile terpisah dengan sleeve kecil
