"""
test_v2b_variants.py — tes variant gate v2.b vs baseline v2.a.
Window 2021-2026. Param SL/TP SAMA (O1-O5 x TP1x/TRAIL/ST_REV/RAWBRK).

BUG FIX vs sample_v2b.py: snapshot wave_A/B/started_bar SAAT FMB
fire (gak di-overwrite nested WAVE_STARTED).

Variant:
  BASE = v2.a (no gate, no reset) — dari A.samples
  A    = #1 reset + #2 depth>=15%
  B    = #1 reset + #2 depth>=15% + #3 maturity>=10
  C    = #1 reset + #2 depth>=15% + #4 smi_pd>=40
  D    = #1+#2+#3+#4 (full, original v2.b)
"""
import sys, io, contextlib
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
import pandas as pd
import numpy as np

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import sample_v2a as A

df = A.df; high = A.high; low = A.low; close = A.close; n = A.n
st_trend = A.st_trend; events = A.events; ev_by_bar = A.ev_by_bar
E = A.E; FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]; smi = E["smi"]

# ── precompute bear_active / bear_trigger (sama spt compare) ──
pl_by_idx = {}
for e in events:
    if e["event"] == "WAVE_STARTED" and e["side"] == "bear":
        pl_by_idx[e["b_bar"]] = e["b_val"]
running_last_pl = np.full(n, np.nan); last_pl_val = None
for i in range(n):
    if i in pl_by_idx: last_pl_val = pl_by_idx[i]
    running_last_pl[i] = last_pl_val
def atr14_arr(high, low, close, period=14):
    tr = np.zeros(len(close)); tr[0] = high[0]-low[0]
    for i in range(1,len(close)):
        tr[i]=max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1]))
    atr=np.zeros(len(close)); atr[0]=tr[0]; alpha=1.0/period
    for i in range(1,len(close)): atr[i]=atr[i-1]+alpha*(tr[i]-atr[i-1])
    return atr
atr14_arr_vals = atr14_arr(high, low, close, 14)
bear_active=np.zeros(n,dtype=bool); bear_active_high=np.full(n,np.nan); prev_active_high=np.nan
for i in range(n):
    rpl=running_last_pl[i]
    if np.isnan(rpl): bear_active[i]=False
    else:
        raw_bear=close[i]<rpl
        dist_ok=(rpl-close[i])>=0.15*atr14_arr_vals[i] if not np.isnan(atr14_arr_vals[i]) else False
        if i==0 or not bear_active[i-1]:
            if raw_bear and dist_ok: bear_active[i]=True
        else:
            still_beyond=close[i]<rpl
            dist_ok2=(rpl-close[i])>=0.15*atr14_arr_vals[i] if not np.isnan(atr14_arr_vals[i]) else False
            if still_beyond and dist_ok2: bear_active[i]=True
    if bear_active[i]:
        bear_active_high[i]=max(prev_active_high,high[i]) if not np.isnan(prev_active_high) else high[i]
        prev_active_high=bear_active_high[i]
    else: prev_active_high=np.nan
bear_trigger=np.zeros(n,dtype=bool)
for i in range(1,n):
    if bear_active[i] and not bear_active[i-1]: bear_trigger[i]=True

bvals=[(e["bar"],e["b_val"]) for e in events if e["side"]=="bear" and e["event"]=="WAVE_STARTED"]
def last_B(i):
    v=None
    for bar,val in bvals:
        if bar<=i: v=val
        else: break
    return v

# ── scan function with configurable gates ──
def scan_v2b(gates):
    samples=[]
    pos_open=False; clear_bar=-1
    wave_A=None; wave_B=None; wave_c=None; wave_started_bar=None
    fmb_b=None; pd_b=None; wave_entry_done=False
    snap_A=None; snap_B=None; snap_ws=None
    for i in range(n):
        if pos_open:
            if i>=clear_bar: pos_open=False; clear_bar=-1
            else: continue
        for e in ev_by_bar.get(i,[]):
            if e["side"]!="bear": continue
            if e["event"]=="WAVE_STARTED":
                wave_A=(e["a_bar"],e["a_val"]); wave_B=(e["b_bar"],e["b_val"]); wave_started_bar=e["bar"]
                wave_entry_done=False
                if pd_b is None:
                    fmb_b=None; wave_c=None; snap_A=None; snap_B=None; snap_ws=None
            elif e["event"]=="C_LOCKED":
                wave_c=(e["c_bar"],e["c_val"],e.get("retrace_pct"))
            elif gates.get("reset") and e["event"] in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED","CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
                fmb_b=None; pd_b=None; snap_A=None; snap_B=None; snap_ws=None
        if not wave_entry_done:
            if FMB[i] and fmb_b is None:
                fmb_b=i
                snap_A=wave_A; snap_B=wave_B; snap_ws=wave_started_bar
            if fmb_b is not None and pd_b is None and PD[i] and i>=fmb_b:
                pd_b=i
            if fmb_b is not None and pd_b is not None and XDN[i] and i>=pd_b:
                if st_trend[i]==-1:
                    depth_ok=True
                    if gates.get("depth") is not None:
                        if snap_A and snap_B:
                            depth_ok=(snap_A[1]-snap_B[1])/snap_A[1] >= gates["depth"]
                        else: depth_ok=False
                    mat_ok=True
                    if gates.get("maturity") is not None:
                        if snap_ws is not None:
                            mat_ok=(i-snap_ws) >= gates["maturity"]
                        else: mat_ok=False
                    smi_ok=True
                    if gates.get("smi_pd") is not None:
                        smi_ok = smi[pd_b] >= gates["smi_pd"]
                    st_ok=True
                    if gates.get("st_cont"):
                        st_ok = (i+1<n) and (st_trend[i+1]==-1)
                    if depth_ok and mat_ok and smi_ok and st_ok:
                        entry=close[i]
                        atr14=A.atr14_at(i); apct=A.atr_pct_at(i)
                        Ch=high[wave_c[0]] if wave_c else np.nan
                        Bval=last_B(i)
                        Bctx=(wave_B[0],Bval) if wave_B is not None else (None,Bval)
                        samples.append(dict(bar=i,entry=entry,A=snap_A,B=Bctx,C=wave_c,
                                            fmb_b=fmb_b,pd_b=pd_b,xdn_b=i,st=st_trend[i],
                                            atr14=atr14,apct=apct,Ch=Ch))
                        pos_open=True; wave_entry_done=True
                        sl=entry*(1+apct/100.0); tp1=entry*(1-apct/100.0)
                        risk=sl-entry; tp2=entry-2*risk; tp3=entry-3*risk
                        fwd_h=high[i+1:]; fwd_l=low[i+1:]
                        ck=240
                        for k in range(len(fwd_h)):
                            if fwd_l[k]<=tp3 or fwd_l[k]<=tp2 or fwd_l[k]<=tp1 or fwd_h[k]>=sl or k>=240:
                                ck=k; break
                        clear_bar=i+1+ck
                fmb_b=None; pd_b=None; snap_A=None; snap_B=None; snap_ws=None
    return samples

def get_sl_tp(entry, Ch, atr14, apct, hi_bar, opt):
    if opt=="O1": return entry*1.10, entry*0.90
    elif opt=="O2":
        if np.isnan(Ch): return None,None
        sl=Ch+atr14
        if sl<=entry: return None,None
        return sl, 2*entry-sl
    elif opt=="O3":
        sl=entry*(1+apct/100.0); return sl, entry*(1-apct/100.0)
    elif opt=="O4": return entry*1.06, entry*0.94
    elif opt=="O5":
        sl=hi_bar+atr14
        if sl<=entry: return None,None
        return sl, 2*entry-sl
    return None,None

def simulate(entry, sl, tp_target, exit_mode, eb, apct):
    fwd_h=high[eb+1:]; fwd_l=low[eb+1:]
    risk=sl-entry; trail_active=False; lowest=entry
    activation_price=entry*(1-(apct/2)/100.0)
    raw_trail_active=False; raw_anchor_high=None
    for k in range(min(len(fwd_h),240)):
        bar_idx=eb+1+k
        if exit_mode=="TP1x":
            if fwd_l[k]<=tp_target: return "TP",k+1,1.0
        if fwd_h[k]>=sl: return "SL",k+1,-1.0
        if exit_mode=="TRAIL":
            if fwd_l[k]<lowest: lowest=fwd_l[k]
            if not trail_active and lowest<=activation_price: trail_active=True
            if trail_active:
                trail_stop=lowest*(1+apct/100.0)
                if fwd_h[k]>=trail_stop: return "TRAIL",k+1,(entry-trail_stop)/risk
        if exit_mode=="ST_REV":
            if bar_idx<n and st_trend[bar_idx]==1 and st_trend[bar_idx-1]==-1:
                exit_pr=min(fwd_l[k],entry); return "ST_REV",k+1,(entry-exit_pr)/risk
        if exit_mode=="RAWBRK":
            if bar_idx<n and not raw_trail_active and bear_trigger[bar_idx]:
                raw_trail_active=True; raw_anchor_high=high[bar_idx]
            if raw_trail_active:
                if bar_idx<n and high[bar_idx]>raw_anchor_high: raw_anchor_high=high[bar_idx]
                if fwd_h[k]>=raw_anchor_high: return "RAWTRL",k+1,(entry-raw_anchor_high)/risk
                if bar_idx<n and bar_idx>0 and bear_active[bar_idx-1] and not bear_active[bar_idx]:
                    exit_pr=min(fwd_l[k],entry); return "RAWBRK",k+1,(entry-exit_pr)/risk
    last_close=fwd_l[min(239,len(fwd_l)-1)] if len(fwd_l)>0 else entry
    return "EXP",min(240,len(fwd_l)),(entry-last_close)/risk

SL_OPTS=["O1","O2","O3","O4","O5"]
EXIT_MODES=["TP1x","TRAIL","ST_REV","RAWBRK"]

def run_backtest(samples, label, show_breakdown=False, show_per_opt=False):
    results=[]
    for s in samples:
        eb=s["bar"]; entry=s["entry"]; Ch=s["Ch"]; atr14=s["atr14"]; apct=s["apct"]; hi_bar=high[eb]
        entry_date=df.index[eb].strftime("%Y-%m-%d")
        for opt in SL_OPTS:
            sl,tp1=get_sl_tp(entry,Ch,atr14,apct,hi_bar,opt)
            if sl is None:
                for em in EXIT_MODES:
                    results.append({"entry_date":entry_date,"opt":opt,"exit":em,"outcome":"INV","R":0.0})
                continue
            for em in EXIT_MODES:
                tp_target=tp1 if em=="TP1x" else None
                outcome,bars,R=simulate(entry,sl,tp_target,em,eb,apct)
                results.append({"entry_date":entry_date,"opt":opt,"exit":em,"outcome":outcome,"R":R})
    # summary: net R per exit mode (sum over O1-O5)
    print(f"\n--- {label}: {len(samples)} trades ---")
    print(f"{'EXIT':<10}{'n':>5}{'WR%':>8}{'TotR':>9}")
    for em in EXIT_MODES:
        sub=[r for r in results if r["exit"]==em and r["outcome"]!="INV"]
        if not sub:
            print(f"{em:<10}{0:>5}{'-':>8}{'-':>9}"); continue
        wins=sum(1 for r in sub if r["R"]>0); losses=sum(1 for r in sub if r["R"]<0)
        tc=wins+losses; wr=wins/tc*100 if tc>0 else 0
        totR=sum(r["R"] for r in sub)
        print(f"{em:<10}{len(sub):>5}{wr:>7.1f}%{totR:>+9.2f}")
    if show_per_opt:
        # per-SL x per-exit breakdown (full grid)
        print(f"  Per-SL x EXIT breakdown (TotR):")
        print(f"  {'SL':<5}{'TP1x':>9}{'TRAIL':>9}{'ST_REV':>9}{'RAWBRK':>9}")
        for opt in SL_OPTS:
            vals=[]
            for em in EXIT_MODES:
                sub=[r for r in results if r["opt"]==opt and r["exit"]==em and r["outcome"]!="INV"]
                if sub:
                    vals.append(f"{sum(r['R'] for r in sub):>+9.2f}")
                else:
                    inv=sum(1 for r in results if r["opt"]==opt and r["exit"]==em and r["outcome"]=="INV")
                    vals.append(f"INVx{inv}" if inv else "  -  ")
            print(f"  {opt:<5}{vals[0]:>9}{vals[1]:>9}{vals[2]:>9}{vals[3]:>9}")
    return results

# ── define variants ──
variants = {
    "BASE (v2.a, no gate)": None,  # use A.samples
    "E: #1 reset only": {"reset":True},
    "A: #1+#2 depth15": {"reset":True, "depth":0.15},
    "B: #1+#2+#3 mat10": {"reset":True, "depth":0.15, "maturity":10},
    "C: #1+#2+#4 smi40": {"reset":True, "depth":0.15, "smi_pd":40.0},
    "D: #1+#2+#3+#4 (full)": {"reset":True, "depth":0.15, "maturity":10, "smi_pd":40.0},
}

print(f"[data] {len(df)} candles 2019-2026")
print("="*70)
all_results = {}
for name, gates in variants.items():
    if gates is None:
        samples = A.samples
    else:
        samples = scan_v2b(gates)
    show_po = name.startswith(("B:", "C:", "D:", "E:"))
    all_results[name] = run_backtest(samples, name, show_per_opt=show_po)

# ── signal count comparison ──
print(f"\n{'='*70}")
print("SIGNAL COUNT COMPARISON")
print(f"{'='*70}")
for name, gates in variants.items():
    if gates is None:
        s = A.samples
    else:
        s = scan_v2b(gates)
    dates=[df.index[x["bar"]].strftime("%Y-%m-%d") for x in s]
    print(f"{name:<28} {len(s):>3} signals")
    print(f"  {dates}")
print("\nDone.")
