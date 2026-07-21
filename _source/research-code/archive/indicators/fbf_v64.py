"""
Fractal Break Filter v6.4 — Python port of TradingView Pine Script indicator.
Pivot detection, ABCD pattern tracking, break state machine with filters,
Supertrend (Adaptive), and MA Cross.
"""

import pandas as pd
import numpy as np


def _rma(series, length):
    """Wilder's RMA"""
    return series.ewm(alpha=1/length, adjust=False).mean()


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
    """
    Adaptive Supertrend with ratchet logic.
    Returns: (st_values, st_trends) — arrays
    st_values: the supertrend line value
    st_trends: 1 for uptrend, -1 for downtrend
    """
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    hl2 = (high + low) / 2.0
    
    # ATR
    tr = np.zeros(len(close))
    tr[0] = high[0] - low[0]
    for i in range(1, len(close)):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
    
    # RMA of TR
    atr = np.zeros(len(close))
    atr[0] = tr[0]
    alpha = 1.0 / period
    for i in range(1, len(close)):
        atr[i] = atr[i-1] + alpha * (tr[i] - atr[i-1])
    
    # Supertrend levels
    up_raw = hl2 - mult * atr
    dn_raw = hl2 + mult * atr
    
    up_final = np.zeros(len(close))
    dn_final = np.zeros(len(close))
    trend = np.ones(len(close), dtype=int)
    
    up_final[0] = up_raw[0]
    dn_final[0] = dn_raw[0]
    
    for i in range(1, len(close)):
        # Ratchet: up can only go up during uptrend
        if close[i-1] > up_final[i-1]:
            up_final[i] = max(up_raw[i], up_final[i-1])
        else:
            up_final[i] = up_raw[i]
        
        # dn can only go down during downtrend
        if close[i-1] < dn_final[i-1]:
            dn_final[i] = min(dn_raw[i], dn_final[i-1])
        else:
            dn_final[i] = dn_raw[i]
        
        # Trend flip
        trend[i] = trend[i-1]
        if trend[i-1] == -1 and close[i] > dn_final[i-1]:
            trend[i] = 1
        elif trend[i-1] == 1 and close[i] < up_final[i-1]:
            trend[i] = -1
    
    # Build the ST line: up_final when trend=1, dn_final when trend=-1
    st_line = np.where(trend == 1, up_final, dn_final)
    
    # Detect signals (trend flip)
    buy_signal = False
    sell_signal = False
    if len(trend) >= 2:
        if trend[-1] == 1 and trend[-2] == -1:
            buy_signal = True
        elif trend[-1] == -1 and trend[-2] == 1:
            sell_signal = True
    
    return {
        "value": round(st_line[-1], 4),
        "trend": trend[-1],
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


def fbf_v64(df, cfg):
    """
    Fractal Break Filter v6.4 — full logic.
    
    Returns dict with:
        phase, phase_label, b_level, break_type, break_confirmed,
        abcd_pattern, st, ma_cross_info, filters_active
    """
    left_bars = cfg.get("left_bars", 3)
    right_bars = cfg.get("right_bars", 3)
    enable_atr = cfg.get("enable_atr_filter", True)
    atr_len = cfg.get("atr_len", 14)
    atr_mult = cfg.get("atr_mult", 0.15)
    enable_persist = cfg.get("enable_persist_filter", False)
    persist_n = cfg.get("persist_n", 2)
    enable_struct = cfg.get("enable_struct_filter", True)
    enable_a_fractal = cfg.get("enable_a_fractal", True)
    a_left = cfg.get("a_left_bars", 5)
    a_right = cfg.get("a_right_bars", 5)
    enable_a_dist = cfg.get("enable_a_dist", True)
    a_dist_mult = cfg.get("a_dist_mult", 1.0)
    no_duplicate = cfg.get("no_duplicate", True)
    cycle_mode = cfg.get("cycle_mode", "ABC")
    
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    
    # --- ATR ---
    tr = np.zeros(len(close))
    tr[0] = high[0] - low[0]
    for i in range(1, len(close)):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
    atr_arr = np.zeros(len(close))
    atr_arr[0] = tr[0]
    alpha = 1.0 / atr_len
    for i in range(1, len(close)):
        atr_arr[i] = atr_arr[i-1] + alpha * (tr[i] - atr_arr[i-1])
    atr_val = atr_arr[-1]
    
    # --- Find pivots ---
    ph_main, pl_main = find_pivots(high, low, left_bars, right_bars)
    ph_big, pl_big = find_pivots(high, low, a_left, a_right) if enable_a_fractal else ([], [])
    
    # --- Track state ---
    last_pivot_high = None  # (bar_idx, price)
    last_pivot_low = None
    last_a_pivot_high = None
    last_a_pivot_low = None
    snap_low_at_high = None  # (bar_idx, price)
    snap_high_at_low = None
    
    # Walk pivots to build state
    all_ph = []  # (bar_idx, price, is_a)
    all_pl = []
    
    if enable_a_fractal:
        for idx, price in ph_big:
            all_ph.append((idx, price, True))
        for idx, price in pl_big:
            all_pl.append((idx, price, True))
    
    for idx, price in ph_main:
        all_ph.append((idx, price, False))
    for idx, price in pl_main:
        all_ph.append((idx, price, False))
    # Actually we need to process them in order
    
    # Simple approach: just track last pivots
    # Process main pivots chronologically
    ph_sorted = sorted(ph_main, key=lambda x: x[0])
    pl_sorted = sorted(pl_main, key=lambda x: x[0])
    
    ph_big_sorted = sorted(ph_big, key=lambda x: x[0]) if enable_a_fractal else []
    pl_big_sorted = sorted(pl_big, key=lambda x: x[0]) if enable_a_fractal else []
    
    # Track the most recent pivots
    if ph_main:
        last_ph = ph_sorted[-1]
    else:
        last_ph = None
    if pl_main:
        last_pl = pl_sorted[-1]
    else:
        last_pl = None
    if enable_a_fractal and ph_big:
        last_ph_a = ph_big_sorted[-1]
    else:
        last_ph_a = None
    if enable_a_fractal and pl_big:
        last_pl_a = pl_big_sorted[-1]
    else:
        last_pl_a = None
    
    # snapLowAtHigh: the last low pivot before the most recent high pivot
    snap_low = None
    for p in pl_sorted:
        if last_ph and p[0] < last_ph[0]:
            snap_low = p
        else:
            break
    
    # snapHighAtLow: the last high pivot before the most recent low pivot  
    snap_high = None
    for p in ph_sorted:
        if last_pl and p[0] < last_pl[0]:
            snap_high = p
        else:
            break
    
    # --- Bull/Bear state machine ---
    bull_active = False
    bull_persist = 0
    bull_ref_val = None
    bull_ref_bar = None
    bull_a_val = None
    bull_a_bar = None
    bull_broken = False
    bull_break_type = None
    
    # Walk from found pivots, simulating break logic
    # For simplicity, use the LATEST pivot high/low as break reference
    
    # --- Bull break candidate ---
    bull_break = None
    if last_ph and close[-1] > last_ph[1]:
        bull_ref_val = last_ph[1]
        bull_ref_bar = last_ph[0]
        
        # A point
        if enable_a_fractal and snap_low:
            bull_a_val = snap_low[1]
            bull_a_bar = snap_low[0]
        elif snap_low:
            bull_a_val = snap_low[1]
            bull_a_bar = snap_low[0]
        else:
            bull_a_val = None
            bull_a_bar = None
        
        # ATR filter
        atr_ok = True
        if enable_atr:
            atr_ok = (close[-1] - bull_ref_val) >= atr_mult * atr_val
        
        # A dist filter
        a_dist_ok = True
        if enable_a_dist and bull_a_val is not None:
            a_dist_ok = (bull_ref_val - bull_a_val) >= a_dist_mult * atr_val
        
        # Structure: C > A (need C point = last low pivot after B)
        c_valid = last_pl and last_pl[0] > bull_ref_bar
        c_val = last_pl[1] if c_valid else None
        
        struct_ok = True
        if enable_struct:
            struct_ok = bull_a_val is not None and c_valid and c_val > bull_a_val
        
        all_filters_ok = atr_ok and a_dist_ok and struct_ok
        
        if all_filters_ok:
            bull_break = {
                "ref_bar": bull_ref_bar,
                "ref_val": round(bull_ref_val, 4),
                "a_val": round(bull_a_val, 4) if bull_a_val else None,
                "a_bar": bull_a_bar,
                "c_val": round(c_val, 4) if c_val else None,
                "c_bar": last_pl[0] if c_valid else None,
                "confirmed": True,
            }
    
    # --- Bear break candidate ---
    bear_break = None
    if last_pl and close[-1] < last_pl[1]:
        bear_ref_val = last_pl[1]
        bear_ref_bar = last_pl[0]
        
        if enable_a_fractal and snap_high:
            bear_a_val = snap_high[1]
            bear_a_bar = snap_high[0]
        elif snap_high:
            bear_a_val = snap_high[1]
            bear_a_bar = snap_high[0]
        else:
            bear_a_val = None
            bear_a_bar = None
        
        atr_ok = True
        if enable_atr:
            atr_ok = (bear_ref_val - close[-1]) >= atr_mult * atr_val
        
        a_dist_ok = True
        if enable_a_dist and bear_a_val is not None:
            a_dist_ok = (bear_a_val - bear_ref_val) >= a_dist_mult * atr_val
        
        c_valid = last_ph and last_ph[0] > bear_ref_bar
        c_val = last_ph[1] if c_valid else None
        
        struct_ok = True
        if enable_struct:
            struct_ok = bear_a_val is not None and c_valid and c_val < bear_a_val
        
        all_filters_ok = atr_ok and a_dist_ok and struct_ok
        
        if all_filters_ok:
            bear_break = {
                "ref_bar": bear_ref_bar,
                "ref_val": round(bear_ref_val, 4),
                "a_val": round(bear_a_val, 4) if bear_a_val else None,
                "a_bar": bear_a_bar,
                "c_val": round(c_val, 4) if c_val else None,
                "c_bar": last_ph[0] if c_valid else None,
                "confirmed": True,
            }
    
    # --- ABCD pattern tracker ---
    abc = track_abcd(df, left_bars, right_bars, cycle_mode, enable_struct)
    
    # --- Supertrend ---
    st = supertrend_adaptive(df, 
        cfg.get("st_period", 10), 
        cfg.get("st_mult", 3.0))
    
    # --- MA Cross ---
    ma_info = ma_cross(df, 
        cfg.get("ma_fast_len", 20),
        cfg.get("ma_slow_len", 50))
    
    # --- Determine phase/phase_label ---
    if bull_break:
        phase = "BULL BREAK"
        phase_label = f"Bull Break @ {bull_break['ref_val']}"
        break_type = "BULL"
        break_confirmed = True
    elif bear_break:
        phase = "BEAR BREAK"
        phase_label = f"Bear Break @ {bear_break['ref_val']}"
        break_type = "BEAR"
        break_confirmed = True
    elif abc and abc.get("phase", 0) > 0:
        phase_num = abc["phase"]
        if phase_num == 1:
            phase_label = "Phase 1: A→B→C? (tracking C)"
            phase = "TRACKING_C"
            break_type = None
            break_confirmed = False
        elif phase_num == 2:
            phase_label = "Phase 2: C locked, D? (tracking D)"
            phase = "TRACKING_D"
            break_type = None
            break_confirmed = False
        else:
            phase_label = "Idle"
            phase = "IDLE"
            break_type = None
            break_confirmed = False
    else:
        phase_label = "Idle (no active pattern)"
        phase = "IDLE"
        break_type = None
        break_confirmed = False
    
    return {
        "phase": phase,
        "phase_label": phase_label,
        "bull_break": bull_break,
        "bear_break": bear_break,
        "break_type": break_type,
        "break_confirmed": break_confirmed,
        "b_level": bull_break["ref_val"] if bull_break else (bear_break["ref_val"] if bear_break else None),
        "abcd": abc,
        "supertrend": st,
        "ma_cross": ma_info,
        "last_pivot_high": last_ph,
        "last_pivot_low": last_pl,
        "atr_val": round(atr_val, 4),
        "raw_bull_break": abc.get("raw_bull_break", False) if abc else False,
        "raw_bear_break": abc.get("raw_bear_break", False) if abc else False,
    }


def track_abcd(df, left_bars, right_bars, cycle_mode, enable_struct):
    """
    ABCD pattern tracker — ported from Pine Script FBF v6.4 Live Tracker (lines 1155-1452).
    Stateful walk through all candles, tracking bull and bear patterns independently.
    
    Pine Script logic:
    - Bull: B = pivot high, A = last pivot low before B (snapLowAtHigh)
    - Bear: B = pivot low, A = last pivot high before B (snapHighAtLow)
    - Phase 0: idle, Phase 1: tracking C, Phase 2: tracking D (Full ABCD only)
    - RESET: bull resets if close < A, bear resets if close > A
    - C lock: pivot confirmed after B, OR close breaks B
    - D break: close breaks B (Full ABCD mode) → pattern complete
    - ABC mode: pattern complete at C lock (phase → 0)
    
    Returns:
        phase, pattern, bull_pattern, bear_pattern,
        raw_bull_break, raw_bear_break,
        last_pivot_high, last_pivot_low
    """
    from collections import defaultdict
    
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    n = len(close)
    
    # Find all pivots
    ph_main, pl_main = find_pivots(high, low, left_bars, right_bars)
    
    # Build pivot event map: confirmed_at_bar -> [(pivot_bar, type, price)]
    # Pivot at bar_idx is confirmed at bar_idx + right_bars (Pine Script behavior)
    pivot_events = defaultdict(list)
    for bar_idx, price in ph_main:
        confirmed_at = bar_idx + right_bars
        if confirmed_at < n:
            pivot_events[confirmed_at].append((bar_idx, "ph", price))
    for bar_idx, price in pl_main:
        confirmed_at = bar_idx + right_bars
        if confirmed_at < n:
            pivot_events[confirmed_at].append((bar_idx, "pl", price))
    
    # Snap points (updated when pivots confirmed, BEFORE last pivot update)
    last_pivot_high = None   # (bar_idx, price)
    last_pivot_low = None
    snap_low_at_high = None  # last pivot low BEFORE most recent pivot high
    snap_high_at_low = None  # last pivot high BEFORE most recent pivot low
    
    # Bull tracker state (Pine: tbPhase, tbA, tbB, tbC, tbD)
    tb_phase = 0
    tb_a = None; tb_a_bar = None
    tb_b = None; tb_b_bar = None
    tb_c = None; tb_c_bar = None
    tb_d = None; tb_d_bar = None
    tb_c_locked = False
    tb_d_broke_b = False
    tb_reset = False
    
    # Bear tracker state (Pine: trPhase, trA, trB, trC, trD)
    tr_phase = 0
    tr_a = None; tr_a_bar = None
    tr_b = None; tr_b_bar = None
    tr_c = None; tr_c_bar = None
    tr_d = None; tr_d_bar = None
    tr_c_locked = False
    tr_d_broke_b = False
    tr_reset = False
    
    # Walk through all bars (simulate Pine Script bar-by-bar processing)
    for i in range(n):
        # --- Get pivots confirmed at this bar ---
        events = pivot_events.get(i, [])
        has_ph = False; ph_val = None; ph_bar = None
        has_pl = False; pl_val = None; pl_bar = None
        for pivot_bar, ptype, price in events:
            if ptype == "ph":
                has_ph = True; ph_val = price; ph_bar = pivot_bar
            elif ptype == "pl":
                has_pl = True; pl_val = price; pl_bar = pivot_bar
        
        # --- Update snap points (BEFORE last pivot update, per Pine Script) ---
        if has_ph:
            snap_low_at_high = last_pivot_low
            last_pivot_high = (ph_bar, ph_val)
        if has_pl:
            snap_high_at_low = last_pivot_high
            last_pivot_low = (pl_bar, pl_val)
        
        # --- Bull tracker ---
        tb_start_ok = False
        if has_ph:
            tb_a_new = snap_low_at_high[1] if snap_low_at_high else None
            tb_a_new_bar = snap_low_at_high[0] if snap_low_at_high else None
            tb_start_ok = (tb_a_new is not None and
                          tb_a_new_bar is not None and
                          tb_a_new < ph_val and
                          tb_a_new_bar < ph_bar)
        
        if tb_start_ok:
            # Start new bull pattern (always replaces old one)
            tb_phase = 1
            tb_a = tb_a_new; tb_a_bar = tb_a_new_bar
            tb_b = ph_val; tb_b_bar = ph_bar
            tb_c = None; tb_c_bar = None
            tb_d = None; tb_d_bar = None
            tb_c_locked = False; tb_d_broke_b = False; tb_reset = False
            # Initial tentative C: scan bars between B and current
            for k in range(right_bars):
                bc = i - k
                if bc > tb_b_bar and bc >= 0:
                    if tb_c is None or low[bc] < tb_c:
                        tb_c = low[bc]; tb_c_bar = bc
        elif tb_phase > 0:
            # Continue tracking
            if close[i] < tb_a:
                # RESET: close below A → pattern invalid
                tb_phase = 0; tb_reset = True
            elif tb_phase == 1:
                # Update tentative C
                if tb_c is None or low[i] < tb_c:
                    tb_c = low[i]; tb_c_bar = i
                # Check C lock: pivot low after B, OR close breaks B
                tb_lock_pivot = has_pl and pl_bar > tb_b_bar
                tb_lock_break = close[i] > tb_b
                if tb_lock_pivot or tb_lock_break:
                    if tb_lock_pivot:
                        c_val = pl_val; c_bar = pl_bar
                    else:
                        c_val = tb_c; c_bar = tb_c_bar
                    tb_ok = not enable_struct or c_val > tb_a
                    if tb_ok:
                        tb_c = c_val; tb_c_bar = c_bar
                        tb_c_locked = True
                        if cycle_mode == "ABC":
                            tb_phase = 0  # Complete at C
                        else:
                            tb_d = high[i]; tb_d_bar = i
                            tb_phase = 2
                    else:
                        tb_phase = 0; tb_reset = True  # Structure fail
            elif tb_phase == 2:
                # Update D
                if tb_d is None or high[i] > tb_d:
                    tb_d = high[i]; tb_d_bar = i
                # Check D break B
                if close[i] > tb_b:
                    tb_d = high[i]; tb_d_bar = i
                    tb_d_broke_b = True
                    tb_phase = 0  # Complete, break occurred
        
        # --- Bear tracker ---
        tr_start_ok = False
        if has_pl:
            tr_a_new = snap_high_at_low[1] if snap_high_at_low else None
            tr_a_new_bar = snap_high_at_low[0] if snap_high_at_low else None
            tr_start_ok = (tr_a_new is not None and
                          tr_a_new_bar is not None and
                          tr_a_new > pl_val and
                          tr_a_new_bar < pl_bar)
        
        if tr_start_ok:
            # Start new bear pattern
            tr_phase = 1
            tr_a = tr_a_new; tr_a_bar = tr_a_new_bar
            tr_b = pl_val; tr_b_bar = pl_bar
            tr_c = None; tr_c_bar = None
            tr_d = None; tr_d_bar = None
            tr_c_locked = False; tr_d_broke_b = False; tr_reset = False
            # Initial tentative C: scan bars between B and current
            for k in range(right_bars):
                bc = i - k
                if bc > tr_b_bar and bc >= 0:
                    if tr_c is None or high[bc] > tr_c:
                        tr_c = high[bc]; tr_c_bar = bc
        elif tr_phase > 0:
            # Continue tracking
            if close[i] > tr_a:
                # RESET: close above A → pattern invalid
                tr_phase = 0; tr_reset = True
            elif tr_phase == 1:
                # Update tentative C
                if tr_c is None or high[i] > tr_c:
                    tr_c = high[i]; tr_c_bar = i
                # Check C lock: pivot high after B, OR close breaks B
                tr_lock_pivot = has_ph and ph_bar > tr_b_bar
                tr_lock_break = close[i] < tr_b
                if tr_lock_pivot or tr_lock_break:
                    if tr_lock_pivot:
                        c_val = ph_val; c_bar = ph_bar
                    else:
                        c_val = tr_c; c_bar = tr_c_bar
                    tr_ok = not enable_struct or c_val < tr_a
                    if tr_ok:
                        tr_c = c_val; tr_c_bar = c_bar
                        tr_c_locked = True
                        if cycle_mode == "ABC":
                            tr_phase = 0  # Complete at C
                        else:
                            tr_d = low[i]; tr_d_bar = i
                            tr_phase = 2
                    else:
                        tr_phase = 0; tr_reset = True  # Structure fail
            elif tr_phase == 2:
                # Update D
                if tr_d is None or low[i] < tr_d:
                    tr_d = low[i]; tr_d_bar = i
                # Check D break B
                if close[i] < tr_b:
                    tr_d = low[i]; tr_d_bar = i
                    tr_d_broke_b = True
                    tr_phase = 0  # Complete, break occurred
    
    # --- Build results ---
    raw_bull_break = last_pivot_high is not None and close[-1] > last_pivot_high[1]
    raw_bear_break = last_pivot_low is not None and close[-1] < last_pivot_low[1]
    
    def build_pattern(direction, phase, a, a_bar, b, b_bar, c, c_bar,
                      d, d_bar, c_locked, d_broke_b):
        p = {
            "direction": direction,
            "a_bar": a_bar, "a_price": round(a, 4) if a is not None else None,
            "b_bar": b_bar, "b_price": round(b, 4) if b is not None else None,
            "c_bar": c_bar, "c_price": round(c, 4) if c is not None else None,
            "phase": phase, "c_locked": c_locked, "struct_ok": True,
        }
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
    
    # Bull pattern: active, completed, or None (reset/idle)
    bull_pattern = None
    if tb_phase > 0:
        bull_pattern = build_pattern("BULL", tb_phase, tb_a, tb_a_bar, tb_b, tb_b_bar,
                                     tb_c, tb_c_bar, tb_d, tb_d_bar, tb_c_locked, tb_d_broke_b)
    elif tb_c_locked and not tb_reset:
        # Completed pattern (C locked in ABC mode, or D broke B in Full ABCD mode)
        bp_phase = 2 if tb_d_broke_b else 1
        bull_pattern = build_pattern("BULL", bp_phase, tb_a, tb_a_bar, tb_b, tb_b_bar,
                                     tb_c, tb_c_bar, tb_d, tb_d_bar, True, tb_d_broke_b)
    
    # Bear pattern: active, completed, or None (reset/idle)
    bear_pattern = None
    if tr_phase > 0:
        bear_pattern = build_pattern("BEAR", tr_phase, tr_a, tr_a_bar, tr_b, tr_b_bar,
                                     tr_c, tr_c_bar, tr_d, tr_d_bar, tr_c_locked, tr_d_broke_b)
    elif tr_c_locked and not tr_reset:
        bp_phase = 2 if tr_d_broke_b else 1
        bear_pattern = build_pattern("BEAR", bp_phase, tr_a, tr_a_bar, tr_b, tr_b_bar,
                                     tr_c, tr_c_bar, tr_d, tr_d_bar, True, tr_d_broke_b)
    
    # Backwards compat
    max_phase = 0
    if bull_pattern: max_phase = max(max_phase, bull_pattern["phase"])
    if bear_pattern: max_phase = max(max_phase, bear_pattern["phase"])
    pattern = None
    candidates = []
    if bull_pattern: candidates.append(("bull", bull_pattern))
    if bear_pattern: candidates.append(("bear", bear_pattern))
    if candidates:
        pattern = max(candidates, key=lambda x: x[1]["b_bar"] or 0)[1]
    
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
    
    # Sort by bar index
    ph_sorted = sorted(ph_main, key=lambda x: x[0])
    pl_sorted = sorted(pl_main, key=lambda x: x[0])
    
    # Bull ABCD: B is a pivot high, A is the pivot low before B
    # Bear ABCD: B is a pivot low, A is the pivot high before B
    
    # Check bull: last pivot high = B, find A = last pivot low before B
    bull_pattern = None
    if ph_sorted:
        b_bar, b_price = ph_sorted[-1]
        
        # Find A = last pivot low before B
        a = None
        for p in pl_sorted:
            if p[0] < b_bar:
                a = p
            else:
                break
        
        if a:
            a_bar, a_price = a
            
            # Find C = lowest point after B
            c_bar = None
            c_price = None
            after_b = [(i, low[i]) for i in range(b_bar + 1, len(close))]
            
            # Track the current lowest after B
            raw_c_bar = b_bar
            raw_c_price = high[b_bar]
            for i in range(b_bar + 1, len(close)):
                if low[i] < (raw_c_price if raw_c_bar != b_bar else high[b_bar]):
                    raw_c_price = low[i]
                    raw_c_bar = i
            
            # Check if there's a pivot low after B that locks C
            locked_c = None
            for p in pl_sorted:
                if p[0] > b_bar:
                    locked_c = p
                    break
            
            c_locked = locked_c is not None and (b_bar + right_bars) < locked_c[0]
            
            # Structure check: C > A
            struct_ok = True
            if enable_struct and locked_c:
                struct_ok = locked_c[1] > a_price
            
            if c_locked and struct_ok:
                c_bar = locked_c[0]
                c_price = locked_c[1]
                
                if cycle_mode == "ABC":
                    # In ABC mode, we stop at C — pattern complete at C
                    bull_pattern = {
                        "direction": "BULL",
                        "a_bar": a_bar, "a_price": round(a_price, 4),
                        "b_bar": b_bar, "b_price": round(b_price, 4),
                        "c_bar": c_bar, "c_price": round(c_price, 4),
                        "phase": 1,
                        "c_locked": True,
                        "struct_ok": struct_ok,
                    }
                else:
                    # Full ABCD: check if D is forming
                    # D = highest after C
                    d_bar = c_bar
                    d_price = low[c_bar]
                    for i in range(c_bar + 1, len(close)):
                        if high[i] > d_price:
                            d_price = high[i]
                            d_bar = i
                    
                    # Check if D broke B
                    d_broke_b = close[-1] > b_price
                    
                    if d_broke_b:
                        bull_pattern = {
                            "direction": "BULL",
                            "a_bar": a_bar, "a_price": round(a_price, 4),
                            "b_bar": b_bar, "b_price": round(b_price, 4),
                            "c_bar": c_bar, "c_price": round(c_price, 4),
                            "d_bar": len(close) - 1, "d_price": round(d_price, 4),
                            "phase": 2,
                            "c_locked": True,
                            "d_broke_b": True,
                            "struct_ok": struct_ok,
                        }
                    else:
                        bull_pattern = {
                            "direction": "BULL",
                            "a_bar": a_bar, "a_price": round(a_price, 4),
                            "b_bar": b_bar, "b_price": round(b_price, 4),
                            "c_bar": c_bar, "c_price": round(c_price, 4),
                            "phase": 2,
                            "c_locked": True,
                            "d_broke_b": False,
                            "struct_ok": struct_ok,
                        }
            else:
                # C not locked yet — tracking
                # Use raw lowest as tentative C
                if raw_c_bar != b_bar:
                    bull_pattern = {
                        "direction": "BULL",
                        "a_bar": a_bar, "a_price": round(a_price, 4),
                        "b_bar": b_bar, "b_price": round(b_price, 4),
                        "c_bar": raw_c_bar, "c_price": round(raw_c_price, 4),
                        "phase": 1,
                        "c_locked": False,
                        "struct_ok": True,
                    }
    
    # Check bear: last pivot low = B, A = last pivot high before B
    bear_pattern = None
    if pl_sorted:
        b_bar, b_price = pl_sorted[-1]
        
        a = None
        for p in ph_sorted:
            if p[0] < b_bar:
                a = p
            else:
                break
        
        if a:
            a_bar, a_price = a
            
            # Find C = highest after B
            raw_c_bar = b_bar
            raw_c_price = low[b_bar]
            for i in range(b_bar + 1, len(close)):
                if high[i] > (raw_c_price if raw_c_bar != b_bar else low[b_bar]):
                    raw_c_price = high[i]
                    raw_c_bar = i
            
            locked_c = None
            for p in ph_sorted:
                if p[0] > b_bar:
                    locked_c = p
                    break
            
            c_locked = locked_c is not None and (b_bar + right_bars) < locked_c[0]
            
            struct_ok = True
            if enable_struct and locked_c:
                struct_ok = locked_c[1] < a_price
            
            if c_locked and struct_ok:
                c_bar = locked_c[0]
                c_price = locked_c[1]
                
                if cycle_mode == "ABC":
                    bear_pattern = {
                        "direction": "BEAR",
                        "a_bar": a_bar, "a_price": round(a_price, 4),
                        "b_bar": b_bar, "b_price": round(b_price, 4),
                        "c_bar": c_bar, "c_price": round(c_price, 4),
                        "phase": 1,
                        "c_locked": True,
                        "struct_ok": struct_ok,
                    }
                else:
                    d_bar = c_bar
                    d_price = high[c_bar]
                    for i in range(c_bar + 1, len(close)):
                        if low[i] < d_price:
                            d_price = low[i]
                            d_bar = i
                    
                    d_broke_b = close[-1] < b_price
                    
                    if d_broke_b:
                        bear_pattern = {
                            "direction": "BEAR",
                            "a_bar": a_bar, "a_price": round(a_price, 4),
                            "b_bar": b_bar, "b_price": round(b_price, 4),
                            "c_bar": c_bar, "c_price": round(c_price, 4),
                            "d_bar": len(close) - 1, "d_price": round(d_price, 4),
                            "phase": 2,
                            "c_locked": True,
                            "d_broke_b": True,
                            "struct_ok": struct_ok,
                        }
                    else:
                        bear_pattern = {
                            "direction": "BEAR",
                            "a_bar": a_bar, "a_price": round(a_price, 4),
                            "b_bar": b_bar, "b_price": round(b_price, 4),
                            "c_bar": c_bar, "c_price": round(c_price, 4),
                            "phase": 2,
                            "c_locked": True,
                            "d_broke_b": False,
                            "struct_ok": struct_ok,
                        }
            else:
                if raw_c_bar != b_bar:
                    bear_pattern = {
                        "direction": "BEAR",
                        "a_bar": a_bar, "a_price": round(a_price, 4),
                        "b_bar": b_bar, "b_price": round(b_price, 4),
                        "c_bar": raw_c_bar, "c_price": round(raw_c_price, 4),
                        "phase": 1,
                        "c_locked": False,
                        "struct_ok": True,
                    }
    
    # Pick most recent pattern for backwards compat
    pattern = None
    candidates = []
    if bull_pattern:
        candidates.append(("bull", bull_pattern))
    if bear_pattern:
        candidates.append(("bear", bear_pattern))
    if candidates:
        pattern = max(candidates, key=lambda x: x[1]["b_bar"])[1]

    # Return BOTH bull and bear patterns for dual-wave detection
    return {
        "phase": max(bull_pattern.get("phase", 0) if bull_pattern else 0,
                     bear_pattern.get("phase", 0) if bear_pattern else 0),
        "pattern": pattern,
        "bull_pattern": bull_pattern,
        "bear_pattern": bear_pattern,
    }