"""
SETUP1 SHORT B — Config
SHORT, multi position: entry di SETIAP wave valid tanpa nunggu posisi clear.
Satu cluster wave bisa menghasilkan >1 posisi parallel.

Trigger: FMB->PD->XDN dalam satu wave (v3).
Exit: TP standalone, ST_REV, RAWBRK.

Root: setup1_short_a — bedanya cuma di rules (no 1-wave-1-position gate).
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
SL_ATR_TIMEFRAME = "current" # "current" | "1d"
ATR_PERIOD = 30
USE_ATR_PCT = True
SHOW_BB = True
BB_PERIOD = 20
BB_STDDEV = 2.0

# ── Exit Methods ─────────────────────────────────
EXIT_METHOD = "tp_standalone"  # "tp_standalone" | "st_rev" | "rawbrk"
TP_MULTIPLIER = 1.0
MAX_BARS = 240

# ── SL/TP dalam satu bar ─────────────────────────
SL_FIRST = True

# ── FBF Config ───────────────────────────────────
FBF_PERIOD = 5
FBF_STRICT = True

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
DATA_PATH = None

# ── Metadata ─────────────────────────────────────
VERSION = "v3"
CASE_STUDY_REF = "strategies/setup1_short_b/case_studies/"
