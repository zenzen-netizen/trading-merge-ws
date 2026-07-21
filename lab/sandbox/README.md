# Sandbox — Eksperimen Bebas

Tempat coba-coba kombinasi indikator/parameter tanpa komit ke proses formal 8 langkah.
Pakai data dan engine asli, tapi belum masuk `strategies/` secara resmi.

## Struktur
```
sandbox/
├─ README.md              # ini
├─ log.md                 # catatan ringkas semua eksperimen
└─ experiments/
   ├─ exp_001_first_run/  # eksperimen pertama
   ├─ exp_002_xxx/
   └─ ...
```

## Aturan Main
- Satu folder per eksperimen: `exp_NNN_nama_singkat/`
- Cek hasil kasar aja (EV, drawdown) — gak perlu proses lengkap
- Kalau menjanjikan → "naik kelas" ke `strategies/`, mulai siklus resmi
- Kalau gak menjanjikan → catat ringkas di `log.md`, folder boleh dihapus

## Log Eksperimen
Lihat `log.md` — satu baris per eksperimen: nomor, tanggal, ide, hasil ringkas, keputusan.
