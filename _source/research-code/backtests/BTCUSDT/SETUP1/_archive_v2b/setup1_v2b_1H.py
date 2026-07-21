"""
setup1_v2b_1h.py — v2.b trigger: 2019-01-01 sampai sekarang, 1H TF.
SL: O1 Liq10x, O3 ATR% current TF, O6 ATR% 1D anchor.
Exit: TP1x, TP3x standalone, RAWBRK (TP3x+RB), ST_REV (TP3x+ST flip).
"""
import sys, os, time
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu")
import datetime as _dt, pandas as pd, numpy as np, requests

HERE = os.path.dirname(os.path.abspath(__file__))
SYM="BTCUSDT"; TF="1h"
START=pd.Timestamp("2019-01-01",tz="UTC")
END=pd.Timestamp.now("UTC").normalize()
IV_MS=3600000  # 1h

SMI_CFG={"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
         "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
         "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG={"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

# ── PHASE 0: Preload 1D data for O6 ──
import atr_percentage as atrp
BASE = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1"
df1d = pd.read_csv(f"{BASE}/1D/data_BTCUSDT_1d_2019now.csv", index_col=0, parse_dates=True)
print(f"[Phase 0] 1D: {len(df1d)} candles  {df1d.index[0].date()}..{df1d.index[-1].date()}")

daily_atr_pct = np.full(len(df1d), np.nan)
for i in range(30, len(df1d)):
    daily_atr_pct[i] = atrp.atr_percentage(df1d.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]

def get_daily_atr_pct(ts):
    for i in range(len(df1d)-1, -1, -1):
        if df1d.index[i] <= ts:
            val = daily_atr_pct[i]
            if np.isnan(val):
                for j in range(i+1, len(df1d)):
                    if not np.isnan(daily_atr_pct[j]):
                        return daily_atr_pct[j]
                return None
            return val
    return None

# ── PHASE 1: Load 1H data ──
CACHE=os.path.join(HERE,"data_BTCUSDT_1h_2019now.csv")
print(f"[Phase 1] loading BTCUSDT 1h 2019..now")
if os.path.exists(CACHE) and (time.time()-os.path.getmtime(CACHE))<86400:
    df=pd.read_csv(CACHE,index_col=0,parse_dates=True)
    print(f"    cache: {len(df)} candles {df.index[0]}..{df.index[-1]}")
else:
    # fetch fallback (shouldn't need since we just fetched)
    def fetch(sym,tf,start_ts,end_ts):
        url="https://api.binance.com/api/v3/klines"
        rows=[]; cur=int(start_ts.timestamp()*1000); end_ms=int(end_ts.timestamp()*1000)
        step=895*IV_MS
        while cur<end_ms:
            nxt=min(cur+step,end_ms)
            r=requests.get(url,params={"symbol":sym,"interval":tf,"startTime":cur,"endTime":nxt,"limit":1000},timeout=30).json()
            if r: rows.extend(r); cur=r[-1][0]+1
            else: cur=nxt
            time.sleep(0.2)
        df2=pd.DataFrame(rows,columns=["ot","o","h","l","c","v","ct","q","t","tb","tq","ig"])
        for c2 in ["o","h","l","c","v"]: df2[c2]=df2[c2].astype(float)
        df2["ot"]=pd.to_datetime(df2["ot"],unit="ms",utc=True)
        df2=df2.set_index("ot").sort_index()
        df2.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"},inplace=True)
        return df2[["open","high","low","close","volume"]]
    df=fetch(SYM,TF,START,END)
    df.to_csv(CACHE)
    print(f"    fetched: {len(df)} candles {df.index[0]}..{df.index[-1]}")

high=df["high"].values.astype(float)
low=df["low"].values.astype(float)
close=df["close"].values.astype(float)
n=len(df)

# ── PHASE 2: Compute indicators ──
print(f"[Phase 2] computing indicators...")

# ST(10,3)
def supertrend_full(period=10,mult=3.0):
    h=high;l=low;c=close
    hl2=(h+l)/2.0; tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n): tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
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
st_trend=supertrend_full(10,3.0)
print(f"    ST done")

# SMI
import smi_events as SM
E=SM.compute_smi_events(df,SMI_CFG)
FMB=E["FMB"]; PD=E["PD"]; XDN=E["XDN"]
print(f"    SMI done")

# FBF v11
import fbf_v11_backtest as V11
times=[int(t.value//1_000_000) for t in df.index]
eng=V11.FBFEngine(times,df["open"].values.astype(float),high,low,close,IV_MS)
breaks,events=eng.run()
ev_by_bar={}
for e in events: ev_by_bar.setdefault(e["bar"],[]).append(e)
print(f"    FBF v11 done: {len(events)} events, {len(breaks)} breaks")

# ATR% current TF helper
def atr_pct_at(i):
    return atrp.atr_percentage(df.iloc[:i+1],ATR_PCT_CFG)["atr_pct"]

# ── PHASE 3: v2.b trigger ──
samples=[]
pos_open=False; clear_bar=-1
fmb_b=None; pd_b=None; wave_entry_done=False
for i in range(n):
    if pos_open:
        if i>=clear_bar: pos_open=False; clear_bar=-1
        else: continue
    for e in ev_by_bar.get(i,[]):
        if e["side"]!="bear": continue
        if e["event"]=="WAVE_STARTED":
            wave_entry_done=False
            if pd_b is None: fmb_b=None
        elif e["event"] in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED",
                            "CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
            fmb_b=None; pd_b=None; wave_entry_done=False
    if not wave_entry_done:
        if FMB[i] and fmb_b is None: fmb_b=i
        if fmb_b is not None and pd_b is None and PD[i] and i>=fmb_b: pd_b=i
        if fmb_b is not None and pd_b is not None and XDN[i] and i>=pd_b:
            if st_trend[i]==-1:
                entry=close[i]
                apct_current=atr_pct_at(i)
                daily_apct=get_daily_atr_pct(df.index[i])
                samples.append(dict(
                    bar=i, entry=entry,
                    apct=apct_current,
                    daily_apct=daily_apct,
                    date=df.index[i]
                ))
                # clear_bar via TP1x O3
                sl0=entry*(1+apct_current/100.0)
                tp0=entry-(sl0-entry)
                fwd_h=high[i+1:]; fwd_l=low[i+1:]; ck=240
                for k in range(len(fwd_h)):
                    if fwd_l[k]<=tp0 or fwd_h[k]>=sl0 or k>=240: ck=k; break
                clear_bar=i+1+ck
                pos_open=True; wave_entry_done=True
            fmb_b=None; pd_b=None

print(f"\n[Phase 3] v2.b trigger: {len(samples)} sinyal")

# ── PHASE 4: BACKTEST ──
# Pivot lows for RAWBRK
def find_pivot_lows(arr,left=3,right=3):
    out=[]
    for ii in range(left,len(arr)-right):
        v=arr[ii]; ok=True
        for j in range(ii-left,ii):
            if arr[j]<=v: ok=False; break
        if ok:
            for j in range(ii+1,ii+right+1):
                if arr[j]<=v: ok=False; break
        if ok: out.append((v,ii))
    return out
pl_arr=find_pivot_lows(low,3,3)
pl_dict={bar:val for val,bar in pl_arr}

def sim_trade_rawbrk(entry, eb, sl, tp_mult):
    """TP=tp_mult*risk + RAWBRK exit."""
    risk=sl-entry
    tp=entry-tp_mult*risk
    fwd_h=high[eb+1:]; fwd_l=low[eb+1:]
    rb_sl=None; rb_bars=[]; rawbreak_price=None
    
    for k in range(len(fwd_h)):
        bi=eb+1+k
        if bi>=n: break
        # HIT check first (from PREVIOUS trigger)
        if rb_sl is not None and fwd_h[k]>=rb_sl:
            return dict(out="RAWBRK_HIT",ex=rb_sl,bars=k+1,R=(entry-rb_sl)/risk,
                       rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rawbreak_price=rb_sl)
        # TP check
        if fwd_l[k]<=tp:
            return dict(out="TP",ex=tp,bars=k+1,R=tp_mult,
                       rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rawbreak_price=None)
        # SL check
        if fwd_h[k]>=sl:
            return dict(out="SL",ex=sl,bars=k+1,R=-1.0,
                       rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rawbreak_price=None)
        # RAWBRK trigger
        cur_pl=None
        for bi2 in sorted(pl_dict.keys(),reverse=True):
            if bi2<=bi: cur_pl=pl_dict[bi2]; break
        if cur_pl is not None and close[bi]<cur_pl:
            if rb_sl is None: rb_sl=high[bi]
            else: rb_sl=max(rb_sl, high[bi])
            rb_bars.append((bi,high[bi]))
    
    lastc=fwd_l[-1] if len(fwd_l)>0 else entry
    return dict(out="EXP",ex=lastc,bars=len(fwd_h),R=(entry-lastc)/risk,
               rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rawbreak_price=None)

def sim_st_rev(entry, eb, sl):
    """TP3x patok + ST flip exit."""
    risk=sl-entry
    tp3=entry-3*risk
    fwd_h=high[eb+1:]; fwd_l=low[eb+1:]
    
    for k in range(len(fwd_h)):
        bi=eb+1+k
        if bi>=n: break
        if fwd_l[k]<=tp3:
            return dict(out="TP3x",ex=tp3,bars=k+1,R=3.0)
        if fwd_h[k]>=sl:
            return dict(out="SL",ex=sl,bars=k+1,R=-1.0)
        if st_trend[bi]==1:  # ST flipped UP
            return dict(out="ST_REV",ex=close[bi],bars=k+1,R=(entry-close[bi])/risk)
    
    lastc=fwd_l[-1] if len(fwd_l)>0 else entry
    return dict(out="EXP",ex=lastc,bars=len(fwd_h),R=(entry-lastc)/risk)

# SL options
def sl_o1(s): return s["entry"]*1.10
def sl_o3(s): return s["entry"]*(1+s["apct"]/100.0)
def sl_o6(s):
    da=s.get("daily_apct")
    if da is None or np.isnan(da) or da<=0: return None
    return s["entry"]*(1+da/100.0)

SL_OPTIONS=[
    ("O1 Liq10x", sl_o1),
    ("O3 ATR%curr", sl_o3),
    ("O6 ATR%1D", sl_o6),
]

# ── REPORT ──
import textwrap
UTC7=_dt.timezone(_dt.timedelta(hours=7))

def fmt_wib(ts):
    """Convert UTC timestamp to WIB (UTC+7) string."""
    if ts.tzinfo is None:
        ts=ts.tz_localize("UTC")
    wib=ts.tz_convert(UTC7)
    return wib.strftime("%d %b %Y %H:%M")

print(f"\n{'='*80}")
print(f"SETUP1 v2.b BACKTEST 1H — 2019-01-01 to {END.strftime('%Y-%m-%d')}")
print(f"{'='*80}")
print(f"Total sinyal: {len(samples)}")
print(f"Data: {len(df)} candles, {df.index[0]}..{df.index[-1]} UTC\n")

# Header
print(f"{'SL':>14} | {'TP1x':>12} | {'TP3x':>12} | {'RAWBRK':>12} | {'ST_REV':>12}")
print(f"{'':->14}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}")

# Aggregate for final summary
ALL_RESULTS=[]

for sl_name, sl_fn in SL_OPTIONS:
    # Filter valid
    valid=[]
    for s in samples:
        sl_val=sl_fn(s)
        if sl_val is not None and sl_val>s["entry"]:
            valid.append((s,sl_val))
    
    n_valid=len(valid)
    if n_valid==0:
        print(f"{sl_name:>14} | {'N/A':>12} | {'N/A':>12} | {'N/A':>12} | {'N/A':>12}")
        continue
    
    # TP1x + RAWBRK
    tp1x_res=[sim_trade_rawbrk(s["entry"],s["bar"],sl,1.0) for s,sl in valid]
    tp1x_tot=sum(r["R"] for r in tp1x_res)
    tp1x_tp=sum(1 for r in tp1x_res if r["out"]=="TP")
    tp1x_sl=sum(1 for r in tp1x_res if r["out"]=="SL")
    tp1x_rb=sum(1 for r in tp1x_res if r["out"]=="RAWBRK_HIT")
    tp1x_exp=sum(1 for r in tp1x_res if r["out"]=="EXP")
    
    # TP3x standalone (pure)
    tp3x_res=[]
    for s,sl in valid:
        risk=sl-s["entry"]
        tp3=s["entry"]-3*risk
        fwd_h=high[s["bar"]+1:]; fwd_l=low[s["bar"]+1:]
        found=False
        for k in range(len(fwd_h)):
            bi=s["bar"]+1+k
            if bi>=n: break
            if fwd_l[k]<=tp3:
                tp3x_res.append(dict(out="TP3x",R=3.0,bars=k+1))
                found=True; break
            if fwd_h[k]>=sl:
                tp3x_res.append(dict(out="SL",R=-1.0,bars=k+1))
                found=True; break
        if not found:
            lastc=fwd_l[-1] if len(fwd_l)>0 else s["entry"]
            tp3x_res.append(dict(out="EXP",R=(s["entry"]-lastc)/risk,bars=len(fwd_h)))
    tp3x_tot=sum(r["R"] for r in tp3x_res)
    tp3x_tp=sum(1 for r in tp3x_res if r["out"]=="TP3x")
    tp3x_sl=sum(1 for r in tp3x_res if r["out"]=="SL")
    tp3x_exp=sum(1 for r in tp3x_res if r["out"]=="EXP")
    
    # RAWBRK (TP3x + RAWBRK)
    rb_res=[sim_trade_rawbrk(s["entry"],s["bar"],sl,3.0) for s,sl in valid]
    rb_tot=sum(r["R"] for r in rb_res)
    rb_tp=sum(1 for r in rb_res if r["out"]=="TP")
    rb_sl=sum(1 for r in rb_res if r["out"]=="SL")
    rb_hit=sum(1 for r in rb_res if r["out"]=="RAWBRK_HIT")
    rb_exp=sum(1 for r in rb_res if r["out"]=="EXP")
    rb_hitR=sum(r["R"] for r in rb_res if r["out"]=="RAWBRK_HIT")
    
    # ST_REV (TP3x + ST flip)
    sr_res=[sim_st_rev(s["entry"],s["bar"],sl) for s,sl in valid]
    sr_tot=sum(r["R"] for r in sr_res)
    sr_tp=sum(1 for r in sr_res if r["out"]=="TP3x")
    sr_sl=sum(1 for r in sr_res if r["out"]=="SL")
    sr_rev=sum(1 for r in sr_res if r["out"]=="ST_REV")
    sr_exp=sum(1 for r in sr_res if r["out"]=="EXP")
    sr_revR=sum(r["R"] for r in sr_res if r["out"]=="ST_REV")
    
    print(f"{sl_name:>14} | {tp1x_tot:>+12.2f} | {tp3x_tot:>+12.2f} | {rb_tot:>+12.2f} | {sr_tot:>+12.2f}")
    
    # Store
    ALL_RESULTS.append(dict(
        sl=sl_name,
        tp1x=dict(tot=tp1x_tot,n=n_valid,tp=tp1x_tp,sl=tp1x_sl,rb=tp1x_rb,exp=tp1x_exp),
        tp3x=dict(tot=tp3x_tot,n=n_valid,tp=tp3x_tp,sl=tp3x_sl,exp=tp3x_exp),
        rawbrk=dict(tot=rb_tot,n=n_valid,tp=rb_tp,sl=rb_sl,rb=rb_hit,exp=rb_exp,rbR=rb_hitR),
        strev=dict(tot=sr_tot,n=n_valid,tp=sr_tp,sl=sr_sl,rev=sr_rev,exp=sr_exp,revR=sr_revR),
    ))

# ── BREAKDOWN TABLES ──
print(f"\n{'='*80}")
print(f"BREAKDOWN — Outcome x Count → Contribution")
print(f"{'='*80}")

for r in ALL_RESULTS:
    print(f"\n─── {r['sl']} ({r['tp1x']['n']} valid trades) ───")
    
    # TP1x
    d=r["tp1x"]
    wr_tp1x=(d["tp"]/(d["tp"]+d["sl"]+d["rb"])*100) if (d["tp"]+d["sl"]+d["rb"])>0 else 0
    print(f"  TP1x+RB:   TP {d['tp']:>4}×+{d['tp']*1:.1f} | SL {d['sl']:>4}×{d['sl']*-1:.1f} | RB_HIT {d['rb']:>4} | EXP {d['exp']:>4} → TotR {d['tot']:+.2f} WR {wr_tp1x:.1f}%")
    
    # TP3x standalone
    d3=r["tp3x"]
    wr_tp3x=(d3["tp"]/(d3["tp"]+d3["sl"])*100) if (d3["tp"]+d3["sl"])>0 else 0
    print(f"  TP3x pure: TP {d3['tp']:>4}×+{d3['tp']*3:.1f} | SL {d3['sl']:>4}×{d3['sl']*-1:.1f} | EXP {d3['exp']:>4} → TotR {d3['tot']:+.2f} WR {wr_tp3x:.1f}%")
    
    # RAWBRK
    d4=r["rawbrk"]
    wr_rb=(d4["tp"]/(d4["tp"]+d4["sl"]+d4["rb"])*100) if (d4["tp"]+d4["sl"]+d4["rb"])>0 else 0
    print(f"  RAWBRK:    TP {d4['tp']:>4}×+{d4['tp']*3:.1f} | SL {d4['sl']:>4}×{d4['sl']*-1:.1f} | RB_HIT {d4['rb']:>4}×{d4['rbR']:+.2f} | EXP {d4['exp']:>4} → TotR {d4['tot']:+.2f} WR {wr_rb:.1f}%")
    
    # ST_REV
    d5=r["strev"]
    wr_sr=(d5["tp"]/(d5["tp"]+d5["sl"]+d5["rev"])*100) if (d5["tp"]+d5["sl"]+d5["rev"])>0 else 0
    print(f"  ST_REV:    TP3x {d5['tp']:>3}×+{d5['tp']*3:.1f} | SL {d5['sl']:>4}×{d5['sl']*-1:.1f} | ST_REV {d5['rev']:>4}×{d5['revR']:+.2f} | EXP {d5['exp']:>4} → TotR {d5['tot']:+.2f} WR {wr_sr:.1f}%")

# ── CROSS-TF COMPARISON (1H vs 4H vs 2H from o6) ──
print(f"\n{'='*80}")
print(f"CROSS-TF: 1H vs 4H vs 2H (O6 ATR%1D)")
print(f"{'='*80}")

# Known results from o6 run (4H/2H)
KNOWN={
    "4H": {"O1":-8.67,"O3":-12.68,"O6":-17.03},
    "2H": {"O1":-12.97,"O3":-16.57,"O6":-24.68},
}
# 1H from our run
for r in ALL_RESULTS:
    sl_short=r["sl"].split()[0]
    if sl_short=="O1": KNOWN["1H"]={"O1":r["rawbrk"]["tot"]}
    if sl_short=="O3": KNOWN.setdefault("1H",{})["O3"]=r["rawbrk"]["tot"]
    if sl_short=="O6": KNOWN.setdefault("1H",{})["O6"]=r["rawbrk"]["tot"]

# ST_REV comparison
KNOWN_STREV={
    "4H": {"O1":+0.02,"O3":-6.29,"O6":-0.81},
    "2H": {"O1":+0.21,"O3":-13.38,"O6":-3.71},
}
for r in ALL_RESULTS:
    sl_short=r["sl"].split()[0]
    if sl_short=="O1": KNOWN_STREV.setdefault("1H",{})["O1"]=r["strev"]["tot"]
    if sl_short=="O3": KNOWN_STREV.setdefault("1H",{})["O3"]=r["strev"]["tot"]
    if sl_short=="O6": KNOWN_STREV.setdefault("1H",{})["O6"]=r["strev"]["tot"]

# Print RAWBRK comparison
print(f"\n--- TP3x+RAWBRK (SumR) ---")
print(f"{'TF':>4} {'O1 Liq10x':>12} {'O3 ATR%c':>12} {'O6 ATR%1D':>12}")
print(f"{'':->4} {'':->12} {'':->12} {'':->12}")
for tf in ["4H","2H","1H"]:
    v=KNOWN.get(tf,{})
    print(f"{tf:>4} {v.get('O1',0):>+12.2f} {v.get('O3',0):>+12.2f} {v.get('O6',0):>+12.2f}")

print(f"\n--- ST_REV (SumR) ---")
print(f"{'TF':>4} {'O1 Liq10x':>12} {'O3 ATR%c':>12} {'O6 ATR%1D':>12}")
print(f"{'':->4} {'':->12} {'':->12} {'':->12}")
for tf in ["4H","2H","1H"]:
    v=KNOWN_STREV.get(tf,{})
    print(f"{tf:>4} {v.get('O1',0):>+12.2f} {v.get('O3',0):>+12.2f} {v.get('O6',0):>+12.2f}")

# ── RECENT SIGNALS ──
print(f"\n{'='*80}")
print(f"5 SIGNAL TERAKHIR (WIB)")
print(f"{'='*80}")
for s in samples[-5:]:
    wib=fmt_wib(s["date"])
    print(f"  {wib} | entry={s['entry']:.2f} | apct={s['apct']:.2f}% | daily_apct={s.get('daily_apct','?'):.2f}%" if s.get('daily_apct') else f"  {wib} | entry={s['entry']:.2f} | apct={s['apct']:.2f}% | daily_apct=None")

print(f"\nSELESAI — {len(samples)} signals, {df.index[0]} to {df.index[-1]} UTC")
