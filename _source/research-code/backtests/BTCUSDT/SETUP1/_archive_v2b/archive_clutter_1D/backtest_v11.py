"""
SETUP 1 — SHORT backtester v11
FBF v11 (bear BREAK) -> mechanics Setup1 TETAP persis:
O1-O5 SL x TP 1x/2x/3x + TRAILING (ATR/ST/RB) + ST_REV + RAWBRK.

Sinyal SHORT = BREAK bear dari FBF v11 (engine default, utuh).
Entry = close bar BREAK (persis label "BREAK" di chart TradingView).
v11 default SUDAH ST-gated -> BREAK bear cuma ada kalau ST downtrend.
SMI 3-step DIBUANG (v11 SMI OFF by default).

BTCUSDT daily, window N bulan terakhir dari hari ini (--months).
"""
import sys, time, os
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/fetchers")
import datetime as _dt
RUN_TS = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTDIR = os.path.join(os.path.dirname(__file__), "results_v11", RUN_TS)
os.makedirs(OUTDIR, exist_ok=True)

import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--symbol", default="BTCUSDT")
ap.add_argument("--interval", default="1d")
ap.add_argument("--months", type=int, default=3,
               help="window: N bulan terakhir dari hari ini")
A = ap.parse_args()
SYM = A.symbol
TF = A.interval
MONTHS = A.months

import requests
import pandas as pd
import numpy as np
import atr_percentage as atrp
import fbf_v11_signal as sigmod

print(f"[v11] SETUP1 SHORT — FBF v11 bear BREAK | {SYM} {TF} | window {MONTHS}bln")

ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

# ---------- fetch (sama persis dgn backtest.py lama) ----------
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

# ---------- pivots (FBF v11 main 3/3) ----------
def find_pivots(high, low, left, right):
    n = len(high); ph = []; pl = []
    for i in range(left, n-right):
        pv = high[i]
        ok = True
        for k in range(1, left+1):
            if high[i-k] > pv or high[i+k] >= pv: ok = False; break
        if ok: ph.append((i, pv))
        pv = low[i]
        ok = True
        for k in range(1, left+1):
            if low[i-k] < pv or low[i+k] <= pv: ok = False; break
        if ok: pl.append((i, pv))
    return ph, pl

# ---------- Supertrend array (adaptive, FBF v6.10/11) ----------
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

# ---------- Bear raw break precompute (FBF bear state machine) ----------
def build_rawbrk(df, pivot_low):
    high = df["high"].values; low = df["low"].values; close = df["close"].values
    pl_by_idx = dict(pivot_low)
    running_last_pl = np.full(len(close), np.nan)
    last_pl_val = None
    for i in range(len(close)):
        if i in pl_by_idx: last_pl_val = pl_by_idx[i]
        running_last_pl[i] = last_pl_val
    tr = np.zeros(len(close)); tr[0] = high[0] - low[0]
    for i in range(1, len(close)):
        tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
    atr_arr = np.zeros(len(close)); atr_arr[0] = tr[0]; alpha = 1.0/14
    for i in range(1, len(close)):
        atr_arr[i] = atr_arr[i-1] + alpha*(tr[i]-atr_arr[i-1])
    bear_active = np.zeros(len(close), dtype=bool)
    _active = False; _ref_val = np.nan; _base_high = np.nan
    bear_last_high = np.nan
    for i in range(len(close)):
        rpl = running_last_pl[i]
        raw_bear = (not np.isnan(rpl)) and (close[i] < rpl)
        if not _active and raw_bear:
            if (rpl - close[i]) >= 0.15 * atr_arr[i]:
                _active = True; _ref_val = rpl; _base_high = high[i]
        elif _active:
            still = close[i] < _ref_val
            d2 = (_ref_val - close[i]) >= 0.15 * atr_arr[i] if not np.isnan(_ref_val) else False
            if not (still and d2): _active = False
        bear_active[i] = _active
        if _active:
            bear_last_high = bear_last_high if not np.isnan(bear_last_high) else _base_high
            if high[i] > bear_last_high: bear_last_high = high[i]
        else:
            bear_last_high = np.nan
    bear_trigger = np.zeros(len(close), dtype=bool)
    for i in range(1, len(close)):
        if bear_active[i] and not bear_active[i-1]: bear_trigger[i] = True
    return bear_active, bear_trigger

# ---------- ATR helpers ----------
def atr_val_at(i, period=14):
    sub = df.iloc[max(0,i-period+1):i+1]
    tr = pd.concat([sub["high"]-sub["low"],
                    (sub["high"]-sub["close"].shift(1)).abs(),
                    (sub["low"]-sub["close"].shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean().iloc[-1]

def get_sl_tp(entry, Ch, atr14, apct, opt, entry_bar=None):
    if opt == "O1": return (entry*1.1, entry*0.9)
    if opt == "O2": sl = Ch + atr14; return (sl, 2*entry - sl)
    if opt == "O3": sl = entry*(1+apct/100.0); return (sl, entry*(1-apct/100.0))
    if opt == "O4": return (entry*1.06, entry*0.94)
    if opt == "O5" and entry_bar is not None:
        conf_hi = df["high"].iloc[entry_bar]
        sl = conf_hi + atr14
        return (sl, 2*entry - sl)
    return (None, None)

# ---------- simulation ----------
def simulate(entry, sl, tp_1, fwd_h, fwd_l, atr_pct):
    risk = sl - entry
    tp_2 = entry - 2*risk
    tp_3 = entry - 3*risk
    activation_price = entry * (1 - (atr_pct/2)/100.0)
    trailing_active = False
    trail_stop = None
    lowest_reached = entry
    for k in range(len(fwd_h)):
        this_high = fwd_h[k]; this_low = fwd_l[k]
        if atr_pct > 0:
            if this_low < lowest_reached: lowest_reached = this_low
            if not trailing_active and lowest_reached <= activation_price:
                trailing_active = True
                trail_stop = lowest_reached * (1 + atr_pct/100.0)
            if trailing_active:
                trail_stop = lowest_reached * (1 + atr_pct/100.0)
                if this_high >= trail_stop:
                    return ("TRAIL", trail_stop, k+1, (entry - trail_stop)/risk)
        if trailing_active: continue
        if this_low <= tp_3: return ("TP3", tp_3, k+1, 3.0)
        if this_low <= tp_2: return ("TP2", tp_2, k+1, 2.0)
        if this_low <= tp_1: return ("TP1", tp_1, k+1, 1.0)
        if this_high >= sl: return ("SL", sl, k+1, -1.0)
        if k >= 240: return ("EXP", this_low, k+1, (entry - this_low)/risk)
    return ("OPEN", None, len(fwd_h), 0)

# ---------- run batch ----------
OPT_KEYS = ["O1","O2","O3","O4","O5"]
OPT_NAMES = {"O1":"Liq10x","O2":"C+ATR14","O3":"ATR%30","O4":"Fix6%","O5":"ConfHi+ATR"}
TP_RATIOS = ["1x","2x","3x"]
TRAIL_VARIANTS = ["ATR","ST","RB"]
COMBOS = []
for ok in OPT_KEYS:
    for tr in TP_RATIOS: COMBOS.append(("A", ok, tr, None))
for ok in OPT_KEYS:
    for tr in TP_RATIOS:
        for tv in TRAIL_VARIANTS: COMBOS.append(("B", ok, tr, tv))
for ok in OPT_KEYS:
    for tv in TRAIL_VARIANTS: COMBOS.append(("C", ok, None, tv))

def run_batch(setup_set, opt_key, mode, tp_ratio, trail_variant):
    out = []
    for s in setup_set:
        eb = s["entry_bar"]; entry = s["entry"]; Ch = s["C_high"]
        fwd_h = df["high"].values[eb+1:]; fwd_l = df["low"].values[eb+1:]
        atr14 = atr_val_at(eb, 14)
        ap = atrp.atr_percentage(df.iloc[:eb+1], ATR_PCT_CFG)
        apct = ap["atr_pct"]
        sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, opt_key, eb)
        if sl is None or sl <= entry or tp1 <= 0:
            out.append(("INV",0,0)); continue
        risk = sl - entry
        tp = None; r_mult = None
        if mode in ("A","B"):
            tp_tgts = {"1x":(tp1,1.0),"2x":(entry-2*risk,2.0),"3x":(entry-3*risk,3.0)}
            tp, r_mult = tp_tgts[tp_ratio]
        tr_active = False; lowest = entry; activation_pr = None; anchor_high = None
        if mode in ("B","C") and trail_variant == "ATR":
            if apct <= 0: out.append(("INV",0,0)); continue
            activation_pr = entry * (1 - (apct/2)/100.0)
        exited = False
        for k in range(len(fwd_h)):
            bar_idx = eb + 1 + k
            if bar_idx >= len(bear_active): break
            if mode in ("A","B") and fwd_l[k] <= tp:
                out.append(("TP", k+1, r_mult)); exited = True; break
            if fwd_h[k] >= sl:
                out.append(("SL", k+1, -1.0)); exited = True; break
            if mode in ("B","C"):
                if trail_variant == "ATR":
                    if fwd_l[k] < lowest: lowest = fwd_l[k]
                    if not tr_active and lowest <= activation_pr: tr_active = True
                    if tr_active:
                        trail = lowest * (1 + apct/100.0)
                        if fwd_h[k] >= trail:
                            R = (entry - trail)/risk
                            out.append(("TRAIL", k+1, R)); exited = True; break
                elif trail_variant == "ST":
                    if bar_idx < len(st_trend):
                        if st_trend[bar_idx] == 1 and (bar_idx == 0 or st_trend[bar_idx-1] == -1):
                            exit_pr = fwd_l[k] if fwd_l[k] < entry else entry
                            R = (entry - exit_pr)/risk
                            out.append(("ST_REV", k+1, R)); exited = True; break
                elif trail_variant == "RB":
                    if not tr_active and bear_trigger[bar_idx]:
                        tr_active = True; anchor_high = df["high"].values[bar_idx]
                    if tr_active:
                        if df["high"].values[bar_idx] > anchor_high: anchor_high = df["high"].values[bar_idx]
                        if fwd_h[k] >= anchor_high:
                            R = (entry - anchor_high)/risk
                            out.append(("RAWTRL", k+1, R)); exited = True; break
                    if tr_active:
                        prev_active = bear_active[bar_idx-1] if bar_idx-1 >= 0 else False
                        cur_active = bear_active[bar_idx]
                        if prev_active and not cur_active:
                            exit_pr = min(fwd_l[k], df["close"].values[bar_idx]) if df["close"].values[bar_idx] < entry else entry
                            R = (entry - exit_pr)/risk
                            out.append(("RAWBRK", k+1, R)); exited = True; break
        if not exited:
            lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
            out.append(("EXP", len(fwd_h), (entry-lastc)/risk))
    return out

# =================== MAIN ===================
print("[fetch] loading + FBF v11 signals...")
df, signals = sigmod.get_short_signals(SYM, TF, MONTHS)
print(f"[data] {len(df)} candles {df.index[0].date()} .. {df.index[-1].date()}")

high = df["high"].values; low = df["low"].values; close = df["close"].values
ph_main, pl_main = find_pivots(high, low, 3, 3)
st_trend = supertrend_full(df, period=10, mult=3.0)
bear_active, bear_trigger = build_rawbrk(df, pl_main)
print(f"[ST] downtrend bars: {int((st_trend==-1).sum())}/{len(st_trend)}")

# map v11 signals -> setup dict (sama shape dgn backtest.py lama)
setups = []
for s in signals:
    eb = s["entry_bar"]
    if eb+1 >= len(close): continue
    e2 = dict(s)
    e2["C_high"] = high[s["C_bar"]] if s["C_bar"] is not None else low[eb]
    e2["st_ok"] = True   # v11 BREAK bear SUDAH ST-gated
    setups.append(e2)
raw_n = len(setups)
gated = [s for s in setups if s.get("st_ok", False)]
print(f"[SETUP1] v11 bear BREAK signals: {raw_n} (all ST-gated)")

# ---------- journal ----------
TRADE_DETAIL = []
results = {}
for mode_label, ok, tp_ratio, trail_variant in COMBOS:
    for setup_set, set_name in [(setups, "V11"), (gated, "V11G")]:
        res = run_batch(setup_set, ok, mode_label, tp_ratio, trail_variant)
        key = (set_name, mode_label, ok, tp_ratio, trail_variant)
        results[key] = res
        for idx, s in enumerate(setup_set):
            if res[idx][0] == "INV": continue
            eb = s["entry_bar"]; entry = s["entry"]; Ch = s["C_high"]
            atr14 = atr_val_at(eb, 14)
            ap = atrp.atr_percentage(df.iloc[:eb+1], ATR_PCT_CFG); apct = ap["atr_pct"]
            sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, ok, eb)
            risk = (sl - entry) if (sl and sl > entry) else 0
            if mode_label in ("A","B") and tp_ratio:
                tp_tgt = {"1x":tp1,"2x":entry-2*risk,"3x":entry-3*risk}[tp_ratio]
            else: tp_tgt = None
            TRADE_DETAIL.append({
                "mode": set_name, "opt": ok, "combo_mode": mode_label,
                "tp_ratio": tp_ratio or "", "trail_variant": trail_variant or "",
                "entry_date": str(df.index[eb].date()), "entry": round(entry,2),
                "sl": round(sl,2) if sl else None,
                "sl_pct": round((sl/entry-1)*100,2) if sl else None,
                "tp_pct": round((tp_tgt/entry-1)*100,2) if tp_tgt else None,
                "apct": round(apct,2),
                "outcome": res[idx][0], "bars": res[idx][1], "R": round(res[idx][2],3),
            })

import csv
with open(os.path.join(OUTDIR, "journal.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["mode","opt","combo_mode","tp_ratio","trail_variant",
                                       "entry_date","entry","sl","sl_pct","tp_pct","apct","outcome","bars","R"])
    w.writeheader(); w.writerows(TRADE_DETAIL)
print(f"[JOURNAL] wrote {len(TRADE_DETAIL)} trades -> {os.path.join(OUTDIR, 'journal.csv')}")

# ---------- summary ----------
def summarize_v3(label, setup_set, set_name):
    print(f"\n{'='*72}")
    print(f"SETUP1 SHORT v11 — MODE A/B/C  [{label}]")
    print(f"BTCUSDT 1D | {len(setup_set)} signals")
    print(f"{'='*72}")
    for mode in ["A","B","C"]:
        mode_desc = {"A":"SL+TP","B":"SL+TP+TRAIL","C":"SL+TRAIL"}[mode]
        print(f"\n── MODE {mode} — {mode_desc} ──")
        print(f"{'combo':<20}{'Tr':>5}{'TP':>5}{'SL':>5}{'ATR':>5}{'SRV':>5}{'RBK':>5}{'RTL':>5}{'EXP':>5}{'WR%':>6}{'TotR':>8}{'AvgR':>8}")
        print("-"*88)
        for combo in COMBOS:
            m, ok, tp, tv = combo
            if m != mode: continue
            key = (set_name, m, ok, tp, tv)
            rs = results.get(key, [])
            valid = [r for r in rs if r[0]!="INV"]
            n = len(valid)
            if n==0: continue
            tp_n = sum(1 for r in valid if r[0]=="TP")
            sl_n = sum(1 for r in valid if r[0]=="SL")
            atr_n = sum(1 for r in valid if r[0]=="TRAIL")
            srv = sum(1 for r in valid if r[0]=="ST_REV")
            rbk = sum(1 for r in valid if r[0]=="RAWBRK")
            rtl = sum(1 for r in valid if r[0]=="RAWTRL")
            exp = sum(1 for r in valid if r[0]=="EXP")
            wins = tp_n+atr_n+srv+rbk+rtl
            wr = wins/(wins+sl_n)*100 if (wins+sl_n)>0 else 0
            totR = sum(r[2] for r in valid if r[0] in ("TP","SL","TRAIL","ST_REV","RAWBRK","RAWTRL"))
            avgR = totR/n
            if mode == "A": name = f"{ok}-{OPT_NAMES[ok]} {tp}"
            elif mode == "B": name = f"{ok}-{OPT_NAMES[ok]} {tp}+{tv}"
            else: name = f"{ok}-{OPT_NAMES[ok]} t-{tv}"
            print(f"{name:<20}{n:>5}{tp_n:>5}{sl_n:>5}{atr_n:>5}{srv:>5}{rbk:>5}{rtl:>5}{exp:>5}{wr:>5.1f}%{totR:>+8.1f}{avgR:>+8.3f}")

print("\n"+"="*72)
summarize_v3("V11 (bear BREAK, all)", setups, "V11")
print("\n"+"="*72)
summarize_v3("V11G (ST-gated, same)", gated, "V11G")
print("\n"+"="*72)
print(f"\nDone. Results: {OUTDIR}")
