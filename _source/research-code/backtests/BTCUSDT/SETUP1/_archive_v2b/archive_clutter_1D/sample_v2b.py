"""
sample_v2a.py — ambil 5 sampel trade BTCUSDT spot Binance DAILY pakai
trigger S1S-TRG-v2.a (lock di B / WAVE_STARTED, SMI 3-step paralel,
no-wait C, + rule 1 wave = 1 posisi).

Untuk tiap sampel cetak:
  - detail event (WAVE_STARTED A/B, SMI FMB/PD/XDN, ST) biar bisa
    di-cross-check ke chart TV.
  - hasil 15 kombo MODE A (5 SL x TP 1x/2x/3x), trail HOLD.

Engine: FBFEngine v11 (utuh) + smi_pro_v3 + supertrend(10,3) + atr%.
SMI 3-step: FMB=fail MID buy, PD=PD TRIGGERED, XDN=cross DN (%K<=%D).
"""
import sys, time, os
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/fetchers")
sys.path.insert(0, "/home/ubuntu")  # FBFEngine default
import datetime as _dt
import pandas as pd
import numpy as np
import requests
import fbf_v11_backtest as V11
import smi_pro
import atr_percentage as atrp

SYM = "BTCUSDT"
TF = "1d"
IV_MS = 86400000
START = pd.Timestamp("2021-01-01", tz="UTC")
END = pd.Timestamp.now("UTC").normalize()
WIB = 7  # UTC+7

SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

# ---------- fetch ----------
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

print("[fetch] BTCUSDT daily ...")
df = fetch_full(SYM, TF, START, END)
print(f"[fetch] {len(df)} candles {df.index[0].date()} .. {df.index[-1].date()}")
high = df["high"].values.astype(float); low = df["low"].values.astype(float)
close = df["close"].values.astype(float); n = len(df)

# ---------- Supertrend (sama dgn backtest: period=10 mult=3) ----------
def supertrend_full(df, period=10, mult=3.0):
    h=df["high"].values; l=df["low"].values; c=df["close"].values
    hl2=(h+l)/2.0; tr=np.zeros(len(c)); tr[0]=h[0]-l[0]
    for i in range(1,len(c)):
        tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    atr=np.zeros(len(c)); atr[0]=tr[0]; alpha=1.0/period
    for i in range(1,len(c)): atr[i]=atr[i-1]+alpha*(tr[i]-atr[i-1])
    up_raw=hl2-mult*atr; dn_raw=hl2+mult*atr
    up_f=np.zeros(len(c)); dn_f=np.zeros(len(c)); trend=np.ones(len(c),dtype=int)
    up_f[0]=up_raw[0]; dn_f[0]=dn_raw[0]
    for i in range(1,len(c)):
        up_f[i]=max(up_raw[i],up_f[i-1]) if c[i-1]>up_f[i-1] else up_raw[i]
        dn_f[i]=min(dn_raw[i],dn_f[i-1]) if c[i-1]<dn_f[i-1] else dn_raw[i]
        trend[i]=trend[i-1]
        if trend[i-1]==-1 and c[i]>dn_f[i-1]: trend[i]=1
        elif trend[i-1]==1 and c[i]<up_f[i-1]: trend[i]=-1
    return trend
st_trend = supertrend_full(df, 10, 3.0)

# ---------- SMI series (vectorized) ----------
def smi_series(df, cfg):
    k=cfg["len_k"]; d=cfg["len_d"]; e=cfg["len_e"]; mid=cfg["mid"]
    h=df["high"]; l=df["low"]; c=df["close"]
    hh=h.rolling(k,min_periods=k).max(); ll=l.rolling(k,min_periods=k).min()
    rel=c-(hh+ll)/2; rng=hh-ll; rng_safe=rng.replace(0,np.nan)
    ema2=lambda s: s.ewm(span=d,adjust=False).mean().ewm(span=d,adjust=False).mean()
    smi=200*(ema2(rel)/ema2(rng_safe))
    smi_ema=smi.ewm(span=e,adjust=False).mean()
    smi_hist=smi-smi_ema
    return smi, smi_ema, smi_hist
smi, smi_ema, smi_hist = smi_series(df, SMI_CFG)
mid = SMI_CFG["mid"]

# ---------- SMI events via single-source module (smi_events.py) ----------
import sys as _sys
_sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
import smi_events as SM
E = SM.compute_smi_events(df, SMI_CFG)
smi, smi_ema, smi_hist = E["smi"], E["smi_ema"], E["smi_hist"]
mid = SMI_CFG["mid"]
FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]
PD_DIP = E["pd_dip"]; PD_READY = E["pd_ready"]
HIST_STATE = E["hist_state"]
import numpy as _np
def smi_state_label(i):
    return (f"SMI={smi[i]:.1f} hist={smi_hist[i]:.1f} [{HIST_STATE[i]}] "
            f"ST={'DN' if st_trend[i]==-1 else 'UP'}")
def describe_bar(i):
    return SM.describe_bar(E, i)

# ---------- ATR% + ATR14 helpers ----------
def atr_pct_at(i):
    return atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]
def atr14_at(i):
    sub=df.iloc[max(0,i-13):i+1]
    tr=pd.concat([sub["high"]-sub["low"],(sub["high"]-sub["close"].shift(1)).abs(),
                  (sub["low"]-sub["close"].shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1]

# ---------- FBF v11 engine events ----------
times=[int(t.value//1_000_000) for t in df.index]
eng=V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, IV_MS)
breaks, events = eng.run()
# index events by bar
ev_by_bar={}
for e in events:
    ev_by_bar.setdefault(e["bar"], []).append(e)

# ---------- v2.a sequential scan ----------
def wib_date(bar):
    # open time UTC + WIB offset, tapi entry = close bar -> +1d - epsilon; kita tampilkan close date WIB
    ot = df.index[bar]  # UTC open
    close_dt = ot + _dt.timedelta(hours=24)  # close next day UTC
    return (close_dt + _dt.timedelta(hours=WIB)).strftime("%Y-%m-%d %H:%M")

samples=[]
pos_open=False
clear_bar=-1
wave_A=None; wave_B=None
wave_c=None  # C_LOCKED captured during wave
wave_started_bar=None  # v2.b: track umur wave
fmb_b=None; pd_b=None
wave_entry_done=False  # 1 posisi per wave (v2.a): begitu entry di wave ini, lock sampai wave baru
# ── v2.b GATE PARAMS ──
GATE_DEPTH = 0.15       # #2 (A-B)/A >= 15%
GATE_MATURITY = 10      # #3 umur wave >= 10 bar
GATE_SMI_PD = 40.0      # #4 SMI[pd] >= 40
bvals=[(e["bar"], e["b_val"]) for e in events if e["side"]=="bear" and e["event"]=="WAVE_STARTED"]
def last_B(i):

    v=None
    for bar,val in bvals:
        if bar<=i: v=val
        else: break
    return v
for i in range(n):
    # v2.a: kalau posisi masih open, cek dulu apa sudah clear
    if pos_open:
        if i >= clear_bar:
            pos_open=False; clear_bar=-1
        else:
            continue  # abaikan wave berikutnya sampai posisi clear
    # WAVE_STARTED -> lock A/B (konteks), reset entry-lock (1 posisi/wave),
    # dan reset SMI tracker HANYA kalau msh di step-1 (pd_b None).
    for e in ev_by_bar.get(i, []):
        if e["side"]!="bear": continue
        if e["event"]=="WAVE_STARTED":
            wave_A=(e["a_bar"], e["a_val"]); wave_B=(e["b_bar"], e["b_val"])
            wave_started_bar=e["bar"]
            wave_entry_done=False
            if pd_b is None:
                fmb_b=None; wave_c=None
        elif e["event"]=="C_LOCKED":
            wave_c=(e["c_bar"], e["c_val"], e.get("retrace_pct"))
        # ── v2.b #1: reset SMI tracker saat wave batal ──
        elif e["event"] in ("WAVE_CANCELLED", "WAVE_STRUCT_REJECTED", "CANDIDATE_INVALIDATED", "CANDIDATE_EVICTED"):
            fmb_b=None; pd_b=None
    # SMI 3-step (sequential, gap allowed, reset only if still step-1): FMB -> PD -> XDN
    if not wave_entry_done:
        if FMB[i] and fmb_b is None:
            fmb_b=i
        if fmb_b is not None and pd_b is None and PD[i] and i>=fmb_b:
            pd_b=i
        if fmb_b is not None and pd_b is not None and XDN[i] and i>=pd_b:
            if st_trend[i]==-1:
                # ── v2.b GATES ──
                # #2 depth
                depth_ok = (wave_A[1] - wave_B[1]) / wave_A[1] >= GATE_DEPTH if (wave_A and wave_B) else False
                # #3 maturity
                maturity_ok = (i - wave_started_bar) >= GATE_MATURITY if wave_started_bar is not None else False
                # #4 SMI pullback strength
                smi_pd_ok = smi[pd_b] >= GATE_SMI_PD
                # #5 ST continuity (ST masih down 1 bar sesudah)
                st_cont_ok = (i+1 < n) and (st_trend[i+1] == -1)
                if depth_ok and maturity_ok and smi_pd_ok and st_cont_ok:
                    entry=close[i]
                    atr14=atr14_at(i); apct=atr_pct_at(i)
                    Ch = high[wave_c[0]] if wave_c else np.nan
                    Bval = last_B(i)
                    Bctx = (wave_B[0], Bval) if wave_B is not None else (None, Bval)
                    samples.append(dict(bar=i, entry=entry, A=wave_A, B=Bctx, C=wave_c,
                                        fmb_b=fmb_b, pd_b=pd_b, xdn_b=i,
                                        st=st_trend[i], atr14=atr14, apct=apct, Ch=Ch,
                                        g_depth=depth_ok, g_mat=maturity_ok, g_smi=smi_pd_ok, g_st=st_cont_ok))
                    pos_open=True
                    wave_entry_done=True
                    sl=entry*(1+apct/100.0); tp1=entry*(1-apct/100.0)
                    risk=sl-entry; tp2=entry-2*risk; tp3=entry-3*risk
                    fwd_h=high[i+1:]; fwd_l=low[i+1:]
                    ck=240
                    for k in range(len(fwd_h)):
                        if fwd_l[k]<=tp3 or fwd_l[k]<=tp2 or fwd_l[k]<=tp1 or fwd_h[k]>=sl or k>=240:
                            ck=k; break
                    clear_bar=i+1+ck
            # reset smi step (boleh XDN lain di wave sama kalau entry blm done)
            fmb_b=None; pd_b=None

# ---------- cetak 5 sampel pertama ----------
def fmt_pct(x): return f"{x:.1f}%" if x is not None else "n/a"
sel = samples[:5]
print(f"\n=== {len(samples)} sinyal v2.a total; tampil 5 pertama ===\n")
for idx, s in enumerate(sel, 1):
    A=s["A"]; B=s["B"]; C=s["C"]
    print(f"--- Sampel {idx} — ENTRY {wib_date(s['bar'])} | close={s['entry']:.2f} ---")
    print(f"  WAVE_STARTED bear: A={A[1]:.2f}@bar{A[0]}  B={B[1]:.2f}@bar{B[0]}")
    if C:
        print(f"  C_LOCKED (dalam window): C={C[1]:.2f}@bar{C[0]}  retrace={fmt_pct(C[2])}")
    else:
        print(f"  C_LOCKED: BELUM (entry tetap valid, no-wait C)")
    # --- detail 3-step SMI dgn kamus Pine ---
    fb=s["fmb_b"]; pb=s["pd_b"]; xb=s["xdn_b"]
    print(f"  SMI FMB = bar {fb} ({wib_date(fb)}) | {smi_state_label(fb)}  [Fail MID Buy: cross MID up lalu balik turun]")
    pdtxt = "PD - Siap Balik (hist melemah)" if PD_READY[pb] else "PD - Dip Mungkin (hist msh naik)"
    print(f"  SMI PD  = bar {pb} ({wib_date(pb)}) | {smi_state_label(pb)}  [{pdtxt}]")
    print(f"  SMI XDN = bar {xb} ({wib_date(xb)}) | {smi_state_label(xb)}  [Cross DOWN: SMI crossunder EMA]  [ENTRY]")
    print(f"  ST gate = {'DOWN (-1) OK' if s['st']==-1 else 'UP (!)'}")
    print(f"  ATR14={s['atr14']:.2f}  ATR%={fmt_pct(s['apct'])}")
    # kombo MODE A (15)
    print(f"  -- Kombo MODE A (SL x TP 1x/2x/3x), trail HOLD --")
    e = s["entry"]
    for opt in ["O1","O2","O3","O4","O5"]:
        if opt in ("O2","O5") and (C is None):
            print(f"    {opt}: n/a (butuh C_high, C blm lock)"); continue
        if opt=="O1": sl=e*1.1; tp1=e*0.9
        elif opt=="O2": sl=s["Ch"]+s["atr14"]; tp1=2*e-sl
        elif opt=="O3": sl=e*(1+s["apct"]/100.0); tp1=e*(1-s["apct"]/100.0)
        elif opt=="O4": sl=e*1.06; tp1=e*0.94
        elif opt=="O5": sl=high[s["bar"]]+s["atr14"]; tp1=2*e-sl
        risk=sl-e
        for tpr in ["1x","2x","3x"]:
            mult=int(tpr[0]); tp=e-mult*risk
            # simulate
            fwd_h=high[s["bar"]+1:]; fwd_l=low[s["bar"]+1:]
            out=None; ex=None; bk=None
            for k in range(len(fwd_h)):
                if fwd_l[k]<=tp: out="TP"; ex=tp; bk=k+1; break
                if fwd_h[k]>=sl: out="SL"; ex=sl; bk=k+1; break
                if k>=240: out="EXP"; ex=fwd_l[k]; bk=k+1; break
            R=(e-ex)/risk if out else 0
            print(f"    {opt}/{tpr}: SL={sl:.2f} TP={tp:.2f} -> {out} {ex:.2f} R={R:+.2f} bars={bk}")
    print()
print("SELESAI")
