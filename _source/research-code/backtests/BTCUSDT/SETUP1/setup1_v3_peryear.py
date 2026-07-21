#!/usr/bin/env python3
"""
setup1_v3_peryear.py — Per-year OLD vs NEW comparison.
Same SL/TP/trail logic as the watcher cron.
Goal: quantify how much the cross-wave bug skewed backtest results.
"""
import sys, os, time, json, datetime as _dt
import pandas as pd, numpy as np

sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu")

import smi_events as SM
import fbf_v11_backtest as V11
import atr_percentage as atrp

# Shared module — source of truth for trigger logic
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
from setup1_trigger import (
    supertrend_full, find_pivot_lows, detect_signals_v3,
    sim_rawbrk, sim_strev, ATR_PCT_CFG
)

SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

BASE = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1"

TF_CONFIGS = [
    ("1D", f"{BASE}/1D/data_BTCUSDT_1d_2019now.csv", 86400000,  "1d"),
    ("4H", f"{BASE}/4H/data_BTCUSDT_4h_2019now.csv", 14400000, "4h"),
    ("2H", f"{BASE}/2H/data_BTCUSDT_2h_2019now.csv",  7200000, "2h"),
    ("1H", f"{BASE}/1H/data_BTCUSDT_1h_2019now.csv",  3600000, "1h"),
]

# ─── DETECT OLD (buggy v2.b — for comparison) ───
def detect_old(df, high, low, close, st_trend, E, ev_by_bar, n):
    """BUGGY v2.b trigger (cross-wave carry-over), but same clear_bar logic as v3."""
    FMB, PD, XDN = E["FMB"], E["PD"], E["XDN"]
    samples = []
    pos_open = False; clear_bar = -1; fmb_b = None; pd_b = None; wave_entry_done = False
    for i in range(n):
        if pos_open:
            if i >= clear_bar: pos_open = False; clear_bar = -1
            else: continue
        for e in ev_by_bar.get(i, []):
            if e.get("side") != "bear": continue
            if e["event"] == "WAVE_STARTED":
                wave_entry_done = False
                if pd_b is None: fmb_b = None   # ← BUG #4
            elif e["event"] in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED","CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
                fmb_b = None; pd_b = None; wave_entry_done = False
        if not wave_entry_done:
            if FMB[i] and fmb_b is None: fmb_b = i
            if fmb_b is not None and pd_b is None and PD[i] and i >= fmb_b: pd_b = i
            if fmb_b is not None and pd_b is not None and XDN[i] and i >= pd_b:
                if st_trend[i] == -1:
                    entry_val = float(close[i])
                    apct_current = atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]
                    samples.append(dict(bar=i, entry=entry_val, date=df.index[i]))
                    # Same O3-based clear_bar as v3
                    sl0 = entry_val * (1 + apct_current/100.0)
                    tp0 = entry_val - (sl0 - entry_val)
                    fwd_h = high[i+1:]; fwd_l = low[i+1:]; ck = 240
                    for k in range(len(fwd_h)):
                        if fwd_l[k] <= tp0 or fwd_h[k] >= sl0 or k >= 240: ck = k; break
                    clear_bar = i + 1 + ck; pos_open = True; wave_entry_done = True
                fmb_b = None; pd_b = None
    return samples

def detect_new(df, high, low, close, st_trend, E, ev_by_bar, n):
    """Alias for shared detect_signals_v3."""
    # Import from shared module — same logic as watcher
    return detect_signals_v3(df, high, low, close, st_trend, E, ev_by_bar)

# ─── PER-TF ANALYSIS ───
def analyze_tf(tf_name, csv_path, iv_ms, tf_binance):
    print(f"\n{'='*65}")
    print(f"  {tf_name}")
    print(f"{'='*65}")

    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    now_utc = _dt.datetime.now(_dt.timezone.utc)
    last_ct_utc = df.index[-1] + _dt.timedelta(milliseconds=iv_ms)
    if now_utc < last_ct_utc and len(df) > 1:
        df = df.iloc[:-1]
    n = len(df)
    print(f"  Candles: {n}")
    
    high = df["high"].values.astype(float)
    low  = df["low"].values.astype(float)
    close = df["close"].values.astype(float)
    st_trend = supertrend_full(high, low, close)
    
    E = SM.compute_smi_events(df, SMI_CFG)
    
    times = [int(t.value // 1_000_000) for t in df.index]
    eng = V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, iv_ms)
    breaks, events = eng.run()
    ev_by_bar = {}
    for e in events: ev_by_bar.setdefault(e["bar"], []).append(e)

    # Trigger
    old_s = detect_old(df, high, low, close, st_trend, E, ev_by_bar, n)
    new_s = detect_new(df, high, low, close, st_trend, E, ev_by_bar, n)
    
    # Pivot
    pl_arr = find_pivot_lows(low, 3, 3)
    pl_dict = {bar: val for val, bar in pl_arr}

    # Preload daily ATR% for O6
    daily_apct = None
    if tf_name != "1D":
        df1d_path = f"{BASE}/1D/data_BTCUSDT_1d_2019now.csv"
        if os.path.exists(df1d_path):
            df1d = pd.read_csv(df1d_path, index_col=0, parse_dates=True)
            dap = np.full(len(df1d), np.nan)
            for i2 in range(30, len(df1d)): dap[i2] = atrp.atr_percentage(df1d.iloc[:i2+1], ATR_PCT_CFG)["atr_pct"]
            daily_apct = dict(zip(df1d.index, dap))

    def get_daily_apct(ts):
        if daily_apct is None: return None
        for dts in sorted(daily_apct.keys(), reverse=True):
            if dts <= ts and not np.isnan(daily_apct[dts]): return daily_apct[dts]
        return None

    def sl_o1(s): return s["entry"] * 1.10
    def sl_o3(s):
        ap = atrp.atr_percentage(df.iloc[:s["bar"]+1], ATR_PCT_CFG)["atr_pct"]
        return s["entry"] * (1 + ap/100.0)
    def sl_o6(s):
        da = get_daily_apct(s["date"])
        if da is None or np.isnan(da) or da <= 0: return None
        return s["entry"] * (1 + da/100.0)

    SL_OPTS = [("O1", sl_o1), ("O3", sl_o3), ("O6", sl_o6)]

    def simulate(samples_list, sl_name, sl_fn):
        if not samples_list: return {}
        results = {}
        for s in samples_list:
            sl_val = sl_fn(s)
            if sl_val is None or sl_val <= s["entry"]: continue
            year = s["date"].year
            if year not in results: results[year] = {"n":0, "tp1x":[], "rawbrk":[], "strev":[]}
            results[year]["n"] += 1
            results[year]["tp1x"].append(sim_rawbrk(s["entry"], s["bar"], sl_val, 1.0, high, low, close, n, pl_dict)["R"])
            results[year]["rawbrk"].append(sim_rawbrk(s["entry"], s["bar"], sl_val, 3.0, high, low, close, n, pl_dict)["R"])
            results[year]["strev"].append(sim_strev(s["entry"], s["bar"], sl_val, high, low, close, st_trend, n)["R"])
        return results

    all_years = {}
    for year in range(2019, 2027):
        for sl_name, sl_fn in SL_OPTS:
            if sl_name not in all_years: all_years[sl_name] = {}
            all_years[sl_name][year] = {"old_n":0, "new_n":0, "old_tp1x":0, "new_tp1x":0, "old_rawbrk":0, "new_rawbrk":0, "old_strev":0, "new_strev":0}

    old_by_sl = {}
    new_by_sl = {}
    for sl_name, sl_fn in SL_OPTS:
        old_by_sl[sl_name] = simulate(old_s, sl_name, sl_fn)
        new_by_sl[sl_name] = simulate(new_s, sl_name, sl_fn)

    for sl_name, sl_fn in SL_OPTS:
        sl_short = sl_name  # "O1", "O3", "O6"
        o_dat = old_by_sl[sl_short]
        n_dat = new_by_sl[sl_short]
        all_yrs = sorted(set(list(o_dat.keys()) + list(n_dat.keys())))
        
        print(f"\n  ─── {sl_short} ───")
        print(f"  {'Year':>5} {'OLDn':>5} {'NEWn':>5} {'Δn':>4} | {'OLD TP1x':>10} {'NEW TP1x':>10} {'Δ TP1x':>8} | {'OLD RBK':>10} {'NEW RBK':>10} {'Δ RBK':>8}")
        print(f"  {'':->5} {'':->5} {'':->5} {'':->4} | {'':->10} {'':->10} {'':->8} | {'':->10} {'':->10} {'':->8}")
        
        total_old_n = 0; total_new_n = 0
        total_old_tp1x = 0; total_new_tp1x = 0
        total_old_rbk = 0; total_new_rbk = 0
        
        for y in sorted(all_yrs):
            o = o_dat.get(y, {"n":0, "tp1x":[0], "rawbrk":[0], "strev":[0]})
            n = n_dat.get(y, {"n":0, "tp1x":[0], "rawbrk":[0], "strev":[0]})
            on = o["n"]; nn = n["n"]
            otp = sum(o["tp1x"]); ntp = sum(n["tp1x"])
            orb = sum(o["rawbrk"]); nrb = sum(n["rawbrk"])
            total_old_n += on; total_new_n += nn
            total_old_tp1x += otp; total_new_tp1x += ntp
            total_old_rbk += orb; total_new_rbk += nrb
            
            if on == 0 and nn == 0: continue
            print(f"  {y:>5} {on:>5} {nn:>5} {nn-on:>+4} | {otp:>+10.2f} {ntp:>+10.2f} {ntp-otp:>+8.2f} | {orb:>+10.2f} {nrb:>+10.2f} {nrb-orb:>+8.2f}")
        
        # Total row
        print(f"  {'TOTAL':>5} {total_old_n:>5} {total_new_n:>5} {total_new_n-total_old_n:>+4} | {total_old_tp1x:>+10.2f} {total_new_tp1x:>+10.2f} {total_new_tp1x-total_old_tp1x:>+8.2f} | {total_old_rbk:>+10.2f} {total_new_rbk:>+10.2f} {total_new_rbk-total_old_rbk:>+8.2f}")

# ─── MAIN ───
def main():
    start = _dt.datetime.now()
    print(f"{'='*65}")
    print(f"  SETUP1 v3 — Per-Year OLD vs NEW Comparison")
    print(f"  Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")
    print(f"\n  Fix applied: cross-wave FMB/PD carry-over (BUG #4)")
    print(f"  OLD: `if pd_b is None: fmb_b = None`       ← partial reset")
    print(f"  NEW: `fmb_b = None; pd_b = None`            ← full reset every WAVE_STARTED")
    
    for tf_name, csv_path, iv_ms, tf_binance in TF_CONFIGS:
        try:
            analyze_tf(tf_name, csv_path, iv_ms, tf_binance)
        except Exception as e:
            print(f"\n  {tf_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    elapsed = (_dt.datetime.now() - start).total_seconds()
    print(f"\n{'='*65}")
    print(f"  Selesai — {elapsed:.1f}s")

if __name__ == "__main__":
    main()
