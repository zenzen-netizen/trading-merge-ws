"""Extract 3 recent trade samples with full event detail."""
import sys, os
sys.path.insert(0, '/home/ubuntu/trading-research')
sys.path.insert(0, '/home/ubuntu/trading-research/indicators')
sys.path.insert(0, '/home/ubuntu')
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'data_BTCUSDT_1d_2021now.csv')
IV_MS = 86400000
SMI_CFG = {'len_k':5,'len_d':3,'len_e':3,'ob':80,'mid':0,'os':-40,
           'akum_candles':2,'dist_candles':2,'div_enabled':True,'div_hidden':False,
           'div_left':5,'div_right':5,'div_range_min':5,'div_range_max':60}

df = pd.read_csv(CACHE, index_col=0, parse_dates=True)
high=df['high'].values.astype(float); low=df['low'].values.astype(float); close=df['close'].values.astype(float)
n=len(df)

# ST
def st_full(period=10, mult=3.0):
    h,l,c=high,low,close; hl2=(h+l)/2.0
    tr=np.zeros(n); tr[0]=h[0]-l[0]
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
st = st_full()

import smi_events as SM
E = SM.compute_smi_events(df, SMI_CFG)
FMB,PD,XDN = E['FMB'],E['PD'],E['XDN']
smi_val,smi_hist,hs = E['smi'],E['smi_hist'],E['hist_state']

import fbf_v11_backtest as V11
times=[int(t.value//1_000_000) for t in df.index]
eng = V11.FBFEngine(times, df['open'].values.astype(float), high, low, close, IV_MS)
_, events = eng.run()
ev_by={}
for e in events: ev_by.setdefault(e['bar'],[]).append(e)

import atr_percentage as atrp
def apct_at(i): return atrp.atr_percentage(df.iloc[:i+1],{'atr_period':30,'use_atr_pct':True,'show_bb':True,'bb_period':20,'bb_stddev':2.0})['atr_pct']
def atr14_at(i):
    sub=df.iloc[max(0,i-13):i+1]
    tr=pd.concat([sub['high']-sub['low'],(sub['high']-sub['close'].shift(1)).abs(),(sub['low']-sub['close'].shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1]

samples=[]; pos_open=False; clear_bar=-1
wA=wB=wc=ws=None; fb=pb=None; wed=False
for i in range(n):
    if pos_open:
        if i>=clear_bar: pos_open=False; clear_bar=-1
        else: continue
    for e in ev_by.get(i,[]):
        if e['side']!='bear': continue
        if e['event']=='WAVE_STARTED':
            wA=(e['a_bar'],e['a_val']); wB=(e['b_bar'],e['b_val']); ws=e['bar']; wed=False
            if pb is None: fb=None; wc=None
        elif e['event']=='C_LOCKED': wc=(e['c_bar'],e['c_val'],e.get('retrace_pct'))
        elif e['event'] in ('WAVE_CANCELLED','WAVE_STRUCT_REJECTED','CANDIDATE_INVALIDATED','CANDIDATE_EVICTED'):
            fb=None; pb=None
    if not wed:
        if FMB[i] and fb is None: fb=i
        if fb is not None and pb is None and PD[i] and i>=fb: pb=i
        if fb is not None and pb is not None and XDN[i] and i>=pb:
            if st[i]==-1:
                entry=close[i]; a14=atr14_at(i); ap=apct_at(i)
                Ch=high[wc[0]] if wc else np.nan
                samples.append(dict(bar=i,entry=entry,A=wA,B=wB,C=wc,fb=fb,pb=pb,xb=i,st=st[i],atr14=a14,apct=ap,Ch=Ch))
                sl0=entry*(1+ap/100.); tp0=entry-(sl0-entry)
                fh=high[i+1:]; fl=low[i+1:]
                for k in range(len(fh)):
                    if fl[k]<=tp0 or fh[k]>=sl0 or k>=240: ck=k; break
                clear_bar=i+1+ck; pos_open=True; wed=True
            fb=None; pb=None

# -- OUTPUT 3 most recent --
sel = samples[-3:]
for idx,s in enumerate(sel,1):
    eb=s['bar']; entry=s['entry']; A=s['A']; B=s['B']; C=s['C']
    fb=s['fb']; pb=s['pb']; xb=s['xb']
    print(f"\n{'='*80}")
    print(f"TRADE #{idx}  ENTRY: {df.index[eb].strftime('%Y-%m-%d')}  PRICE: {entry:.2f}  ATR%: {s['apct']:.2f}%")
    print(f"{'='*80}")
    
    print(f"\n[FBF v11 WAVE EVENTS bar {A[0]}->{eb}]")
    print(f"  WAVE_STARTED: A={A[1]:.2f}@{df.index[A[0]].strftime('%Y-%m-%d')}  B={B[1]:.2f}@{df.index[B[0]].strftime('%Y-%m-%d')}")
    for bi in range(A[0],eb+1):
        for e in ev_by.get(bi,[]):
            if e['side']!='bear': continue
            cv=e.get('c_val'); cs=f" C={cv:.0f}" if cv else ''
            rp=e.get('retrace_pct'); rs=f" ret={rp:.1f}%" if rp else ''
            tag=''
            if bi==fb: tag=' <=FMB'
            if bi==pb: tag=' <=PD'
            if bi==xb: tag=' <=XDN ENTRY!'
            print(f"  bar{bi:>5} {df.index[bi].strftime('%Y-%m-%d')} {e['event']:28s}{cs}{rs}{tag}")
    
    print(f"\n[SMI 3-STEP]")
    print(f"  FMB bar{fb} {df.index[fb].strftime('%Y-%m-%d')} smi={smi_val[fb]:.1f} hist={smi_hist[fb]:.1f} [{hs[fb]}] ST={'DN' if st[fb]==-1 else 'UP'}")
    print(f"  PD  bar{pb} {df.index[pb].strftime('%Y-%m-%d')} smi={smi_val[pb]:.1f} hist={smi_hist[pb]:.1f} [{hs[pb]}] ST={'DN' if st[pb]==-1 else 'UP'}")
    print(f"  XDN bar{xb} {df.index[xb].strftime('%Y-%m-%d')} smi={smi_val[xb]:.1f} hist={smi_hist[xb]:.1f} [{hs[xb]}] ST={'DN' if st[xb]==-1 else 'UP'} <=ENTRY")
    
    if C: print(f"\n[C] C={C[1]:.2f}@{df.index[C[0]].strftime('%Y-%m-%d')} retrace={C[2]:.1f}% (no-wait-C: OK)")
    else: print(f"\n[C] BELUM LOCKED (no-wait-C: OK)")
    
    print(f"\n[SL/TP LEVELS]")
    for name, sl in [('O1 Liq10x',entry*1.10),('O3 ATR%30',entry*(1+s['apct']/100.)),('O4 Fix6%',entry*1.06)]:
        print(f"  {name:12s} SL={sl:.2f}  TP1x={entry-(sl-entry):.2f}  TP3x={entry-3*(sl-entry):.2f}")
    if not np.isnan(s['Ch']):
        sl2=s['Ch']+s['atr14']; print(f"  O2 C+ATR14   SL={sl2:.2f}  TP1x={entry-(sl2-entry):.2f}  TP3x={entry-3*(sl2-entry):.2f}")
    else: print(f"  O2 C+ATR14   N/A (C belum lock)")
    
    print(f"\n[PRICE +/-3]")
    print(f"  {'date':>12} {'open':>10} {'high':>10} {'low':>10} {'close':>10} ST  FMB PD XDN")
    for i in range(max(0,eb-3),min(n,eb+4)):
        d=df.index[i].strftime('%Y-%m-%d'); o=df['open'].iloc[i]; h=high[i]; l=low[i]; c=close[i]
        sd='DN' if st[i]==-1 else 'UP'
        f='FMB' if FMB[i] else '   '; p='PD' if PD[i] else '  '; x='XDN' if XDN[i] else '   '
        m=' <=E' if i==eb else ''
        print(f"  {d:>12} {o:>10.2f} {h:>10.2f} {l:>10.2f} {c:>10.2f} {sd}  {f} {p} {x}{m}")

print(f"\n{'='*80}")
print(f"DONE. 3 samples ready.")
