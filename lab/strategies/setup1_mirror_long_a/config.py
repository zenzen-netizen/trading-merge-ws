"""
SETUP1 MIRROR LONG A — Config
LONG (counter-trend), 1 posisi per wave.
Trigger IDENTIK setup1_short_a: FBF bear wave + SMI FMB->PD->XDN + ST DOWN.
Cuma arah dibalik: entry bearish exhaustion → buka LONG (reversal play).

SL di BAWAH entry, TP di ATAS entry (mirror dari SHORT).

Root: setup1_short_a — beda cuma di DIRECTION + formula SL/TP mirror.
"""

# ── Risk & Position ─────────────────────────────
RISK_PCT = 1.0
INITIAL_CAPITAL = 10000.0
FIXED_FRACTIONAL = True
DIRECTION = "long"

# ── Stop Loss Methods ────────────────────────────
# O1 = Liq10x     — entry * 0.90 (mirror)
# O3 = ATR%30     — entry * (1 - apct/100) (mirror)
# O6 = ATR%1D     — entry * (1 - daily_apct/100) (mirror)
SL_METHOD = "atr_pct"
SL_ATR_TIMEFRAME = "current"
ATR_PERIOD = 30
USE_ATR_PCT = True
SHOW_BB = True
BB_PERIOD = 20
BB_STDDEV = 2.0

# ── Exit Methods ─────────────────────────────────
EXIT_METHOD = "tp_standalone"
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
VERSION = "v3 (mirror)"
CASE_STUDY_REF = "strategies/setup1_mirror_long_a/case_studies/"
