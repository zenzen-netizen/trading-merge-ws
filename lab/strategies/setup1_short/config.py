"""
SETUP1 SHORT — Config
Strategi short BTCUSDT: FBF bear wave + SMI distribution + Supertrend gate.

Trigger logic: FMB → PD → XDN dalam satu wave (v3).
Exit: TP stand-alone (1x/2x/3x), ST_REV (TP3x), RAWBRK (TP3x + raw break).

Referensi: trading-research/backtests/BTCUSDT/SETUP1/
"""

# ── Risk & Position ─────────────────────────────
RISK_PCT = 1.0
INITIAL_CAPITAL = 10000.0
FIXED_FRACTIONAL = True
DIRECTION = "short"

# ── Stop Loss Methods ────────────────────────────
# O1 = Liq10x     — entry * 1.10
# O3 = ATR%30     — entry * (1 + apct/100)
# O6 = ATR%1D     — entry * (1 + daily_apct/100)
SL_METHOD = "atr_pct"       # "liq10x" | "atr_pct" | "atr_1d"
SL_ATR_TIMEFRAME = "current" # "current" | "1d" (untuk O3/O6)
ATR_PERIOD = 30
USE_ATR_PCT = True
SHOW_BB = True
BB_PERIOD = 20
BB_STDDEV = 2.0

# ── Exit Methods ─────────────────────────────────
EXIT_METHOD = "tp_standalone"  # "tp_standalone" | "st_rev" | "rawbrk"
TP_MULTIPLIER = 1.0            # 1.0 = 1x risk, 2.0 = 2x, 3.0 = 3x
MAX_BARS = 240

# ── SL/TP dalam satu bar ─────────────────────────
SL_FIRST = True    # True = konservatif (SL duluan)

# ── FBF Config ───────────────────────────────────
FBF_PERIOD = 5     # lookback untuk fractal
FBF_STRICT = True  # FBF v11 strict mode

# ── SMI Config ───────────────────────────────────
SMI_K = 5
SMI_D = 3
SMI_E = 3
SMI_OB = 80
SMI_MID = 0
SMI_OS = -40

# ── Supertrend Config ────────────────────────────
ST_PERIOD = 10
ST_MULTIPLIER = 3.0

# ── Data ─────────────────────────────────────────
SYMBOL = "BTCUSDT"
TIMEFRAME = "1d"
DATA_PATH = None  # None = otomatis dari SYMBOL+TIMEFRAME

# ── Metadata ─────────────────────────────────────
VERSION = "v3"
CASE_STUDY_REF = "strategies/setup1_short/case_studies/"
