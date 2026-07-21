# SETUP1 DAILY — WORK-TREE NODE CONCEPT (FINAL)

Sumber naming: smi_pro.py (SMI Pro v3), fbf_v610.py (FBF v6.10), setup1_backtest_v3.py.
Cross-check ONLY — code belum diubah. RAWBRK model user BUTUH PATCH code.

KEPUTUSAN:
1. timezone     = WIB (Asia/Shanghai, UTC+8)
2. combo        = TETAP (3 slot: [SL_opt]+[exit_mekanik]+[TP_patok])
3. RAWBRK       = MODEL USER (trailing-anchor di high rawbreak) — PATCH NANTI
4. SMI          = FULL PATH (zone_path + hist_state + pa_pd)
5. FBF          = CATAT break_lvl (pivot low price)

================================================================
LEVEL 0 — TRADE (1 node per entry)
================================================================
id            : BTCUSDT-1D-20260708
pair/tf       : BTCUSDT / 1D
entry_price   : 62290.00
entry_date    : 2026-07-08
entry_time    : HH:MM  (WIB / UTC+8)
reason_entry  : lihat LEVEL 2a

================================================================
LEVEL 1 — EXIT
================================================================
exit_date     : 2026-07-09
exit_time     : HH:MM  (WIB / UTC+8)
outcome_state : HIT | SL | EXP | TRAIL_HIT     # hasil, PISAH dari reason
R             : +0.138
bars_held     : 1

OUTCOME_PER_COMBO:
  (tiap combo dari 1 entry, hasil akhir + reason trigger)
  format: [KODE] → OUTCOME (R) reason
  contoh Trade2 2026-06-17:
    O1+TP1x   → TP        (+1.000R)  TP1x kena
    O1+TRAIL  → TRAIL_HIT (+0.002R)  trail_stop touch bar-1
    O1+STREV  → EXP       (+0.435R)  ST gak flip
    O1+RAWBRK → EXP       (+0.435R)  rawbreak gak trigger
    O2+TP1x   → TP        (+1.000R)
    O2+TRAIL  → TRAIL_HIT (+0.003R)
    O2+STREV  → EXP       (+0.514R)
    O2+RAWBRK → EXP       (+0.514R)
    O3+TP1x   → TP        (+1.000R)
    O3+TP2x   → TP        (+2.000R)
    O3+TRAIL  → TRAIL_HIT (+0.007R)
    O3+STREV  → EXP       (+1.219R)
    O3+RAWBRK → EXP       (+1.219R)
    O4+TP1x   → TP        (+1.000R)
    O4+TRAIL  → TRAIL_HIT (+0.004R)
    O4+STREV  → EXP       (+0.724R)
    O4+RAWBRK → EXP       (+0.724R)
    O5+TP1x   → TP        (+1.000R)
    O5+TRAIL  → TRAIL_HIT (+0.003R)
    O5+STREV  → EXP       (+0.609R)  ST gak flip, TP2x gak kena, expire +4.35%
    O5+RAWBRK → EXP       (+0.609R)
  (Trade1 2026-07-08: semua EXP R kecil, bars=1, gak ada yg trigger)

IN_RANGE_EFF (Range Occupancy / Time-in-Range Efficiency):
  (proporsi waktu price berada di zona SL↔TP vs nyentuh salah satu)
  bars_total    : 22
  bars_inrange  : 18  (price di antara SL & TP, gak trigger)
  bars_slzone   : 2   (price dekat SL-side, rawan rugi)
  bars_tpzone   : 2   (price dekat TP-side, rawan menang)
  time_inrange % : 81.8%   (18/22)
  time_slzone  % : 9.1%
  time_tpzone  % : 9.1%
  sl_zone_width % : 7.14%   (jarak entry→SL, O5)
  tp_zone_width % : 14.28%  (jarak entry→TP2x)
  eff_ratio     : time_inrange / (sl%+tp%) = 81.8 / 21.42 = 3.82
                  (tinggi = lama ngurung, gak effisien;
                   rendah = cepet kena TP/SL)
  # Contoh Trade1 2026-07-08 (bars=1): semua zone = 1 bar,
  # time_inrange 100%, eff_ratio tinggi (gak sempat gerak).

================================================================
LEVEL 2a — REASON_ENTRY (istilah resmi dari code)
================================================================
smi (SMI Pro v3) — FULL PATH:
  zone_path   : OB Zone → Upper Normal → Middle → Lower Normal → OS Zone
  at_entry    : cross_down (confirm)   # %K cross di bawah %D
  hist_state  : Shr Bear | Exp Bear     # momentum quality
  vs_ema      : Bear
  pa_pd       : pa_ready | pa_dip       # akumulasi sebelum move
  failed_mid  : failed_mid_sell (opt)
fbf (FBF v6.10):
  state       : bear_active = True      # persist lock (state machine)
  break_lvl   : <pivot low price>       # ATR×0.15 buffer — DICATAT
  persist     : req_n bars beyond B      # confirm
combo_entry  : "SMI:cross_down + FBF:bear_active"

# Entry short phase progression (resmi):
#   SMI : Upper Normal → cross_down → Middle → Lower Normal
#   FBF : bull_active → bear break → bear_active lock (persist)

================================================================
LEVEL 2b — REASON_EXIT (tree)
================================================================
├─ SL_OPTS (catat semua utk compare, pilih 1 per run)
│    O1 Liq10x     | lvl | sl_pct (jarak SL←entry)
│    O2 C+ATR14    | lvl | sl_pct
│    O3 ATR%30     | lvl | sl_pct
│    O4 Fix6%      | lvl | sl_pct
│    O5 ConfHi+ATR | lvl | sl_pct
│
├─ TP_OPTS (jarak entry→TP)
│    1x | tgt | tp_pct
│    2x | tgt | tp_pct
│    3x | tgt | tp_pct
│    R:R implied = tp_pct / sl_pct
│
├─ TRAIL_OPTS
│    pre-trigger  : TP 1x/2x/3x jalan (patok)
│    activation   : entry × (1 − atr%/2)
│    trail_stop   : lowest × (1 + atr_pct/100)   # buffer = atr% PENUH
│    lowest       : titik terendah saat aktif
│    post-trigger : trailing ambil alih, exit pas high touch stop
│    triggered    : Y | N
│
├─ RAWBRK_OPTS (MODEL USER — trailing-anchor)
│    pre-trigger  : TP patok jalan
│    trigger      : candle rawbreak CONFIRM muncul
│    anchor_high  : HIGH candle rawbreak = SL trailing start
│    trail_logic  : SL ngikut high rawbreak, jalan terus
│    exit_rule    : exit pas ada candle HILANG tanda rawbreak
│                  (atau SL trailing kena)
│    break_lvl    : <pivot low price> (FBF bear break ref)
│    triggered    : Y | N
│    NOTE        : CODE V3 SUDAH model user (confirmed line 426-451:
                 bear_active_high = rolling max high saat break aktif,
                 exit pas break hilang = "RAWBRK", trail kena = "RAWTRL").
                 Journal: 1101 RAWBRK + 146 RAWTRL. NO PATCH NEEDED.
│
├─ ST_REV_OPTS (Supertrend)
│    pre-trigger  : TP patok jalan
│    flip_lvl     : ST -1 → +1
│    triggered    : Y | N
│    post-trigger : exit di flip
│
└─ COMBO (TETAP 3 slot)
     format: [SL_opt] + [exit_mekanik] + [TP_patok pre-trigger]
     FUNGSI: "resep" 1 trade — tentukan SL mana,
             mekanik EXIT mana (TRAIL/RAWBRK/ST_REV/TP),
             TP patok berapa (1x/2x/3x) SEBELUM mekanik exit trigger.
     Contoh: O5 + ST_REV + TP2x
       = SL ConfHi+ATR, exit utama nunggu ST flip (-1→+1),
         TP2x (-14.28%) patok sebelum flip — kalau price
         sampe TP2x duluan = menang, kalau ST flip duluan = exit di flip.
     Contoh2: O3 + RAWBRK(model user) + TP1x
       = SL ATR%30, exit pas rawbreak trail habis,
         sebelum rawbreak TP1x patok jalan.

================================================================
GLOSSARY — ISTILAH & SINGKATAN
================================================================
ENTRY / POSITION
  entry_price  : harga masuk (close bar confirm)
  entry_date   : tanggal bar entry (1D)
  entry_time   : jam menit close bar (WIB)
  pair/tf      : simbol + timeframe (BTCUSDT / 1D)

SMI Pro v3 (smi_pro.py)
  zone_path    : lintasan zona SMI (OB→Upper→Middle→Lower→OS)
  cross_down   : %K cross di bawah %D = sinyal bear confirm (XDown)
  cross_up     : %K cross di atas %D = sinyal bull
  hist_state   : Exp Bull / Shr Bull / Shr Bear / Exp Bear (momentum)
  vs_ema       : Bull / Bear (SMI vs EMA-nya)
  pa_pd        : pa_ready / pa_dip = akumulasi (PA) / distribusi (PD)
  failed_mid   : failed_mid_buy / failed_mid_sell (gagal hold di mid)
  OB / OS      : OverBought / OverSold zone

FBF v6.10 (fbf_v610.py)
  bear_active  : state machine lock bear (persist)
  bull_active  : state machine lock bull
  break_lvl    : harga pivot low yang di-break (ATR×0.15 buffer)
  persist      : req_n bar konfirmasi lewat break (anti false)
  pivot        : titik high/low ekstrem (find_pivots)

EXIT
  outcome_state: HIT (TP kena) | SL (stop kena) | EXP (kadaluarsa) |
                 TRAIL_HIT (trailing stop kena)
  EXP          : EXPIRED — posisi gak kena SL/TP/mekanik dalam
                 window max 240 bar, tutup paksa di bar terakhir.
                 R kecil positif/negatif = sisa gerak price.
  R            : Return relatif thd risk. R=+1 = menang 1× risk.
                 R=-1 = rugi 1× risk (SL).
  bars_held    : jumlah bar posisi dibiarin hidup

EXIT MECHANICS
  SL           : Stop Loss — keluar pas price sentuh level (rugi)
  TP           : Take Profit — target fixed (1x/2x/3x = n× risk)
  TRAIL        : Trailing stop — stop ngikut price, lock profit
  RAWBRK       : Raw break — exit pas FBF bear break trigger
                 (model user: trailing anchor di high rawbreak)
  ST_REV       : Supertrend reversal — exit pas ST flip -1→+1
  COMBO        : resep [SL]+[exit_mekanik]+[TP_patok] per trade

SL OPTIONS (O1-O5)
  O1 Liq10x    : SL 10% di atas entry (liquidation-style wide)
  O2 C+ATR14   : SL = Close + ATR(14)
  O3 ATR%30    : SL = ATR% × 30 (tight)
  O4 Fix6%     : SL fix 6%
  O5 ConfHi+ATR: SL = Confirm high + ATR

MISC
  WIB          : Waktu Indonesia Barat (UTC+8)
  atr%         : ATR sebagai % dari price
  risk         : SL - entry (jarak stop, positif utk short)
  R:R          : Reward:Risk = tp_pct / sl_pct

IN_RANGE_EFF (Range Occupancy / Time-in-Range Efficiency)
  bars_total   : total bar posisi hidup
  bars_inrange : bar price di antara SL & TP (gak nyentuh level)
  bars_slzone  : bar price dekat SL-side (rawan rugi)
  bars_tpzone  : bar price dekat TP-side (rawan menang)
  time_inrange % : % bar di in-range = bars_inrange/bars_total
  time_slzone  % : % bar di SL-zone
  time_tpzone  % : % bar di TP-zone
  sl_zone_width % : jarak % entry→SL
  tp_zone_width % : jarak % entry→TP (patok)
  eff_ratio    : time_inrange / (sl%+tp%)
                tinggi = lama ngurung, gak effisien
                rendah = cepet kena TP/SL
  SL_ZONE      : bagian dekat SL (rawan rugi)
  TP_ZONE      : bagian dekat TP (rawan menang)
  ZONE_WIDTH   : jarak % entry→level

================================================================
NEXT ACTION
================================================================
- RAWBRK: CODE SUDAH model user (confirmed). NO PATCH.
- Optional: extract RAWBRK trace buat 2 trade terakhir (bear_active
  start bar, anchor_high, exit level) buat bukti visual di concept.
- Optional: journal CSV tambah kolom exit_price + triggered + break_lvl
  utk cross-check chart lebih gampang.
