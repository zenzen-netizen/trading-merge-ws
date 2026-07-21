"""
SETUP1 MIRROR LONG A — Rules
LONG (counter-trend), 1 posisi per wave.
Trigger IDENTIK setup1_short_a: FBF bear + SMI FMB->PD->XDN + ST DOWN.
Yang berubah: arah posisi — SL di bawah entry, TP di atas entry.

Mirror rules:
  SHORT: sl = entry * (1 + pct), tp = entry - risk*n
  LONG:  sl = entry * (1 - pct), tp = entry + risk*n
  ST_REV: exit saat ST flip +1 -> -1 (instead of -1 -> +1)
  RAWBRK: close > lastPivotHigh, SL = LOW candle
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Set

from indicators.python.setup1_trigger import (
    detect_signals_v3,
    supertrend_full,
    sl_o1, sl_o3, sl_o6,
)

_signal_bars: Optional[Set[int]] = None
_df_ref: Optional[pd.DataFrame] = None


def _init_signals(df: pd.DataFrame):
    """Precompute sinyal — IDENTIK dengan setup1_short_a."""
    import config as cfg
    globals()["_df_ref"] = df

    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    close = df["close"].values.astype(float)

    st = supertrend_full(high, low, close, cfg.ST_PERIOD, cfg.ST_MULTIPLIER)
    E = {
        "FMB": df["SMI_FMB"].values.astype(bool),
        "PD":  df["SMI_PD"].values.astype(bool),
        "XDN": df["SMI_XDN"].values.astype(bool),
    }
    ev_by_bar: Dict[int, list] = {}
    if "FBF_EVENT" in df.columns:
        for i in range(len(df)):
            ev = df["FBF_EVENT"].iloc[i]
            if isinstance(ev, str) and ev:
                ev_by_bar[i] = [{"event": ev, "side": "bear"}]

    # Trigger IDENTIK short_a — sinyal bearish exhaustion yang SAMA
    samples = detect_signals_v3(df, high, low, close, st, E, ev_by_bar)

    globals()["_signal_bars"] = {s["bar"] for s in samples}
    print(f"[setup1_mirror_long_a] Precomputed {len(samples)} signals ({len(_signal_bars)} unique bars)")


def entry_signal(df: pd.DataFrame, i: int) -> bool:
    """True kalau bar i sinyal entry — IDENTIK short_a."""
    global _signal_bars
    if _signal_bars is None:
        _init_signals(df)
    return i in _signal_bars


def exit_signal(df: pd.DataFrame, i: int, position: Dict) -> bool:
    """Sinyal exit dinamis — ST_REV flip (LONG: +1 -> -1)."""
    import config as cfg

    if cfg.EXIT_METHOD == "st_rev":
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        close = df["close"].values.astype(float)
        if i <= 0: return False
        st = supertrend_full(
            high[:i+1], low[:i+1], close[:i+1],
            cfg.ST_PERIOD, cfg.ST_MULTIPLIER,
        )
        # LONG: exit saat ST flip +1 -> -1 (dari uptrend ke downtrend)
        return len(st) > 1 and st[-2] == 1 and st[-1] == -1

    return False


def sl_price(df: pd.DataFrame, i: int, entry_price: float) -> float:
    """SL price — LONG, di BAWAH entry."""
    import config as cfg
    from indicators.python.setup1_trigger import ATR_PCT_CFG

    pct = 10.0

    if cfg.SL_METHOD == "liq10x":
        # Mirror O1: entry * 0.90
        return entry_price * 0.90

    if cfg.SL_METHOD == "atr_pct":
        apct = _get_atr_pct(df, i, cfg)
        if apct is not None and not np.isnan(apct) and apct > 0:
            return entry_price * (1 - apct / 100.0)
        return entry_price * 0.90

    if cfg.SL_METHOD == "atr_1d":
        apct = _get_atr_pct(df, i, cfg)
        if apct is not None and not np.isnan(apct) and apct > 0:
            return entry_price * (1 - apct / 100.0)
        return entry_price * 0.90

    return entry_price * 0.90


def tp_price(df: pd.DataFrame, i: int, entry_price: float) -> Optional[float]:
    """TP price — LONG, di ATAS entry."""
    import config as cfg

    if cfg.TP_MULTIPLIER is None:
        return None

    risk = abs(entry_price - sl_price(df, i, entry_price))
    # LONG: tp = entry + risk * multiplier
    return entry_price + cfg.TP_MULTIPLIER * risk


def _get_atr_pct(df: pd.DataFrame, i: int, cfg) -> float:
    from indicators.python.setup1_trigger import ATR_PCT_CFG
    if cfg.SL_ATR_TIMEFRAME == "1d":
        return _get_daily_atr_pct(i)
    sub = df.iloc[:i+1]
    if len(sub) < 2: return 1.0
    try:
        from indicators.python.atr_percentage import atr_percentage
        result = atr_percentage(sub, ATR_PCT_CFG)
        vals = result["atr_pct"]
        return float(vals.iloc[-1]) if len(vals) > 0 else 1.0
    except Exception:
        return 1.0


def _get_daily_atr_pct(i: int) -> float:
    return 2.0  # TODO: daily ATR anchor
