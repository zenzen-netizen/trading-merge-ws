# SETUP 1 — SHORT (FBF AB + SMI Confluence)

Market  : Binance Perp Futures, isolated margin, 10x leverage
TF      : Daily (1D)
Data tes: spot (diabaikan bedanya dgn perp)

## FLOW & ALUR

### PHASE 1 — FBF AB CONFIRM (Bear)
- FBF deteksi A (swing high) lalu close break pivot low B
- B valid setelah 3-bar confirmation
- Status -> TRACKING C
- TIDAK BOLEH entry sebelum masuk fase ini

### PHASE 2 — TRACKING C (Pullback)
- Harga pullback NAIK, bentuk C (higher pivot)
- Pantau SMI daily tiap close
- Entry HANYA lewat SMI 3-step di bawah

### PHASE 3 — SMI 3-STEP (wajib urut)
- STEP 1 (Tanda 1): SMI = "! Fail MID Buy"
    -> SMI cross ke atas 0, belum kuat = bounce pertama di pullback C
- STEP 2 (Tanda 2): SMI = "PD jenis apapun"
    ("~ PD - Dip Mungkin" / "PD - Siap Balik" / "PD - Yakin Balik" / dst)
    -> C hampir matang, dip siap balik
- STEP 3 (TRIGGER): SMI = "X Cross DN" + CONFIRM
    (close cross DOWN di bawah EMA)
    -> C SELESAI, momentum balik bear

### PHASE 4 — ENTRY
- SHORT di CLOSE bar X Cross DN terkonfirmasi
- Instrumen: Perp isolated 10x
- Contoh kasus (BTCUSDT 2026):
    12 Jun Fail MID Buy (11.6)
    13 Jun PD Dip Mungkin (33.2)
    14-16 Jun S Bias Atas (C naik 65-66k)
    17 Jun X Cross DN (35.3) -> ENTRY ~64,509

### PHASE 5 — STOP LOSS (4 opsi)
- OPSI 1 (Liq-based): SL = liquidation price saat 10x full margin used
    SHORT: rugi kalau harga NAIK -> liq di ATAS entry
    Rumus Binance USDⓈ-M isolated:
      LiqPrice = Entry * (1 + 1/Lev) / (1 + MMR)
      MMR (maintenance margin rate) ~0.5% utk 10x
    Contoh E=64,509, Lev=10, MMR=0.005:
      Liq = 64,509 * 1.1 / 1.005 = 70,607 (di atas entry)
    SL ditaruh di BAWAH liq biar gak kena liquidation:
      SL = 70,500 (≈9.3% di atas)
    TP = 1:1 -> 64,509 - (70,500-64,509) = 58,518 (di bawah)
    Note: E*1.1 (70,960) itu aproksimasi kasar, liq asli 70,607
- OPSI 2 (C + ATR): SL = C_high + ATR(period default)
    C_high = high bar C (15 Jun = 67,292)
    ATR = atr_value saat entry
- OPSI 3 (ATR%): SL = entry + (atr_pct% dari close) sebagai offset
    atr_pct = atr_percentage(df).atr_pct (dalam %)
    SL = entry * (1 + atr_pct/100)  [untuk short, SL di atas]
- OPSI 4 (Fix %): SL = entry * 1.06 (fix 6% di atas entry)

### PHASE 6 — TAKE PROFIT
- TP = 1:1 terhadap SL distance
- TP = entry - (SL - entry)  [untuk short]
- TP = entry - (entry - SL) = 2*entry - SL
- Contoh OPSI 4 (SL = entry*1.06):
    entry 64,509 -> SL 68,380 (dist +3,871)
    TP = 64,509 - 3,871 = 60,638 (dist -3,871) = 1:1

### RISK NOTE (10x isolated)
- Move adverse = 10x lipat vs margin
- Position sizing: SL hit = risk tolerable, BUKAN liquidation
- OPSI 1 (liq SL) = paling agresif, OPSI 4 (fix 6%) = paling konservatif

## BACKTEST PLAN
1. Scan semua historical BTCUSDT daily cari FBF AB + SMI 3-step
2. Untuk tiap opsi SL, hitung: win rate, R-multiple, max DD
3. Bandingkan OPSI 1 vs 2 vs 3 vs 4 -> pilih terbaik
4. TP bisa disesuaikan (1:1 / 1:1.5 / 1:2) setelah lihat hasil
