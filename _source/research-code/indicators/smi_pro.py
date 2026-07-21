"""
SMI Pro Enhanced v3 — Python port of TradingView Pine Script indicator.
Calculates SMI (Stochastic Momentum Index), histogram momentum states,
PA/PD phases, cross detection, divergence, and bar state classification.
"""

import pandas as pd
import numpy as np


def ema_ema(series, length):
    """Double EMA — ta.ema(ta.ema(s, l), l)"""
    return series.ewm(span=length, adjust=False).mean().ewm(span=length, adjust=False).mean()


def smi_pro_v3(df, cfg):
    """
    Calculate SMI Pro v3 indicator.

    Args:
        df: DataFrame with columns ['open','high','low','close','volume']
            (sorted ascending by timestamp, oldest first)
        cfg: dict with keys:
            len_k, len_d, len_e, ob, mid, os,
            akum_candles, dist_candles,
            div_enabled, div_hidden, div_left, div_right,
            div_range_min, div_range_max

    Returns:
        dict with latest indicator state:
            smi, smi_ema, smi_hist,
            zone, zone_label, hist_state, vs_ema,
            signal, signal_strength, strength_bar,
            pa_pd_text, bar_state, bar_state_emoji,
            cross_up, cross_down, cross_mid_up, cross_mid_down,
            entered_ob, entered_os, exited_ob, exited_os,
            divergence (list of recent divergences),
            consecutive_below, consecutive_above  # for PA/PD counter
    """
    len_k = cfg.get("len_k", 5)
    len_d = cfg.get("len_d", 3)
    len_e = cfg.get("len_e", 3)
    ob = cfg.get("ob", 80)
    mid = cfg.get("mid", 0)
    os_ = cfg.get("os", -40)
    akum_candles = cfg.get("akum_candles", 2)
    dist_candles = cfg.get("dist_candles", 2)

    close = df["close"]
    high = df["high"]
    low = df["low"]

    # SMI calculation
    hh = high.rolling(window=len_k, min_periods=len_k).max()
    ll = low.rolling(window=len_k, min_periods=len_k).min()
    rel = close - (hh + ll) / 2
    rng = hh - ll

    # Avoid division by zero
    rng_safe = rng.replace(0, np.nan)
    smi = 200 * (ema_ema(rel, len_d) / ema_ema(rng_safe, len_d))
    smi_ema = smi.ewm(span=len_e, adjust=False).mean()
    smi_hist = smi - smi_ema

    # End of array values
    smi_val = smi.iloc[-1]
    smi_ema_val = smi_ema.iloc[-1]
    smi_hist_val = smi_hist.iloc[-1]
    smi_hist_prev = smi_hist.iloc[-2] if len(smi_hist) > 1 else 0

    # --- Zone classification ---
    if smi_val > ob:
        zone = "OB"
        zone_label = "OB Zone"
    elif smi_val > mid:
        zone = "Upper N"
        zone_label = "Upper Normal"
    elif smi_val > 0:
        zone = "Middle"
        zone_label = "Middle"
    elif smi_val > os_:
        zone = "Lower N"
        zone_label = "Lower Normal"
    else:
        zone = "OS"
        zone_label = "OS Zone"

    # --- vs EMA ---
    s_ab = smi_val >= smi_ema_val
    vs_ema = "Bull" if s_ab else "Bear"

    # --- Histogram momentum states ---
    # AU: SMI>EMA, hist rising (bull kuat)
    # AD: SMI>EMA, hist falling (bull lemah)
    # BD: SMI<EMA, hist falling (bear kuat)
    # BU: SMI<EMA, hist rising (bear lemah)
    if smi_hist_val > 0:
        hist_state = "Exp Bull" if smi_hist_val > smi_hist_prev else "Shr Bull"
    else:
        hist_state = "Shr Bear" if smi_hist_val < smi_hist_prev else "Exp Bear"

    # --- Cross detection ---
    cross_up = False
    cross_down = False
    if len(smi) >= 2:
        prev_smi = smi.iloc[-2]
        prev_ema = smi_ema.iloc[-2]
        if prev_smi < prev_ema and smi_val >= smi_ema_val:
            cross_up = True
        elif prev_smi > prev_ema and smi_val <= smi_ema_val:
            cross_down = True

    # --- Cross MID (0-line) ---
    cross_mid_up = False
    cross_mid_down = False
    if len(smi) >= 2:
        prev_smi = smi.iloc[-2]
        if prev_smi < mid and smi_val >= mid:
            cross_mid_up = True
        elif prev_smi > mid and smi_val <= mid:
            cross_mid_down = True

    # --- Enter/Exit OB/OS zones ---
    entered_ob = False
    entered_os = False
    exited_ob = False
    exited_os = False
    if len(smi) >= 2:
        prev_smi = smi.iloc[-2]
        # Enter OB
        if prev_smi <= ob and smi_val > ob:
            entered_ob = True
        # Exit OB
        if prev_smi > ob and smi_val <= ob:
            exited_ob = True
        # Enter OS
        if prev_smi >= os_ and smi_val < os_:
            entered_os = True
        # Exit OS
        if prev_smi < os_ and smi_val >= os_:
            exited_os = True

    # --- PA/PD counter (only count the MOST RECENT consecutive streak) ---
    consecutive_above = 0
    consecutive_below = 0
    latest_smi = smi.iloc[-1]
    if latest_smi > mid:
        # Count consecutive candles above mid from latest backwards
        for i in range(len(smi) - 1, -1, -1):
            if smi.iloc[i] > mid:
                consecutive_above += 1
            else:
                break
    elif latest_smi < mid:
        # Count consecutive candles below mid from latest backwards
        for i in range(len(smi) - 1, -1, -1):
            if smi.iloc[i] < mid:
                consecutive_below += 1
            else:
                break
    # If latest is exactly at mid, both stay 0

    # --- PA/PD detection ---
    pa_momentum_rising = smi_hist_val >= smi_hist_prev
    pa_momentum_falling = smi_hist_val < smi_hist_prev

    pre_akum = consecutive_below == akum_candles
    pre_dist = consecutive_above == dist_candles

    pa_dip = pre_akum and pa_momentum_falling
    pa_ready = pre_akum and pa_momentum_rising
    pd_dip = pre_dist and pa_momentum_rising
    pd_ready = pre_dist and pa_momentum_falling

    # --- Failed MID hold ---
    failed_mid_buy = False
    failed_mid_sell = False
    if len(smi) >= 2 and len(smi) >= 3:
        # failedMIDHoldBuy: SMI > MID now, was < MID before, previous had consecutive_below > 0
        if smi_val > mid and smi.iloc[-2] < mid:
            # Check if there was bear streak before
            prev_below = False
            if len(smi) >= 3:
                # Count how many consecutive below before the cross
                count_b = 0
                for v in smi.iloc[-2::-1]:
                    if v < mid:
                        count_b += 1
                    else:
                        break
                if count_b > 0:
                    failed_mid_buy = True

        # failedMIDHoldSell: SMI < MID now, was > MID before, previous had consecutive_above > 0
        if smi_val < mid and smi.iloc[-2] > mid:
            count_a = 0
            for v in smi.iloc[-2::-1]:
                if v > mid:
                    count_a += 1
                else:
                    break
            if count_a > 0:
                failed_mid_sell = True

    # --- PA/PD text ---
    if pa_ready:
        pa_pd_text = "PA - Siap Balik"
    elif pa_dip:
        pa_pd_text = "PA - Dip Mungkin"
    elif pd_ready:
        pa_pd_text = "PD - Siap Balik"
    elif pd_dip:
        pa_pd_text = "PD - Dip Mungkin"
    elif consecutive_below > 0:
        if consecutive_below < akum_candles:
            pa_pd_text = f"PA {consecutive_below}/{akum_candles}"
        else:
            pa_pd_text = "PA TRIGGERED"
    elif consecutive_above > 0:
        if consecutive_above < dist_candles:
            pa_pd_text = f"PD {consecutive_above}/{dist_candles}"
        else:
            pa_pd_text = "PD TRIGGERED"
    else:
        pa_pd_text = "-"

    # --- Signal ---
    if smi_val > ob and not s_ab:
        signal = "STR SELL"
    elif smi_val < os_ and s_ab:
        signal = "STR BUY"
    elif s_ab and smi_val > 0:
        signal = "BUY"
    elif not s_ab and smi_val < 0:
        signal = "SELL"
    else:
        signal = "NEUTRAL"

    # --- Signal strength bar ---
    if signal in ("STR BUY", "STR SELL"):
        strength_val = 90
    elif signal in ("BUY", "SELL"):
        strength_val = 70
    else:
        strength_val = 30
    filled = strength_val // 10
    strength_bar = "🟦" * filled + "─" * (10 - filled)

    # --- Bar state cascade (priority order) ---
    if cross_up:
        bar_state = "[X] Cross UP"
        bar_state_emoji = "⚡"
    elif cross_down:
        bar_state = "[X] Cross DN"
        bar_state_emoji = "⚡"
    elif smi_val > ob:
        bar_state = "[!!] OB Zone"
        bar_state_emoji = "🔴"
    elif smi_val < os_:
        bar_state = "[!!] OS Zone"
        bar_state_emoji = "🟢"
    elif pa_dip:
        bar_state = "[~] PA - Dip Mungkin"
        bar_state_emoji = "🟡"
    elif pa_ready:
        bar_state = "[OK] PA - Siap Balik"
        bar_state_emoji = "🟢"
    elif pd_dip:
        bar_state = "[~] PD - Dip Mungkin"
        bar_state_emoji = "🟠"
    elif pd_ready:
        bar_state = "[OK] PD - Siap Balik"
        bar_state_emoji = "🟠"
    elif failed_mid_buy:
        bar_state = "[!] Fail MID Buy"
        bar_state_emoji = "⚠️"
    elif failed_mid_sell:
        bar_state = "[!] Fail MID Sell"
        bar_state_emoji = "⚠️"
    elif smi_val < mid:
        bar_state = "[B] Bias Bawah"
        bar_state_emoji = "⬇️"
    elif smi_val > mid:
        bar_state = "[S] Bias Atas"
        bar_state_emoji = "⬆️"
    else:
        bar_state = "[-] Netral"
        bar_state_emoji = "➖"

    return {
        "smi": round(smi_val, 2),
        "smi_ema": round(smi_ema_val, 2),
        "smi_hist": round(smi_hist_val, 2),
        "zone": zone,
        "zone_label": zone_label,
        "hist_state": hist_state,
        "vs_ema": vs_ema,
        "signal": signal,
        "strength_bar": strength_bar,
        "pa_pd_text": pa_pd_text,
        "bar_state": bar_state,
        "bar_state_emoji": bar_state_emoji,
        "cross_up": cross_up,
        "cross_down": cross_down,
        "cross_mid_up": cross_mid_up,
        "cross_mid_down": cross_mid_down,
        "entered_ob": entered_ob,
        "entered_os": entered_os,
        "exited_ob": exited_ob,
        "exited_os": exited_os,
        "consecutive_below": consecutive_below,
        "consecutive_above": consecutive_above,
        "pa_dip": pa_dip,
        "pa_ready": pa_ready,
        "pd_dip": pd_dip,
        "pd_ready": pd_ready,
    }


def detect_smi_divergence(df, smi_series, cfg):
    """
    Detect bullish/bearish divergence using pivot detection on SMI vs price.
    Returns list of recent divergences.
    """
    div_left = cfg.get("div_left", 5)
    div_right = cfg.get("div_right", 5)
    div_range_min = cfg.get("div_range_min", 5)
    div_range_max = cfg.get("div_range_max", 60)
    div_hidden = cfg.get("div_hidden", False)

    smi = smi_series.values
    highs = df["high"].values
    lows = df["low"].values

    # Find pivot lows and highs
    pivot_lows = []
    pivot_highs = []

    for i in range(div_left, len(smi) - div_right):
        # Pivot low: SMI[i] is the lowest in [i-div_left, i+div_right]
        is_pl = True
        for j in range(i - div_left, i + div_right + 1):
            if j != i and smi[j] <= smi[i]:
                is_pl = False
                break
        if is_pl:
            pivot_lows.append((i, smi[i], lows[i]))

        # Pivot high
        is_ph = True
        for j in range(i - div_left, i + div_right + 1):
            if j != i and smi[j] >= smi[i]:
                is_ph = False
                break
        if is_ph:
            pivot_highs.append((i, smi[i], highs[i]))

    divergences = []

    # Check regular bullish: price lower low, SMI higher low
    if len(pivot_lows) >= 2:
        pl1 = pivot_lows[-2]
        pl2 = pivot_lows[-1]
        bar_gap = pl2[0] - pl1[0]
        if div_range_min <= bar_gap <= div_range_max:
            if pl2[2] < pl1[2] and pl2[1] > pl1[1]:  # price LL, SMI HL
                divergences.append({
                    "type": "bullish",
                    "bar_idx": pl2[0],
                    "smi_val": pl2[1],
                })
            if div_hidden:
                if pl2[2] > pl1[2] and pl2[1] < pl1[1]:  # price HL, SMI LL
                    divergences.append({
                        "type": "hidden_bullish",
                        "bar_idx": pl2[0],
                        "smi_val": pl2[1],
                    })

    # Check regular bearish: price higher high, SMI lower high
    if len(pivot_highs) >= 2:
        ph1 = pivot_highs[-2]
        ph2 = pivot_highs[-1]
        bar_gap = ph2[0] - ph1[0]
        if div_range_min <= bar_gap <= div_range_max:
            if ph2[2] > ph1[2] and ph2[1] < ph1[1]:  # price HH, SMI LH
                divergences.append({
                    "type": "bearish",
                    "bar_idx": ph2[0],
                    "smi_val": ph2[1],
                })
            if div_hidden:
                if ph2[2] < ph1[2] and ph2[1] > ph1[1]:  # price LH, SMI HH
                    divergences.append({
                        "type": "hidden_bearish",
                        "bar_idx": ph2[0],
                        "smi_val": ph2[1],
                    })

    return divergences