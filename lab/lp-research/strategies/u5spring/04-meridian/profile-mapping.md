# Meridian Profile Mapping — Meteora Reclaim Setup

Tujuan:
- memetakan thesis dan playbook ke profile Meridian nyata,
- memisahkan baseline produksi, dual-side experiment, dan manual sandbox,
- menjaga audit tetap bersih.

## 1. Struktur profile yang direkomendasikan

### Profile A — Production Baseline

Peran:
- bot utama
- guarded live utama
- baseline pembanding resmi

Karakter:
```json
{
  "activeSetup": "meteora-reclaim-baseline",
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

Policy:
- profile ini jangan dipakai eksperimen liar
- profile ini jadi source of truth pembanding
- management dibaca sebagai `BE1 style`

Use case:
- deploy harian utama
- paper/live pembanding
- candidate normal bagus

### Profile B — Dual-Side Experiment

Peran:
- eksperimen upside sleeve
- guarded live kecil atau paper
- pembanding langsung lawan baseline

Karakter:
```json
{
  "activeSetup": "meteora-reclaim-dualside-exp",
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

Policy:
- compare terhadap baseline, bukan random discretionary trade
- jangan ubah bins, screening, sizing, dan management sekaligus
- satu eksperimen, satu pertanyaan utama

Use case:
- test apakah upside sleeve tambah hasil
- test tanpa mengubah thesis inti reclaim

### Profile C — Manual Sandbox

Peran:
- discretionary operator
- candidate premium
- optional `curve` exploration
- management variation terbatas

Karakter dasar:
```json
{
  "activeSetup": "meteora-reclaim-manual",
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

Policy:
- manual boleh lebih selektif
- `curve` hanya di sandbox ini
- `bid_ask` hanya kalau thesis memang bergeser ke dip/fee capture
- jangan pakai hasil sandbox sebagai alasan mengubah produksi tanpa pembanding jelas

## 2. Nama profile operasional yang disarankan

Kalau mau naming rapih:
- `meteora-baseline`
- `meteora-dualside-exp`
- `meteora-manual-sandbox`

Atau kalau mau lebih pendek:
- `mrec-base`
- `mrec-dual`
- `mrec-manual`

## 3. Mapping keputusan ke profile

### Kandidat normal bagus
Pakai:
- Profile A — Production Baseline

### Kandidat premium, tapi masih ingin disiplin thesis
Pakai:
- default tetap Profile A
- kalau manual dan ada alasan kuat, evaluasi juga di Profile C

### Mau test upside sleeve kecil
Pakai:
- Profile B

### Mau test `curve`
Pakai:
- Profile C

### Mau test thesis dip-capture / fee-chop
Pakai:
- bukan Profile A
- sebaiknya Profile C atau profile eksperimen baru terpisah

## 4. Field discipline per profile

### Profile A
Jangan sentuh sering-sering:
- `strategyLock`
- `dualSideEnabled`
- `minBinsBelow/maxBinsBelow/defaultBinsBelow`
- sizing utama
- screening looseness

Tujuan:
- jaga comparator tetap stabil

### Profile B
Boleh berubah terbatas:
- `dualSideTokenPct`
- `dualSideUpsidePct`
- optional size kecil

Jangan berubah bersamaan:
- bins
- strategyLock
- screening looseness besar
- management tolerance besar

### Profile C
Boleh paling fleksibel, tapi:
- tetap tulis perubahan dengan niat jelas
- jangan campur semua eksperimen dalam satu sesi
- hasil bagus di sini belum otomatis valid untuk produksi

## 5. Risk / sizing stance per profile

### Profile A
- konservatif
- baseline size
- tujuan observasi bersih

### Profile B
- lebih kecil atau sama dengan baseline
- jangan lebih besar dari baseline sebelum ada bukti

### Profile C
- discretionary kecil-menengah
- size naik hanya untuk candidate premium yang benar-benar jelas

## 6. Management stance per profile

### Profile A
- `BE1 style`
- cut ambiguity cepat

### Profile B
- tetap dekat `BE1 style`
- jangan sekaligus longgarkan management waktu deploy expression berubah

### Profile C
- `BE1 style` default
- optional sedikit lebih sabar untuk candidate premium
- tetap bukan deep-recovery cult

## 7. Audit questions

Sebelum ubah apa pun, tanya:
- profile ini memang untuk apa?
- perubahan ini menjawab pertanyaan apa?
- comparator-nya siapa?
- kalau hasil bagus, apakah saya bisa jelaskan kenapa?

Kalau jawaban kabur:
- jangan ubah dulu

## 8. Bottom line

Layout paling bersih:
- A = produksi baseline
- B = dual-side experiment
- C = manual sandbox

Rule emas:
- produksi stabil
- eksperimen terpisah
- sandbox jangan mencemari baseline
