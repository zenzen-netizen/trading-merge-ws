"""
live_trigger_state.py
=====================
Probe state LIVE terakhir SETUP1 SHORT v2.b (Variant E / RESET-ONLY).
Re-run engine modules + trigger loop SAMA persis setup1_v2b_clean.py,
tapi rekam state di bar TERAKHIR:
  - ada wave bear aktif? (wave_started tapi belum entry)
  - SMI 3-step progression: fmb_b / pd_b / xdn sudah sampai mana
  - ST(10,3) trend di bar terakhir
  - bear_active (RAWBRK) di bar terakhir + last pivot-low + jarak ke break
  - 5 sinyal terakhir (tanggal entry)
Gak bikin chart, gak butuh fbf_v610 utk RAWBRK precompute (pivot low
dihitung inline).
"""
import sys, os, time
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/archive/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
sys.path.insert(0, "/home/ubuntu")
import datetime as _dt
import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data_BTCUSDT_1d_2021now.csv")
SYM, TF = "BTCUSDT", "1d"
START = pd.Timestamp("2021-01-01", tz="UTC")
END = pd.Timestamp.now("UTC").normalize()
WIB = 7
IV_MS = 86400000

SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

df = pd.read_csv(CACHE, index_col=0, parse_dates=True)
high = df["high"].values.astype(float)
low  = df["low"].values.astype(float)
close= df["close"].values.astype(float)
n = len(df)
print(f"[*] data: {n} candles {df.index[0].date()} .. {df.index[-1].date()}")

# --- Supertrend(10,3) ---
def supertrend_full(period=10, mult=3.0):
    h,l,c = high,low,close
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
st_trend = supertrend_full(10,3.0)

# --- SMI Pro v3 ---
import smi_events as SM
E = SM.compute_smi_events(df, SMI_CFG)
FMB, PD, XDN = E["FMB"], E["PD"], E["XDN"]
smi, smi_hist, hist_state = E["smi"], E["smi_hist"], E["hist_state"]

# --- FBF v11 ---
import fbf_v11_backtest as V11
times=[int(t.value//1_000_000) for t in df.index]
eng = V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, IV_MS)
breaks, events = eng.run()
ev_by_bar={}
for e in events:
    ev_by_bar.setdefault(e["bar"], []).append(e)
nbear = len([e for e in events if e.get("side")=="bear"])
print(f"[FBF v11] {nbear} bear events")

# --- ATR helpers ---
import atr_percentage as atrp
def atr_pct_at(i): return atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]
def atr14_at(i):
    sub=df.iloc[max(0,i-13):i+1]
    tr=pd.concat([sub["high"]-sub["low"],(sub["high"]-sub["close"].shift(1)).abs(),
                  (sub["low"]-sub["close"].shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1]

# --- pivot lows (inline, sama dgn fbf_v610.find_pivots left=3,right=3) ---
import fbf_v610 as fbfmod
ph_arr, pl_arr = fbfmod.find_pivots(high, low, 3, 3)
pl_by_idx = dict(pl_arr)
running_last_pl = np.full(n, np.nan)
for i in range(n):
    if i in pl_by_idx: running_last_pl[i]=pl_by_idx[i]

# --- bear_active (RAWBRK ref) ---
tr=np.zeros(n); tr[0]=high[0]-low[0]
for i in range(1,n): tr[i]=max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1]))
atr_arr=np.zeros(n); atr_arr[0]=tr[0]; alpha=1.0/14
for i in range(1,n): atr_arr[i]=atr_arr[i-1]+alpha*(tr[i]-atr_arr[i-1])
bear_active=np.zeros(n,dtype=bool)
_active=False; _ref_val=np.nan
for i in range(n):
    rpl=running_last_pl[i]
    raw_bear = (not np.isnan(rpl)) and (close[i]<rpl)
    if not _active and raw_bear:
        if (rpl-close[i])>=0.15*atr_arr[i]:
            _active=True; _ref_val=rpl
    elif _active:
        if close[i]<_ref_val and (rpl-close[i])>=0.15*atr_arr[i]:
            pass
        else: _active=False
    bear_active[i]=_active

# ============================================================
# TRIGGER LOOP v2.b + LIVE STATE RECORDER
# ============================================================
samples=[]
pos_open=False; clear_bar=-1
wave_A=None; wave_B=None; wave_c=None; wave_started_bar=None
fmb_b=None; pd_b=None; wave_entry_done=False
# recorder state terakhir
last = dict(bar=n-1, wave_started=False, wave_A=None, wave_B=None, wave_c=None,
            fmb_b=None, pd_b=None, wave_entry_done=False, pos_open=False,
            smi_step="IDLE", st=-1, bear_active=False)

for i in range(n):
    if pos_open:
        if i >= clear_bar: pos_open=False; clear_bar=-1
        else:
            # tetep rekam state posisi terbuka
            last.update(wave_started=True, wave_A=wave_A, wave_B=wave_B,
                        wave_c=wave_c, fmb_b=fmb_b, pd_b=pd_b,
                        wave_entry_done=wave_entry_done, pos_open=True,
                        smi_step=("FMB" if fmb_b is not None else "IDLE")+
                                  ("+PD" if pd_b is not None else "")+
                                  (">XDN" if (fmb_b is not None and pd_b is not None) else ""),
                        st=st_trend[i], bear_active=bear_active[i])
            continue
    for e in ev_by_bar.get(i, []):
        if e["side"]!="bear": continue
        if e["event"]=="WAVE_STARTED":
            wave_A=(e["a_bar"], e["a_val"]); wave_B=(e["b_bar"], e["b_val"])
            wave_started_bar=e["bar"]; wave_entry_done=False
            if pd_b is None: fmb_b=None; wave_c=None
        elif e["event"]=="C_LOCKED":
            wave_c=(e["c_bar"], e["c_val"], e.get("retrace_pct"))
        elif e["event"] in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED",
                            "CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
            fmb_b=None; pd_b=None
    if not wave_entry_done:
        if FMB[i] and fmb_b is None: fmb_b=i
        if fmb_b is not None and pd_b is None and PD[i] and i>=fmb_b: pd_b=i
        if fmb_b is not None and pd_b is not None and XDN[i] and i>=pd_b:
            if st_trend[i]==-1:
                entry=close[i]
                atr14=atr14_at(i); apct=atr_pct_at(i)
                Ch = high[wave_c[0]] if wave_c else np.nan
                samples.append(dict(bar=i, entry=entry, A=wave_A, B=wave_B, C=wave_c,
                                    fmb_b=fmb_b, pd_b=pd_b, xdn_b=i,
                                    st=st_trend[i], atr14=atr14, apct=apct, Ch=Ch))
                sl0=entry*(1+apct/100.0); tp0=entry-(sl0-entry)
                fwd_h=high[i+1:]; fwd_l=low[i+1:]; ck=240
                for k in range(len(fwd_h)):
                    if fwd_l[k]<=tp0 or fwd_h[k]>=sl0 or k>=240: ck=k; break
                clear_bar=i+1+ck
                pos_open=True; wave_entry_done=True
            fmb_b=None; pd_b=None
    # rekam state bar ini (SETELAH update)
    if not pos_open:
        step = "IDLE"
        if wave_A is not None:
            step = "WAVE_ONLY"
            if fmb_b is not None: step="FMB.."
            if pd_b is not None: step="FMB+PD.."
            if fmb_b is not None and pd_b is not None: step="FMB+PD>XDN_WAIT"
        last.update(wave_started=(wave_A is not None),
                    wave_A=wave_A, wave_B=wave_B, wave_c=wave_c,
                    fmb_b=fmb_b, pd_b=pd_b, wave_entry_done=wave_entry_done,
                    pos_open=False, smi_step=step, st=st_trend[i],
                    bear_active=bear_active[i])

print(f"\n{'='*70}")
print(f"SETUP1 SHORT v2.b — LIVE STATE @ {df.index[-1].strftime('%Y-%m-%d')} (bar {n-1})")
print(f"{'='*70}")
print(f"  Close terakhir       : {close[-1]:,.2f}")
print(f"  ST(10,3) trend       : {'DOWN (-1)' if st_trend[-1]==-1 else 'UP (+1)'}")
print(f"  bear_active (RAWBRK) : {bear_active[-1]}")
# last pivot low
lp=None; lpb=None
for bi in sorted(pl_by_idx.keys()):
    if bi<=n-1: lp=pl_by_idx[bi]; lpb=bi
    else: break
if lp is not None:
    gap=(close[-1]-lp)/close[-1]*100
    print(f"  Last pivot-low (FBF): {lp:,.2f} @ {df.index[lpb].strftime('%Y-%m-%d')}  (entry di atas {gap:.2f}%)")
    need=0.15*atr14_at(n-1)
    print(f"  Jarak tembus break   : butuh close < {lp:,.2f} (PL - {need:,.2f}$)  -> {'(SUDAH TEMBUS)' if close[-1]<lp else 'belum'}")
print(f"  {'-'*70}")
print(f"  WAVE AKTIF?          : {last['wave_started']}")
if last['wave_started'] and last['wave_A']:
    A=last['wave_A']; B=last['wave_B']; C=last['wave_c']
    print(f"    WAVE_STARTED A={A[1]:,.2f}@{df.index[A[0]].strftime('%Y-%m-%d')}  B={B[1]:,.2f}@{df.index[B[0]].strftime('%Y-%m-%d')}")
    if C: print(f"    C_LOCKED     C={C[1]:,.2f}@{df.index[C[0]].strftime('%Y-%m-%d')} retrace={C[2]:.1f}%")
    else: print(f"    C_LOCKED     : BELUM (no-wait C -> entry valid tanpa C)")
    print(f"  SMI 3-STEP state     : {last['smi_step']}")
    if last['fmb_b'] is not None:
        print(f"    FMB @ {df.index[last['fmb_b']].strftime('%Y-%m-%d')} SMI={smi[last['fmb_b']]:.1f} [{hist_state[last['fmb_b']]}] ST={'DN' if st_trend[last['fmb_b']]==-1 else 'UP'}")
    if last['pd_b'] is not None:
        print(f"    PD  @ {df.index[last['pd_b']].strftime('%Y-%m-%d')} SMI={smi[last['pd_b']]:.1f} [{hist_state[last['pd_b']]}] ST={'DN' if st_trend[last['pd_b']]==-1 else 'UP'}")
    # verdict
    armed = (last['smi_step'] in ('FMB..','FMB+PD..','FMB+PD>XDN_WAIT')) and st_trend[-1]==-1
    print(f"  >>> TRIGGER ARMED?   : {'YA — nunggu XDN confirm' if armed else 'TIDAK (idle / gak di-window)'}")
else:
    print(f"    Tidak ada wave bear aktif -> trigger IDLE (nunggu WAVE_STARTED baru)")
print(f"{'='*70}")
print(f"  TOTAL SINYAL 2021-2026 : {len(samples)}")
sel = samples[-5:]
print(f"  5 sinyal terakhir      : " + ", ".join(df.index[s['bar']].strftime('%Y-%m-%d') for s in sel))
print(f"  Sinyal terakhir entry  : {df.index[sel[-1]['bar']].strftime('%Y-%m-%d')} (close {sel[-1]['entry']:,.2f})")
print(f"{'='*70}")
