"""
sample_trades.py — Pick 1 representative trade per combo × outcome × TF.
"""
import sys, os
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu")
import pandas as pd, numpy as np, random

# Same config & helpers as sample_o6_rawbrk_2025.py
from sample_o6_rawbrk_2025 import (
    SMI_CFG, ATR_PCT_CFG, BASE, supertrend_full, find_pivot_lows,
    atr_pct_at, get_daily_atr_pct, sim_rawbrk, sim_pure, sim_st_rev,
    TF_CONFIGS, CUTOFF, fmt_wib,
)
import smi_events as SM, fbf_v11_backtest as V11
import atr_percentage as atrp

random.seed(42)

for tf_name, csv_path, iv_ms in TF_CONFIGS:
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    high = df["high"].values.astype(float)
    low  = df["low"].values.astype(float)
    close = df["close"].values.astype(float)
    n = len(df)
    
    st_trend = supertrend_full(high, low, close)
    
    E = SM.compute_smi_events(df, SMI_CFG)
    FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]
    
    times = [int(t.value // 1_000_000) for t in df.index]
    eng = V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, iv_ms)
    breaks, events = eng.run()
    ev_by_bar = {}
    for e in events: ev_by_bar.setdefault(e["bar"], []).append(e)
    
    # v2.b trigger (same as sample_o6_rawbrk_2025.py)
    samples = []
    pos_open = False; clear_bar = -1
    fmb_b = None; pd_b = None; wave_entry_done = False
    for i in range(n):
        if pos_open:
            if i >= clear_bar: pos_open = False; clear_bar = -1
            else: continue
        for e in ev_by_bar.get(i, []):
            if e["side"] != "bear": continue
            if e["event"] == "WAVE_STARTED":
                wave_entry_done = False
                if pd_b is None: fmb_b = None
            elif e["event"] in ("WAVE_CANCELLED", "WAVE_STRUCT_REJECTED",
                                "CANDIDATE_INVALIDATED", "CANDIDATE_EVICTED"):
                fmb_b = None; pd_b = None; wave_entry_done = False
        if not wave_entry_done:
            if FMB[i] and fmb_b is None: fmb_b = i
            if fmb_b is not None and pd_b is None and PD[i] and i >= fmb_b: pd_b = i
            if fmb_b is not None and pd_b is not None and XDN[i] and i >= pd_b:
                if st_trend[i] == -1:
                    entry = close[i]
                    apct_current = atr_pct_at(df, i)
                    daily_apct = get_daily_atr_pct(df.index[i])
                    samples.append(dict(
                        bar=i, entry=entry,
                        apct=apct_current,
                        daily_apct=daily_apct,
                        date=df.index[i]
                    ))
                    sl0 = entry * (1 + apct_current/100.0)
                    tp0 = entry - (sl0 - entry)
                    fwd_h = high[i+1:]; fwd_l = low[i+1:]
                    ck = 240
                    for k in range(len(fwd_h)):
                        if fwd_l[k] <= tp0 or fwd_h[k] >= sl0 or k >= 240:
                            ck = k; break
                    clear_bar = i + 1 + ck
                    pos_open = True; wave_entry_done = True
                fmb_b = None; pd_b = None
    
    recent = [s for s in samples if s["date"] >= CUTOFF]
    if len(recent) == 0: continue
    
    pl_arr = find_pivot_lows(low, 3, 3)
    pl_dict = {bar: val for val, bar in pl_arr}
    
    def sl_o6(s):
        da = s.get("daily_apct")
        if da is None or np.isnan(da) or da <= 0: return None
        return s["entry"] * (1 + da/100.0)
    
    valid = []
    for s in recent:
        sl_val = sl_o6(s)
        if sl_val is not None and sl_val > s["entry"]:
            valid.append((s, sl_val))
    
    if len(valid) == 0: continue
    
    N = len(valid)
    
    # Collect ALL trades with outcomes per scenario
    trades = []
    for idx, (s, sl) in enumerate(valid):
        r_a = sim_pure(s["entry"], s["bar"], sl, 1.0, high, low, close, n)
        r_b = sim_pure(s["entry"], s["bar"], sl, 3.0, high, low, close, n)
        r_c = sim_rawbrk(s["entry"], s["bar"], sl, 3.0, high, low, close, n, pl_dict)
        r_d = sim_st_rev(s["entry"], s["bar"], sl, high, low, close, st_trend, n)
        
        risk = sl - s["entry"]
        tp1 = s["entry"] - 1.0 * risk
        tp3 = s["entry"] - 3.0 * risk
        date_str = fmt_wib(s["date"])
        da_str = f"{s['daily_apct']:.1f}%"
        
        trades.append({
            "idx": idx+1, "date": date_str, "bar": s["bar"],
            "entry": s["entry"],
            "sl": sl, "da": da_str, "risk": risk,
            "tp1": tp1, "tp3": tp3,
            "A_out": r_a["out"], "A_bars": r_a["bars"], "A_R": r_a["R"],
            "B_out": r_b["out"], "B_bars": r_b["bars"], "B_R": r_b["R"],
            "C_out": r_c["out"], "C_bars": r_c["bars"], "C_R": r_c["R"],
            "C_rb": r_c.get("rawbreak_count", 0),
            "C_rb_price": r_c.get("rawbreak_price", None),
            "D_out": r_d["out"], "D_bars": r_d["bars"], "D_R": r_d["R"],
        })
    
    # Pick 1 sample per combo × outcome
    combos = [
        ("A. TP1x standalone", "A"),
        ("B. TP3x standalone", "B"),
        ("C. TP3x + RAWBRK", "C"),
        ("D. TP3x + ST_REV", "D"),
    ]
    
    # Outcomes we care about per combo
    wanted = {
        "A": ["TP", "SL"],
        "B": ["TP", "SL", "EXP"],
        "C": ["TP", "SL", "RAWBRK_HIT"],
        "D": ["TP", "SL", "ST_REV"],
    }
    
    print(f"\n{'='*72}")
    print(f"  SAMPLES — {tf_name} — O6 (ATR% 1D) — 2026 only (WIB, {N} sinyal)")
    print(f"{'='*72}")
    
    for combo_name, key in combos:
        outcomes = wanted[key]
        print(f"\n  ── {combo_name} ──")
        print(f"  {'OUTCOME':<12} {'#':>3} {'DATE':>17} {'EXIT':>17} {'ENTRY':>10} {'SL O6':>10} {'ATR%1D':>7} {'TP':>10} {'BARS':>5} {'R':>8}  DETAIL")
        print(f"  {'':->12} {'':->3} {'':->17} {'':->17} {'':->10} {'':->10} {'':->7} {'':->10} {'':->5} {'':->8}  {'':->30}")
        
        for out in outcomes:
            # Pick first match (or random if multiple)
            candidates = [t for t in trades if t[f"{key}_out"] == out]
            if not candidates:
                print(f"  {out:<12} {'— NO SAMPLE —'}")
                continue
            t = candidates[0]  # first chronological
            
            tp_val = t["tp1"] if key == "A" else t["tp3"]
            bars = t[f"{key}_bars"]
            r_val = t[f"{key}_R"]
            
            # Exit timestamp
            exit_idx = min(t["bar"] + bars, n - 1)
            exit_str = fmt_wib(df.index[exit_idx])
            
            # Build detail explanation
            rb_str = ""
            if key == "C" and out == "RAWBRK_HIT":
                rb_price = t.get("C_rb_price")
                rb_count = t.get("C_rb", 0)
                if rb_price is not None:
                    rb_str = f" | rb#{rb_count} @ {rb_price:.1f}"
                else:
                    rb_str = f" | rawbreak #{rb_count}"
            
            if out == "TP":
                detail = f"Price hit TP target — full win"
            elif out == "SL":
                detail = f"Price hit stop loss — full loss"
            elif out == "RAWBRK_HIT":
                detail = f"Exit via rawbreak pivot low — partial win{rb_str}"
            elif out == "ST_REV":
                detail = f"Exit via Supertrend flip -1→+1"
            elif out == "EXP":
                detail = f"Still open at data end — partial"
            else:
                detail = ""
            
            print(f"  {out:<12} {t['idx']:>3} {t['date']:>17} {exit_str:>17} {t['entry']:>10.1f} {t['sl']:>10.1f} {t['da']:>7} {tp_val:>10.1f} {bars:>5} {r_val:>+8.2f}  {detail}")

print()
