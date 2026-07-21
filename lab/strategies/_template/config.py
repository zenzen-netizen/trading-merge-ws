"""
Strategy config template.
Copy ke strategies/[nama_strategi]/config.py dan sesuaikan.

Semua parameter yang bisa di-tuning ada di sini.
Jangan ubah logic di rules.py — cukup ubah angka di sini.
"""

# ── Risk & Position ─────────────────────────────
RISK_PCT = 1.0             # % risk per trade dari modal
INITIAL_CAPITAL = 10000.0  # modal awal
FIXED_FRACTIONAL = True    # True = fixed fractional, False = compounding
DIRECTION = "short"        # "long" | "short"

# ── Stop Loss & Take Profit ─────────────────────
SL_METHOD = "fixed_pct"    # "fixed_pct" | "atr" | "structure"
SL_PCT = 6.0               # % jarak SL dari entry (kalau SL_METHOD = fixed_pct)
TP_MULTIPLIER = None       # None = no TP, 2.0 = 2x risk, 3.0 = 3x risk

# ── Trade Management ────────────────────────────
MAX_BARS = 240             # max bar posisi dibiarkan hidup
FEE_PCT = 0.1              # fee round-trip % (spot: 0.1, futures taker: 0.05)
SL_FIRST = True            # True = SL diasumsikan kena duluan (konservatif)

# ── Data ────────────────────────────────────────
SYMBOL = "BTCUSDT"
TIMEFRAME = "1d"
DATA_PATH = "data/raw/BTCUSDT_1d_latest.csv"  # override path atau None

# ── Metadata (versi + acuan) ───────────────────
VERSION = "v0"
CASE_STUDY_REF = ""        # e.g. "strategies/nama_strategi/case_studies/case_v1.md"
