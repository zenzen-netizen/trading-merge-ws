# Meridian Operator Playbook — Compact

Tujuan:
- versi super ringkas,
- cepat dibaca sebelum sesi deploy,
- jaga operator tetap di thesis benar.

## 1. Thesis inti

Setup ini = `bullish reclaim timing overlay`.
Bukan `deep dip accumulation engine`.

Urutan pikir:
1. pool quality
2. 15m context
3. 5m reclaim timing
4. deploy expression
5. management discipline

## 2. Default baseline

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

Default behavior:
- SOL pair only
- `spot` single-side
- 15m = context
- 5m = engine
- management = `BE1 style`

## 3. Deploy only if

Semua ini iya:
- pool quality sehat
- 15m context tidak rusak
- 5m reclaim clean
- reward belum telat dimakan extension
- operator masih main thesis reclaim, bukan thesis lain

## 4. Skip if

Salah satu ini iya:
- pool tipis / hygiene jelek / organic jelek
- 15m rusak
- 5m reclaim telat / chaos / dead-cat feel
- ingin ubah terlalu banyak variabel sekaligus
- conviction kabur dan butuh cerita panjang buat membenarkan trade

## 5. Candidate premium

Premium jika:
- quality di atas rata-rata
- 15m bersih
- 5m reclaim clean
- narasi hidup
- edge bisa dijelaskan sederhana

Premium boleh:
- size sedikit lebih percaya diri
- management sedikit lebih sabar
- manual `curve` test di sandbox

Premium TIDAK otomatis boleh:
- dual-side besar
- pindah ke `bid_ask`
- longgar total pada risk discipline

## 6. Baseline vs dual-side

Baseline untuk:
- production
- guarded live pertama
- paper comparator
- candidate normal
- semua kondisi ragu

Dual-side hanya jika:
- baseline sudah jelas
- profile terpisah
- motif eksperimen jelas
- size kecil
- compare lawan baseline

Preset dual-side awal:
```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": true,
  "dualSideTokenPct": 10,
  "dualSideUpsidePct": 12,
  "dualSideStrategy": "spot"
}
```

## 7. Operator checklist

Sebelum deploy:
1. pool sehat?
2. 15m sehat?
3. 5m reclaim clean?
4. biasa atau premium?
5. baseline cukup?
6. kalau eksperimen gagal, alasannya tetap auditable?

Kalau 2 jawaban kabur:
- skip

## 8. Golden rules

- chart bagus tidak menyelamatkan pool jelek
- strategy kreatif tidak menebus conviction lemah
- dual-side bukan tambal sulam conviction
- ragu baseline vs eksperimen: baseline
- ragu deploy vs skip: skip
