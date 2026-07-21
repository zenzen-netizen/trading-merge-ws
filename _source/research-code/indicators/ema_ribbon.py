"""
EMA Ribbon Pro — Python port of TradingView Pine Script indicator.
Calculates 12 MAs (8 short + 4 long), trend classification, ribbon strength,
alignment, volatility, ATR SL, and verdict.
"""

import pandas as pd
import numpy as np


def _hma(series, length):
    """Hull MA"""
    half = max(1, round(length / 2))
    sqrtl = max(1, round(np.sqrt(length)))
    wma_half = series.rolling(window=half).apply(
        lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1)),
        raw=True
    )
    wma_full = series.rolling(window=length).apply(
        lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1)),
        raw=True
    )
    wma_result = (2 * wma_half - wma_full).rolling(window=sqrtl).apply(
        lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1)),
        raw=True
    )
    return wma_result


def _dema(series, length):
    """Double EMA"""
    e = series.ewm(span=length, adjust=False).mean()
    return 2 * e - e.ewm(span=length, adjust=False).mean()


def _tema(series, length):
    """Triple EMA"""
    e1 = series.ewm(span=length, adjust=False).mean()
    e2 = e1.ewm(span=length, adjust=False).mean()
    e3 = e2.ewm(span=length, adjust=False).mean()
    return 3 * e1 - 3 * e2 + e3


def _rma(series, length):
    """Wilder's RMA (same as ATR calc)"""
    return series.ewm(alpha=1/length, adjust=False).mean()


def _kama_calc(series, length):
    """Kaufman Adaptive MA"""
    values = series.values
    result = np.empty_like(values, dtype=float)
    result[0] = values[0]
    
    fast_sc = 2.0 / 3.0
    slow_sc = 2.0 / 31.0
    
    for i in range(1, len(values)):
        if i < length:
            result[i] = values[i]
            continue
        
        direction = abs(values[i] - values[i - length])
        noise = np.sum(np.abs(values[i-length+1:i+1] - values[i-length:i]))
        if noise != 0:
            er = direction / noise
        else:
            er = 0.0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        result[i] = result[i-1] + sc * (values[i] - result[i-1])
    
    return pd.Series(result, index=series.index)


def _get_ma(series, length, ma_type):
    """Get MA by type"""
    if ma_type == "SMA":
        return series.rolling(window=length).mean()
    elif ma_type == "EMA":
        return series.ewm(span=length, adjust=False).mean()
    elif ma_type == "WMA":
        return series.rolling(window=length).apply(
            lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1)),
            raw=True
        )
    elif ma_type == "RMA":
        return _rma(series, length)
    elif ma_type == "HMA":
        return _hma(series, length)
    elif ma_type == "DEMA":
        return _dema(series, length)
    elif ma_type == "TEMA":
        return _tema(series, length)
    elif ma_type == "KAMA":
        return _kama_calc(series, length)
    else:
        return series.ewm(span=length, adjust=False).mean()


def _mad(series, length):
    """Approx Median Absolute Deviation via SMA"""
    sma = series.rolling(window=length).mean()
    return (series - sma).abs().rolling(window=length).mean()


def ema_ribbon_pro(df, cfg):
    """
    Calculate EMA Ribbon Pro indicator.
    
    Returns dict with:
        trend_label, trend_emoji, ribbon_strength, long_strength,
        alignment, divergence_pct, volatility_label, atr_label,
        verdict, long_sl, short_sl, ma_values (dict of all MAs),
        aligned_bull, aligned_bear
    """
    ma_type = cfg.get("ma_type", "EMA")
    short_lens = cfg.get("short_lens", [20, 25, 30, 35, 40, 45, 50, 55])
    long_lens = cfg.get("long_lens", [100, 200, 300, 365])
    show_long = cfg.get("show_long_ma", True)
    
    trend_method = cfg.get("trend_method", "Ribbon Divergence")
    div_bull_strong = cfg.get("div_bull_strong", 3.0)
    div_bull_weak = cfg.get("div_bull_weak", 1.0)
    div_overext_mult = cfg.get("div_overext_mult", 5.0)
    use_atr_filter = cfg.get("use_atr_filter", False)
    atr_sl_mult = cfg.get("atr_sl_mult", 1.5)
    dev_mult = cfg.get("dev_mult", 1.0)
    dev_period = cfg.get("dev_period", 20)
    use_mad = cfg.get("use_mad", True)
    
    close = df["close"]
    high = df["high"]
    low = df["low"]
    
    # Calculate all MAs
    short_mAs = []
    for l in short_lens:
        short_mAs.append(_get_ma(close, l, ma_type))
    
    long_mAs = []
    if show_long:
        for l in long_lens:
            long_mAs.append(_get_ma(close, l, ma_type))
    
    # Latest values
    short_vals = [m.iloc[-1] for m in short_mAs]
    long_vals = [m.iloc[-1] for m in long_mAs] if show_long else []
    
    ma_dict = {}
    for i, l in enumerate(short_lens):
        ma_dict[f"ma{i+1}"] = round(short_vals[i], 4) if not np.isnan(short_vals[i]) else None
    if show_long:
        for i, l in enumerate(long_lens):
            ma_dict[f"ma{9+i}"] = round(long_vals[i], 4) if not np.isnan(long_vals[i]) else None
    
    price = close.iloc[-1]
    
    # --- Ribbon Divergence ---
    ma1_val = short_vals[0]
    ma12_val = long_vals[3] if show_long and len(long_vals) >= 4 else None
    div_pct = 0.0
    if ma12_val and ma12_val != 0:
        div_pct = (ma1_val - ma12_val) / ma12_val * 100.0
    overext_thresh = div_bull_strong * div_overext_mult
    
    # --- ATR ---
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = _rma(tr, 14)
    atr_val = atr.iloc[-1]
    sl_dist = atr_val * atr_sl_mult
    long_sl = price - sl_dist
    short_sl = price + sl_dist
    
    # --- Volatility (self-calibrating) ---
    dev_raw = _mad(close, dev_period) if use_mad else close.rolling(window=dev_period).std()
    dev = dev_raw * dev_mult
    dev_val = dev.iloc[-1]
    
    dev_pct = (dev_val / price * 100) if price != 0 else 0
    atr_pct = (atr_val / price * 100) if price != 0 else 0
    
    norm_len = max(2, dev_period * 2)
    dev_pct_series = (dev / close * 100).replace(0, np.nan)
    atr_pct_series = (atr / close * 100).replace(0, np.nan)
    dev_pct_avg = dev_pct_series.rolling(window=norm_len).mean()
    atr_pct_avg = atr_pct_series.rolling(window=norm_len).mean()
    
    dev_ratio = (dev_pct / dev_pct_avg.iloc[-1]) if dev_pct_avg.iloc[-1] != 0 else 1.0
    atr_ratio = (atr_pct / atr_pct_avg.iloc[-1]) if atr_pct_avg.iloc[-1] != 0 else 1.0
    
    def vol_label(ratio):
        if ratio < 0.7:
            return "RENDAH", "🔵"
        elif ratio > 1.3:
            return "TINGGI", "🔴"
        else:
            return "NORMAL", "🟡"
    
    dev_vol_label, dev_vol_emoji = vol_label(dev_ratio)
    atr_vol_label, atr_vol_emoji = vol_label(atr_ratio)
    
    # --- ATR trend filter ---
    atr_sma = atr.rolling(window=20).mean()
    is_trending = atr_val > atr_sma.iloc[-1]
    
    # --- Trend label ---
    if use_atr_filter and not is_trending:
        trend_label = "Ranging ↔"
        trend_emoji = "↔️"
    elif trend_method == "MA200 Cross":
        ma10_val = long_vals[1] if len(long_vals) >= 2 else None
        if ma10_val and price >= ma10_val:
            trend_label = "Bullish ▲"
            trend_emoji = "🟢"
        else:
            trend_label = "Bearish ▼"
            trend_emoji = "🔴"
    elif trend_method == "Ribbon Divergence":
        if div_pct >= overext_thresh:
            trend_label = "OverExt ▲▲▲"
            trend_emoji = "🔺"
        elif div_pct >= div_bull_strong:
            trend_label = "Strong Bull ▲▲"
            trend_emoji = "🟢"
        elif div_pct >= div_bull_weak:
            trend_label = "Bull ▲"
            trend_emoji = "🟢"
        elif div_pct <= -overext_thresh:
            trend_label = "OverExt ▼▼▼"
            trend_emoji = "🔻"
        elif div_pct <= -div_bull_strong:
            trend_label = "Strong Bear ▼▼"
            trend_emoji = "🔴"
        elif div_pct <= -div_bull_weak:
            trend_label = "Bear ▼"
            trend_emoji = "🔴"
        else:
            trend_label = "Choppy ↔"
            trend_emoji = "↔️"
    elif trend_method == "Short vs Long Ribbon":
        avg_short = sum(short_vals) / len(short_vals)
        avg_long = sum(long_vals) / len(long_vals) if long_vals else avg_short
        if avg_short >= avg_long:
            trend_label = "Bullish ▲"
            trend_emoji = "🟢"
        else:
            trend_label = "Bearish ▼"
            trend_emoji = "🔴"
    elif trend_method == "Ribbon Alignment":
        aligned_bull_val = all(short_vals[i] > short_vals[i+1] for i in range(len(short_vals)-1))
        aligned_bear_val = all(short_vals[i] < short_vals[i+1] for i in range(len(short_vals)-1))
        if aligned_bull_val:
            trend_label = "Strong Bull ▲▲"
            trend_emoji = "🟢"
        elif aligned_bear_val:
            trend_label = "Strong Bear ▼▼"
            trend_emoji = "🔴"
        else:
            trend_label = "Choppy ↔"
            trend_emoji = "↔️"
    else:
        trend_label = "N/A"
        trend_emoji = "❓"
    
    # --- Alignment ---
    aligned_bull = all(short_vals[i] > short_vals[i+1] for i in range(len(short_vals)-1))
    aligned_bear = all(short_vals[i] < short_vals[i+1] for i in range(len(short_vals)-1))
    
    # --- Ribbon strength (short) ---
    strength_count = sum(1 for v in short_vals if price > v)
    ribbon_strength = (strength_count / len(short_vals)) * 100.0
    
    # --- Long strength ---
    long_str_count = sum(1 for v in long_vals if price > v) if show_long else 0
    
    # --- Contextual short strength ---
    is_bull_ctx = "Bull" in trend_label or "bullish" in trend_label.lower()
    is_bear_ctx = "Bear" in trend_label or "bearish" in trend_label.lower()
    
    if is_bull_ctx:
        if ribbon_strength >= 87.5:
            short_str_ctx = "✔ MOMENTUM"
        elif ribbon_strength >= 50.0:
            short_str_ctx = "↑ PULLBACK?"
        else:
            short_str_ctx = "⚠ LEMAH"
    elif is_bear_ctx:
        if ribbon_strength >= 75.0:
            short_str_ctx = "⚠ RETEST!"
        elif ribbon_strength >= 50.0:
            short_str_ctx = "⚠ BOUNCE?"
        else:
            short_str_ctx = "✔ KONFIRM"
    else:
        short_str_ctx = "↔ SIDEWAYS"
    
    # --- Long strength context ---
    if long_str_count == 4:
        long_str_ctx = "MACRO BULL"
    elif long_str_count == 3:
        long_str_ctx = "ABOVE 3/4"
    elif long_str_count == 2:
        long_str_ctx = "MIXED"
    elif long_str_count == 1:
        long_str_ctx = "NEARLY BEAR"
    else:
        long_str_ctx = "MACRO BEAR"
    
    # --- Verdict ---
    if "OverExt" in trend_label and "▲" in trend_label:
        verdict = "⚠ PARABOLIC — TRAIL SL"
    elif "OverExt" in trend_label and "▼" in trend_label:
        verdict = "⚠ CAPITULATE — WAIT"
    elif any(x in trend_label for x in ["Strong Bull", "Bull ▲", "Bullish"]):
        if strength_count >= 6 and long_str_count >= 3:
            verdict = "✔ STRONG BUY"
        elif strength_count >= 6 and long_str_count < 3:
            verdict = "◑ HOLD — MACRO LEMAH"
        else:
            verdict = "↓ BUY DIP — TUNGGU"
    elif any(x in trend_label for x in ["Strong Bear", "Bear ▼", "Bearish"]):
        if ribbon_strength >= 75.0:
            verdict = "⚠ AVOID — RETEST"
        else:
            verdict = "✖ SELL / SHORT"
    else:
        verdict = "⏸ WAIT — NO TRADE"
    
    # --- EMA Slope/Angle (compare EMA20 3 candles back) ---
    ma1_series = short_mAs[0]  # EMA20 (short_lens[0])
    slope_val = 0.0
    slope_angle = 0.0
    slope_label = "Flat"
    slope_emoji = "➡️"
    
    if len(ma1_series) >= 4 and not np.isnan(ma1_series.iloc[-1]) and not np.isnan(ma1_series.iloc[-4]):
        current = ma1_series.iloc[-1]
        past = ma1_series.iloc[-4]  # 3 candles back
        slope_val = current - past
        
        # Calculate angle in degrees: arctan(rise/run)
        # "run" = 3 candles, "rise" = slope_val
        # Normalize rise by price to get percentage, then angle
        if past != 0:
            slope_pct = (slope_val / past) * 100
            # angle = arctan(slope_pct / 3) * (180/pi) — per candle basis
            # Actually use raw rise over 3 candle "units"
            angle_rad = np.arctan2(slope_val, 3 * (past / 100))  # normalize by price scale
            slope_angle = np.degrees(angle_rad)
        
        # Classification
        abs_angle = abs(slope_angle)
        if abs_angle < 2:
            slope_label = "Flat/Netral"
            slope_emoji = "➡️"
        elif abs_angle < 10:
            if slope_val > 0:
                slope_label = "Rising Bull"
                slope_emoji = "↗️"
            else:
                slope_label = "Falling Bear"
                slope_emoji = "↘️"
        elif abs_angle < 25:
            if slope_val > 0:
                slope_label = "Steep Bull"
                slope_emoji = "📈"
            else:
                slope_label = "Steep Bear"
                slope_emoji = "📉"
        elif abs_angle < 45:
            if slope_val > 0:
                slope_label = "Very Steep Bull"
                slope_emoji = "🚀"
            else:
                slope_label = "Very Steep Bear"
                slope_emoji = "💀"
        else:
            if slope_val > 0:
                slope_label = "Parabolic Bull"
                slope_emoji = "🚀🚀"
            else:
                slope_label = "Cliff Drop Bear"
                slope_emoji = "💀💀"
    
    return {
        "trend_label": trend_label,
        "trend_emoji": trend_emoji,
        "ribbon_strength": round(ribbon_strength, 1),
        "ribbon_strength_count": strength_count,
        "ribbon_strength_total": len(short_vals),
        "short_str_ctx": short_str_ctx,
        "long_str_count": long_str_count,
        "long_str_total": len(long_vals) if show_long else 0,
        "long_str_ctx": long_str_ctx,
        "aligned_bull": aligned_bull,
        "aligned_bear": aligned_bear,
        "alignment": "BULL ALIGNED" if aligned_bull else "BEAR ALIGNED" if aligned_bear else "MISALIGNED",
        "divergence_pct": round(div_pct, 2),
        "overext_threshold": round(overext_thresh, 2),
        "dev_vol_label": dev_vol_label,
        "dev_vol_emoji": dev_vol_emoji,
        "atr_vol_label": atr_vol_label,
        "atr_vol_emoji": atr_vol_emoji,
        "verdict": verdict,
        "long_sl": round(long_sl, 4),
        "short_sl": round(short_sl, 4),
        "atr_val": round(atr_val, 4),
        "ma_values": ma_dict,
        "ema_slope": round(slope_val, 6),
        "ema_slope_angle": round(slope_angle, 1),
        "ema_slope_label": slope_label,
        "ema_slope_emoji": slope_emoji,
    }