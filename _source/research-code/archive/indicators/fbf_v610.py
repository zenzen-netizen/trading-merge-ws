"""
Fractal Break Filter v6.10 — Python port of TradingView Pine Script indicator.
Auto-generated from reference code. Hold — NOT yet wired into screener.py.

Key enhancements from v6.4:
- Stateful break machine (persist counter per bar, multi-bar confirmation)
- Fibo C2 retracement filter (0.5–0.786)
- Supertrend trend gate (info flag, NOT hard filter)
- SMI agreement filter (optional, config default off)
- ALookback for A point (optional, off by default)
- CFractal (optional, off by default)
- Anti-duplicate break detection
- Live ABCD tracker with progressive zigzag
"""

import pandas as pd
import numpy as np
from collections import defaultdict


def _rma(series, length):
    """Wilder's RMA (same as EMA alpha=1/length)"""
    return series.ewm(alpha=1 / length, adjust=False).mean()


def _ema_ema(s, l):
    """Double EMA — ema(ema(s, l), l)"""
    return s.ewm(span=l, adjust=False).mean().ewm(span=l, adjust=False).mean()


def find_pivots(high_arr, low_arr, left, right):
    """
    Find pivot highs and lows.
    Returns: (pivot_highs, pivot_lows)
    Each is list of (bar_index, price)
    """
    n = len(high_arr)
    pivot_highs = []
    pivot_lows = []

    for i in range(left, n - right):
        # Pivot high
        is_ph = True
        for j in range(i - left, i + right + 1):
            if j != i and high_arr[j] >= high_arr[i]:
                is_ph = False
                break
        if is_ph:
            pivot_highs.append((i, high_arr[i]))

        # Pivot low
        is_pl = True
        for j in range(i - left, i + right + 1):
            if j != i and low_arr[j] <= low_arr[i]:
                is_pl = False
                break
        if is_pl:
            pivot_lows.append((i, low_arr[i]))

    return pivot_highs, pivot_lows


def supertrend_adaptive(df, period=10, mult=3.0):
    """Adaptive Supertrend with ratchet logic. Same as v6.4."""
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    hl2 = (high + low) / 2.0

    tr = np.zeros(len(close))
    tr[0] = high[0] - low[0]
    for i in range(1, len(close)):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))

    atr = np.zeros(len(close))
    atr[0] = tr[0]
    alpha = 1.0 / period
    for i in range(1, len(close)):
        atr[i] = atr[i - 1] + alpha * (tr[i] - atr[i - 1])

    up_raw = hl2 - mult * atr
    dn_raw = hl2 + mult * atr
    up_final = np.zeros(len(close))
    dn_final = np.zeros(len(close))
    trend = np.ones(len(close), dtype=int)

    up_final[0] = up_raw[0]
    dn_final[0] = dn_raw[0]

    for i in range(1, len(close)):
        # Ratchet: up can only go up during uptrend
        if close[i - 1] > up_final[i - 1]:
            up_final[i] = max(up_raw[i], up_final[i - 1])
        else:
            up_final[i] = up_raw[i]

        if close[i - 1] < dn_final[i - 1]:
            dn_final[i] = min(dn_raw[i], dn_final[i - 1])
        else:
            dn_final[i] = dn_raw[i]

        trend[i] = trend[i - 1]
        if trend[i - 1] == -1 and close[i] > dn_final[i - 1]:
            trend[i] = 1
        elif trend[i - 1] == 1 and close[i] < up_final[i - 1]:
            trend[i] = -1

    st_line = np.where(trend == 1, up_final, dn_final)

    buy_signal = False
    sell_signal = False
    if len(trend) >= 2:
        if trend[-1] == 1 and trend[-2] == -1:
            buy_signal = True
        elif trend[-1] == -1 and trend[-2] == 1:
            sell_signal = True

    return {
        "value": round(st_line[-1], 4),
        "trend": int(trend[-1]),
        "trend_label": "Uptrend ⬆" if trend[-1] == 1 else "Downtrend ⬇",
        "buy_signal": buy_signal,
        "sell_signal": sell_signal,
    }


def supertrend_classic(df, period=10, mult=3.0, src="hl2"):
    """Classic Supertrend."""
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    if src == "hl2":
        src_val = (high + low) / 2.0
    else:
        src_val = close

    tr = np.zeros(len(close))
    tr[0] = high[0] - low[0]
    for i in range(1, len(close)):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))

    atr = np.zeros(len(close))
    atr[0] = tr[0]
    alpha = 1.0 / period
    for i in range(1, len(close)):
        atr[i] = atr[i - 1] + alpha * (tr[i] - atr[i - 1])

    up_raw = src_val - mult * atr
    dn_raw = src_val + mult * atr
    up_final = np.zeros(len(close))
    dn_final = np.zeros(len(close))
    trend = np.ones(len(close), dtype=int)

    up_final[0] = up_raw[0]
    dn_final[0] = dn_raw[0]

    for i in range(1, len(close)):
        if close[i - 1] > up_final[i - 1]:
            up_final[i] = max(up_raw[i], up_final[i - 1])
        else:
            up_final[i] = up_raw[i]

        if close[i - 1] < dn_final[i - 1]:
            dn_final[i] = min(dn_raw[i], dn_final[i - 1])
        else:
            dn_final[i] = dn_raw[i]

        trend[i] = trend[i - 1]
        if trend[i - 1] == -1 and close[i] > dn_final[i - 1]:
            trend[i] = 1
        elif trend[i - 1] == 1 and close[i] < up_final[i - 1]:
            trend[i] = -1

    st_line = np.where(trend == 1, up_final, dn_final)

    buy_signal = False
    sell_signal = False
    if len(trend) >= 2:
        if trend[-1] == 1 and trend[-2] == -1:
            buy_signal = True
        elif trend[-1] == -1 and trend[-2] == 1:
            sell_signal = True

    return {
        "value": round(st_line[-1], 4),
        "trend": int(trend[-1]),
        "trend_label": "Uptrend ⬆" if trend[-1] == 1 else "Downtrend ⬇",
        "buy_signal": buy_signal,
        "sell_signal": sell_signal,
    }


def ma_cross(df, fast_len=20, slow_len=50, ma_type="EMA"):
    """EMA or SMA cross detection."""
    close = df["close"]

    if ma_type == "EMA":
        fast = close.ewm(span=fast_len, adjust=False).mean()
        slow = close.ewm(span=slow_len, adjust=False).mean()
    else:
        fast = close.rolling(window=fast_len).mean()
        slow = close.rolling(window=slow_len).mean()

    cross_up = False
    cross_down = False
    if len(close) >= 2:
        if fast.iloc[-2] < slow.iloc[-2] and fast.iloc[-1] >= slow.iloc[-1]:
            cross_up = True
        elif fast.iloc[-2] > slow.iloc[-2] and fast.iloc[-1] <= slow.iloc[-1]:
            cross_down = True

    return {
        "fast_val": round(fast.iloc[-1], 4),
        "slow_val": round(slow.iloc[-1], 4),
        "fast_above_slow": fast.iloc[-1] > slow.iloc[-1],
        "cross_up": cross_up,
        "cross_down": cross_down,
        "label": "Bull (20>50)" if fast.iloc[-1] > slow.iloc[-1] else "Bear (20<50)",
    }


# ---------------------------------------------------------------------------
# Internal SMI for agreement filter (v6.10 enableSmiFilter)
# ---------------------------------------------------------------------------
def _calc_smi(df, len_k=5, len_d=3, len_e=3):
    """SMI oscillator, returns (smi_value, smi_ema) at last bar."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    hh = high.rolling(window=len_k, min_periods=len_k).max()
    ll = low.rolling(window=len_k, min_periods=len_k).min()
    rel = close - (hh + ll) / 2
    rng = hh - ll

    # Prevent division by zero
    rng_safe = rng.replace(0, np.nan)

    smi_series = 200 * (_ema_ema(rel, len_d) / _ema_ema(rng_safe, len_d))
    smi_ema = smi_series.ewm(span=len_e, adjust=False).mean()

    if len(smi_series) > 0 and not pd.isna(smi_series.iloc[-1]):
        smi_val = round(smi_series.iloc[-1], 2)
        smi_ema_val = round(smi_ema.iloc[-1], 2)
        return smi_val, smi_ema_val
    return None, None


# ---------------------------------------------------------------------------
# ABCD live tracker (v6.10 style — bar-by-bar progressive)
# ---------------------------------------------------------------------------
def track_abcd_v610(df, cfg):
    """
    ABCD pattern live tracker — v6.10 state machine bar-by-bar.
    Tracks bull/bear patterns independently with progressive zigzag updates.

    Config keys used:
        left_bars, right_bars, enable_a_fractal, a_left_bars, a_right_bars,
        enable_c_fractal, c_left_bars, c_right_bars, enable_struct,
        enable_fibo_bc, bc_fibo_min, bc_fibo_max, cycle_mode, enable_a_lookback,
        a_lookback_bars
    """
    left_bars = cfg.get("left_bars", 3)
    right_bars = cfg.get("right_bars", 3)
    enable_a_fractal = cfg.get("enable_a_fractal", True)
    a_left = cfg.get("a_left_bars", 5)
    a_right = cfg.get("a_right_bars", 5)
    enable_c_fractal = cfg.get("enable_c_fractal", False)
    c_left = cfg.get("c_left_bars", 5)
    c_right = cfg.get("c_right_bars", 5)
    enable_struct = cfg.get("enable_struct_filter", True)
    enable_fibo_bc = cfg.get("enable_fibo_bc", True)
    bc_fibo_min = cfg.get("bc_fibo_min", 0.5)
    bc_fibo_max = cfg.get("bc_fibo_max", 0.786)
    cycle_mode = cfg.get("cycle_mode", "ABC")
    enable_a_lookback = cfg.get("enable_a_lookback", False)
    a_lookback_bars = cfg.get("a_lookback_bars", 50)

    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    n = len(close)

    # Find all pivots
    ph_main, pl_main = find_pivots(high, low, left_bars, right_bars)
    ph_big, pl_big = find_pivots(high, low, a_left, a_right) if enable_a_fractal else ([], [])
    ph_cbig, pl_cbig = find_pivots(high, low, c_left, c_right) if enable_c_fractal else ([], [])

    # Build pivot event map: confirmed_at_bar -> [(pivot_bar, type, price)]
    pivot_events = defaultdict(list)
    for bar_idx, price in ph_main:
        confirmed_at = bar_idx + right_bars
        if confirmed_at < n:
            pivot_events[confirmed_at].append((bar_idx, "ph", price))
    for bar_idx, price in pl_main:
        confirmed_at = bar_idx + right_bars
        if confirmed_at < n:
            pivot_events[confirmed_at].append((bar_idx, "pl", price))

    ph_big_map = {}
    for bar_idx, price in ph_big:
        ph_big_map[bar_idx] = price
    pl_big_map = {}
    for bar_idx, price in pl_big:
        pl_big_map[bar_idx] = price
    ph_cbig_map = {}
    for bar_idx, price in ph_cbig:
        ph_cbig_map[bar_idx] = price
    pl_cbig_map = {}
    for bar_idx, price in pl_cbig:
        pl_cbig_map[bar_idx] = price

    # State variables
    last_pivot_high = None  # (bar_idx, price)
    last_pivot_low = None
    last_a_pivot_high = None
    last_a_pivot_low = None
    snap_low_at_high = None  # A point candidate for bull
    snap_high_at_low = None  # A point candidate for bear

    # Bull tracker
    tb_phase = 0
    tb_a = None
    tb_a_bar = None
    tb_b = None
    tb_b_bar = None
    tb_c = None
    tb_c_bar = None
    tb_d = None
    tb_d_bar = None
    tb_c_locked = False
    tb_d_broke_b = False
    tb_reset = False
    tb_c_pivot_confirmed = False
    tb_fibo_pct = None  # C retracement % when locked

    # Bear tracker
    tr_phase = 0
    tr_a = None
    tr_a_bar = None
    tr_b = None
    tr_b_bar = None
    tr_c = None
    tr_c_bar = None
    tr_d = None
    tr_d_bar = None
    tr_c_locked = False
    tr_d_broke_b = False
    tr_reset = False
    tr_c_pivot_confirmed = False
    tr_fibo_pct = None

    # Bar-by-bar walk
    for i in range(n):
        events = pivot_events.get(i, [])
        has_ph = False
        ph_val = None
        ph_bar = None
        has_pl = False
        pl_val = None
        pl_bar = None
        for pivot_bar, ptype, price in events:
            if ptype == "ph":
                has_ph = True
                ph_val = price
                ph_bar = pivot_bar
            elif ptype == "pl":
                has_pl = True
                pl_val = price
                pl_bar = pivot_bar

        # Track big (A) pivot confirmations
        if enable_a_fractal:
            if ph_bar is not None and ph_bar in ph_big_map:
                last_a_pivot_high = (ph_bar, ph_big_map[ph_bar])
            if pl_bar is not None and pl_bar in pl_big_map:
                last_a_pivot_low = (pl_bar, pl_big_map[pl_bar])

        # Update snap points BEFORE last pivot update (Pine behavior)
        if has_ph:
            if enable_a_fractal:
                snap_low_at_high = last_a_pivot_low
            else:
                snap_low_at_high = last_pivot_low
            last_pivot_high = (ph_bar, ph_val)
        if has_pl:
            if enable_a_fractal:
                snap_high_at_low = last_a_pivot_high
            else:
                snap_high_at_low = last_pivot_high
            last_pivot_low = (pl_bar, pl_val)

        # ------- Bull tracker -------
        # Start new pattern?
        tb_start_ok = False
        if has_ph:
            tb_a_new = snap_low_at_high[1] if snap_low_at_high else None
            tb_a_new_bar = snap_low_at_high[0] if snap_low_at_high else None
            tb_start_ok = (tb_a_new is not None and tb_a_new_bar is not None
                           and tb_a_new < ph_val and tb_a_new_bar < ph_bar)

        if tb_start_ok:
            tb_phase = 1
            tb_a = tb_a_new
            tb_a_bar = tb_a_new_bar
            tb_b = ph_val
            tb_b_bar = ph_bar
            tb_c = None
            tb_c_bar = None
            tb_d = None
            tb_d_bar = None
            tb_c_locked = False
            tb_d_broke_b = False
            tb_reset = False
            tb_c_pivot_confirmed = False
            tb_fibo_pct = None
            # Initial tentative C
            for k in range(right_bars):
                bc = i - k
                if bc > tb_b_bar and bc >= 0:
                    if tb_c is None or low[bc] < tb_c:
                        tb_c = low[bc]
                        tb_c_bar = bc

        elif tb_phase > 0:
            if close[i] < tb_a:
                # RESET: close below A
                tb_phase = 0
                tb_reset = True
                tb_c = None
                tb_c_bar = None
                tb_d = None
                tb_d_bar = None
                tb_fibo_pct = None
            elif tb_phase == 1:
                # Update tentative C
                if tb_c is None or low[i] < tb_c:
                    tb_c = low[i]
                    tb_c_bar = i

                # Check C lock: pivot low after B OR close > B
                # Also check C fractal requirement
                tb_lock_pivot = has_pl and pl_bar > tb_b_bar
                tb_lock_break = close[i] > tb_b

                # For C fractal check — C pivot must match big fractal if enabled
                tb_c_fractal_ok = True
                if tb_lock_pivot and enable_c_fractal:
                    tb_c_fractal_ok = pl_bar in pl_cbig_map

                if (tb_lock_pivot or tb_lock_break) and tb_c_fractal_ok:
                    if tb_lock_pivot:
                        c_val = pl_val
                        c_bar = pl_bar
                        tb_c_pivot_confirmed = True
                    else:
                        c_val = tb_c
                        c_bar = tb_c_bar
                        tb_c_pivot_confirmed = False

                    # Structure check: C > A ?
                    tb_ok = not enable_struct or c_val > tb_a

                    if tb_ok:
                        tb_c = c_val
                        tb_c_bar = c_bar
                        tb_c_locked = True

                        # Fibo C2 check
                        if enable_fibo_bc and tb_a is not None and tb_b is not None:
                            leg_ab = tb_b - tb_a
                            if leg_ab > 0:
                                retrace = tb_b - tb_c
                                tb_fibo_pct = round(retrace / leg_ab, 3)

                        if cycle_mode == "ABC":
                            tb_phase = 0  # Complete at C
                        else:
                            tb_d = high[i]
                            tb_d_bar = i
                            tb_phase = 2
                    else:
                        tb_phase = 0
                        tb_reset = True

            elif tb_phase == 2:
                # Update D
                if tb_d is None or high[i] > tb_d:
                    tb_d = high[i]
                    tb_d_bar = i
                # Check D break B
                if close[i] > tb_b:
                    tb_d = high[i]
                    tb_d_bar = i
                    tb_d_broke_b = True
                    tb_phase = 0  # Complete

        # ------- Bear tracker -------
        tr_start_ok = False
        if has_pl:
            tr_a_new = snap_high_at_low[1] if snap_high_at_low else None
            tr_a_new_bar = snap_high_at_low[0] if snap_high_at_low else None
            tr_start_ok = (tr_a_new is not None and tr_a_new_bar is not None
                           and tr_a_new > pl_val and tr_a_new_bar < pl_bar)

        if tr_start_ok:
            tr_phase = 1
            tr_a = tr_a_new
            tr_a_bar = tr_a_new_bar
            tr_b = pl_val
            tr_b_bar = pl_bar
            tr_c = None
            tr_c_bar = None
            tr_d = None
            tr_d_bar = None
            tr_c_locked = False
            tr_d_broke_b = False
            tr_reset = False
            tr_c_pivot_confirmed = False
            tr_fibo_pct = None
            for k in range(right_bars):
                bc = i - k
                if bc > tr_b_bar and bc >= 0:
                    if tr_c is None or high[bc] > tr_c:
                        tr_c = high[bc]
                        tr_c_bar = bc

        elif tr_phase > 0:
            if close[i] > tr_a:
                tr_phase = 0
                tr_reset = True
                tr_c = None
                tr_c_bar = None
                tr_d = None
                tr_d_bar = None
                tr_fibo_pct = None
            elif tr_phase == 1:
                if tr_c is None or high[i] > tr_c:
                    tr_c = high[i]
                    tr_c_bar = i

                tr_lock_pivot = has_ph and ph_bar > tr_b_bar
                tr_lock_break = close[i] < tr_b

                tr_c_fractal_ok = True
                if tr_lock_pivot and enable_c_fractal:
                    tr_c_fractal_ok = ph_bar in ph_cbig_map

                if (tr_lock_pivot or tr_lock_break) and tr_c_fractal_ok:
                    if tr_lock_pivot:
                        c_val = ph_val
                        c_bar = ph_bar
                        tr_c_pivot_confirmed = True
                    else:
                        c_val = tr_c
                        c_bar = tr_c_bar
                        tr_c_pivot_confirmed = False

                    tr_ok = not enable_struct or c_val < tr_a

                    if tr_ok:
                        tr_c = c_val
                        tr_c_bar = c_bar
                        tr_c_locked = True

                        if enable_fibo_bc and tr_a is not None and tr_b is not None:
                            leg_ab = tr_a - tr_b
                            if leg_ab > 0:
                                retrace = tr_c - tr_b
                                tr_fibo_pct = round(retrace / leg_ab, 3)

                        if cycle_mode == "ABC":
                            tr_phase = 0
                        else:
                            tr_d = low[i]
                            tr_d_bar = i
                            tr_phase = 2
                    else:
                        tr_phase = 0
                        tr_reset = True

            elif tr_phase == 2:
                if tr_d is None or low[i] < tr_d:
                    tr_d = low[i]
                    tr_d_bar = i
                if close[i] < tr_b:
                    tr_d = low[i]
                    tr_d_bar = i
                    tr_d_broke_b = True
                    tr_phase = 0

    # ---- Build pattern dicts ----
    def _phase_label(direction, phase, c_locked, d_broke_b):
        lbl = f"{direction}"
        if phase == 0:
            return f"{lbl} IDLE"
        if phase == 1 and not c_locked:
            return f"{lbl} AB✓ ?C"
        if phase == 1 and c_locked:
            return f"{lbl} ABC✓"
        if phase == 2 and d_broke_b:
            return f"{lbl} ⚡D>B"
        if phase == 2:
            return f"{lbl} ABC✓ ⏳D"
        return f"{lbl} Phase {phase}"

    def build_pattern(direction, phase, a, a_bar, b, b_bar, c, c_bar,
                      d, d_bar, c_locked, d_broke_b, fibo_pct=None):
        p = {
            "direction": direction,
            "a_bar": a_bar, "a_price": round(a, 4) if a is not None else None,
            "b_bar": b_bar, "b_price": round(b, 4) if b is not None else None,
            "c_bar": c_bar, "c_price": round(c, 4) if c is not None else None,
            "phase": phase, "c_locked": c_locked, "struct_ok": True,
            "phase_label": _phase_label(direction, phase, c_locked, d_broke_b),
        }
        if fibo_pct is not None:
            p["fibo_pct"] = round(fibo_pct * 100, 1)  # percentage
        if d_broke_b:
            p["d_bar"] = d_bar
            p["d_price"] = round(d, 4) if d is not None else None
            p["d_broke_b"] = True
        elif phase == 2:
            p["d_bar"] = d_bar
            p["d_price"] = round(d, 4) if d is not None else None
            p["d_broke_b"] = False
        else:
            p["d_broke_b"] = False
        return p

    # Raw break at last bar
    raw_bull_break = last_pivot_high is not None and close[-1] > last_pivot_high[1]
    raw_bear_break = last_pivot_low is not None and close[-1] < last_pivot_low[1]

    # Build bull pattern
    bull_pattern = None
    if tb_phase > 0:
        bull_pattern = build_pattern("BULL", tb_phase, tb_a, tb_a_bar, tb_b, tb_b_bar,
                                     tb_c, tb_c_bar, tb_d, tb_d_bar,
                                     tb_c_locked, tb_d_broke_b, tb_fibo_pct)
    elif tb_c_locked and not tb_reset and tb_b is not None:
        bp_phase = 2 if tb_d_broke_b else 1
        bull_pattern = build_pattern("BULL", bp_phase, tb_a, tb_a_bar, tb_b, tb_b_bar,
                                     tb_c, tb_c_bar, tb_d, tb_d_bar,
                                     True, tb_d_broke_b, tb_fibo_pct)

    # Build bear pattern
    bear_pattern = None
    if tr_phase > 0:
        bear_pattern = build_pattern("BEAR", tr_phase, tr_a, tr_a_bar, tr_b, tr_b_bar,
                                     tr_c, tr_c_bar, tr_d, tr_d_bar,
                                     tr_c_locked, tr_d_broke_b, tr_fibo_pct)
    elif tr_c_locked and not tr_reset and tr_b is not None:
        bp_phase = 2 if tr_d_broke_b else 1
        bear_pattern = build_pattern("BEAR", bp_phase, tr_a, tr_a_bar, tr_b, tr_b_bar,
                                     tr_c, tr_c_bar, tr_d, tr_d_bar,
                                     True, tr_d_broke_b, tr_fibo_pct)

    max_phase = 0
    if bull_pattern:
        max_phase = max(max_phase, bull_pattern["phase"])
    if bear_pattern:
        max_phase = max(max_phase, bear_pattern["phase"])

    # Pick most recent by B bar
    pattern = None
    candidates = []
    if bull_pattern:
        candidates.append(bull_pattern)
    if bear_pattern:
        candidates.append(bear_pattern)
    if candidates:
        pattern = max(candidates, key=lambda x: x.get("b_bar") or 0)

    return {
        "phase": max_phase,
        "pattern": pattern,
        "bull_pattern": bull_pattern,
        "bear_pattern": bear_pattern,
        "raw_bull_break": raw_bull_break,
        "raw_bear_break": raw_bear_break,
        "last_pivot_high": last_pivot_high,
        "last_pivot_low": last_pivot_low,
    }


# ---------------------------------------------------------------------------
# Main entry: FBF v6.10
# ---------------------------------------------------------------------------
def fbf_v610(df, cfg):
    """
    Fractal Break Filter v6.10 — full Python port of Pine Script indicator.

    This is the main entry point. Replaces fbf_v64() for the v6.10 upgrade.

    Parameters (config dict):
        === Fractal ===
        left_bars (int=3): Pivot left window
        right_bars (int=3): Pivot right window

        === Raw Candidate ===
        (visual only in Pine — always tracked in Python)

        === Filter ATR ===
        enable_atr_filter (bool=True): ATR buffer filter
        atr_len (int=14): ATR period
        atr_mult (float=0.15): Min break distance in ×ATR

        === Filter Persistence ===
        enable_persist_filter (bool=False): Require N bars beyond B
        persist_n (int=2): Number of consecutive bars

        === Filter SMI Agreement ===
        enable_smi_filter (bool=False): SMI agreement (off = bypass)
        smi_len_k (int=5)
        smi_len_d (int=3)
        smi_len_e (int=3)

        === Filter Struktur Pola ===
        enable_struct_filter (bool=True): C > A (bull) / C < A (bear)

        === Filter Trend Visual (GATE) ===
        enable_st_trend_filter (bool=True): Supertrent trend gate
            When True AND Supertrend is enabled:
            bull break confirmed only if ST is uptrend (trend == 1)
            bear break confirmed only if ST is downtrend (trend == -1)
            NOTE: In Pine this is purely visual hide.
            In Python, this acts as an INFO flag — the break IS still
            reported but flagged with st_ok=False. Set st_ok=False
            does NOT cancel the break.

        === Filter Leg A ===
        enable_a_fractal (bool=True): Big fractal for A point
        a_left_bars (int=5)
        a_right_bars (int=5)
        enable_a_dist (bool=True): Min A-B distance in ×ATR
        a_dist_mult (float=1.0)
        enable_a_lookback (bool=False): Scan back N bars for extreme A
        a_lookback_bars (int=50)

        === Filter Leg BC ===
        enable_c_fractal (bool=False): Big fractal for C point
        c_left_bars (int=5)
        c_right_bars (int=5)
        enable_fibo_bc (bool=True): Fibo retracement zone for C
        bc_fibo_min (float=0.5)
        bc_fibo_max (float=0.786)

        === Visual Break ===
        (visual only in Pine — ignored in Python)

        === Anti Duplikat ===
        no_duplicate (bool=True): Prevent duplicate break on same B level

        === Mode Siklus ===
        cycle_mode (str="ABC"): "ABC" | "Full ABCD"

        === MA Cross ===
        enable_ma (bool=True)
        ma_fast_type (str="EMA")
        ma_fast_len (int=20)
        ma_slow_type (str="EMA")
        ma_slow_len (int=50)

        === Supertrend ===
        enable_st (bool=True)
        st_mode (str="Adaptive"): "Adaptive" | "Classic"
        st_period (int=10)
        st_mult (float=3.0)

        === HTF MA & Supertrend ===
        enable_htf (bool=False) — NOT implemented in Python (no multi-TF)
    """
    # ---- Extract config with defaults ----
    left_bars = cfg.get("left_bars", 3)
    right_bars = cfg.get("right_bars", 3)

    enable_atr_filter = cfg.get("enable_atr_filter", True)
    atr_len = cfg.get("atr_len", 14)
    atr_mult = cfg.get("atr_mult", 0.15)

    enable_persist_filter = cfg.get("enable_persist_filter", False)
    persist_n = cfg.get("persist_n", 2)
    req_n = persist_n if enable_persist_filter else 1

    enable_smi_filter = cfg.get("enable_smi_filter", False)
    smi_len_k = cfg.get("smi_len_k", 5)
    smi_len_d = cfg.get("smi_len_d", 3)
    smi_len_e = cfg.get("smi_len_e", 3)

    enable_struct_filter = cfg.get("enable_struct_filter", True)

    enable_st_trend_filter = cfg.get("enable_st_trend_filter", True)

    enable_a_fractal = cfg.get("enable_a_fractal", True)
    a_left = cfg.get("a_left_bars", 5)
    a_right = cfg.get("a_right_bars", 5)
    enable_a_dist = cfg.get("enable_a_dist", True)
    a_dist_mult = cfg.get("a_dist_mult", 1.0)
    enable_a_lookback = cfg.get("enable_a_lookback", False)
    a_lookback_bars = cfg.get("a_lookback_bars", 50)

    enable_c_fractal = cfg.get("enable_c_fractal", False)
    c_left = cfg.get("c_left_bars", 5)
    c_right = cfg.get("c_right_bars", 5)
    enable_fibo_bc = cfg.get("enable_fibo_bc", True)
    bc_fibo_min = cfg.get("bc_fibo_min", 0.5)
    bc_fibo_max = cfg.get("bc_fibo_max", 0.786)

    no_duplicate = cfg.get("no_duplicate", True)
    cycle_mode = cfg.get("cycle_mode", "ABC")

    enable_ma = cfg.get("enable_ma", True)
    ma_fast_type = cfg.get("ma_fast_type", "EMA")
    ma_fast_len = cfg.get("ma_fast_len", 20)
    ma_slow_type = cfg.get("ma_slow_type", "EMA")
    ma_slow_len = cfg.get("ma_slow_len", 50)

    enable_st = cfg.get("enable_st", True)
    st_mode = cfg.get("st_mode", "Adaptive")
    st_period = cfg.get("st_period", 10)
    st_mult = cfg.get("st_mult", 3.0)

    # ---- Data arrays ----
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    n = len(close)

    # ---- ATR ----
    tr = np.zeros(n)
    atr_arr = np.zeros(n)
    tr[0] = high[0] - low[0]
    atr_arr[0] = tr[0]
    alpha = 1.0 / atr_len
    for i in range(1, n):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        atr_arr[i] = atr_arr[i - 1] + alpha * (tr[i] - atr_arr[i - 1])
    atr_val = atr_arr[-1]
    _atr14 = atr_val  # approximation

    # ---- SMI (if enabled) ----
    smi_val = None
    smi_ema_val = None
    if enable_smi_filter:
        smi_val, smi_ema_val = _calc_smi(df, smi_len_k, smi_len_d, smi_len_e)

    # ---- Pivots ----
    ph_main, pl_main = find_pivots(high, low, left_bars, right_bars)
    ph_big, pl_big = find_pivots(high, low, a_left, a_right) if enable_a_fractal else ([], [])
    ph_cbig, pl_cbig = find_pivots(high, low, c_left, c_right) if enable_c_fractal else ([], [])

    # ---- Build pivot event map ----
    pivot_events = defaultdict(list)
    for bar_idx, price in ph_main:
        confirmed_at = bar_idx + right_bars
        if confirmed_at < n:
            pivot_events[confirmed_at].append((bar_idx, "ph", price))
    for bar_idx, price in pl_main:
        confirmed_at = bar_idx + right_bars
        if confirmed_at < n:
            pivot_events[confirmed_at].append((bar_idx, "pl", price))

    ph_big_map = {bi: p for bi, p in ph_big}
    pl_big_map = {bi: p for bi, p in pl_big}
    ph_cbig_map = {bi: p for bi, p in ph_cbig} if enable_c_fractal else {}
    pl_cbig_map = {bi: p for bi, p in pl_cbig} if enable_c_fractal else {}

    # ---- Fast helpers for ALookback ----
    # We use rolling min/max windows. For the A-lookback extreme search,
    # at each break bar (when B pivot is confirmed), we look back N bars
    # for the most extreme low/high. Since we need it at the pivot point,
    # we can precompute rolling lookback.

    # ---- State ----
    last_pivot_high = None
    last_pivot_high_bar = None
    last_pivot_low = None
    last_pivot_low_bar = None
    last_a_pivot_high = None
    last_a_pivot_low = None

    snap_low_at_high_val = None
    snap_low_at_high_bar = None
    snap_high_at_low_val = None
    snap_high_at_low_bar = None

    # Break state machine
    bull_active = False
    bull_persist = 0
    bull_ref_val = None
    bull_ref_bar = None
    bull_a_val = None
    bull_a_bar = None
    bull_last_confirmed_bar = None
    # [PATCH] collector for all confirmed breaks (observability only)
    all_breaks = []
    bull_confirmed_val = None
    bull_confirmed_a_val = None
    bull_confirmed_a_bar = None
    bull_confirmed_fibo_pct = None
    bull_confirmed_struct_ok = None
    bull_confirmed_st_ok = None  # anti-duplicate

    bear_active = False
    bear_persist = 0
    bear_ref_val = None
    bear_ref_bar = None
    bear_a_val = None
    bear_a_bar = None
    bear_last_confirmed_bar = None
    bear_confirmed_val = None
    bear_confirmed_a_val = None
    bear_confirmed_a_bar = None
    bear_confirmed_fibo_pct = None
    bear_confirmed_struct_ok = None
    bear_confirmed_st_ok = None

    # ---- Bar-by-bar walk ----
    for i in range(n):
        events = pivot_events.get(i, [])
        has_ph = False
        ph_val = None
        ph_bar = None
        has_pl = False
        pl_val = None
        pl_bar = None

        for pivot_bar, ptype, price in events:
            if ptype == "ph":
                has_ph = True
                ph_val = price
                ph_bar = pivot_bar
            elif ptype == "pl":
                has_pl = True
                pl_val = price
                pl_bar = pivot_bar

        # Track big (A) pivot confirmations
        if enable_a_fractal:
            if ph_bar is not None and ph_bar in ph_big_map:
                last_a_pivot_high = (ph_bar, ph_big_map[ph_bar])
            if pl_bar is not None and pl_bar in pl_big_map:
                last_a_pivot_low = (pl_bar, pl_big_map[pl_bar])

        # Update snap + last pivot
        if has_ph:
            if enable_a_fractal and last_a_pivot_low is not None:
                snap_low_at_high_val = last_a_pivot_low[1]
                snap_low_at_high_bar = last_a_pivot_low[0]
            else:
                snap_low_at_high_val = last_pivot_low if last_pivot_low is not None else None
                snap_low_at_high_bar = last_pivot_low_bar
            last_pivot_high = ph_val
            last_pivot_high_bar = ph_bar

        if has_pl:
            if enable_a_fractal and last_a_pivot_high is not None:
                snap_high_at_low_val = last_a_pivot_high[1]
                snap_high_at_low_bar = last_a_pivot_high[0]
            else:
                snap_high_at_low_val = last_pivot_high if last_pivot_high is not None else None
                snap_high_at_low_bar = last_pivot_high_bar
            last_pivot_low = pl_val
            last_pivot_low_bar = pl_bar

        # ---- RAW candidate checks ----
        raw_bull = last_pivot_high is not None and close[i] > last_pivot_high
        raw_bear = last_pivot_low is not None and close[i] < last_pivot_low

        # ---- BULL BREAK state machine ----
        if not bull_active and raw_bull:
            dist_ok = not enable_atr_filter or (close[i] - last_pivot_high) >= atr_mult * atr_arr[i]
            if dist_ok:
                bull_active = True
                bull_persist = 1
                bull_ref_val = last_pivot_high
                bull_ref_bar = last_pivot_high_bar

                # A point
                if enable_a_lookback:
                    # Scan last N bars from B for lowest low (extreme)
                    look_start = max(0, bull_ref_bar - a_lookback_bars)
                    look_slice = low[look_start:bull_ref_bar + 1]
                    if len(look_slice) > 0:
                        min_idx = np.argmin(look_slice)
                        bull_a_val = look_slice[min_idx]
                        bull_a_bar = look_start + min_idx
                    else:
                        bull_a_val = snap_low_at_high_val
                        bull_a_bar = snap_low_at_high_bar
                else:
                    bull_a_val = snap_low_at_high_val
                    bull_a_bar = snap_low_at_high_bar

        elif bull_active:
            still_beyond = close[i] > bull_ref_val
            dist_ok2 = not enable_atr_filter or (close[i] - bull_ref_val) >= atr_mult * atr_arr[i]
            if still_beyond and dist_ok2:
                bull_persist += 1
            else:
                bull_active = False
                bull_persist = 0

        # ---- BULL confirmation gates ----
        bull_time_ok = bull_active and bull_persist >= req_n
        # C validation: find the last pivot low after bullRefBar
        bull_c_valid = False
        bull_c_val = None
        bull_c_bar = None
        if bull_active and bull_ref_bar is not None:
            for pb, pv in pl_main:
                if pb > bull_ref_bar and pb < i:
                    if not bull_c_valid or pb > bull_c_bar:
                        bull_c_valid = True
                        bull_c_val = pv
                        bull_c_bar = pb
        bull_a_valid = bull_a_val is not None
        bull_adist_ok = not enable_a_dist or (bull_a_valid and (bull_ref_val - bull_a_val) >= a_dist_mult * atr_arr[i])
        bull_struct_ok = not enable_struct_filter or (bull_a_valid and bull_c_valid and bull_c_val > bull_a_val)

        # C fractal ok (C must be big pivot if enbled)
        bull_c_fractal_ok = True
        if bull_c_valid and enable_c_fractal:
            bull_c_fractal_ok = bull_c_bar in pl_cbig_map if enable_c_fractal else True

        # Fibo C2
        bull_fibo_ok = True
        bull_fibo_pct = None
        if enable_fibo_bc and bull_a_valid and bull_c_valid and bull_active:
            leg_ab = bull_ref_val - bull_a_val
            if leg_ab > 0:
                retrace = bull_ref_val - bull_c_val
                bull_fibo_pct = retrace / leg_ab
                bull_fibo_ok = bc_fibo_min <= bull_fibo_pct <= bc_fibo_max
                bull_fibo_pct = round(bull_fibo_pct * 100, 1)  # %

        # SMI agreement
        bull_smi_ok = True
        if enable_smi_filter and smi_val is not None and smi_ema_val is not None:
            bull_smi_ok = smi_val >= smi_ema_val

        # ST trend gate (INFO flag — does NOT hard cancel)
        bull_st_ok = True
        if enable_st_trend_filter and enable_st:
            df_slice = df.iloc[:i + 1]
            if st_mode == "Adaptive":
                st_info = supertrend_adaptive(df_slice, st_period, st_mult)
            else:
                st_info = supertrend_classic(df_slice, st_period, st_mult)
            bull_st_ok = st_info["trend"] == 1

        bull_confirmed = (bull_time_ok and bull_struct_ok and bull_adist_ok
                          and bull_c_fractal_ok and bull_fibo_ok and bull_smi_ok)

        # Anti-duplicate
        is_dup_bull = no_duplicate and bull_last_confirmed_bar is not None and bull_ref_bar == bull_last_confirmed_bar

        if bull_confirmed and not is_dup_bull:
            bull_last_confirmed_bar = bull_ref_bar
            bull_confirmed_val = bull_ref_val
            bull_confirmed_a_val = bull_a_val
            bull_confirmed_a_bar = bull_a_bar
            bull_confirmed_fibo_pct = bull_fibo_pct
            bull_confirmed_struct_ok = bull_struct_ok
            bull_confirmed_st_ok = bull_st_ok
            bull_active = False
            bull_persist = 0
            # [PATCH] record this confirmed bull break
            all_breaks.append({
                "kind": "bull", "ref_bar": bull_ref_bar,
                "ref_val": round(bull_ref_val, 4) if bull_ref_val is not None else None,
                "a_val": round(bull_a_val, 4) if bull_a_val is not None else None,
                "a_bar": bull_a_bar,
                "fibo_pct": round(bull_fibo_pct, 1) if bull_fibo_pct is not None else None,
                "struct_ok": bull_struct_ok, "st_ok": bull_st_ok,
                "confirm_bar": i,
            })

        # ---- BEAR BREAK state machine ----
        if not bear_active and raw_bear:
            dist_ok = not enable_atr_filter or (last_pivot_low - close[i]) >= atr_mult * atr_arr[i]
            if dist_ok:
                bear_active = True
                bear_persist = 1
                bear_ref_val = last_pivot_low
                bear_ref_bar = last_pivot_low_bar

                if enable_a_lookback:
                    look_start = max(0, bear_ref_bar - a_lookback_bars)
                    look_slice = high[look_start:bear_ref_bar + 1]
                    if len(look_slice) > 0:
                        max_idx = np.argmax(look_slice)
                        bear_a_val = look_slice[max_idx]
                        bear_a_bar = look_start + max_idx
                    else:
                        bear_a_val = snap_high_at_low_val
                        bear_a_bar = snap_high_at_low_bar
                else:
                    bear_a_val = snap_high_at_low_val
                    bear_a_bar = snap_high_at_low_bar

        elif bear_active:
            still_beyond = close[i] < bear_ref_val
            dist_ok2 = not enable_atr_filter or (bear_ref_val - close[i]) >= atr_mult * atr_arr[i]
            if still_beyond and dist_ok2:
                bear_persist += 1
            else:
                bear_active = False
                bear_persist = 0

        bear_time_ok = bear_active and bear_persist >= req_n
        # C validation
        bear_c_valid = False
        bear_c_val = None
        bear_c_bar = None
        if bear_active and bear_ref_bar is not None:
            for pb, pv in ph_main:
                if pb > bear_ref_bar and pb < i:
                    if not bear_c_valid or pb > bear_c_bar:
                        bear_c_valid = True
                        bear_c_val = pv
                        bear_c_bar = pb
        bear_a_valid = bear_a_val is not None
        bear_adist_ok = not enable_a_dist or (bear_a_valid and (bear_a_val - bear_ref_val) >= a_dist_mult * atr_arr[i])
        bear_struct_ok = not enable_struct_filter or (bear_a_valid and bear_c_valid and bear_c_val < bear_a_val)

        bear_c_fractal_ok = True
        if bear_c_valid and enable_c_fractal:
            bear_c_fractal_ok = bear_c_bar in ph_cbig_map if enable_c_fractal else True

        bear_fibo_ok = True
        bear_fibo_pct = None
        if enable_fibo_bc and bear_a_valid and bear_c_valid and bear_active:
            leg_ab = bear_a_val - bear_ref_val
            if leg_ab > 0:
                retrace = bear_c_val - bear_ref_val
                bear_fibo_pct = retrace / leg_ab
                bear_fibo_ok = bc_fibo_min <= bear_fibo_pct <= bc_fibo_max
                bear_fibo_pct = round(bear_fibo_pct * 100, 1)

        bear_smi_ok = True
        if enable_smi_filter and smi_val is not None and smi_ema_val is not None:
            bear_smi_ok = smi_val <= smi_ema_val

        bear_st_ok = True
        if enable_st_trend_filter and enable_st:
            df_slice = df.iloc[:i + 1]
            if st_mode == "Adaptive":
                st_info = supertrend_adaptive(df_slice, st_period, st_mult)
            else:
                st_info = supertrend_classic(df_slice, st_period, st_mult)
            bear_st_ok = st_info["trend"] == -1

        bear_confirmed = (bear_time_ok and bear_struct_ok and bear_adist_ok
                          and bear_c_fractal_ok and bear_fibo_ok and bear_smi_ok)

        is_dup_bear = no_duplicate and bear_last_confirmed_bar is not None and bear_ref_bar == bear_last_confirmed_bar

        if bear_confirmed and not is_dup_bear:
            bear_last_confirmed_bar = bear_ref_bar
            bear_confirmed_val = bear_ref_val
            bear_confirmed_a_val = bear_a_val
            bear_confirmed_a_bar = bear_a_bar
            bear_confirmed_fibo_pct = bear_fibo_pct
            bear_confirmed_struct_ok = bear_struct_ok
            bear_confirmed_st_ok = bear_st_ok
            bear_active = False
            bear_persist = 0
            # [PATCH] record this confirmed bear break
            all_breaks.append({
                "kind": "bear", "ref_bar": bear_ref_bar,
                "ref_val": round(bear_ref_val, 4) if bear_ref_val is not None else None,
                "a_val": round(bear_a_val, 4) if bear_a_val is not None else None,
                "a_bar": bear_a_bar,
                "fibo_pct": round(bear_fibo_pct, 1) if bear_fibo_pct is not None else None,
                "struct_ok": bear_struct_ok, "st_ok": bear_st_ok,
                "confirm_bar": i,
            })

    # ---- Supertrend (full df, last bar) ----
    st = {}
    if enable_st:
        if st_mode == "Adaptive":
            st = supertrend_adaptive(df, st_period, st_mult)
        else:
            st = supertrend_classic(df, st_period, st_mult)

    # ---- MA Cross ----
    ma_info = {}
    if enable_ma:
        ma_info = ma_cross(df, ma_fast_len, ma_slow_len, ma_fast_type)

    # ---- ABCD tracker ----
    abc = track_abcd_v610(df, cfg)

    # ---- Final result ----
    # Determine active break (bull or bear)
    bull_break = None
    bear_break = None
    if bull_last_confirmed_bar is not None:
        bull_break = {
            "ref_bar": bull_last_confirmed_bar,
            "ref_val": round(bull_confirmed_val, 4) if bull_confirmed_val is not None else None,
            "a_val": round(bull_confirmed_a_val, 4) if bull_confirmed_a_val is not None else None,
            "a_bar": bull_confirmed_a_bar,
            "fibo_pct": bull_confirmed_fibo_pct,
            "struct_ok": bull_confirmed_struct_ok,
            "st_ok": bull_confirmed_st_ok,
        }
    if bear_last_confirmed_bar is not None:
        bear_break = {
            "ref_bar": bear_last_confirmed_bar,
            "ref_val": round(bear_confirmed_val, 4) if bear_confirmed_val is not None else None,
            "a_val": round(bear_confirmed_a_val, 4) if bear_confirmed_a_val is not None else None,
            "a_bar": bear_confirmed_a_bar,
            "fibo_pct": bear_confirmed_fibo_pct,
            "struct_ok": bear_confirmed_struct_ok,
            "st_ok": bear_confirmed_st_ok,
        }

    return {
        "phase": abc["phase"],
        "phase_label": abc["pattern"].get("phase_label", "Idle") if abc.get("pattern") else "Idle",
        "bull_break": bull_break,
        "bear_break": bear_break,
        "b_level": (bull_break or {}).get("ref_val") or (bear_break or {}).get("ref_val"),
        "abcd": abc,
        "supertrend": st,
        "ma_cross": ma_info,
        "raw_bull_break": abc["raw_bull_break"],
        "raw_bear_break": abc["raw_bear_break"],
        "all_breaks": all_breaks,  # [PATCH] list of every confirmed break in df
        "atr_val": round(atr_val, 4),
        "smi_value": smi_val,
        "smi_ema": smi_ema_val,
        # Filters status matrix (for formatter)
        "filters": {
            "atr": enable_atr_filter,
            "persist": enable_persist_filter,
            "smi": enable_smi_filter,
            "struct": enable_struct_filter,
            "st_trend_gate": enable_st_trend_filter,
            "a_fractal": enable_a_fractal,
            "a_dist": enable_a_dist,
            "a_lookback": enable_a_lookback,
            "c_fractal": enable_c_fractal,
            "fibo_bc": enable_fibo_bc,
            "dup_check": no_duplicate,
        },
    }
