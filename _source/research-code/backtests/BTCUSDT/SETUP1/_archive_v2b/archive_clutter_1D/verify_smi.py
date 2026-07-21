"""verify_smi.py — pakai smi_events.compute_smi_events (single source of truth)
lalu:
(A) list SEMUA event SMI per bar @ 4 window rujukan (cross MID, OB/OS, EMA,
    PA/PD flavour, FailMID, bias) — buat lo cross-check ke TV.
(B) 6 sampel recent dgn detail 3-step + konteks event.
"""
import sys, io, contextlib
import pandas as pd
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import sample_v2a as S   # triggers 3-step tetap dari modul
import smi_events as SM

df = S.df
E = S.E
st_trend = S.st_trend
high, low, close = S.high, S.low, S.close
n = S.n
events = S.events
ev_by_bar = S.ev_by_bar
samples = S.samples

# ============================================================
# (A) 4 WINDOW RUJUKAN — SEMUA event per bar
# ============================================================
windows = [
    ("11-19 Jun 2026", "2026-06-11", "2026-06-19"),
    ("08-13 Feb 2026", "2026-02-08", "2026-02-13"),
    ("25 Nov - 02 Dec 2025", "2025-11-25", "2025-12-02"),
    ("12-16 Oct 2025", "2025-10-12", "2025-10-16"),
]
print("="*130)
print("BAGIAN A — SEMUA EVENT SMI per bar @ 4 WINDOW RUJUKAN (cross-check ke TV)")
print("  M+=cross MID up  M-=cross MID dn  EO=enter OB  ES=enter OS  XO=exit OB  XS=exit OS")
print("  FMB=Fail MID Buy  FMS=Fail MID Sell  PAD=PA Dip  PAR=PA Ready  PDD=PD Dip  PDR=PD Ready")
print("  XU=Cross Up(EMA)  XD=Cross Dn(EMA)  H=hist-state  bias=B/U")
print("="*130)
for nm, a, b in windows:
    print(f"\n### WINDOW: {nm}")
    print(f"{'date':<16}{'close':>10}{'SMI':>8}{'H':>3}  {'M+':>3}{'M-':>3}{'EO':>3}{'ES':>3}{'XO':>3}{'XS':>3}  {'FMB':>4}{'FMS':>4}{'PAD':>4}{'PAR':>4}{'PDD':>4}{'PDR':>4}  {'XU':>3}{'XD':>3}  FBF-event")
    for bi in range(n):
        if df.index[bi] < pd.Timestamp(a, tz="UTC") or df.index[bi] > pd.Timestamp(b, tz="UTC"):
            continue
        dt = df.index[bi]
        c = close[bi]; s = E["smi"][bi]
        def x(name): return "X" if E[name][bi] else ""
        evs = []
        for e in ev_by_bar.get(bi, []):
            if e["side"]!="bear": continue
            if e["event"]=="WAVE_STARTED": evs.append(f"WS(A{e['a_val']:.0f},B{e['b_val']:.0f})")
            elif e["event"]=="C_LOCKED": evs.append(f"CL(C{e['c_val']:.0f})")
            elif e["event"] in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED","CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
                evs.append(e["event"][:6])
        evstr = ",".join(evs)
        bias = "B" if s < 0 else ("U" if s > 0 else "-")
        print(f"{dt.strftime('%Y-%m-%d'):<16}{c:>10.1f}{s:>8.1f}{E['hist_state'][bi]:>3}  "
              f"{x('cross_mid_up'):>3}{x('cross_mid_down'):>3}{x('entered_ob'):>3}{x('entered_os'):>3}{x('exited_ob'):>3}{x('exited_os'):>3}  "
              f"{x('fail_mid_buy'):>4}{x('fail_mid_sell'):>4}{x('pa_dip'):>4}{x('pa_ready'):>4}{x('pd_dip'):>4}{x('pd_ready'):>4}  "
              f"{x('cross_up'):>3}{x('cross_down'):>3}  {evstr}")

# ============================================================
# (B) SAMPEL RECENT
# ============================================================
def fmt_pct(x): return f"{x:.1f}%" if x is not None else "n/a"
def tv(bar): return df.index[bar].strftime("%Y-%m-%d")
recent = [s for s in samples if df.index[s["bar"]] >= pd.Timestamp("2025-01-01", tz="UTC")]
print("\n"+"="*130)
print(f"BAGIAN B — 6 SAMPEL RECENT (entry >= 2025-01-01): {len(recent)} dari {len(samples)} total")
print("="*130)
for idx, s in enumerate(recent[:6], 1):
    A=s["A"]; B=s["B"]; C=s["C"]
    print(f"\n--- Sampel Recent {idx} — ENTRY {tv(s['bar'])} | close={s['entry']:.2f} ---")
    print(f"  WAVE_STARTED bear: A={A[1]:.2f}@bar{A[0]}  B={B[1]:.2f}@bar{B[0]}")
    if C:
        print(f"  C_LOCKED: C={C[1]:.2f}@bar{C[0]}  retrace={fmt_pct(C[2])}")
    else:
        print(f"  C_LOCKED: BELUM (entry valid, no-wait C)")
    fb=s["fmb_b"]; pb=s["pd_b"]; xb=s["xdn_b"]
    print(f"  STEP1 FMB = bar {fb} ({tv(fb)}) | {S.describe_bar(fb)}  [Fail MID Buy: cross MID up lalu balik turun]")
    # trigger step-2 = PD (hist melemah 2 bar) = flavour Siap Balik; tampilkan juga
    # flavour kamus Pine (pd_ready / pd_dip) kalau kebetulan beda.
    if E["pd_ready"][pb]:
        flav = "Siap Balik (hist melemah)"
    elif E["pd_dip"][pb]:
        flav = "Dip Mungkin (hist msh naik)"
    else:
        flav = "triggered (hist<prev2, no plain flavour)"
    print(f"  STEP2 PD  = bar {pb} ({tv(pb)}) | {S.describe_bar(pb)}  [PD - {flav}]")
    print(f"  STEP3 XDN = bar {xb} ({tv(xb)}) | {S.describe_bar(xb)}  [Cross DOWN: SMI crossunder EMA]  [ENTRY]")
    print(f"  ST gate = {'DOWN (-1) OK' if s['st']==-1 else 'UP (!)'}")
    print(f"  ATR14={s['atr14']:.2f}  ATR%={fmt_pct(s['apct'])}")
    print(f"  -- Kombo MODE A (SL x TP 1x/2x/3x), trail HOLD --")
    e=s["entry"]
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
            fwd_h=high[s["bar"]+1:]; fwd_l=low[s["bar"]+1:]
            out=None; ex=None; bk=None
            for k in range(len(fwd_h)):
                if fwd_l[k]<=tp: out="TP"; ex=tp; bk=k+1; break
                if fwd_h[k]>=sl: out="SL"; ex=sl; bk=k+1; break
                if k>=240: out="EXP"; ex=fwd_l[k]; bk=k+1; break
            R=(e-ex)/risk if out else 0
            print(f"    {opt}/{tpr}: SL={sl:.2f} TP={tp:.2f} -> {out} {ex:.2f} R={R:+.2f} bars={bk}")
print("\nSELESAI")
