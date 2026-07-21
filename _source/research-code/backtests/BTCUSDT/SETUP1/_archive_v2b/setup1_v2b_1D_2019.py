"""setup1_v2b_2023.py — v2.b trigger test: 2019-01-01 sampai sekarang.
SL: ATR%, Liq10x, C+ATR. TP: 1x. RAWBRK tracked.
"""
import sys, os, time
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
sys.path.insert(0, "/home/ubuntu")
import datetime as _dt, pandas as pd, numpy as np, requests

HERE = os.path.dirname(os.path.abspath(__file__))
SYM="BTCUSDT"; TF="1d"
START=pd.Timestamp("2019-01-01",tz="UTC")
END=pd.Timestamp.now("UTC").normalize()
WIB=7; IV_MS=86400000

SMI_CFG={"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
         "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
         "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG={"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

# fetch
CACHE2019=os.path.join(HERE,"data_BTCUSDT_1d_2019now.csv")
def fetch(sym,tf,start_ts,end_ts):
    url="https://api.binance.com/api/v3/klines"
    rows=[]; cur=int(start_ts.timestamp()*1000); end_ms=int(end_ts.timestamp()*1000)
    step=895*86400000
    while cur<end_ms:
        nxt=min(cur+step,end_ms)
        r=requests.get(url,params={"symbol":sym,"interval":tf,"startTime":cur,"endTime":nxt,"limit":1000},timeout=30).json()
        if r: rows.extend(r); cur=r[-1][0]+1
        else: cur=nxt
        time.sleep(0.2)
    df=pd.DataFrame(rows,columns=["ot","o","h","l","c","v","ct","q","t","tb","tq","ig"])
    for c2 in ["o","h","l","c","v"]: df[c2]=df[c2].astype(float)
    df["ot"]=pd.to_datetime(df["ot"],unit="ms",utc=True)
    df=df.set_index("ot").sort_index()
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"},inplace=True)
    return df[["open","high","low","close","volume"]]

print(f"[*] loading BTCUSDT 1d 2019..now")
if os.path.exists(CACHE2019) and (time.time()-os.path.getmtime(CACHE2019))<86400:
    df=pd.read_csv(CACHE2019,index_col=0,parse_dates=True)
    print(f"    cache: {len(df)} candles {df.index[0].date()}..{df.index[-1].date()}")
else:
    df=fetch(SYM,TF,START,END)
    df.to_csv(CACHE2019)
    print(f"    fetched: {len(df)} candles {df.index[0].date()}..{df.index[-1].date()}")

high=df["high"].values.astype(float)
low=df["low"].values.astype(float)
close=df["close"].values.astype(float)
n=len(df)

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

# SMI
import smi_events as SM
E=SM.compute_smi_events(df,SMI_CFG)
FMB=E["FMB"]; PD=E["PD"]; XDN=E["XDN"]
smi=E["smi"]; smi_hist=E["smi_hist"]; hist_state=E["hist_state"]

# FBF v11
import fbf_v11_backtest as V11
times=[int(t.value//1_000_000) for t in df.index]
eng=V11.FBFEngine(times,df["open"].values.astype(float),high,low,close,IV_MS)
breaks,events=eng.run()
ev_by_bar={}
for e in events: ev_by_bar.setdefault(e["bar"],[]).append(e)

# ATR helper
def atr14_at(i):
    sub=df.iloc[max(0,i-13):i+1]
    tr=pd.concat([sub["high"]-sub["low"],(sub["high"]-sub["close"].shift(1)).abs(),
                  (sub["low"]-sub["close"].shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1]

import atr_percentage as atrp
def atr_pct_at(i): return atrp.atr_percentage(df.iloc[:i+1],ATR_PCT_CFG)["atr_pct"]

# v2.b trigger
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
                entry=close[i]; atr14=atr14_at(i); apct=atr_pct_at(i)
                samples.append(dict(bar=i,entry=entry,atr14=atr14,apct=apct,
                                    fmb_b=fmb_b,pd_b=pd_b,xdn_b=i))
                sl0=entry*(1+apct/100.0); tp0=entry-(sl0-entry)
                fwd_h=high[i+1:]; fwd_l=low[i+1:]; ck=240
                for k in range(len(fwd_h)):
                    if fwd_l[k]<=tp0 or fwd_h[k]>=sl0 or k>=240: ck=k; break
                clear_bar=i+1+ck
                pos_open=True; wave_entry_done=True
            fmb_b=None; pd_b=None

# RAWBRK (NEW LOGIC: close < lastPivotLow, SL=HIGH candle rawbreak)
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

def sim_trade(s, sl):
    """Simulate: entry -> exit with given SL, TP=3x, RAWBRK as exit mech."""
    entry=s["entry"]; eb=s["bar"]
    risk=sl-entry
    tp=entry-3*risk          # TP=3x risk
    fwd_h=high[eb+1:]; fwd_l=low[eb+1:]
    rb_sl=None; rb_bars=[]; rb_trig_bar=None
    
    for k in range(len(fwd_h)):
        bi=eb+1+k
        if bi>=n: break
        # TP / SL check
        if fwd_l[k]<=tp:
            return dict(out="TP",ex=tp,bars=k+1,R=3.0,rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rb_trig_bar=rb_trig_bar)
        if fwd_h[k]>=sl:
            return dict(out="SL",ex=sl,bars=k+1,R=-1.0,rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rb_trig_bar=rb_trig_bar)
        # RAWBRK check (NEW LOGIC)
        cur_pl=find_last_pl(bi)
        if cur_pl is not None and close[bi] < cur_pl:
            if rb_sl is None: rb_trig_bar=bi; rb_sl=high[bi]
            else: rb_sl=max(rb_sl, high[bi])  # update SL ke HIGH tertinggi
            rb_bars.append((bi,high[bi]))
        # If rawbreak active, check if price hits rb_sl
        if rb_sl is not None and fwd_h[k] >= rb_sl:
            ex=rb_sl
            return dict(out="RAWBRK_HIT",ex=ex,bars=k+1,R=(entry-ex)/risk,rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rb_trig_bar=rb_trig_bar)
    
    lastc=fwd_l[-1] if len(fwd_l)>0 else entry
    return dict(out="EXP",ex=lastc,bars=len(fwd_h),R=(entry-lastc)/risk,rawbreak_bars=rb_bars,rawbreak_sl=rb_sl,rb_trig_bar=rb_trig_bar)

def find_last_pl(bar):
    for bi in sorted(pl_dict.keys(),reverse=True):
        if bi<=bar: return pl_dict[bi]
    return None

# ── RUN BACKTEST ──
print(f"\n{'='*80}")
print(f"SETUP1 v2.b BACKTEST — 2019-01-01 to {END.strftime('%Y-%m-%d')}")
print(f"SL: ATR% / Liq10x   |   TP: 1x & 3x+RAWBRK")
print(f"{'='*80}")
print(f"Total sinyal: {len(samples)}")

# TP=1x + RAWBRK simulator
def sim_tp1x_rawbrk(s,sl):
    entry=s["entry"]; eb=s["bar"]
    risk=sl-entry; tp=entry-1*risk
    fwd_h=high[eb+1:]; fwd_l=low[eb+1:]
    rb_sl=None; rb_bars=[]
    for k in range(len(fwd_h)):
        bi=eb+1+k
        if bi>=n: break
        if fwd_l[k]<=tp:
            return dict(out="TP",ex=tp,bars=k+1,R=1.0)
        if fwd_h[k]>=sl:
            return dict(out="SL",ex=sl,bars=k+1,R=-1.0)
        cur_pl=find_last_pl(bi)
        if cur_pl is not None and close[bi] < cur_pl:
            if rb_sl is None: rb_sl=high[bi]
            else: rb_sl=max(rb_sl, high[bi])
            rb_bars.append((bi,high[bi]))
        if rb_sl is not None and fwd_h[k] >= rb_sl:
            return dict(out="RAWBRK_HIT",ex=rb_sl,bars=k+1,R=(entry-rb_sl)/risk)
    lastc=fwd_l[-1] if len(fwd_l)>0 else entry
    return dict(out="EXP",ex=lastc,bars=len(fwd_h),R=(entry-lastc)/risk)

# Per SL type
for sl_name, sl_fn in [
    ("ATR%", lambda s: s["entry"]*(1+s["apct"]/100.0)),
    ("Liq10x", lambda s: s["entry"]*1.10),
]:
    # TP=1x + RAWBRK
    r1x=[sim_tp1x_rawbrk(s,sl_fn(s)) for s in samples if sl_fn(s) is not None and sl_fn(s)>s["entry"]]
    t1_tp=sum(1 for r in r1x if r["out"]=="TP")
    t1_sl=sum(1 for r in r1x if r["out"]=="SL")
    t1_rb=sum(1 for r in r1x if r["out"]=="RAWBRK_HIT")
    t1_exp=sum(1 for r in r1x if r["out"]=="EXP")
    t1_tot=sum(r["R"] for r in r1x)
    t1_wr=(t1_tp/(t1_tp+t1_sl+t1_rb)*100) if (t1_tp+t1_sl+t1_rb)>0 else 0
    
    # TP=3x + RAWBRK
    results=[]
    for s in samples:
        sl=sl_fn(s)
        if sl is None or sl <= s["entry"]: continue
        r=sim_trade(s,sl)
        results.append(r)
    
    tp_count=sum(1 for r in results if r["out"]=="TP")
    sl_count=sum(1 for r in results if r["out"]=="SL")
    rb_count=sum(1 for r in results if r["out"]=="RAWBRK_HIT")
    exp_count=sum(1 for r in results if r["out"]=="EXP")
    totR=sum(r["R"] for r in results)
    wr=(tp_count/(tp_count+sl_count+rb_count)*100) if (tp_count+sl_count+rb_count)>0 else 0
    rb_hitR=sum(r["R"] for r in results if r["out"]=="RAWBRK_HIT")
    
    print(f"\n{sl_name}: {len(results)} trades tested")
    print(f"  TP=1x+RB: TP:{t1_tp:>3} SL:{t1_sl:>3} RB:{t1_rb:>3} EXP:{t1_exp:>3} | TotR: {t1_tot:+.2f} WR: {t1_wr:.1f}%")
    print(f"  TP=3x:  TP:{tp_count:>3}  SL:{sl_count:>3}  RB:{rb_count:>3}  EXP:{exp_count:>3}  |  TotR: {totR:+.2f}  WR: {wr:.1f}%  RB_R: {rb_hitR:+.2f}")
    
    # Per-trade detail
    print(f"  {'date':>12} {'entry':>10} {'SL':>10} {'TP(3x)':>10} {'outcome':>12} {'exit$':>10} {'R':>7} rawbreak")
    for idx,(s,r) in enumerate(zip(samples,results)):
        risk=sl_fn(s)-s["entry"]
        tp3=s["entry"]-3*risk
        rb_info=""
        if r["rawbreak_bars"]:
            nrb=len(r["rawbreak_bars"])
            rb_sl_final=r["rawbreak_sl"]
            rb_info=f"RAW@{nrb}b sl={rb_sl_final:.0f}"
        if r["out"]=="TP":
            print(f"  {df.index[s['bar']].strftime('%Y-%m-%d'):>12} {s['entry']:>10.2f} {sl_fn(s):>10.2f} {tp3:>10.2f} {r['out']:>12} {r['ex']:>10.2f} {r['R']:+7.2f} {rb_info}")
        elif r["out"]=="SL":
            print(f"  {df.index[s['bar']].strftime('%Y-%m-%d'):>12} {s['entry']:>10.2f} {sl_fn(s):>10.2f} {tp3:>10.2f} {r['out']:>12} {r['ex']:>10.2f} {r['R']:+7.2f}")
        elif r["out"]=="RAWBRK_HIT":
            print(f"  {df.index[s['bar']].strftime('%Y-%m-%d'):>12} {s['entry']:>10.2f} {sl_fn(s):>10.2f} {tp3:>10.2f} {r['out']:>12} {r['ex']:>10.2f} {r['R']:+7.2f} {rb_info}")

print(f"\nSELESAI — {len(samples)} signals, {df.index[0].date()} to {df.index[-1].date()}")
