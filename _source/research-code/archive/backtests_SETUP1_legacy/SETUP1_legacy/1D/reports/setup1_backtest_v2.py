"""
SETUP 1 — SHORT backtester v2
FBF AB + SMI 3-step confluence
BTCUSDT daily, 2023-01-01 .. now

Extended: 4 SL x 3 TP ratios (1x, 2x, 3x) + trailing stop.

Trailing: when price moves in favor by half-atr_pct from entry,
trailing activates. Trailing stop = lowest_reached * (1 + atr_pct/100).
Exit when high >= trail_stop.
"""
import sys, time
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/fetchers")
import requests
import pandas as pd
import numpy as np
import fbf_v610 as fbfmod
import smi_pro
import atr_percentage as atrp

SYM = "BTCUSDT"
TF = "1d"
START = pd.Timestamp("2023-01-01", tz="UTC")
END = pd.Timestamp.now("UTC").normalize()

SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

# ---------- fetch ----------
def fetch_full(sym, tf, start_ts, end_ts):
    url = "https://api.binance.com/api/v3/klines"
    all_rows = []
    cur = int(start_ts.timestamp()*1000)
    end_ms = int(end_ts.timestamp()*1000)
    step = 895*24*60*60*1000
    while cur < end_ms:
        nxt = min(cur+step, end_ms)
        r = requests.get(url, params={"symbol":sym,"interval":tf,
                         "startTime":cur,"endTime":nxt,"limit":1000}, timeout=30).json()
        if r: all_rows.extend(r); cur=r[-1][0]+1
        else: cur=nxt
        time.sleep(0.2)
    df = pd.DataFrame(all_rows, columns=[
        "ot","o","h","l","c","v","ct","q","t","tb","tq","ig"])
    for c2 in ["o","h","l","c","v"]: df[c2] = df[c2].astype(float)
    df["ot"] = pd.to_datetime(df["ot"], unit="ms", utc=True)
    df = df.set_index("ot").sort_index()
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    return df[["open","high","low","close","volume"]]

print("[fetch] BTCUSDT daily 2023..now")
df = fetch_full(SYM, TF, START, END)
print(f"[fetch] {len(df)} candles  {df.index[0].date()} .. {df.index[-1].date()}")

# ---------- pivots ----------
high = df["high"].values
low = df["low"].values
close = df["close"].values
ph_main, pl_main = fbfmod.find_pivots(high, low, 3, 3)
PH = dict(ph_main); PL = dict(pl_main)
ph_bars = sorted(PH.keys()); pl_bars = sorted(PL.keys())

# ---------- AB detection ----------
def next_ph_after(b):
    for x in ph_bars:
        if x > b: return x, PH[x]
    return None, None

ab_events = []
for B_bar, B_val in pl_main:
    if B_bar < 50: continue
    A_bar = None; A_val = None
    for b in reversed(ph_bars):
        if b < B_bar: A_bar,A_val = b,PH[b]; break
    if A_bar is None or not (A_val > B_val): continue
    confirm_bar = B_bar + 3
    if confirm_bar >= len(close): continue
    C_bar, C_val = next_ph_after(B_bar)
    if C_bar is None or C_bar < confirm_bar: continue
    if not (C_val > B_val): continue
    ab_events.append({"bar":confirm_bar, "A_bar":A_bar, "A_val":A_val,
                      "B_bar":B_bar, "B_val":B_val, "C_bar":C_bar, "C_val":C_val})
seen_B = set(); ab_clean = []
for e in sorted(ab_events, key=lambda x: x["bar"]):
    if e["B_bar"] not in seen_B: seen_B.add(e["B_bar"]); ab_clean.append(e)
print(f"[AB] events: {len(ab_clean)}")

# ---------- Supertrend array (adaptive, FBF v6.10) ----------
print("[ST] building supertrend trend array...")
# supertrend_adaptive returns only last; build full series manually
def supertrend_full(df, period=10, mult=3.0):
    high = df["high"].values; low = df["low"].values; close = df["close"].values
    hl2 = (high + low) / 2.0
    tr = np.zeros(len(close)); tr[0] = high[0] - low[0]
    for i in range(1, len(close)):
        tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
    atr = np.zeros(len(close)); atr[0] = tr[0]; alpha = 1.0/period
    for i in range(1, len(close)):
        atr[i] = atr[i-1] + alpha * (tr[i] - atr[i-1])
    up_raw = hl2 - mult*atr; dn_raw = hl2 + mult*atr
    up_f = np.zeros(len(close)); dn_f = np.zeros(len(close))
    trend = np.ones(len(close), dtype=int)
    up_f[0] = up_raw[0]; dn_f[0] = dn_raw[0]
    for i in range(1, len(close)):
        up_f[i] = max(up_raw[i], up_f[i-1]) if close[i-1] > up_f[i-1] else up_raw[i]
        dn_f[i] = min(dn_raw[i], dn_f[i-1]) if close[i-1] < dn_f[i-1] else dn_raw[i]
        trend[i] = trend[i-1]
        if trend[i-1] == -1 and close[i] > dn_f[i-1]: trend[i] = 1
        elif trend[i-1] == 1 and close[i] < up_f[i-1]: trend[i] = -1
    return trend  # 1=up, -1=down

st_trend = supertrend_full(df, period=10, mult=3.0)
print(f"[ST] done. downtrend bars: {int((st_trend==-1).sum())}/{len(st_trend)}")

# ---------- Bear raw break precompute (FBF bear state machine) ----------
print("[RAWBRK] building bear active series...")
# replicate the FBF v6.10 bear break state machine
ph_arr, pl_arr = fbfmod.find_pivots(high, low, 3, 3)
pl_by_idx = dict(pl_arr)
ph_map = dict(ph_arr)
last_pl_val, last_pl_bar = None, None
# iterate bars to track running last pivot low
running_last_pl = np.full(len(close), np.nan)
for i in range(len(close)):
    if i in pl_by_idx:
        last_pl_val = pl_by_idx[i]
        last_pl_bar = i
    running_last_pl[i] = last_pl_val

# atr array (same as fbf: atr_len=14, no ema, just ewm)
tr = np.zeros(len(close)); tr[0] = high[0] - low[0]
for i in range(1, len(close)):
    tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
atr_arr = np.zeros(len(close)); atr_arr[0] = tr[0]; alpha = 1.0/14
for i in range(1, len(close)):
    atr_arr[i] = atr_arr[i-1] + alpha*(tr[i]-atr_arr[i-1])

bear_active = np.zeros(len(close), dtype=bool)
bear_ref_val = np.full(len(close), np.nan)
bear_ref_bar = np.full(len(close), -1, dtype=int)
bear_active_high = np.full(len(close), np.nan)  # rolling max high while active
bear_last_high = np.nan

_active = False
_ref_val = np.nan
_ref_bar = -1
_base_high = np.nan
for i in range(len(close)):
    rpl = running_last_pl[i]
    if not np.isnan(rpl):
        raw_bear = close[i] < rpl
    else:
        raw_bear = False

    if not _active and raw_bear:
        dist_ok = (rpl - close[i]) >= 0.15 * atr_arr[i]  # atr_mult=0.15
        if dist_ok:
            _active = True
            _ref_val = rpl
            _ref_bar = i
            _base_high = high[i]
    elif _active:
        still_beyond = close[i] < _ref_val
        dist_ok2 = (_ref_val - close[i]) >= 0.15 * atr_arr[i] if not np.isnan(_ref_val) else False
        if still_beyond and dist_ok2:
            pass  # stay active, persist++
        else:
            _active = False

    bear_active[i] = _active
    bear_ref_val[i] = _ref_val
    bear_ref_bar[i] = _ref_bar
    if _active:
        bear_last_high = bear_last_high if not np.isnan(bear_last_high) else _base_high
        if high[i] > bear_last_high: bear_last_high = high[i]
        bear_active_high[i] = bear_last_high
    else:
        bear_last_high = np.nan

print(f"[RAWBRK] bear active at last bar: {bear_active[-1]}, total bars break-active: {int(bear_active.sum())}")

# ---------- SMI 3-step ----------
def smi_at(i):
    return smi_pro.smi_pro_v3(df.iloc[:i+1], SMI_CFG)

setups = []
for e in ab_clean:
    Bb,Bv,Cb = e["B_bar"],e["B_val"],e["C_bar"]
    end = len(close)-1
    for i in range(Bb+1, len(close)):
        if close[i] < Bv: end=i; break
    if Cb > end: continue
    # ST gate (combined): downtrend at C bar AND at entry bar
    st_c = st_trend[Cb] == -1 if Cb < len(st_trend) else False
    seq = []
    for i in range(max(Bb,2), end+1):
        s = smi_at(i); bs = s["bar_state"]
        if bs == "[!] Fail MID Buy": seq.append(("FMB",i))
        elif bs.startswith("[~] PD") or bs.startswith("[OK] PD") or bs=="PD TRIGGERED": seq.append(("PD",i))
        elif bs == "[X] Cross DN": seq.append(("XDN",i))
    fmb = [x[1] for x in seq if x[0]=="FMB"]
    pd_ = [x[1] for x in seq if x[0]=="PD"]
    xdn = [x[1] for x in seq if x[0]=="XDN"]
    found = None
    for f in fmb:
        pc = [p for p in pd_ if p>f]
        if not pc: continue
        p = pc[0]
        xc = [x for x in xdn if x>p]
        if not xc: continue
        found = (f,p,xc[0]); break
    if found:
        eb = found[2]
        st_entry = st_trend[eb] == -1 if eb < len(st_trend) else False
        st_ok = st_c and st_entry
        e2 = dict(e); e2["entry_bar"] = eb; e2["entry"] = close[eb]
        e2["C_high"] = high[Cb]
        e2["st_ok"] = st_ok
        setups.append(e2)

raw_n = len(setups)
gated = [s for s in setups if s.get("st_ok", False)]
print(f"[SETUP1] raw signals: {raw_n} | ST-gated (C+entry downtrend): {len(gated)}")

# ---------- helpers ----------
def atr_val_at(i, period=14):
    sub = df.iloc[max(0,i-period+1):i+1]
    tr = pd.concat([sub["high"]-sub["low"], (sub["high"]-sub["close"].shift(1)).abs(),
                    (sub["low"]-sub["close"].shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean().iloc[-1]

def get_sl_tp(entry, Ch, atr14, apct, opt, entry_bar=None):
    """Return (sl, tp) for the given option key. entry_bar needed for O5."""
    if opt == "O1": return (entry*1.1, entry*0.9)
    if opt == "O2": sl = Ch + atr14; return (sl, 2*entry - sl)
    if opt == "O3": sl = entry*(1+apct/100.0); return (sl, entry*(1-apct/100.0))
    if opt == "O4": return (entry*1.06, entry*0.94)
    if opt == "O5" and entry_bar is not None:
        conf_hi = high[entry_bar]
        sl = conf_hi + atr14
        return (sl, 2*entry - sl)
    return (None, None)

# ---------- simulation ----------
def simulate(entry, sl, tp_1, fwd_h, fwd_l, atr_pct):
    """
    Simulate fixed TP at 1x ratio (tp_1).
    Returns (outcome, exit_price, bars_held, win_amt).

    For 2x and 3x risk:
      - risk = sl - entry  (positive number, distance above)
      - tp_2 = entry - 2*risk
      - tp_3 = entry - 3*risk
    """
    risk = sl - entry  # SL distance (positive, since sl > entry for short)
    tp_2 = entry - 2*risk
    tp_3 = entry - 3*risk

    # trailing stop config
    activation_price = entry * (1 - (atr_pct/2)/100.0)  # half-atr% below entry
    trailing_active = False
    trail_stop = None
    lowest_reached = entry

    for k in range(len(fwd_h)):
        this_high = fwd_h[k]
        this_low = fwd_l[k]

        # --- trailing logic ---
        if atr_pct > 0:
            # update lowest reached
            if this_low < lowest_reached:
                lowest_reached = this_low

            # check activation
            if not trailing_active and lowest_reached <= activation_price:
                trailing_active = True
                trail_stop = lowest_reached * (1 + atr_pct/100.0)

            # update trail
            if trailing_active:
                # recalc trail from current lowest
                trail_stop = lowest_reached * (1 + atr_pct/100.0)
                # check if hit
                if this_high >= trail_stop:
                    return ("TRAIL", trail_stop, k+1, (entry - trail_stop)/risk)

        # --- check TP levels ---
        # catch-up: if trailing active, skip TP checking
        if trailing_active:
            continue

        # 1x, 2x, 3x TP check (reached by lowest of the bar)
        if this_low <= tp_3:
            return ("TP3", tp_3, k+1, 3.0)
        if this_low <= tp_2:
            return ("TP2", tp_2, k+1, 2.0)
        if this_low <= tp_1:
            return ("TP1", tp_1, k+1, 1.0)

        # --- check SL ----------
        if this_high >= sl:
            return ("SL", sl, k+1, -1.0)

        if k >= 240:  # max 240 bars (~8 months)
            return ("EXP", this_low, k+1, (entry - this_low)/risk)

    return ("OPEN", None, len(fwd_h), 0)

# ---------- run ----------
OPT_KEYS = ["O1","O2","O3","O4","O5"]
OPT_NAMES = {"O1":"Liq10x","O2":"C+ATR14","O3":"ATR%30","O4":"Fix6%","O5":"ConfHi+ATR"}
TP_RATIOS = ["1x","2x","3x","TRAIL","ST_REV","RAWBRK"]

results = {}  # results[(opt, tp_rat)] = list of (outcome, bars, R)
for ok in OPT_KEYS:
    for tr in TP_RATIOS:
        results[(ok, tr)] = []

for s in setups:
    eb = s["entry_bar"]; entry = s["entry"]; Ch = s["C_high"]
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    atr14 = atr_val_at(eb, 14)
    ap = atrp.atr_percentage(df.iloc[:eb+1], ATR_PCT_CFG)
    apct = ap["atr_pct"]

    for ok in OPT_KEYS:
        sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, ok)
        if sl is None or sl <= entry or tp1 <= 0:
            for tr in TP_RATIOS:
                results[(ok, tr)].append(("INV",0,0,0))
            continue

        # 1x, 2x, 3x, TRAIL — all via simulate
        outcome, px, bars, R = simulate(entry, sl, tp1, fwd_h, fwd_l, apct)
        # map outcomes to ratios:
        # simulate returns TP1/TP2/TP3/TRAIL/SL/EXP/OPEN
        # For 1x: check if TP1 (1.0R), or SL/EXP
        # For 2x: check TP2 (2.0R) else SL
        # For 3x: check TP3 (3.0R) else SL
        # For TRAIL: use trailing outcome
        # We need to simulate differently for each TP ratio...
        pass

# ---- Hmm, let me restructure ----
# Simulate per (opt, tp_ratio) separately for clarity.

# ---------- simulation per opt x ratio ----------
def run_batch(setups, opt_key, tp_ratio):
    """Run all setups for one (opt, tp_ratio) combo. Returns list of (outcome, bars, R)."""
    out = []
    for s in setups:
        eb = s["entry_bar"]; entry = s["entry"]; Ch = s["C_high"]
        fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
        atr14 = atr_val_at(eb, 14)
        ap = atrp.atr_percentage(df.iloc[:eb+1], ATR_PCT_CFG)
        apct = ap["atr_pct"]
        sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, opt_key, eb)
        if sl is None or sl <= entry or tp1 <= 0:
            out.append(("INV",0,0))
            continue

        risk = sl - entry
        tp_targets = {"1x": (tp1, 1.0),
                      "2x": (entry - 2*risk, 2.0),
                      "3x": (entry - 3*risk, 3.0)}

        if tp_ratio in tp_targets:
            # Fixed TP mode
            tp, r_mult = tp_targets[tp_ratio]
            exited = False
            for k in range(len(fwd_h)):
                if fwd_l[k] <= tp:
                    out.append(("TP", k+1, r_mult)); exited = True; break
                if fwd_h[k] >= sl:
                    out.append(("SL", k+1, -1.0)); exited = True; break
            if not exited:
                lastc = fwd_l[-1] if len(fwd_l)>0 else entry
                out.append(("EXP", len(fwd_h), (entry-lastc)/risk))

        elif tp_ratio == "TRAIL":
            # Trailing mode
            if apct <= 0:
                out.append(("INV",0,0)); continue
            activation_pr = entry * (1 - (apct/2)/100.0)
            trailing = False
            lowest = entry
            exited = False
            for k in range(len(fwd_h)):
                if fwd_l[k] < lowest: lowest = fwd_l[k]
                if not trailing and lowest <= activation_pr:
                    trailing = True
                if trailing:
                    trail = lowest * (1 + apct/100.0)
                    if fwd_h[k] >= trail:
                        R = (entry - trail) / risk
                        out.append(("TRAIL", k+1, R)); exited = True; break
                # SL still active
                if fwd_h[k] >= sl:
                    out.append(("SL", k+1, -1.0)); exited = True; break
            if not exited:
                lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
                out.append(("EXP", len(fwd_h), (entry-lastc)/risk))

        elif tp_ratio == "ST_REV":
            # Exit short when Supertrend flips from downtrend(-1) to uptrend(+1)
            exited = False
            for k in range(len(fwd_h)):
                bar_idx = eb + 1 + k
                if bar_idx >= len(st_trend): break
                # Check SL first
                if fwd_h[k] >= sl:
                    out.append(("SL", k+1, -1.0)); exited = True; break
                # Check for ST flip -1→+1
                if st_trend[bar_idx] == 1 and (bar_idx == 0 or st_trend[bar_idx-1] == -1):
                    exit_pr = fwd_l[k] if fwd_l[k] < entry else entry
                    R = (entry - exit_pr) / risk
                    out.append(("ST_REV", k+1, R)); exited = True; break
            if not exited:
                lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
                out.append(("EXP", len(fwd_h), (entry-lastc)/risk))

        elif tp_ratio == "RAWBRK":
            # Exit when bear raw break becomes inactive, trail at active high
            exited = False
            for k in range(len(fwd_h)):
                bar_idx = eb + 1 + k
                if bar_idx >= len(bear_active): break
                # Check SL first
                if fwd_h[k] >= sl:
                    out.append(("SL", k+1, -1.0)); exited = True; break
                # has the break just become inactive? (was active last bar)
                prev_active = bear_active[bar_idx-1] if bar_idx-1 >= 0 else False
                cur_active = bear_active[bar_idx]
                if prev_active and not cur_active:
                    # break lost — exit at this bar's low or close
                    exit_pr = min(fwd_l[k], close[bar_idx]) if close[bar_idx] < entry else entry
                    R = (entry - exit_pr) / risk
                    out.append(("RAWBRK", k+1, R)); exited = True; break
                # trailing: if break active, check trail at bear_active_high
                if cur_active and not np.isnan(bear_active_high[bar_idx]):
                    trail_hi = bear_active_high[bar_idx]
                    if fwd_h[k] >= trail_hi:
                        R = (entry - trail_hi) / risk
                        out.append(("RAWTRL", k+1, R)); exited = True; break
            if not exited:
                lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
                out.append(("EXP", len(fwd_h), (entry-lastc)/risk))

    return out

# ---------- per-trade journal ----------
TRADE_DETAIL = []
def run_batch_detail(setups, opt_key, tp_ratio, mode):
    out = run_batch(setups, opt_key, tp_ratio)
    for idx, s in enumerate(setups):
        eb = s["entry_bar"]; entry = s["entry"]; Ch = s["C_high"]
        atr14 = atr_val_at(eb, 14)
        ap = atrp.atr_percentage(df.iloc[:eb+1], ATR_PCT_CFG)
        apct = ap["atr_pct"]
        sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, opt_key, eb)
        risk = (sl - entry) if (sl and sl > entry) else 0
        tp_tgt = {"1x": tp1, "2x": entry-2*risk, "3x": entry-3*risk}.get(tp_ratio, None)
        TRADE_DETAIL.append({
            "mode": mode, "opt": opt_key, "tp_ratio": tp_ratio,
            "entry_date": str(df.index[eb].date()), "entry": round(entry,2),
            "sl": round(sl,2) if sl else None,
            "sl_pct": round((sl/entry-1)*100,2) if sl else None,
            "tp_pct": round((tp_tgt/entry-1)*100,2) if tp_tgt else None,
            "apct": round(apct,2),
            "outcome": out[idx][0], "bars": out[idx][1], "R": round(out[idx][2],3),
        })
    return out
all_res = {}
for ok in OPT_KEYS:
    for tr in TP_RATIOS:
        all_res[("RAW",ok,tr)] = run_batch_detail(setups, ok, tr, "RAW")
        all_res[("GATED",ok,tr)] = run_batch_detail(gated, ok, tr, "GATED")
import csv
with open("/home/ubuntu/trading-research/setup1_v2_journal.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=["mode","opt","tp_ratio","entry_date","entry","sl","sl_pct","tp_pct","apct","outcome","bars","R"])
    w.writeheader(); w.writerows(TRADE_DETAIL)
print(f"[JOURNAL] wrote {len(TRADE_DETAIL)} trades -> setup1_v2_journal.csv")

# ---------- report ----------
def summarize(label, mode):
    print(f"\n{'='*72}")
    print(f"SETUP 1 SHORT — BACKTEST v2  [{label}]")
    print(f"BTCUSDT 1D | {len(df)} candles | "
          f"{len(setups if mode=='RAW' else gated)} signals")
    print(f"{'='*72}")
    best_key = None; best_R = -1e9
    for ok in OPT_KEYS:
        print(f"\n━━━ {ok} {OPT_NAMES[ok]} ━━━")
        print(f"{'TP_Ratio':<8} {'Tr':>4} {'TP':>4} {'SL':>4} {'TR':>4} {'SRV':>4} "
              f"{'RBK':>4} {'RTL':>4} {'EXP':>4} {'WR%':>6} {'TotR':>7} {'AvgR':>7} {'AvgD':>5}")
        print("-"*80)
        for tr in TP_RATIOS:
            rs = all_res[(mode,ok,tr)]
            valid = [r for r in rs if r[0]!="INV"]
            n = len(valid)
            tp = sum(1 for r in valid if r[0]=="TP")
            sl = sum(1 for r in valid if r[0]=="SL")
            trl = sum(1 for r in valid if r[0]=="TRAIL")
            srv = sum(1 for r in valid if r[0]=="ST_REV")
            rbk = sum(1 for r in valid if r[0]=="RAWBRK")
            rtl = sum(1 for r in valid if r[0]=="RAWTRL")
            exp = sum(1 for r in valid if r[0]=="EXP")
            opn = sum(1 for r in valid if r[0]=="OPEN")
            if n==0: continue
            wins = tp+trl+srv+rbk+rtl
            wr = wins/(wins+sl)*100 if (wins+sl)>0 else 0
            totR = sum(r[2] for r in valid if r[0] in ("TP","SL","TRAIL","ST_REV","RAWBRK","RAWTRL"))
            avgR = totR/n
            bheld = [r[1] for r in valid if r[0] in ("TP","SL","TRAIL","ST_REV","RAWBRK","RAWTRL")]
            avgD = sum(bheld)/len(bheld) if bheld else 0
            print(f"{tr:<8} {n:>4} {tp:>4} {sl:>4} {trl:>4} {srv:>4} "
                  f"{rbk:>4} {rtl:>4} {exp:>4} {wr:>5.1f}% {totR:>+6.1f}R {avgR:>+6.3f} {avgD:>4.0f}d")
            if totR > best_R:
                best_R = totR; best_key = (mode,ok,tr)
    if best_key:
        print(f"\n═══ BEST [{label}]: {best_key[1]} {OPT_NAMES[best_key[1]]} × {best_key[2]} ═══")
        print(f"  Net R: {best_R:+.1f}R")
    return best_key, best_R

print("\n" + "="*72)
summarize("RAW (no ST filter)", "RAW")
best_g, R_g = summarize("GATED (ST downtrend @ C + entry)", "GATED")

# Comparison table: RAW vs GATED best per option
print(f"\n{'='*72}")
print("COMPARISON: RAW vs GATED (best TP per option)")
print(f"{'Option':<10} {'RAW_TotR':>10} {'GATED_TotR':>12} {'ΔR':>8}")
print("-"*44)
for ok in OPT_KEYS:
    # best TP for RAW
    raw_best = max(TP_RATIOS, key=lambda tr: sum(r[2] for r in all_res[("RAW",ok,tr)] if r[0] in ("TP","SL","TRAIL")))
    gat_best = max(TP_RATIOS, key=lambda tr: sum(r[2] for r in all_res[("GATED",ok,tr)] if r[0] in ("TP","SL","TRAIL")))
    rawR = sum(r[2] for r in all_res[("RAW",ok,raw_best)] if r[0] in ("TP","SL","TRAIL"))
    gatR = sum(r[2] for r in all_res[("GATED",ok,gat_best)] if r[0] in ("TP","SL","TRAIL"))
    print(f"{ok:<10} {rawR:>+9.1f}R {gatR:>+11.1f}R {gatR-rawR:>+7.1f}")
print("="*72)

# trailing detail
print(f"\n{'▸ TRAILING STOP (both modes)'}")
print(f"  Activation: price drops by half atr_pct% from entry")
print(f"  Trail gap: 1× ATR% from lowest_reached")
print(f"  SL still active during trailing")
print("="*72)

# canonical
from datetime import date
canon = [s for s in setups if df.index[s["entry_bar"]].date() >= date(2026,6,1)
         and df.index[s["entry_bar"]].date() <= date(2026,7,1)]
if canon:
    print(f"\n━━━ CANONICAL 2026 (RAW) ━━━")
    s = canon[0]; eb=s["entry_bar"]; entry=s["entry"]
    Ch=s["C_high"]; atr14=atr_val_at(eb,14)
    ap=atrp.atr_percentage(df.iloc[:eb+1],ATR_PCT_CFG); apct=ap["atr_pct"]
    st_c = st_trend[s["C_bar"]] == -1
    st_e = st_trend[eb] == -1
    print(f"  Entry {df.index[eb].date()} @ {entry:.0f}  C_high={Ch:.0f}  APCT={apct:.1f}%")
    print(f"  ST@C={'DOWN' if st_c else 'UP'}  ST@Entry={'DOWN' if st_e else 'UP'}  → ST_OK={s.get('st_ok',False)}")
    for ok in OPT_KEYS:
        sl,_ = get_sl_tp(entry,Ch,atr14,apct,ok,eb)
        ri = [x for x in range(len(setups)) if setups[x] is s][0]
        for tr in TP_RATIOS:
            r = all_res[("RAW",ok,tr)][ri]
            if r[0]=="INV": continue
            print(f"  {OPT_NAMES[ok]:>8}×{tr:<5} → {r[0]:>5} in {r[1]:>3}d  R={r[2]:+.2f}")
print("\n"+"="*72)
