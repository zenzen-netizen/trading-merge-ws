"""
ATR Percentage with Bollinger Bands — Python port of TradingView Pine Script.
Calculates ATR as % of close, then optionally wraps Bollinger Bands around
ATR% (or raw ATR) to detect volatility regimes.

Default params from Pine:
  ATRPeriods = 22
  useAtrAsPercent = True
  BBPeriods = 20
  StdDev = 2.0
"""

import pandas as pd
import numpy as np


def _rma(series, length):
    """Wilder's RMA (same as Pine's rma / atr built-in)."""
    return series.ewm(alpha=1 / length, adjust=False).mean()


def _sma(series, length):
    """Simple Moving Average."""
    return series.rolling(window=length, min_periods=length).mean()


def _stddev(series, length):
    """Population std dev (ddof=0) matching Pine's stdev()."""
    return series.rolling(window=length, min_periods=length).std(ddof=0)


def atr_percentage(df, cfg=None):
    """
    Calculate ATR Percentage (+ Bollinger Bands on ATR%).

    Args:
        df: DataFrame with columns ['high','low','close']
        cfg: dict with keys:
            atr_period (default: 22)
            use_atr_pct (default: True) — BB on atrPercent vs raw atr
            show_bb (default: True)
            bb_period (default: 20)
            bb_stddev (default: 2.0)

    Returns:
        dict with:
            atr: raw ATR value
            atr_pct: ATR as % of close
            bb_middle, bb_top, bb_bottom
            bb_width: band width (top - bottom)
            bb_width_pct: band width as % of price
            zone: "ABOVE_TOP", "INSIDE", "BELOW_BOTTOM", "NaN"
            position_pct: where atr_pct sits in [bottom, top], 0–100%
            atr_pct_mean: SMA of atr_pct over bb_period
            atr_pct_std: stddev of atr_pct over bb_period
    """
    if cfg is None:
        cfg = {}

    atr_period = cfg.get("atr_period", 30)
    use_atr_pct = cfg.get("use_atr_pct", True)
    show_bb = cfg.get("show_bb", True)
    bb_period = cfg.get("bb_period", 20)
    bb_stddev = cfg.get("bb_stddev", 2.0)

    high = df["high"]
    low = df["low"]
    close = df["close"]

    # --- True Range ---
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    # --- ATR ---
    atr = _rma(tr, atr_period)
    atr_val = atr.iloc[-1]
    close_val = close.iloc[-1]

    # --- ATR% ---
    atr_pct_series = (atr / close) * 100.0
    atr_pct_val = atr_pct_series.iloc[-1]

    result = {
        "atr": round(atr_val, 6),
        "atr_pct": round(atr_pct_val, 4),
    }

    # --- Bollinger Bands ---
    if show_bb:
        source = atr_pct_series if use_atr_pct else atr

        middle = _sma(source, bb_period)
        std = _stddev(source, bb_period)

        top = middle + bb_stddev * std
        bottom = middle - bb_stddev * std

        mid_val = middle.iloc[-1]
        top_val = top.iloc[-1]
        bot_val = bottom.iloc[-1]
        std_val = std.iloc[-1]

        result["bb_middle"] = round(mid_val, 4) if not np.isnan(mid_val) else None
        result["bb_top"] = round(top_val, 4) if not np.isnan(top_val) else None
        result["bb_bottom"] = round(bot_val, 4) if not np.isnan(bot_val) else None
        result["bb_std"] = round(std_val, 4) if not np.isnan(std_val) else None

        # Band width in same units (atr% or raw atr)
        bw = top_val - bot_val
        result["bb_width"] = round(bw, 4) if not np.isnan(bw) else None

        # Band width as % of price (useful for context)
        bw_pct = (bw / close_val * 100) if not use_atr_pct and close_val != 0 else bw
        result["bb_width_pct"] = round(bw_pct, 4) if not np.isnan(bw_pct) else None

        # Zone classification
        if np.isnan(atr_pct_val) or np.isnan(top_val) or np.isnan(bot_val):
            result["zone"] = "NaN"
            result["position_pct"] = None
        elif atr_pct_val > top_val:
            result["zone"] = "HIGH_VOL"  # ATR% above upper BB → high vol regime
        elif atr_pct_val < bot_val:
            result["zone"] = "LOW_VOL"  # ATR% below lower BB → low vol regime
        else:
            result["zone"] = "NORMAL"

        # Position within BB as 0-100%
        if not np.isnan(bw) and bw != 0 and not np.isnan(bot_val):
            pos = ((atr_pct_val - bot_val) / bw) * 100.0
            result["position_pct"] = round(pos, 1)
        else:
            result["position_pct"] = None

        # atr_pct mean & std (for reference)
        result["atr_pct_mean"] = round(mid_val, 4) if not np.isnan(mid_val) else None
        result["atr_pct_std"] = round(std_val, 4) if not np.isnan(std_val) else None
    else:
        result["bb_middle"] = None
        result["bb_top"] = None
        result["bb_bottom"] = None
        result["bb_width"] = None
        result["zone"] = "N/A"
        result["position_pct"] = None

    return result
