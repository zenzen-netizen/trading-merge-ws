"""
compare_v2a_v2b.py — bandingkan v2.a (sebelum) vs v2.b (sesudah usulan)
window 2021-2026, param SL/TP SAMA (O1-O5 × TP1x/TRAIL/ST_REV/RAWBRK).
"""
import sys, io, contextlib
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
import pandas as pd
import numpy as np

# load v2.a
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import sample_v2a as A
# load v2.b
buf2 = io.StringIO()
with contextlib.redirect_stdout(buf2):
    import sample_v2b as B

print(f"[load] v2.a: {len(A.samples)} signals, v2.b: {len(B.samples)} signals")

df = A.df; high = A.high; low = A.low; close = A.close; n = A.n
st_trend = A.st_trend; events = A.events; ev_by_bar = A.ev_by_bar
E = A.E

# ── precompute bear_active / bear_trigger ──
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
        dist_ok = (rpl - close[i]) >= 0.15 * atr14_arr_vals[i] if not np.isnan(atr14_arr_vals[i]) else False
        if i == 0 or not bear_active[i-1]:
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

def get_sl_tp(entry, Ch, atr14, apct, hi_bar, opt):
    if opt == "O1":
        return entry * 1.10, entry * 0.90
    elif opt == "O2":
        if np.isnan(Ch): return None, None
        sl = Ch + atr14
        if sl <= entry: return None, None
        return sl, 2*entry - sl
    elif opt == "O3":
        sl = entry * (1 + apct/100.0)
        return sl, entry * (1 - apct/100.0)
    elif opt == "O4":
        return entry * 1.06, entry * 0.94
    elif opt == "O5":
        sl = hi_bar + atr14
        if sl <= entry: return None, None
        return sl, 2*entry - sl
    return None, None

def simulate(entry, sl, tp_target, exit_mode, eb, apct):
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    risk = sl - entry
    trail_active = False; lowest = entry
    activation_price = entry * (1 - (apct/2)/100.0)
    raw_trail_active = False; raw_anchor_high = None
    for k in range(min(len(fwd_h), 240)):
        bar_idx = eb + 1 + k
        if exit_mode == "TP1x":
            if fwd_l[k] <= tp_target: return "TP", k+1, 1.0
        if fwd_h[k] >= sl: return "SL", k+1, -1.0
        if exit_mode == "TRAIL":
            if fwd_l[k] < lowest: lowest = fwd_l[k]
            if not trail_active and lowest <= activation_price: trail_active = True
            if trail_active:
                trail_stop = lowest * (1 + apct/100.0)
                if fwd_h[k] >= trail_stop:
                    return "TRAIL", k+1, (entry - trail_stop)/risk
        if exit_mode == "ST_REV":
            if bar_idx < n and st_trend[bar_idx] == 1 and st_trend[bar_idx-1] == -1:
                exit_pr = min(fwd_l[k], entry)
                return "ST_REV", k+1, (entry - exit_pr)/risk
        if exit_mode == "RAWBRK":
            if bar_idx < n and not raw_trail_active and bear_trigger[bar_idx]:
                raw_trail_active = True; raw_anchor_high = high[bar_idx]
            if raw_trail_active:
                if bar_idx < n and high[bar_idx] > raw_anchor_high: raw_anchor_high = high[bar_idx]
                if fwd_h[k] >= raw_anchor_high:
                    return "RAWTRL", k+1, (entry - raw_anchor_high)/risk
                if bar_idx < n and bar_idx > 0 and bear_active[bar_idx-1] and not bear_active[bar_idx]:
                    exit_pr = min(fwd_l[k], entry)
                    return "RAWBRK", k+1, (entry - exit_pr)/risk
    last_close = fwd_l[min(239, len(fwd_l)-1)] if len(fwd_l) > 0 else entry
    return "EXP", min(240, len(fwd_l)), (entry - last_close)/risk

SL_OPTS = ["O1","O2","O3","O4","O5"]
EXIT_MODES = ["TP1x","TRAIL","ST_REV","RAWBRK"]

def run_backtest(samples, label):
    print(f"\n{'='*90}")
    print(f"BACKTEST {label} — 2021-2026 ({len(samples)} trades)")
    print(f"{'='*90}")
    results = []
    for s in samples:
        eb = s["bar"]; entry = s["entry"]; Ch = s["Ch"]
        atr14 = s["atr14"]; apct = s["apct"]; hi_bar = high[eb]
        entry_date = df.index[eb].strftime("%Y-%m-%d")
        for opt in SL_OPTS:
            sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, hi_bar, opt)
            if sl is None:
                for em in EXIT_MODES:
                    results.append({"entry_date":entry_date,"entry":round(entry,2),"opt":opt,
                                    "exit":em,"sl":None,"tp":None,"apct":round(apct,2),
                                    "outcome":"INV","bars":0,"R":0.0})
                continue
            for em in EXIT_MODES:
                tp_target = tp1 if em == "TP1x" else None
                outcome, bars, R = simulate(entry, sl, tp_target, em, eb, apct)
                results.append({"entry_date":entry_date,"entry":round(entry,2),"opt":opt,
                                "exit":em,"sl":round(sl,2),"tp":round(tp_target,2) if tp_target else None,
                                "apct":round(apct,2),"outcome":outcome,"bars":bars,"R":round(R,3)})

    # summary
    print(f"\n{'COMBO':<14}{'Tr':>5}{'TP':>5}{'SL':>5}{'TRL':>5}{'SRV':>5}{'RTL':>5}{'RBK':>5}{'EXP':>5}{'INV':>5}{'WR%':>8}{'TotR':>9}{'AvgR':>8}{'AvgB':>6}")
    print("-"*92)
    for opt in SL_OPTS:
        for em in EXIT_MODES:
            sub = [r for r in results if r["opt"]==opt and r["exit"]==em]
            valid = [r for r in sub if r["outcome"]!="INV"]
            if not valid: continue
            c = {}
            for r in valid: c[r["outcome"]] = c.get(r["outcome"],0)+1
            n_tr=len(valid)
            tp_c=c.get("TP",0); sl_c=c.get("SL",0); trl_c=c.get("TRAIL",0)
            srv_c=c.get("ST_REV",0); rtl_c=c.get("RAWTRL",0); rbk_c=c.get("RAWBRK",0); exp_c=c.get("EXP",0)
            inv_c=len([r for r in sub if r["outcome"]=="INV"])
            wins=tp_c+trl_c+srv_c+rtl_c+rbk_c; losses=sl_c; tc=wins+losses
            wr=wins/tc*100 if tc>0 else 0
            totR=sum(r["R"] for r in valid); avgR=totR/n_tr
            avgB=sum(r["bars"] for r in valid)/n_tr
            print(f"{opt+' '+em:<14}{n_tr:>5}{tp_c:>5}{sl_c:>5}{trl_c:>5}{srv_c:>5}{rtl_c:>5}{rbk_c:>5}{exp_c:>5}{inv_c:>5}{wr:>7.1f}%{totR:>+9.2f}{avgR:>+8.3f}{avgB:>6.0f}")
    return results

# ── run both ──
res_a = run_backtest(A.samples, "v2.a (SEBELUM usulan)")
res_b = run_backtest(B.samples, "v2.b (SESADAH usulan - 5 gate)")

# ── compare signal lists ──
print(f"\n\n{'='*90}")
print("SIGNAL COMPARISON (entry dates)")
print(f"{'='*90}")
dates_a = [df.index[s["bar"]].strftime("%Y-%m-%d") for s in A.samples]
dates_b = [df.index[s["bar"]].strftime("%Y-%m-%d") for s in B.samples]
print(f"\nv2.a ({len(dates_a)}): {dates_a}")
print(f"v2.b ({len(dates_b)}): {dates_b}")
only_a = [d for d in dates_a if d not in dates_b]
only_b = [d for d in dates_b if d not in dates_a]
print(f"\nOnly in v2.a (filtered OUT by v2.b): {only_a}")
print(f"Only in v2.b (added): {only_b}")

# ── net R per exit mode (avg over all SL) ──
print(f"\n{'='*90}")
print("NET R by EXIT MODE (sum over O1-O5, valid trades)")
print(f"{'='*90}")
print(f"{'EXIT':<10}{'v2.a TotR':>14}{'v2.a WR%':>11}{'v2.b TotR':>14}{'v2.b WR%':>11}")
for em in EXIT_MODES:
    for version, res in [("v2.a", res_a), ("v2.b", res_b)]:
        sub=[r for r in res if r["exit"]==em and r["outcome"]!="INV"]
        totR=sum(r["R"] for r in sub); n_tr=len(sub)
        wins=sum(1 for r in sub if r["R"]>0); losses=sum(1 for r in sub if r["R"]<0)
        tc=wins+losses; wr=wins/tc*100 if tc>0 else 0
        if version=="v2.a":
            aR=totR; aWR=wr
        else:
            bR=totR; bWR=wr
    print(f"{em:<10}{aR:>+14.2f}{aWR:>10.1f}%{bR:>+14.2f}{bWR:>10.1f}%")

print("\nDone.")
