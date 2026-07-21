import sys
sys.path.insert(0,"/home/ubuntu/trading-research");sys.path.insert(0,"/home/ubuntu/trading-research/indicators")
sys.path.insert(0,"/home/ubuntu/trading-research/fetchers");sys.path.insert(0,"/home/ubuntu")
import pandas as pd,numpy as np
df=pd.read_pickle("/tmp/df1d.pkl")
cfg={"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,"akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,"div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
k=cfg["len_k"];d=cfg["len_d"];e=cfg["len_e"];mid=cfg["mid"]
hh=df["high"].rolling(k).max();ll=df["low"].rolling(k).min();rel=df["close"]-(hh+ll)/2;rng=(hh-ll).replace(0,np.nan)
ema2=lambda s:s.ewm(span=d,adjust=False).mean().ewm(span=d,adjust=False).mean()
S=200*(ema2(rel)/ema2(rng));SE=S.ewm(span=e,adjust=False).mean()
cmu=(S.shift(1)<mid)&(S>=mid);below_run=(S<mid).astype(int)
def tr(s):
    o=np.zeros(len(s),dtype=int);run=0
    for i in range(len(s)):
        if s[i]==1:run+=1
        else:run=0
        o[i]=run
    return o
tb=tr(below_run.values);FMB=(cmu.values)&(tb<1)
SH=S-SE
PD=(S.values>mid)&(SH.values<np.concatenate([[0],SH.values[:-1]]))&(SH.values<np.concatenate([[0,0],SH.values[:-2]]))
XDN=((S.shift(1)>SE.shift(1))&(S<=SE)).values
times=[int(t.value//1_000_000) for t in df.index]
import fbf_v11_backtest as V11
eng=V11.FBFEngine(times,df["open"].values.astype(float),df["high"].values.astype(float),df["low"].values.astype(float),df["close"].values.astype(float),86400000)
br,eve=eng.run();ev_by_bar={}
for ev in eve: ev_by_bar.setdefault(ev["bar"],[]).append(ev)
bvals=[(ev["bar"],ev["b_val"]) for ev in eve if ev["side"]=="bear" and ev["event"]=="WAVE_STARTED"]
def last_B(i):
    v=None
    for bar,val in bvals:
        if bar<=i: v=val
        else:break
    return v
def st(df,p=10,m=3.0):
    h=df["high"].values;l=df["low"].values;cl=df["close"].values;hl2=(h+l)/2
    t2=np.zeros(len(cl));t2[0]=h[0]-l[0]
    for i in range(1,len(cl)):t2[i]=max(h[i]-l[i],abs(h[i]-cl[i-1]),abs(l[i]-cl[i-1]))
    atr=np.zeros(len(cl));atr[0]=t2[0];a=1/p
    for i in range(1,len(cl)):atr[i]=atr[i-1]+a*(t2[i]-atr[i-1])
    up=hl2-m*atr;dn=hl2+m*atr;uf=np.zeros(len(cl));df2=np.zeros(len(cl));t=np.ones(len(cl),dtype=int)
    uf[0]=up[0];df2[0]=dn[0]
    for i in range(1,len(cl)):
        uf[i]=max(up[i],uf[i-1]) if cl[i-1]>uf[i-1] else up[i]
        df2[i]=min(dn[i],df2[i-1]) if cl[i-1]<df2[i-1] else dn[i]
        t[i]=t[i-1]
        if t[i-1]==-1 and cl[i]>df2[i-1]:t[i]=1
        elif t[i-1]==1 and cl[i]<uf[i-1]:t[i]=-1
    return t
stt=st(df);close=df["close"].values;n=len(df)
windows=[("11-19Jun2026","2026-06-11","2026-06-19"),("08-13Feb2026","2026-02-08","2026-02-13"),
("25Nov-02Dec2025","2025-11-25","2025-12-02"),("12-16Oct2025","2025-10-12","2025-10-16")]
for nm,a,b in windows:
    print(f"\n== {nm} ==")
    for bi in range(n):
        if df.index[bi]<pd.Timestamp(a,tz="UTC") or df.index[bi]>pd.Timestamp(b,tz="UTC"):continue
        fmb="F" if FMB[bi] else "."
        pdv="P" if PD[bi] else "."
        xdn="X" if XDN[bi] else "."
        print(f"  {df.index[bi].strftime('%m-%d')} c={close[bi]:.0f} S={S.values[bi]:5.1f} h={SH.values[bi]:5.1f} {fmb}{pdv}{xdn} ST={'DN' if stt[bi]==-1 else 'UP'}")
fmb=None;pd=None;cnt=0;sigs=[]
for i in range(n):
    for ev in ev_by_bar.get(i,[]):
        if ev["side"]!="bear":continue
        if ev["event"]=="WAVE_STARTED" and pd is None: fmb=None;pd=None
    if FMB[i] and fmb is None:fmb=i
    if fmb is not None and pd is None and PD[i] and i>=fmb:pd=i
    if fmb is not None and pd is not None and XDN[i] and i>=pd:
        if stt[i]==-1:
            cnt+=1;sigs.append(i)
        fmb=None;pd=None
print(f"\nNEW-PD count (reset WS kalau pd blm set, ST-down): {cnt}")
dates=[df.index[b].strftime('%Y-%m-%d') for b in sigs]
print("4 window capture:", [t for t in ['2026-06-17','2026-02-12','2025-11-30','2025-10-15'] if t in dates])
