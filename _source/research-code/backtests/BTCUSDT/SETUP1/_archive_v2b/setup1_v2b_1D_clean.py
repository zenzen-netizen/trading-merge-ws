"""
setup1_v2b_clean.py
========================
SETUP1 SHORT v2.b (Variant E / RESET-ONLY) — CLEAN STUDY + 5-TRADE BACKTEST

Engine (semua yang TERBARU, tidak ada campur aduk):
  - FBF  = FBFEngine v11 (fbf_v11_backtest)
  - SMI  = SMI Pro v3 latest trigger (smi_events: FMB -> PD -> XDN)
  - v2.b = Variant E (RESET ONLY):
           SMI 3-step + ST(10,3) DOWN + no-wait-C + 1 wave=1 posisi
           + reset fmb_b/pd_b saat WAVE_CANCELLED / WAVE_STRUCT_REJECTED /
             CANDIDATE_INVALIDATED / CANDIDATE_EVICTED.
           TANPA gate depth / maturity / smi_pd (itulah Variant E).

Backtest 5 trade DAILY paling recent:
  SL diuji ISOLATED (satu-satu):
    A = ATR%   (O3): sl = entry*(1 + apct/100)
    B = Liq10x (O1): sl = entry*1.10            (= 10%)
    C = C+ATR  (O2): sl = C_high + atr14       (n/a kalau C blm lock)
  TP DIPATOK 1x SAJA: tp = 2*entry - sl  (R=+1 TP, R=-1 SL)
  RAWBRK dipantau & dicatat: trigger = bear_active False->True
    (close tembus pivot-low terakhir dgn jarak >= 0.15*ATR14).

Output:
  - per-trade event window (FBF chain + SMI 3-step + RAWBRK rule & kenapa loss)
  - tabel ringkas ATR% / Liq10x / C+ATR x 1x-TP
  - chart dark (mobile-friendly): entry / SL / TP(1x) / RAWBRK-ref / pivlow FBF
"""
import sys, os, io, contextlib, time
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
sys.path.insert(0, "/home/ubuntu")  # FBFEngine default (fbf_v11_backtest.py)
import datetime as _dt
import pandas as pd
import numpy as np
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data_BTCUSDT_1d_2021now.csv")
SYM = "BTCUSDT"; TF = "1d"
START = pd.Timestamp("2021-01-01", tz="UTC")
END = pd.Timestamp.now("UTC").normalize()
WIB = 7
IV_MS = 86400000

SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

# ============================================================
# 1. FETCH / CACHE
# ============================================================
def fetch_full(sym, tf, start_ts, end_ts):
    url = "https://api.binance.com/api/v3/klines"
    all_rows = []; cur = int(start_ts.timestamp()*1000); end_ms = int(end_ts.timestamp()*1000)
    step = 895*24*60*60*1000
    while cur < end_ms:
        nxt = min(cur+step, end_ms)
        r = requests.get(url, params={"symbol":sym,"interval":tf,
                     "startTime":cur,"endTime":nxt,"limit":1000}, timeout=30).json()
        if r: all_rows.extend(r); cur=r[-1][0]+1
        else: cur=nxt
        time.sleep(0.2)
    df = pd.DataFrame(all_rows, columns=["ot","o","h","l","c","v","ct","q","t","tb","tq","ig"])
    for c2 in ["o","h","l","c","v"]: df[c2]=df[c2].astype(float)
    df["ot"]=pd.to_datetime(df["ot"],unit="ms",utc=True)
    df=df.set_index("ot").sort_index()
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    return df[["open","high","low","close","volume"]]

print("[*] loading data BTCUSDT 1d (2021..now) ...")
if os.path.exists(CACHE) and (time.time()-os.path.getmtime(CACHE)) < 2*86400:
    df = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    print(f"[*] cache hit: {len(df)} candles {df.index[0].date()} .. {df.index[-1].date()}")
else:
    df = fetch_full(SYM, TF, START, END)
    df.to_csv(CACHE)
    print(f"[*] fetched & cached: {len(df)} candles {df.index[0].date()} .. {df.index[-1].date()}")

high = df["high"].values.astype(float)
low  = df["low"].values.astype(float)
close= df["close"].values.astype(float)
n = len(df)

# ============================================================
# 2. SUPERTREND (period=10 mult=3) — sama spt spec
# ============================================================
def supertrend_full(period=10, mult=3.0):
    h=high; l=low; c=close
    hl2=(h+l)/2.0; tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n):
        tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    atr=np.zeros(n); atr[0]=tr[0]; alpha=1.0/period
    for i in range(1,n): atr[i]=atr[i-1]+alpha*(tr[i]-atr[i-1])
    up_raw=hl2-mult*atr; dn_raw=hl2+mult*atr
    up_f=np.zeros(n); dn_f=np.zeros(n); trend=np.ones(n,dtype=int)
    up_f[0]=up_raw[0]; dn_f[0]=dn_raw[0]
    for i in range(1,n):
        up_f[i]=max(up_raw[i],up_f[i-1]) if c[i-1]>up_f[i-1] else up_raw[i]
        dn_f[i]=min(dn_raw[i],dn_f[i-1]) if c[i-1]<dn_f[i-1] else dn_raw[i]
        trend[i]=trend[i-1]
        if trend[i-1]==-1 and c[i]>dn_f[i-1]: trend[i]=1
        elif trend[i-1]==1 and c[i]<up_f[i-1]: trend[i]=-1
    return trend
st_trend = supertrend_full(10, 3.0)

# ============================================================
# 3. SMI Pro v3 (smi_events) — latest trigger
# ============================================================
import smi_events as SM
E = SM.compute_smi_events(df, SMI_CFG)
FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]
smi = E["smi"]; smi_hist = E["smi_hist"]; hist_state = E["hist_state"]
def describe_bar(i): return SM.describe_bar(E, i)

# ============================================================
# 4. FBF v11 ENGINE (terbaru)
# ============================================================
import fbf_v11_backtest as V11
times=[int(t.value//1_000_000) for t in df.index]
eng = V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, IV_MS)
breaks, events = eng.run()
ev_by_bar={}
for e in events:
    ev_by_bar.setdefault(e["bar"], []).append(e)
print(f"[FBF v11] {len([e for e in events if e['side']=='bear'])} bear events")

# ============================================================
# 5. v2.b TRIGGER (RESET-ONLY / Variant E)
# ============================================================
import atr_percentage as atrp
def atr_pct_at(i): return atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]
def atr14_at(i):
    sub=df.iloc[max(0,i-13):i+1]
    tr=pd.concat([sub["high"]-sub["low"],(sub["high"]-sub["close"].shift(1)).abs(),
                  (sub["low"]-sub["close"].shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1]

samples=[]
pos_open=False; clear_bar=-1
wave_A=None; wave_B=None; wave_c=None; wave_started_bar=None
fmb_b=None; pd_b=None; wave_entry_done=False
for i in range(n):
    if pos_open:
        if i >= clear_bar: pos_open=False; clear_bar=-1
        else: continue
    for e in ev_by_bar.get(i, []):
        if e["side"]!="bear": continue
        if e["event"]=="WAVE_STARTED":
            wave_A=(e["a_bar"], e["a_val"]); wave_B=(e["b_bar"], e["b_val"])
            wave_started_bar=e["bar"]; wave_entry_done=False
            if pd_b is None: fmb_b=None; wave_c=None
        elif e["event"]=="C_LOCKED":
            wave_c=(e["c_bar"], e["c_val"], e.get("retrace_pct"))
        # --- v2.b #1: RESET SMI tracker saat wave batal ---
        elif e["event"] in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED",
                            "CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
            fmb_b=None; pd_b=None
    # SMI 3-step (sequential, gap allowed)
    if not wave_entry_done:
        if FMB[i] and fmb_b is None: fmb_b=i
        if fmb_b is not None and pd_b is None and PD[i] and i>=fmb_b: pd_b=i
        if fmb_b is not None and pd_b is not None and XDN[i] and i>=pd_b:
            if st_trend[i]==-1:   # <- satu-satunya gate: ST down di entry
                entry=close[i]
                atr14=atr14_at(i); apct=atr_pct_at(i)
                Ch = high[wave_c[0]] if wave_c else np.nan
                Bctx = wave_B if wave_B is not None else (None, None)
                samples.append(dict(bar=i, entry=entry, A=wave_A, B=Bctx, C=wave_c,
                                    fmb_b=fmb_b, pd_b=pd_b, xdn_b=i,
                                    st=st_trend[i], atr14=atr14, apct=apct, Ch=Ch))
                # clear bar via 1x TP/SL (O3) supaya 1 wave=1 posisi
                sl0=entry*(1+apct/100.0); tp0=entry-(sl0-entry)
                fwd_h=high[i+1:]; fwd_l=low[i+1:]; ck=240
                for k in range(len(fwd_h)):
                    if fwd_l[k]<=tp0 or fwd_h[k]>=sl0 or k>=240: ck=k; break
                clear_bar=i+1+ck
                pos_open=True; wave_entry_done=True
            fmb_b=None; pd_b=None

print(f"[v2.b] total sinyal (START=2021): {len(samples)}")
sel = samples[-5:]
print(f"[v2.b] 5 trade recent: " + ", ".join(df.index[s['bar']].strftime('%Y-%m-%d') for s in sel))

# ============================================================
# 6. RAWBRK PRECOMPUTE (fbf_v610.find_pivots, atr_mult=0.15) — PERSIS backtest.py
# ============================================================
import fbf_v610 as fbfmod
ph_arr, pl_arr = fbfmod.find_pivots(high, low, 3, 3)
pl_by_idx = dict(pl_arr)
running_last_pl = np.full(n, np.nan)
for i in range(n):
    if i in pl_by_idx: running_last_pl[i]=pl_by_idx[i]
tr=np.zeros(n); tr[0]=high[0]-low[0]
for i in range(1,n): tr[i]=max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1]))
atr_arr=np.zeros(n); atr_arr[0]=tr[0]; alpha=1.0/14
for i in range(1,n): atr_arr[i]=atr_arr[i-1]+alpha*(tr[i]-atr_arr[i-1])
bear_active=np.zeros(n,dtype=bool); bear_last_high=np.nan
_active=False; _ref_val=np.nan; _base_high=np.nan
for i in range(n):
    rpl=running_last_pl[i]
    raw_bear = (not np.isnan(rpl)) and (close[i]<rpl)
    if not _active and raw_bear:
        if (rpl-close[i])>=0.15*atr_arr[i]:
            _active=True; _ref_val=rpl; _base_high=high[i]
    elif _active:
        if close[i]<_ref_val and (rpl-close[i])>=0.15*atr_arr[i]:
            pass
        else: _active=False
    bear_active[i]=_active
bear_trigger=np.zeros(n,dtype=bool)
for i in range(1,n):
    if bear_active[i] and not bear_active[i-1]: bear_trigger[i]=True

# ============================================================
# 7. BACKTEST per trade (3 SL isolated, TP=1x, RAWBRK tracked)
# ============================================================
def get_sl(entry, Ch, atr14, apct, kind):
    if kind=="ATR":  return entry*(1+apct/100.0)
    if kind=="LIQ":  return entry*1.10
    if kind=="CATR":
        if np.isnan(Ch): return None
        return Ch+atr14
    return None

def sim(s, sl):
    if sl is None or sl<=s["entry"]: return None
    entry=s["entry"]; eb=s["bar"]
    tp=2*entry-sl; risk=sl-entry
    fwd_h=high[eb+1:]; fwd_l=low[eb+1:]
    tr_active=False; anchor=None; rb_trig_bar=None
    for k in range(len(fwd_h)):
        bi=eb+1+k
        if bi>=n: break
        if fwd_l[k]<=tp: return dict(out="TP", ex=tp, bars=k+1, R=1.0, rb_trig=rb_trig_bar)
        if fwd_h[k]>=sl: return dict(out="SL", ex=sl, bars=k+1, R=-1.0, rb_trig=rb_trig_bar)
        if not tr_active and bear_trigger[bi]:
            tr_active=True; anchor=high[bi]; rb_trig_bar=bi
        if tr_active:
            if high[bi]>anchor: anchor=high[bi]
            if fwd_h[k]>=anchor: return dict(out="RAWTRL", ex=anchor, bars=k+1,
                                            R=(entry-anchor)/risk, rb_trig=rb_trig_bar)
            if bi>0 and bear_active[bi-1] and not bear_active[bi]:
                ex=min(fwd_l[k],close[bi]) if close[bi]<entry else entry
                return dict(out="RAWBRK", ex=ex, bars=k+1, R=(entry-ex)/risk, rb_trig=rb_trig_bar)
    lastc=fwd_l[-1] if len(fwd_l)>0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk, rb_trig=rb_trig_bar)

KINDS=["ATR","LIQ","CATR"]
print("\n"+"="*100)
print("RAWBRK RULE: trigger = bear_active False->True  <=>  close < pivot-low terakhir")
print("           DAN jarak(PL - close) >= 0.15 * ATR14.")
print("           Setelah trigger: anchor = high tertinggi sejak trigger; exit bila high >= anchor.")
print("           (break LOST = bear_active active->inactive => exit di bawah entry)")
print("="*100)

for idx, s in enumerate(sel, 1):
    eb=s["bar"]; entry=s["entry"]; A=s["A"]; B=s["B"]; C=s["C"]
    fmb_b=s["fmb_b"]; pd_b=s["pd_b"]; xdn_b=s["xdn_b"]
    print("\n"+"="*100)
    print(f"TRADE #{idx} | ENTRY {df.index[eb].strftime('%Y-%m-%d')} | close={entry:.2f}")
    print("="*100)
    # FBF
    print(f"\n  [FBF v11 BEAR WAVE]")
    print(f"    WAVE_STARTED: A={A[1]:.2f}@{df.index[A[0]].strftime('%Y-%m-%d')}  B={B[1]:.2f}@{df.index[B[0]].strftime('%Y-%m-%d')}")
    if C: print(f"    C_LOCKED:     C={C[1]:.2f}@{df.index[C[0]].strftime('%Y-%m-%d')} retrace={C[2]:.1f}%")
    else: print(f"    C_LOCKED:     BELUM (no-wait C -> entry valid tanpa C)")
    chain=[(i,e["event"],e) for i in range(A[0], eb+1) for e in ev_by_bar.get(i,[]) if e["side"]=="bear"]
    if chain:
        print(f"    FBF EVENT CHAIN (bar {A[0]} -> {eb}):")
        for bi,evt,evd in chain:
            cv=evd.get('c_val'); c_val=f" C={cv:.0f}" if cv is not None else ""
            bv=evd.get('b_val'); b_val=f" B={bv:.0f}" if bv is not None else ""
            rp=evd.get('retrace_pct'); retr=f" ret={rp:.1f}%" if rp is not None else ""
            print(f"      bar {bi:>5} {df.index[bi].strftime('%Y-%m-%d'):>12}  {evt:26s}{c_val}{b_val}{retr}")
    # SMI
    print(f"\n  [SMI 3-STEP]")
    print(f"    FMB={df.index[fmb_b].strftime('%Y-%m-%d')} SMI={smi[fmb_b]:.1f} hist={smi_hist[fmb_b]:.1f} [{hist_state[fmb_b]}] ST={'DN' if st_trend[fmb_b]==-1 else 'UP'}")
    print(f"    PD ={df.index[pd_b].strftime('%Y-%m-%d')} SMI={smi[pd_b]:.1f} hist={smi_hist[pd_b]:.1f} [{hist_state[pd_b]}] ST={'DN' if st_trend[pd_b]==-1 else 'UP'}")
    print(f"    XDN={df.index[xdn_b].strftime('%Y-%m-%d')} SMI={smi[xdn_b]:.1f} hist={smi_hist[xdn_b]:.1f} [{hist_state[xdn_b]}] ST={'DN' if st_trend[xdn_b]==-1 else 'UP'}  <- ENTRY")
    # RAWBRK rule & why
    print(f"\n  [RAWBRK RULE & WHY]")
    rpl=running_last_pl[eb]
    pl_bar=int(np.where(np.isclose(np.array(list(pl_by_idx.values())) if False else np.full(1,np.nan),0))[0].sum()) if False else None
    # cari bar pivot-low terakhir
    last_pl_bar=None; last_pl_val=None
    for bi in sorted(pl_by_idx.keys()):
        if bi<=eb: last_pl_bar=bi; last_pl_val=pl_by_idx[bi]
        else: break
    if last_pl_val is not None:
        gap=(entry-last_pl_val)/entry*100
        need=0.15*atr14_at(eb)
        print(f"    RAWBRK ref = last pivot-low {last_pl_val:.2f} @ {df.index[last_pl_bar].strftime('%Y-%m-%d')}")
        print(f"    entry={entry:.2f} -> harus tembus DI BAWAH {last_pl_val:.2f} (jarak {gap:.1f}% dari entry, butuh close>=PL-{need:.2f}$)")
        # forward lowest (low & close)
        fwd_lw=low[eb+1:min(n,eb+241)]; fwd_cl=close[eb+1:min(n,eb+241)]
        if len(fwd_lw):
            ml=int(np.argmin(fwd_lw)); mlv=fwd_lw[ml]; mlb=eb+1+ml
            mc=int(np.argmin(fwd_cl)); mcv=fwd_cl[mc]; mcb=eb+1+mc
            low_below = mlv < last_pl_val
            close_below = mcv < last_pl_val
            # cek jarak close terdalam vs PL
            deepest_close_below = None
            for k in range(len(fwd_cl)):
                if fwd_cl[k] < last_pl_val:
                    d=(last_pl_val-fwd_cl[k])
                    if deepest_close_below is None or d>deepest_close_below[1]:
                        deepest_close_below=(eb+1+k, d)
            print(f"    Forward LOW  terdalam = {mlv:.2f} @ {df.index[mlb].strftime('%Y-%m-%d')}  -> {'DI BAWAH' if low_below else 'DI ATAS'} PL ref")
            print(f"    Forward CLOSE terdalam = {mcv:.2f} @ {df.index[mcb].strftime('%Y-%m-%d')}  -> {'DI BAWAH' if close_below else 'DI ATAS'} PL ref")
            if close_below and deepest_close_below:
                dgap=deepest_close_below[1]
                print(f"    Close pernah tembus PL: jarak terdalam {dgap:.2f}$ vs butuh {need:.2f}$ -> {'CUKUP (trigger)' if dgap>=need else 'KURANG (gak cukup utk trigger)'}")
                print(f"    => RAWBRK {'mungkin trigger' if dgap>=need else 'pre-trigger tp jarak kurang'}")
            else:
                print(f"    Close TIDAK pernah tembus PL (walau low sempet nyentuh: {low_below}) -> RAWBRK TIDAK pernah trigger")
    # sim each SL
    print(f"\n  [BACKTEST: 3 SL x TP(1x)]")
    print(f"    {'SL':>5} {'level':>11} {'TP(1x)':>11} {'OUT':>7} {'exit$':>10} {'bars':>5} {'R':>6}  RAWBRK-trig")
    for kind in KINDS:
        sl=get_sl(entry, s["Ch"], s["atr14"], s["apct"], kind)
        if sl is None:
            print(f"    {kind:>5} {'n/a':>11} {'':>11} {'-':>7} {'':>10} {'':>5} {'':>6}  (C blm lock)")
            continue
        r=sim(s, sl)
        if r is None: continue
        tg = df.index[r['rb_trig']].strftime('%Y-%m-%d') if r['rb_trig'] is not None else "-"
        print(f"    {kind:>5} {sl:>11.2f} {2*entry-sl:>11.2f} {r['out']:>7} {r['ex']:>10.2f} {r['bars']:>5} {r['R']:>+6.2f}  {tg}")
    # price context +/-5
    print(f"\n  [PRICE +/-5 bar]")
    print(f"  {'date':>12} {'open':>10} {'high':>10} {'low':>10} {'close':>10} ST")
    for i in range(max(0,eb-5), min(n,eb+6)):
        st="DN" if st_trend[i]==-1 else "UP"
        mk=" <- ENTRY" if i==eb else ""
        print(f"  {df.index[i].strftime('%Y-%m-%d'):>12} {df['open'].iloc[i]:>10.2f} {high[i]:>10.2f} {low[i]:>10.2f} {close[i]:>10.2f} {st}{mk}")

# ============================================================
# 8. RINGKASAN TABEL
# ============================================================
print("\n"+"#"*100)
print("# RINGKASAN: 5 trade x (ATR% / Liq10x / C+ATR) x TP(1x)  [R = (entry-exit)/risk]")
print("#"*100)
print(f"  {'#':>2} {'ENTRY':>12} | {'ATR%':>7} {'Liq10x':>8} {'C+ATR':>8} | RAWBRK-trig?")
for idx,s in enumerate(sel,1):
    eb=s["bar"]; entry=s["entry"]
    rs={}
    for kind in KINDS:
        sl=get_sl(entry,s["Ch"],s["atr14"],s["apct"],kind)
        rs[kind]= sim(s,sl) if sl is not None else None
    def fmt(r): return f"{r['R']:+.2f}" if r else " n/a"
    # rawbrk trigger global (pakai ATR% run sbg proxy pantauan)
    rb = rs["ATR"]; rbtrig = df.index[rb['rb_trig']].strftime('%Y-%m-%d') if (rb and rb['rb_trig'] is not None) else "TIDAK"
    print(f"  {idx:>2} {df.index[eb].strftime('%Y-%m-%d'):>12} | {fmt(rs['ATR']):>7} {fmt(rs['LIQ']):>8} {fmt(rs['CATR']):>8} | {rbtrig}")

# ============================================================
# 9. CHART (dark, mobile-friendly)
# ============================================================
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.style.use("dark_background")
    fig, axes = plt.subplots(5, 1, figsize=(8, 13), sharex=False)
    fig.suptitle("SETUP1 v2.b — 5 Trade Recent + RAWBRK Rule", color="white", fontsize=11)
    for ax, s in zip(axes, sel):
        eb=s["bar"]; entry=s["entry"]
        a0=max(0,eb-12); a1=min(n,eb+130)
        xx=range(a0,a1)
        ax.plot(xx, close[a0:a1], color="#88aaff", lw=1.1, label="close")
        # pivot lows (FBF) sebagai titik
        for bi in pl_by_idx:
            if a0<=bi<a1: ax.scatter([bi],[pl_by_idx[bi]], color="#ffaa44", s=10, zorder=5)
        # last pivot low ref (RAWBRK)
        lastpv=None
        for bi in sorted(pl_by_idx.keys()):
            if bi<=eb: lastpv=pl_by_idx[bi]
            else: break
        if lastpv is not None:
            ax.axhline(lastpv, color="#ffff66", ls="--", lw=0.8, label="RAWBRK ref (last PL)")
        # SL (ATR%) & TP(1x)
        slA=get_sl(entry,s["Ch"],s["atr14"],s["apct"],"ATR")
        if slA: 
            ax.axhline(slA, color="#ff4444", ls="-", lw=0.9, label="SL(ATR%)")
            ax.axhline(2*entry-slA, color="#44ff88", ls="-", lw=0.9, label="TP(1x)")
        ax.axhline(entry, color="#00ffff", ls="-", lw=0.9, label="ENTRY")
        # mark entry
        ax.axvline(eb, color="#00ffff", ls=":", lw=0.6)
        # bear_active shading (RAWBRK active)
        for i in range(a0+1,a1):
            if bear_active[i] and not bear_active[i-1]:
                ax.axvline(i, color="#ff00ff", ls=":", lw=0.7)
        ax.set_title(f"#{sel.index(s)+1} {df.index[eb].strftime('%Y-%m-%d')} entry={entry:.0f}", color="white", fontsize=9)
        ax.tick_params(colors="white", labelsize=7)
        ax.legend(loc="upper left", fontsize=6, ncol=2)
    fig.tight_layout(rect=[0,0,1,0.97])
    CHART=os.path.join(HERE,"rawbrk_visual_5trades.png")
    fig.savefig(CHART, dpi=110)
    print(f"\n[CHART] saved -> {CHART}")
except Exception as ex:
    print(f"\n[CHART] skipped: {ex}")
print("\nSELESAI")
