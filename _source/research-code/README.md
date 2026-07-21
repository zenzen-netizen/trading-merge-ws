# TRADING-RESEARCH — INDEX

Struktur scalabel per pair / per timeframe. Tambah pair baru →
buat folder di `backtests/`.

## Navigasi Cepat
- `TRADE_TEMPLATE.md`     — work-tree concept (format pencatatan trade
  resmi: entry→exit→combo→outcome). PAKAI buat analisis trade baru.
- `backtests/BTCUSDT/SETUP1/` — rumah SETUP1 SHORT (engine v2.b).
  - `1D/setup1_v2b_clean.py`   ★ ENGINE UTAMA (FBF v11 + SMI v3 + v2.b)
  - `TRIGGER_SPEC_v2b.md`      ★ SPEC FINAL (LOCKED Variant E)
  - `data_BTCUSDT_*_2021now.csv` — cache kline per TF (gak fetch ulang)
- `indicators/`  — SMI + FBF + ATR (engine aktif). Legacy di `archive/`
- `fetchers/`    — data fetcher Binance/Bybit
- `lib/`         — helper CLI (format/extract journal)
- `archive/`     — semua hasil lama (legacy backtest, indicators mati,
  journals v3, reports). FROZEN — jgn diutak-atik.

## Struktur
```
trading-research/
├─ README.md                 # ini
├─ TRADE_TEMPLATE.md         # work-tree concept (template trade)
├─ indicators/               # SMI/FBF/ATR (aktif)
├─ fetchers/                 # data fetcher (binance/bybit)
├─ lib/                      # helper scripts (format/extract)
├─ backtests/
│  └─ BTCUSDT/
│     └─ SETUP1/             # engine v2.b + spec + cache
│        ├─ 1D/  setup1_v2b_clean.py + data_1d.csv
│        ├─ 2H/  data_2h.csv
│        ├─ 4H/  data_4h.csv
│        ├─ fetch_data_tf.py
│        └─ TRIGGER_SPEC_v2b.md  ★
└─ archive/                  # FROZEN (legacy/old)
```

## Cara Tambah Pair / TF Baru
1. `mkdir -p backtests/PAIR/TF/`
2. Copy `setup1_v2b_clean.py` → ganti SYM + TF + path CSV.
3. Jalankan → hasil ke file lokal / chart.
4. Analisis mengikuti `TRADE_TEMPLATE.md`.

## Glossary Singkat
- RAW / GATED = mode filter sinyal.
- O1-O5 = opsi SL (Liq10x / C+ATR14 / ATR%30 / Fix6% / ConfHi+ATR).
- 1x/2x/3x = TP fixed (n× risk). TRAIL = trailing stop.
  RAWBRK/RAWTRL = FBF bear break (model user).
  ST_REV = Supertrend flip. EXP = expired.
- Lihat `TRADE_TEMPLATE.md` untuk penjelasan lengkap.
- Lihat `backtests/BTCUSDT/SETUP1/TRIGGER_SPEC_v2b.md` untuk
  spesifikasi ENTRY trigger v2.b (LOCKED).
