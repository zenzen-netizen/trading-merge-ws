"""
SETUP 1 — SHORT backtester
FBF AB (bear structure) + SMI 3-step confluence
BTCUSDT daily, 2023-01-01 .. now
TP = 1:1, 4 SL options compared.

Entry rule (per setup1_flow.md):
  PHASE 1  FBF AB confirmed (B pivot valid, A > B)
  PHASE 2  TRACKING C = next pivot high after B (pullback up)
  PHASE 3  SMI 3-step during C pullback (in order):
             STEP1  bar_state == "[!] Fail MID Buy"
             STEP2  bar_state contains PD ("[~] PD" / "[OK] PD" / "PD TRIGGERED")
             STEP3  bar_state == "[X] Cross DN"  (trigger)
           Entry = close of the X Cross DN bar
  PHASE 4  Short entry (perp isolated 10x)
  PHASE 5  SL per 4 options; PHASE 6 TP = 1:1

AB confirm = B pivot low validated at bar+3 (not close-break dependent).
Window for SMI = from B_bar .. next close < B_val (breakdown) or end.
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

# ---------- fetch 2023..now paginated ----------
def fetch_full(sym, tf, start_ts, end_ts):
    url = "https://api.binance.com/api/v3/klines"
    all_rows = []
    cur = int(start_ts.timestamp()*1000)
    end_ms = int(end_ts.timestamp()*1000)
    step = 895*24*60*60*1000  # ~895d in ms
    while cur < end_ms:
        nxt = min(cur + step, end_ms)
        params = {"symbol":sym,"interval":tf,"startTime":cur,"endTime":nxt,"limit":1000}
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            cur = nxt; continue
        all_rows.extend(rows)
        cur = rows[-1][0] + 1
        time.sleep(0.2)
    df = pd.DataFrame(all_rows, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","qav","trades","tbav","tqav","ignore"])
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("open_time").sort_index()
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
ph_bars = sorted(PH.keys())
pl_bars = sorted(PL.keys())

# ---------- FBF bear structure (AB) detection ----------
# AB: swing high A, then pivot low B confirmed at B+3.
#   A must be > B (bear downmove).
# After B confirmed = TRACKING C mode.
# C = next pivot high after B (pullback up), C > B_val.

def next_ph_after(bar):
    for b in ph_bars:
        if b > bar:
            return b, PH[b]
    return None, None

ab_events = []
for B_bar, B_val in pl_main:
    if B_bar < 50: continue
    # last PH before B_bar = A
    A_bar = None; A_val = None
    for b in reversed(ph_bars):
        if b < B_bar:
            A_bar, A_val = b, PH[b]; break
    if A_bar is None: continue
    if not (A_val > B_val): continue  # A must be higher
    confirm_bar = B_bar + 3  # B pivot confirmed
    if confirm_bar >= len(close): continue
    # C = first PH after B_bar
    C_bar, C_val = next_ph_after(B_bar)
    if C_bar is None or C_bar < confirm_bar: continue
    if not (C_val > B_val): continue
    ab_events.append(dict(bar=confirm_bar, A_bar=A_bar, A_val=A_val,
                          B_bar=B_bar, B_val=B_val, C_bar=C_bar, C_val=C_val))

# dedup per B
seen_B = set(); ab_clean = []
for e in sorted(ab_events, key=lambda x: x["bar"]):
    if e["B_bar"] not in seen_B:
        seen_B.add(e["B_bar"])
        ab_clean.append(e)
print(f"[AB] bear-structure events (2023..now): {len(ab_clean)}")

# ---------- SMI 3-step inside pullback window ----------
# Pullback window = [B_bar .. first close < B_val (breakdown) or end]
# C pullback: after B, price rises (pullback C), then eventually breaks below B.
# 3-step (FMB -> PD -> XDN) must complete inside this window.
# Entry = close of X Cross DN bar.

def smi_at(i):
    return smi_pro.smi_pro_v3(df.iloc[:i+1], SMI_CFG)

setups = []
for e in ab_clean:
    Bb, Bv, Cb, Cv = e["B_bar"], e["B_val"], e["C_bar"], e["C_val"]
    # breakdown = first bar after Bb where close < Bv
    end = len(close)-1
    for i in range(Bb+1, len(close)):
        if close[i] < Bv:
            end = i; break
    # C must form before breakdown (pullback exists)
    if Cb > end: continue
    # scan for FMB -> PD -> XDN
    seq = []
    for i in range(max(Bb, 2), end+1):
        s = smi_at(i)
        bs = s["bar_state"]
        if bs == "[!] Fail MID Buy":
            seq.append(("FMB", i))
        elif bs.startswith("[~] PD") or bs.startswith("[OK] PD") or bs == "PD TRIGGERED":
            seq.append(("PD", i))
        elif bs == "[X] Cross DN":
            seq.append(("XDN", i))
    fmb_idx = [x[1] for x in seq if x[0]=="FMB"]
    pd_idx = [x[1] for x in seq if x[0]=="PD"]
    xdn_idx = [x[1] for x in seq if x[0]=="XDN"]
    found = None
    for f in fmb_idx:
        pc = [p for p in pd_idx if p > f]
        if not pc: continue
        p = pc[0]
        xc = [x for x in xdn_idx if x > p]
        if not xc: continue
        x = xc[0]
        found = (f, p, x); break
    if found:
        entry_bar = found[2]
        e2 = dict(e)
        e2["entry_bar"] = entry_bar
        e2["entry"] = close[entry_bar]
        e2["C_high"] = high[Cb]
        e2["fmb"] = df.index[found[0]].date()
        e2["pd"] = df.index[found[1]].date()
        e2["entry_date"] = df.index[entry_bar].date()
        setups.append(e2)

print(f"[SETUP1] valid signals (FMB->PD->XDN in window): {len(setups)}")

# print each for verification
if len(setups) <= 20:
    for s in setups:
        print(f"  AB_con={df.index[s['bar']].date():>12} "
              f"A={df.index[s['A_bar']].date():>12}({s['A_val']:.0f}) "
              f"B={df.index[s['B_bar']].date():>12}({s['B_val']:.0f}) "
              f"C={df.index[s['C_bar']].date():>12}({s['C_val']:.0f}) "
              f"FMB={s['fmb']} PD={s['pd']} ENTRY={s['entry_date']}({s['entry']:.0f})")

# ---------- backtest: each setup x 4 options, 1:1 R:R ----------
def atr_val_at(i, period=14):
    sub = df.iloc[max(0,i-period+1):i+1]
    tr = pd.concat([sub["high"]-sub["low"],
                    (sub["high"]-sub["close"].shift(1)).abs(),
                    (sub["low"]-sub["close"].shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean().iloc[-1]

def simulate(entry, sl, tp, fwd_high, fwd_low):
    """return (outcome, exit_price, bars_held)"""
    for k in range(len(fwd_high)):
        if fwd_low[k] <= tp:
            return "TP", tp, k+1
        if fwd_high[k] >= sl:
            return "SL", sl, k+1
        if k >= 120:  # max hold 120 bars
            return "EXP", fwd_low[k], k+1
    return "OPEN", None, len(fwd_high)

results = {k: [] for k in ["O1","O2","O3","O4"]}
for s in setups:
    eb = s["entry_bar"]; entry = s["entry"]; Ch = s["C_high"]
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    # option SL/TP
    sl1 = entry*1.1;     tp1 = entry*0.9
    atr14 = atr_val_at(eb, 14); sl2 = Ch + atr14; tp2 = 2*entry - sl2
    ap = atrp.atr_percentage(df.iloc[:eb+1], ATR_PCT_CFG)
    atr_pct = ap["atr_pct"]
    sl3 = entry*(1+atr_pct/100.0); tp3 = entry*(1-atr_pct/100.0)
    sl4 = entry*1.06;    tp4 = entry*0.94
    opts = {"O1":(sl1,tp1),"O2":(sl2,tp2),"O3":(sl3,tp3),"O4":(sl4,tp4)}
    for k,(sl,tp) in opts.items():
        if tp <= 0 or sl <= entry:
            results[k].append(("INV",None,0)); continue
        res, px, bars = simulate(entry, sl, tp, fwd_h, fwd_l)
        results[k].append((res, px, bars))

# ---------- report ----------
n_setups = len(setups)
print("\n" + "="*72)
print("SETUP 1 SHORT — BACKTEST REPORT")
print(f"BTCUSDT 1D | 2023-01-01 .. {df.index[-1].date()} | {len(df)} candles")
print(f"AB bear-structure events: {len(ab_clean)} | Setup1 signals: {n_setups}")
print("="*72)

names = {"O1":"Liq10x (E*1.1)","O2":"C+ATR14","O3":"ATR%30","O4":"Fix6% (E*1.06)"}
print(f"\n{'Option':<14}{'Trades':>6} {'TP':>4} {'SL':>4} {'EXP':>4} {'WR%':>6} "
      f"{'TotR':>6} {'AvgR':>6} {'AvgB':>6}")
print("-"*72)
for k in ["O1","O2","O3","O4"]:
    rs = results[k]
    valid = [(r,b) for r,b in zip(rs,[s["entry_bar"] for s in setups]) if r[0]!="INV"]
    n = len(valid)
    wins = sum(1 for r,_ in valid if r[0]=="TP")
    loss = sum(1 for r,_ in valid if r[0]=="SL")
    exp  = sum(1 for r,_ in valid if r[0]=="EXP")
    opn  = sum(1 for r,_ in valid if r[0]=="OPEN")
    if n==0:
        print(f"{names[k]:<14}{'-- no valid':>20}")
        continue
    wr = (wins/(wins+loss))*100 if (wins+loss)>0 else 0
    R = wins*1.0 - loss*1.0
    avgR = R/n
    # bars_held from simulate result (r[2]), NOT entry_bar!
    bheld = [r[2] for r,_ in valid if r[0] in ("TP","SL")]
    avgB = sum(bheld)/len(bheld) if bheld else 0
    print(f"{names[k]:<14}{n:>6} {wins:>4} {loss:>4} {exp:>4} {wr:>5.1f}% {R:>+5.1f}R {avgR:>+.3f} {avgB:>5.1f}d")

# highlight the first 2026 canonical trade (entry ~ Jun 2026)
from datetime import date
canon_entry = [s for s in setups
               if s["entry_date"] >= date(2026,6,1) and s["entry_date"] <= date(2026,7,1)]
if len(canon_entry) > 0:
    print(f"\n━━━ CANONICAL 2026 trade (our example) ━━━")
    print(f"{'Entry':<14} {'E':>7} {'FMB':>12} {'PD':>12}")
    s = canon_entry[0]
    print(f"{str(s['entry_date']):<14} {s['entry']:>7.0f} {str(s['fmb']):>12} {str(s['pd']):>12}")
    print(f"  A={df.index[s['A_bar']].date()} {s['A_val']:.0f}  "
          f"B={df.index[s['B_bar']].date()} {s['B_val']:.0f}  "
          f"C={df.index[s['C_bar']].date()} {s['C_val']:.0f}")
    for opt in ["O1","O2","O3","O4"]:
        r = results[opt][setups.index(s)]
        print(f"  {names[opt]:<14} → {r[0]} in {r[2]}d")

print("\n" + "="*72)
