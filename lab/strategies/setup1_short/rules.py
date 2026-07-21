"""
SETUP1 SHORT — Rules
Entry/exit logic untuk SETUP1 SHORT v3.

Trigger: FMB->PD->XDN dalam satu FBF bear wave (v3).
Exit:   TP standalone | ST_REV | RAWBRK (via config).

Shared module: indicators/python/setup1_trigger.py
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Set

# ── Shared trigger module ────────────────────────
from indicators.python.setup1_trigger import (
    detect_signals_v3,
    supertrend_full,
    sl_o1, sl_o3, sl_o6,
)

# ── Cache (lazy init, sekali per run) ────────────
_signal_bars: Optional[Set[int]] = None
_signal_data: Optional[list] = None
_df_ref: Optional[pd.DataFrame] = None


def _init_signals(df: pd.DataFrame):
    """Precompute sinyal SETUP1 v3 — cache bar index entry."""
    import config as cfg

    globals()["_df_ref"] = df

    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    close = df["close"].values.astype(float)

    # Supertrend
    st = supertrend_full(high, low, close, cfg.ST_PERIOD, cfg.ST_MULTIPLIER)

    # SMI state arrays — asumsi kolom udah ada
    E = {
        "FMB": df["SMI_FMB"].values.astype(bool),
        "PD": df["SMI_PD"].values.astype(bool),
        "XDN": df["SMI_XDN"].values.astype(bool),
    }

    # FBF events by bar — asumsi kolom event udah ada
    ev_by_bar: Dict[int, list] = {}
    if "FBF_EVENT" in df.columns:
        for i in range(len(df)):
            ev = df["FBF_EVENT"].iloc[i]
            if isinstance(ev, str) and ev:
                ev_by_bar[i] = [{"event": ev, "side": "bear"}]

    samples = detect_signals_v3(df, high, low, close, st, E, ev_by_bar)
    globals()["_signal_bars"] = {s["bar"] for s in samples}
    globals()["_signal_data"] = samples

    print(f"[setup1_short] Precomputed {len(samples)} signals ({len(_signal_bars)} unique bars)")


def entry_signal(df: pd.DataFrame, i: int) -> bool:
    """True kalau bar i adalah bar sinyal entry.

    Precompute sekali via detect_signals_v3(). Engine masuk di open bar i+1.
    """
    global _signal_bars, _df_ref
    if _signal_bars is None:
        _init_signals(df)
    return i in _signal_bars


def exit_signal(df: pd.DataFrame, i: int, position: Dict) -> bool:
    """Sinyal exit dinamis (diluar SL/TP fixed).

    - ST_REV: exit saat Supertrend flip -1 -> +1
    - RAWBRK: exit ketika rawbreak kena (complex, TODO)
    - TP standalone: return False (exit via SL/TP engine)
    """
    import config as cfg

    if cfg.EXIT_METHOD == "st_rev":
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        close = df["close"].values.astype(float)
        if i <= 0:
            return False
        st = supertrend_full(
            high[: i + 1], low[: i + 1], close[: i + 1],
            cfg.ST_PERIOD, cfg.ST_MULTIPLIER,
        )
        return len(st) > 1 and st[-2] == -1 and st[-1] == 1

    # RAWBRK — butuh tracking pivot + SL update, belum diimplementasikan
    # TP standalone — no dynamic exit
    return False


def sl_price(df: pd.DataFrame, i: int, entry_price: float) -> float:
    """SL price berdasarkan SL_METHOD di config."""
    import config as cfg
    from indicators.python.setup1_trigger import ATR_PCT_CFG

    if cfg.SL_METHOD == "liq10x":
        return sl_o1(entry_price)

    if cfg.SL_METHOD == "atr_pct":
        apct = _get_atr_pct(df, i, cfg)
        sl = sl_o3(entry_price, apct)
        if sl is None:
            return entry_price * 1.10  # fallback
        return sl

    if cfg.SL_METHOD == "atr_1d":
        apct = _get_atr_pct(df, i, cfg)
        sl = sl_o6(entry_price, apct)
        if sl is None:
            return entry_price * 1.10
        return sl

    # fallback
    return entry_price * 1.10


def tp_price(df: pd.DataFrame, i: int, entry_price: float) -> Optional[float]:
    """TP price — fixed multiplier dari risk."""
    import config as cfg

    if cfg.TP_MULTIPLIER is None:
        return None

    risk = abs(entry_price - sl_price(df, i, entry_price))
    if cfg.DIRECTION == "short":
        return entry_price - cfg.TP_MULTIPLIER * risk
    else:
        return entry_price + cfg.TP_MULTIPLIER * risk


# ── Helper ───────────────────────────────────────
def _get_atr_pct(df: pd.DataFrame, i: int, cfg) -> float:
    """ATR% pada bar i (current timeframe atau 1d anchor)."""
    from indicators.python.setup1_trigger import ATR_PCT_CFG

    if cfg.SL_ATR_TIMEFRAME == "1d":
        # butuh data 1d anchor — TODO: daily ATR lookup
        return _get_daily_atr_pct(i)

    # Current TF ATR%
    sub = df.iloc[: i + 1]
    if len(sub) < 2:
        return 1.0
    try:
        from indicators.legacy.atr_percentage import atr_percentage
        result = atr_percentage(sub, ATR_PCT_CFG)
        vals = result["atr_pct"]
        return float(vals.iloc[-1]) if len(vals) > 0 else 1.0
    except Exception:
        return 1.0


def _get_daily_atr_pct(i: int) -> float:
    """ATR% 1D anchor — placeholder, butuh daily df terpisah."""
    return 2.0  # TODO: implement daily anchor lookup
