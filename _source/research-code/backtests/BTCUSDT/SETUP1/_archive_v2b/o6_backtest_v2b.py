"""
o6_backtest.py — v2.b trigger + ALL 6 SL options (include O6 ATR% 1D anchor).
Tests on 4H and 2H data. O6 uses ATR% from 1D chart, not current TF.

2026-07-13 — O6 added per user request.
"""
import sys, os
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu")
import pandas as pd, numpy as np

# ============================================================
# CONFIG
# ============================================================
SMI_CFG = {
    "len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
    "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
    "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60
}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

BASE = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1"

# ============================================================
# PHASE 0: Preload 1D data + compute daily ATR%
# ============================================================
print("=" * 80)
print("PHASE 0: Loading 1D data for O6 anchor...")
print("=" * 80)

import atr_percentage as atrp
df1d = pd.read_csv(f"{BASE}/1D/data_BTCUSDT_1d_2019now.csv", index_col=0, parse_dates=True)
print(f"  1D: {len(df1d)} candles  {df1d.index[0].date()}..{df1d.index[-1].date()}")

# Precompute daily ATR% for every bar
daily_atr_pct = np.full(len(df1d), np.nan)
for i in range(30, len(df1d)):  # need 30 bars for ATR%
    daily_atr_pct[i] = atrp.atr_percentage(df1d.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]

# Helper: given a timestamp, find the last daily ATR% before or at that time
def get_daily_atr_pct(ts):
    """Find the most recent 1D bar that closed before/at ts."""
    for i in range(len(df1d)-1, -1, -1):
        if df1d.index[i] <= ts:
            val = daily_atr_pct[i]
            if np.isnan(val):
                # fallback: use next available
                for j in range(i+1, len(df1d)):
                    if not np.isnan(daily_atr_pct[j]):
                        return daily_atr_pct[j]
                return None
            return val
    return None

print(f"  Daily ATR% range: {np.nanmin(daily_atr_pct):.2f}% .. {np.nanmax(daily_atr_pct):.2f}%")
print(f"  Latest daily ATR%: {daily_atr_pct[-1]:.2f}%")

# ============================================================
# PHASE 1 & 2: Per-TF backtest
# ============================================================
import smi_events as SM
import fbf_v11_backtest as V11

TF_CONFIGS = [
    ("4H", f"{BASE}/4H/data_BTCUSDT_4h_2019now.csv", 14400000, "4h"),
    ("2H", f"{BASE}/2H/data_BTCUSDT_2h_2019now.csv",  7200000, "2h"),
]

def supertrend_full(high, low, close, period=10, mult=3.0):
    n = len(close)
    h, l, c = high, low, close
    hl2 = (h+l)/2.0
    tr = np.zeros(n); tr[0] = h[0]-l[0]
    for i in range(1,n):
        tr[i] = max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
    atr = np.zeros(n); atr[0] = tr[0]; alpha = 1.0/period
    for i in range(1,n): atr[i] = atr[i-1] + alpha*(tr[i]-atr[i-1])
    up_raw = hl2 - mult*atr
    dn_raw = hl2 + mult*atr
    up_f = np.zeros(n); dn_f = np.zeros(n); trend = np.ones(n, dtype=int)
    up_f[0] = up_raw[0]; dn_f[0] = dn_raw[0]
    for i in range(1,n):
        up_f[i] = max(up_raw[i], up_f[i-1]) if c[i-1] > up_f[i-1] else up_raw[i]
        dn_f[i] = min(dn_raw[i], dn_f[i-1]) if c[i-1] < dn_f[i-1] else dn_raw[i]
        trend[i] = trend[i-1]
        if trend[i-1] == -1 and c[i] > dn_f[i-1]: trend[i] = 1
        elif trend[i-1] == 1 and c[i] < up_f[i-1]: trend[i] = -1
    return trend

def find_pivot_lows(arr, left=3, right=3):
    out = []
    for ii in range(left, len(arr)-right):
        v = arr[ii]; ok = True
        for j in range(ii-left, ii):
            if arr[j] <= v: ok = False; break
        if ok:
            for j in range(ii+1, ii+right+1):
                if arr[j] <= v: ok = False; break
        if ok: out.append((v, ii))
    return out

def atr_pct_at(df_slice, idx):
    return atrp.atr_percentage(df_slice.iloc[:idx+1], ATR_PCT_CFG)["atr_pct"]

def sim_trade_rawbrk(entry, eb, sl, tp_mult, high, low, close, n, pl_dict):
    """Generic sim: entry -> exit with SL, TP=tp_mult*risk, RAWBRK."""
    risk = sl - entry
    tp = entry - tp_mult * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    rb_sl = None; rb_bars = []
    
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp:
            return dict(out="TP", ex=tp, bars=k+1, R=tp_mult, rawbreak_bars=rb_bars, rawbreak_sl=rb_sl)
        if fwd_h[k] >= sl:
            return dict(out="SL", ex=sl, bars=k+1, R=-1.0, rawbreak_bars=rb_bars, rawbreak_sl=rb_sl)
        # RAWBRK
        cur_pl = None
        for bi2 in sorted(pl_dict.keys(), reverse=True):
            if bi2 <= bi: cur_pl = pl_dict[bi2]; break
        if cur_pl is not None and close[bi] < cur_pl:
            if rb_sl is None: rb_sl = high[bi]
            else: rb_sl = max(rb_sl, high[bi])
            rb_bars.append((bi, high[bi]))
        if rb_sl is not None and fwd_h[k] >= rb_sl:
            return dict(out="RAWBRK_HIT", ex=rb_sl, bars=k+1, R=(entry-rb_sl)/risk, rawbreak_bars=rb_bars, rawbreak_sl=rb_sl)
    
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk, rawbreak_bars=rb_bars, rawbreak_sl=rb_sl)

def sim_st_rev(entry, eb, sl, high, low, close, st_trend, n):
    """ST_REV: TP3x patok, exit when ST flips -1→+1."""
    risk = sl - entry
    tp3 = entry - 3 * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp3:
            return dict(out="TP3x", ex=tp3, bars=k+1, R=3.0)
        if fwd_h[k] >= sl:
            return dict(out="SL", ex=sl, bars=k+1, R=-1.0)
        if st_trend[bi] == 1:  # ST flipped UP
            return dict(out="ST_REV", ex=close[bi], bars=k+1, R=(entry-close[bi])/risk)
    
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk)

# ============================================================
# RUN per TF
# ============================================================
ALL_RESULTS = []

for tf_name, csv_path, iv_ms, tf_binance in TF_CONFIGS:
    # Load
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    high = df["high"].values.astype(float)
    low  = df["low"].values.astype(float)
    close = df["close"].values.astype(float)
    n = len(df)
    
    # ST
    st_trend = supertrend_full(high, low, close)
    
    # SMI
    E = SM.compute_smi_events(df, SMI_CFG)
    FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]
    
    # FBF v11
    times = [int(t.value // 1_000_000) for t in df.index]
    eng = V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, iv_ms)
    breaks, events = eng.run()
    ev_by_bar = {}
    for e in events: ev_by_bar.setdefault(e["bar"], []).append(e)
    
    # v2.b trigger
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
                    apct_current = atr_pct_at(df, i)  # O3: current TF
                    daily_apct = get_daily_atr_pct(df.index[i])  # O6: 1D anchor
                    samples.append(dict(
                        bar=i, entry=entry,
                        apct=apct_current,           # O3
                        daily_apct=daily_apct,       # O6
                        date=df.index[i]
                    ))
                    # clear_bar via TP1x O3
                    sl0 = entry * (1 + apct_current/100.0)
                    tp0 = entry - (sl0 - entry)
                    fwd_h = high[i+1:]; fwd_l = low[i+1:]; ck = 240
                    for k in range(len(fwd_h)):
                        if fwd_l[k] <= tp0 or fwd_h[k] >= sl0 or k >= 240: ck = k; break
                    clear_bar = i + 1 + ck
                    pos_open = True; wave_entry_done = True
                fmb_b = None; pd_b = None
    
    print(f"\n{'='*80}")
    print(f"{tf_name} — {len(samples)} sinyal | {df.index[0].date()}..{df.index[-1].date()}")
    print(f"{'='*80}")
    
    if len(samples) == 0:
        print("  NO SIGNALS — skip")
        continue
    
    # Pivot lows
    pl_arr = find_pivot_lows(low, 3, 3)
    pl_dict = {bar: val for val, bar in pl_arr}
    
    # ============================================================
    # SL OPTIONS
    # ============================================================
    def sl_o1(s):   # Liq10x
        return s["entry"] * 1.10
    
    def sl_o3(s):   # ATR% current TF
        return s["entry"] * (1 + s["apct"]/100.0)
    
    def sl_o6(s):   # ATR% 1D
        da = s.get("daily_apct")
        if da is None or np.isnan(da) or da <= 0: return None
        return s["entry"] * (1 + da/100.0)
    
    SL_OPTIONS = [
        ("O1 Liq10x", sl_o1),
        ("O3 ATR%curr", sl_o3),
        ("O6 ATR%1D", sl_o6),
    ]
    
    # ============================================================
    # RUN ALL COMBOS
    # ============================================================
    HEADER = f"{'SL':>14} {'TP1x':>12} {'TP3x':>12} {'RAWBRK':>12} {'ST_REV':>12}"
    print(f"\n{HEADER}")
    print(f"{'':->14} {'':->12} {'':->12} {'':->12} {'':->12}")
    
    for sl_name, sl_fn in SL_OPTIONS:
        # Compute SL for all samples, filter invalid
        valid = []
        for s in samples:
            sl_val = sl_fn(s)
            if sl_val is not None and sl_val > s["entry"]:
                valid.append((s, sl_val))
        
        if len(valid) == 0:
            row = f"{sl_name:>14} {'N/A':>12} {'N/A':>12} {'N/A':>12} {'N/A':>12} {'N/A':>12}"
            print(row)
            continue
        
        # TP1x (standalone, no RAWBRK)
        tp1x_results = [sim_trade_rawbrk(s["entry"], s["bar"], sl, 1.0, high, low, close, n, pl_dict) for s, sl in valid]
        tp1x_tot = sum(r["R"] for r in tp1x_results)
        
        # TP3x (standalone, no RAWBRK)
        tp3x_standalone = [sim_trade_rawbrk(s["entry"], s["bar"], sl, 3.0, high, low, close, n, pl_dict) for s, sl in valid]
        # For TP3x standalone: remove RAWBRK logic — treat as pure TP3x vs SL
        tp3x_results = []
        for s, sl in valid:
            risk = sl - s["entry"]
            tp3 = s["entry"] - 3 * risk
            fwd_h = high[s["bar"]+1:]; fwd_l = low[s["bar"]+1:]
            found = False
            for k in range(len(fwd_h)):
                bi = s["bar"] + 1 + k
                if bi >= n: break
                if fwd_l[k] <= tp3:
                    tp3x_results.append(dict(out="TP3x", R=3.0, bars=k+1))
                    found = True; break
                if fwd_h[k] >= sl:
                    tp3x_results.append(dict(out="SL", R=-1.0, bars=k+1))
                    found = True; break
            if not found:
                lastc = fwd_l[-1] if len(fwd_l) > 0 else s["entry"]
                tp3x_results.append(dict(out="EXP", R=(s["entry"]-lastc)/risk, bars=len(fwd_h)))
        tp3x_tot = sum(r["R"] for r in tp3x_results)
        
        # RAWBRK (TP3x + RAWBRK)
        rawbrk_results = [sim_trade_rawbrk(s["entry"], s["bar"], sl, 3.0, high, low, close, n, pl_dict) for s, sl in valid]
        rawbrk_tot = sum(r["R"] for r in rawbrk_results)
        
        # ST_REV (TP3x + ST flip)
        strev_results = [sim_st_rev(s["entry"], s["bar"], sl, high, low, close, st_trend, n) for s, sl in valid]
        strev_tot = sum(r["R"] for r in strev_results)
        
        row = (f"{sl_name:>14} {tp1x_tot:>+12.2f} {tp3x_tot:>+12.2f} "
               f"{rawbrk_tot:>+12.2f} {strev_tot:>+12.2f}")
        print(row)
        
        # Store for summary
        ALL_RESULTS.append(dict(
            tf=tf_name, sl=sl_name,
            tp1x=dict(tot=tp1x_tot, n=len(valid),
                      tp=sum(1 for r in tp1x_results if r["out"]=="TP"),
                      sl=sum(1 for r in tp1x_results if r["out"]=="SL")),
            tp3x=dict(tot=tp3x_tot, n=len(valid),
                      tp=sum(1 for r in tp3x_results if r["out"]=="TP3x"),
                      sl=sum(1 for r in tp3x_results if r["out"]=="SL")),
            rawbrk=dict(tot=rawbrk_tot, n=len(valid),
                        tp=sum(1 for r in rawbrk_results if r["out"]=="TP"),
                        sl=sum(1 for r in rawbrk_results if r["out"]=="SL"),
                        rb=sum(1 for r in rawbrk_results if r["out"]=="RAWBRK_HIT")),
            strev=dict(tot=strev_tot, n=len(valid),
                       tp=sum(1 for r in strev_results if r["out"]=="TP3x"),
                       rev=sum(1 for r in strev_results if r["out"]=="ST_REV"),
                       sl=sum(1 for r in strev_results if r["out"]=="SL")),
        ))

# ============================================================
# PHASE 3: CROSS-TF SUMMARY
# ============================================================
print(f"\n{'='*80}")
print(f"SUMMARY — O6 vs O3 vs O1 across 4H & 2H")
print(f"{'='*80}")

EXITS = ["tp1x", "tp3x", "rawbrk", "strev"]
EXIT_LABELS = {"tp1x":"TP1x","tp3x":"TP3x","rawbrk":"RAWBRK","strev":"ST_REV"}

for exit_key in EXITS:
    label = EXIT_LABELS[exit_key]
    print(f"\n--- {label} ---")
    print(f"{'TF':>4} {'O1 Liq10x':>12} {'O3 ATR%c':>12} {'O6 ATR%1D':>12}  |   BEST")
    for tf in ["4H", "2H"]:
        vals = {}
        for r in ALL_RESULTS:
            if r["tf"] == tf:
                sl_short = r["sl"].split()[0]  # O1, O3, O6
                vals[sl_short] = r[exit_key]["tot"]
        o1 = vals.get("O1", 0)
        o3 = vals.get("O3", 0)
        o6 = vals.get("O6", 0)
        best = max(o1, o3, o6)
        best_label = []
        if o1 == best: best_label.append("O1")
        if o3 == best: best_label.append("O3")
        if o6 == best: best_label.append("O6")
        print(f"{tf:>4} {o1:>+12.2f} {o3:>+12.2f} {o6:>+12.2f}  |   {','.join(best_label)}")

# O6 vs O3 detail
print(f"\n{'='*80}")
print(f"O6 vs O3 — BREAKDOWN")
print(f"{'='*80}")
for tf in ["4H", "2H"]:
    o3_data = None; o6_data = None
    for r in ALL_RESULTS:
        if r["tf"] == tf:
            if "O3" in r["sl"]: o3_data = r
            if "O6" in r["sl"]: o6_data = r
    if o3_data and o6_data:
        print(f"\n{tf}:")
        print(f"  O3 ATR% curr: {o3_data['apct_avg'] if 'apct_avg' in o3_data else 'N/A'}")
        print(f"  O6 ATR% 1D:   {o6_data['apct_avg'] if 'apct_avg' in o6_data else 'N/A'}")
        
        for exit_key in ["tp1x", "tp3x", "rawbrk"]:
            o3_val = o3_data[exit_key]["tot"]
            o6_val = o6_data[exit_key]["tot"]
            diff = o6_val - o3_val
            better = "O6 BETTER" if diff > 0 else ("O3 BETTER" if diff < 0 else "SAME")
            print(f"  {EXIT_LABELS[exit_key]:>8}: O3={o3_val:+.2f}  O6={o6_val:+.2f}  Δ={diff:+.2f}  → {better}")

print(f"\n{'='*80}")
print(f"DONE — {len(ALL_RESULTS)} result rows")
print(f"{'='*80}")
