"""study_windows.py — identifikasi event SMI (FMB/PD/XDN) + ST + FBF
di 4 window rujukan BTCUSDT daily, buat clarifikasi fase SMI step.
"""
import sys
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/fetchers")
sys.path.insert(0, "/home/ubuntu")
import pandas as pd, numpy as np
import smi_pro, fbf_v11_backtest as V11

df = pd.read_pickle("/tmp/df1d.pkl")
cfg = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
       "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
       "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
k=cfg["len_k"]; d=cfg["len_d"]; e=cfg["len_e"]; mid=cfg["mid"]
def ema2(s): return s.ewm(span=d, adjust=False).mean().ewm(span=d, adjust=False).mean()
hh=df["high"].rolling(k).max(); ll=df["low"].rolling(k).min()
rel=df["close"]-(hh+ll)/2; rng=(hh-ll).replace(0, np.nan)
S=200*(ema2(rel)/ema2(rng)); SE=S.ewm(span=e, adjust=False).mean()
# FMB: cross UP dari bawah mid
cmu=(S.shift(1)<mid)&(S>=mid)
below_run=(S<mid).astype(int)
def tr(s):
    o=np.zeros(len(s),dtype=int); run=0
    for i in range(len(s)):
        if s[i]==1: run+=1
        else: run=0
        o[i]=run
    return o
tb=tr(below_run.values); FMB=(cmu.values)&(tb<1)
# PD: 2 bar di atas mid + momentum turun
ab=(S>mid).astype(int); ta=tr(1-ab.values); SH=S-SE
PD=(ta==2)&(SH.values<np.concatenate([[0],SH.values[:-1]]))
# XDN: S cross DOWN ke SE
XDN=((S.shift(1)>SE.shift(1))&(S<=SE)).values
# ST
def st(df,p=10,m=3.0):
    h=df["high"].values; l=df["low"].values; cl=df["close"].values; hl2=(h+l)/2
    t2=np.zeros(len(cl)); t2[0]=h[0]-l[0]
    for i in range(1,len(cl)): t2[i]=max(h[i]-l[i],abs(h[i]-cl[i-1]),abs(l[i]-cl[i-1]))
    atr=np.zeros(len(cl)); atr[0]=t2[0]; a=1/p
    for i in range(1,len(cl)): atr[i]=atr[i-1]+a*(t2[i]-atr[i-1])
    up=hl2-m*atr; dn=hl2+m*atr; uf=np.zeros(len(cl)); df2=np.zeros(len(cl)); t=np.ones(len(cl),dtype=int)
    uf[0]=up[0]; df2[0]=dn[0]
    for i in range(1,len(cl)):
        uf[i]=max(up[i],uf[i-1]) if cl[i-1]>uf[i-1] else up[i]
        df2[i]=min(dn[i],df2[i-1]) if cl[i-1]<df2[i-1] else dn[i]
        t[i]=t[i-1]
        if t[i-1]==-1 and cl[i]>df2[i-1]: t[i]=1
        elif t[i-1]==1 and cl[i]<uf[i-1]: t[i]=-1
    return t
stt=st(df)
# FBF events
times=[int(t.value//1_000_000) for t in df.index]
eng=V11.FBFEngine(times, df["open"].values.astype(float), df["high"].values.astype(float),
                  df["low"].values.astype(float), df["close"].values.astype(float), 86400000)
br, eve = eng.run()

windows = [
    ("11 Jun - 19 Jun 2026", "2026-06-11", "2026-06-19"),
    ("08 Feb - 13 Feb 2026", "2026-02-08", "2026-02-13"),
    ("25 Nov - 02 Dec 2025", "2025-11-25", "2025-12-02"),
    ("12 Oct - 16 Oct 2025", "2025-10-12", "2025-10-16"),
]
# build per-bar FBF bear event string
ev_str={}
for ev in eve:
    if ev["side"]!="bear": continue
    s=ev["event"]
    if s=="WAVE_STARTED": s=f"WS(A{ev['a_val']:.0f},B{ev['b_val']:.0f})"
    elif s=="C_LOCKED": s=f"CL(C{ev['c_val']:.0f})"
    ev_str.setdefault(ev["bar"], []).append(s)

for name, a, b in windows:
    sub = df.loc[a:b]
    print(f"\n{'='*92}\nWINDOW: {name}   (UTC daily, WIB = +7j stay same date)\n{'='*92}")
    print(f"{'date':<12}{'close':>10}{'SMI':>8}{'SE':>8}{'hist':>7}  {'FMB':>3}{'PD':>3}{'XDN':>3}  {'ST':>4}  FBF")
    for bi in range(len(df)):
        if df.index[bi] < pd.Timestamp(a, tz="UTC") or df.index[bi] > pd.Timestamp(b, tz="UTC"):
            continue
        dt = df.index[bi]
        lbl = dt.strftime("%Y-%m-%d")
        close=df["close"].values[bi]; s=S.values[bi]; se=SE.values[bi]; h=s-se
        fmb="X" if FMB[bi] else ""; pdv="X" if PD[bi] else ""; xdn="X" if XDN[bi] else ""
        sts = "DN" if stt[bi]==-1 else "UP"
        evs = ",".join(ev_str.get(bi, []))
        print(f"{lbl:<12}{close:>10.1f}{s:>8.1f}{se:>8.1f}{h:>7.1f}  {fmb:>3}{pdv:>3}{xdn:>3}  {sts:>4}  {evs}")
