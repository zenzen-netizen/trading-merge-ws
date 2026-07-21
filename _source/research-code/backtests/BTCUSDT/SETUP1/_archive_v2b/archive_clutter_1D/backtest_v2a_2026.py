"""
backtest_v2a_2026.py — quick backtest SETUP1 v2.a, 2026 only.
Combo: 5 SL (O1-O5) × 4 exit (TP1x, TRAIL, ST_REV, RAWBRK) = 20 combo.
"""
import sys, io, contextlib
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
import datetime as _dt
import pandas as pd
import numpy as np
import csv

# ── load sample_v2a module (suppress its prints) ──
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import sample_v2a as S

df = S.df; high = S.high; low = S.low; close = S.close; n = S.n
st_trend = S.st_trend; events = S.events; ev_by_bar = S.ev_by_bar
E = S.E
samples_all = S.samples

print(f"[load] {len(df)} candles, {len(samples_all)} signals total")

# ── filter 2026 only ──
cut = pd.Timestamp("2026-01-01", tz="UTC")
samples = [s for s in samples_all if df.index[s["bar"]] >= cut]
print(f"[filter] {len(samples)} signals in 2026")

if not samples:
    print("[!] No 2026 signals. Latest signals:")
    for s in samples_all[-5:]:
        print(f"  bar {s['bar']} {df.index[s['bar']]} entry={s['entry']:.2f}")
    sys.exit(1)

# ── precompute bear_active / bear_trigger for RAWBRK ──
# pivot lows from FBF v11 events
pl_by_idx = {}
for e in events:
    if e["event"] == "WAVE_STARTED" and e["side"] == "bear":
        pl_by_idx[e["b_bar"]] = e["b_val"]

running_last_pl = np.full(n, np.nan)
last_pl_val = None
for i in range(n):
    if i in pl_by_idx:
        last_pl_val = pl_by_idx[i]
    running_last_pl[i] = last_pl_val

# ATR14 for FBF distance check
def atr14_arr(high, low, close, period=14):
    tr = np.zeros(len(close))
    tr[0] = high[0] - low[0]
    for i in range(1, len(close)):
        tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
    atr = np.zeros(len(close))
    atr[0] = tr[0]
    alpha = 1.0/period
    for i in range(1, len(close)):
        atr[i] = atr[i-1] + alpha*(tr[i]-atr[i-1])
    return atr
atr14_arr_vals = atr14_arr(high, low, close, 14)

bear_active = np.zeros(n, dtype=bool)
bear_active_high = np.full(n, np.nan)
prev_active_high = np.nan
for i in range(n):
    rpl = running_last_pl[i]
    if np.isnan(rpl):
        bear_active[i] = False
    else:
        raw_bear = close[i] < rpl
        if not np.isnan(atr14_arr_vals[i]):
            dist_ok = (rpl - close[i]) >= 0.15 * atr14_arr_vals[i]
        else:
            dist_ok = False
        if not bear_active[i-1] if i > 0 else not False:
            if raw_bear and dist_ok:
                bear_active[i] = True
        else:
            still_beyond = close[i] < rpl
            dist_ok2 = (rpl - close[i]) >= 0.15 * atr14_arr_vals[i] if not np.isnan(atr14_arr_vals[i]) else False
            if still_beyond and dist_ok2:
                bear_active[i] = True
    if bear_active[i]:
        bear_active_high[i] = max(prev_active_high, high[i]) if not np.isnan(prev_active_high) else high[i]
        prev_active_high = bear_active_high[i]
    else:
        prev_active_high = np.nan

bear_trigger = np.zeros(n, dtype=bool)
for i in range(1, n):
    if bear_active[i] and not bear_active[i-1]:
        bear_trigger[i] = True

# ── helpers ──
def atr14_at(i):
    return atr14_arr_vals[i]

def atr_pct_at(i):
    import atr_percentage as atrp
    return atrp.atr_percentage(df.iloc[:i+1], S.ATR_PCT_CFG)["atr_pct"]

# ── SL options ──
def get_sl_tp(entry, Ch, atr14, apct, hi_bar, opt):
    """Returns (sl, tp1x) or (None, None) if invalid (e.g., O2/O5 without C)."""
    if opt == "O1":
        return entry * 1.10, entry * 0.90
    elif opt == "O2":
        if np.isnan(Ch):
            return None, None
        sl = Ch + atr14
        if sl <= entry:
            return None, None  # invalid trade
        tp = 2*entry - sl
        return sl, tp
    elif opt == "O3":
        sl = entry * (1 + apct/100.0)
        tp = entry * (1 - apct/100.0)
        return sl, tp
    elif opt == "O4":
        return entry * 1.06, entry * 0.94
    elif opt == "O5":
        sl = hi_bar + atr14
        if sl <= entry:
            return None, None
        tp = 2*entry - sl
        return sl, tp
    return None, None

# ── simulate one combo ──
def simulate(entry, sl, tp_target, exit_mode, eb, apct):
    """
    exit_mode: "TP1x", "TRAIL", "ST_REV", "RAWBRK"
    Returns (outcome, bars_held, R_multiple)
    """
    fwd_h = high[eb+1:]
    fwd_l = low[eb+1:]
    risk = sl - entry

    # TRAIL state
    trail_active = False
    lowest = entry
    activation_price = entry * (1 - (apct/2)/100.0)

    # RAWBRK state
    raw_trail_active = False
    raw_anchor_high = None

    for k in range(min(len(fwd_h), 240)):
        bar_idx = eb + 1 + k

        # ── TP check (for TP1x) ──
        if exit_mode == "TP1x":
            if fwd_l[k] <= tp_target:
                return "TP", k+1, 1.0  # 1R win

        # ── SL check (all modes) ──
        if fwd_h[k] >= sl:
            return "SL", k+1, -1.0

        # ── TP check for TRAIL/ST_REV/RAWBRK (no fixed TP, skip) ──
        # (only TP1x has a price target; others rely on their own exit)

        # ── TRAIL (ATR%) ──
        if exit_mode == "TRAIL":
            if fwd_l[k] < lowest:
                lowest = fwd_l[k]
            if not trail_active and lowest <= activation_price:
                trail_active = True
            if trail_active:
                trail_stop = lowest * (1 + apct/100.0)
                if fwd_h[k] >= trail_stop:
                    R = (entry - trail_stop) / risk
                    return "TRAIL", k+1, R

        # ── ST_REV ──
        if exit_mode == "ST_REV":
            if bar_idx < len(st_trend) and st_trend[bar_idx] == 1 and st_trend[bar_idx-1] == -1:
                exit_pr = min(fwd_l[k], entry)  # conservative: exit at low or entry
                R = (entry - exit_pr) / risk
                return "ST_REV", k+1, R

        # ── RAWBRK ──
        if exit_mode == "RAWBRK":
            # Check if a new rawbreak trigger fires during trade
            if bar_idx < n and not raw_trail_active and bear_trigger[bar_idx]:
                raw_trail_active = True
                raw_anchor_high = high[bar_idx]
            if raw_trail_active:
                # ratchet anchor
                if bar_idx < n and high[bar_idx] > raw_anchor_high:
                    raw_anchor_high = high[bar_idx]
                # check if price hits anchor (exit)
                if fwd_h[k] >= raw_anchor_high:
                    R = (entry - raw_anchor_high) / risk
                    return "RAWTRL", k+1, R
                # check if break lost (active -> inactive)
                if bar_idx < n and bar_idx > 0 and bear_active[bar_idx-1] and not bear_active[bar_idx]:
                    exit_pr = min(fwd_l[k], entry)
                    R = (entry - exit_pr) / risk
                    return "RAWBRK", k+1, R

    # ── EXPIRED ──
    last_close = fwd_l[min(239, len(fwd_l)-1)] if len(fwd_l) > 0 else entry
    R = (entry - last_close) / risk
    return "EXP", min(240, len(fwd_l)), R

# ── run all combos ──
SL_OPTS = ["O1", "O2", "O3", "O4", "O5"]
EXIT_MODES = ["TP1x", "TRAIL", "ST_REV", "RAWBRK"]

print(f"\n{'='*80}")
print(f"BACKTEST SETUP1 v2.a — 2026 only ({len(samples)} trades)")
print(f"{'='*80}")

results = []  # list of dicts

for idx, s in enumerate(samples):
    eb = s["bar"]
    entry = s["entry"]
    Ch = s["Ch"]
    atr14 = s["atr14"]
    apct = s["apct"]
    hi_bar = high[eb]
    entry_date = df.index[eb].strftime("%Y-%m-%d")

    for opt in SL_OPTS:
        sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, hi_bar, opt)
        if sl is None:
            # invalid trade (e.g., O2/O5 without C, or SL <= entry)
            for em in EXIT_MODES:
                results.append({
                    "entry_date": entry_date, "entry": round(entry, 2),
                    "opt": opt, "exit": em,
                    "sl": None, "tp": None, "apct": round(apct, 2),
                    "outcome": "INV", "bars": 0, "R": 0.0
                })
            continue

        for em in EXIT_MODES:
            tp_target = tp1 if em == "TP1x" else None
            outcome, bars, R = simulate(entry, sl, tp_target, em, eb, apct)
            results.append({
                "entry_date": entry_date, "entry": round(entry, 2),
                "opt": opt, "exit": em,
                "sl": round(sl, 2), "tp": round(tp_target, 2) if tp_target else None,
                "apct": round(apct, 2),
                "outcome": outcome, "bars": bars, "R": round(R, 3)
            })

# ── summary per combo ──
print(f"\n{'COMBO':<14} {'Tr':>4} {'TP':>4} {'SL':>4} {'TRL':>4} {'SRV':>4} {'RTL':>4} {'RBK':>4} {'EXP':>4} {'INV':>4} {'WR%':>7} {'TotR':>8} {'AvgR':>7} {'AvgB':>5}")
print("-"*85)

for opt in SL_OPTS:
    for em in EXIT_MODES:
        sub = [r for r in results if r["opt"] == opt and r["exit"] == em]
        valid = [r for r in sub if r["outcome"] != "INV"]
        if not valid:
            continue
        counts = {}
        for r in valid:
            counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
        n_tr = len(valid)
        tp_c = counts.get("TP", 0)
        sl_c = counts.get("SL", 0)
        trl_c = counts.get("TRAIL", 0)
        srv_c = counts.get("ST_REV", 0)
        rtl_c = counts.get("RAWTRL", 0)
        rbk_c = counts.get("RAWBRK", 0)
        exp_c = counts.get("EXP", 0)
        inv_c = len([r for r in sub if r["outcome"] == "INV"])

        wins = tp_c + trl_c + srv_c + rtl_c + rbk_c
        losses = sl_c
        total_closed = wins + losses
        wr = wins/total_closed*100 if total_closed > 0 else 0
        total_R = sum(r["R"] for r in valid)
        avg_R = total_R/n_tr if n_tr > 0 else 0
        avg_bars = sum(r["bars"] for r in valid)/n_tr if n_tr > 0 else 0

        label = f"{opt}+{em}"
        print(f"{label:<14} {n_tr:>4} {tp_c:>4} {sl_c:>4} {trl_c:>4} {srv_c:>4} {rtl_c:>4} {rbk_c:>4} {exp_c:>4} {inv_c:>4} {wr:>6.1f}% {total_R:>+8.2f} {avg_R:>+7.3f} {avg_bars:>5.0f}")

# ── per-trade detail ──
print(f"\n{'='*80}")
print("PER-TRADE DETAIL (2026 only)")
print(f"{'='*80}")
print(f"{'Date':<12} {'Entry':>10} {'Opt':>4} {'Exit':>7} {'SL':>10} {'TP':>10} {'apct%':>6} {'Out':>7} {'Bars':>5} {'R':>8}")
print("-"*85)
for r in results:
    if r["outcome"] == "INV":
        continue
    sl_s = f"{r['sl']:.2f}" if r['sl'] else "n/a"
    tp_s = f"{r['tp']:.2f}" if r['tp'] else "-"
    print(f"{r['entry_date']:<12} {r['entry']:>10.2f} {r['opt']:>4} {r['exit']:>7} {sl_s:>10} {tp_s:>10} {r['apct']:>6.2f} {r['outcome']:>7} {r['bars']:>5} {r['R']:>+8.3f}")

print(f"\nDone. {len(results)} rows total.")
