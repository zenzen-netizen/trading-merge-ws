"""
analyze_2026.py — bongkar FBF + SMI phase utk 4 trade 2026.
"""
import sys, io, contextlib
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
import pandas as pd
import numpy as np

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import sample_v2a as S

df = S.df; high = S.high; low = S.low; close = S.close; n = S.n
st_trend = S.st_trend; events = S.events; ev_by_bar = S.ev_by_bar
E = S.E; samples_all = S.samples
FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]
smi = E["smi"]; smi_hist = E["smi_hist"]; hist_state = E["hist_state"]

cut = pd.Timestamp("2026-01-01", tz="UTC")
samples = [s for s in samples_all if df.index[s["bar"]] >= cut]

print(f"Total sinyal 2026: {len(samples)}")
print()

for idx, s in enumerate(samples, 1):
    eb = s["bar"]
    entry = s["entry"]
    A = s["A"]; B = s["B"]; C = s["C"]
    fmb_b = s["fmb_b"]; pd_b = s["pd_b"]; xdn_b = s["xdn_b"]

    print("="*100)
    print(f"TRADE #{idx}  |  ENTRY: {df.index[eb].strftime('%Y-%m-%d')}  |  close={entry:.2f}")
    print("="*100)

    # ── FBF WAVE ──
    print(f"\n  FBF v11 BEAR WAVE:")
    print(f"    WAVE_STARTED: A={A[1]:.2f} @ bar {A[0]} ({df.index[A[0]].strftime('%Y-%m-%d')})")
    print(f"                  B={B[1]:.2f} @ bar {B[0]} ({df.index[B[0]].strftime('%Y-%m-%d')})")
    if C:
        print(f"    C_LOCKED:     C={C[1]:.2f} @ bar {C[0]} ({df.index[C[0]].strftime('%Y-%m-%d')})  retrace={C[2]:.1f}%")
    else:
        print(f"    C_LOCKED:     BELUM (no-wait C — entry valid tanpa C)")

    # ── All FBF events between WAVE_STARTED and entry ──
    ws_bar = A[0]  # WAVE_STARTED bar
    fbf_events = []
    for i in range(ws_bar, eb+1):
        for e in ev_by_bar.get(i, []):
            if e["side"] == "bear":
                fbf_events.append((i, e["event"], e))
    if fbf_events:
        print(f"\n  FBF EVENT CHAIN (bar {ws_bar} → {eb}):")
        for bar_i, evt, evd in fbf_events:
            cv = evd.get('c_val'); c_val = f" C={cv:.0f}" if cv is not None else ""
            bv = evd.get('b_val'); b_val = f" B={bv:.0f}" if bv is not None else ""
            rp = evd.get('retrace_pct'); retr = f" ret={rp:.1f}%" if rp is not None else ""
            print(f"    bar {bar_i:>5} {df.index[bar_i].strftime('%Y-%m-%d'):>12}  {evt:30s}{c_val}{b_val}{retr}")
    else:
        print(f"\n  FBF: no events in window")

    # ── SMI 3-step walk ──
    print(f"\n  SMI 3-STEP:")
    print(f"    STEP1 FMB = bar {fmb_b} ({df.index[fmb_b].strftime('%Y-%m-%d')})")
    print(f"          SMI={smi[fmb_b]:.1f}  hist={smi_hist[fmb_b]:.1f} [{hist_state[fmb_b]}]  ST={'DN' if st_trend[fmb_b]==-1 else 'UP'}")
    print(f"          zone={S.describe_bar(fmb_b)}")
    print(f"    STEP2 PD  = bar {pd_b} ({df.index[pd_b].strftime('%Y-%m-%d')})")
    print(f"          SMI={smi[pd_b]:.1f}  hist={smi_hist[pd_b]:.1f} [{hist_state[pd_b]}]  ST={'DN' if st_trend[pd_b]==-1 else 'UP'}")
    print(f"          zone={S.describe_bar(pd_b)}")
    if E["pd_ready"][pd_b]: flav="Siap Balik (hist melemah)"
    elif E["pd_dip"][pd_b]: flav="Dip Mungkin (hist naik)"
    else: flav="triggered (hist<prev2, no flavour)"
    print(f"          flavour: {flav}")
    print(f"    STEP3 XDN = bar {xdn_b} ({df.index[xdn_b].strftime('%Y-%m-%d')})  ← ENTRY")
    print(f"          SMI={smi[xdn_b]:.1f}  hist={smi_hist[xdn_b]:.1f} [{hist_state[xdn_b]}]  ST={'DN' if st_trend[xdn_b]==-1 else 'UP'}")
    print(f"          zone={S.describe_bar(xdn_b)}")

    # ── SMI walk from FMB to XDN ──
    print(f"\n  SMI BAR-BY-BAR (FMB → XDN):")
    print(f"  {'bar':>5} {'date':>12} {'close':>10} {'SMI':>7} {'hist':>7} {'HIST':>5} {'zone':>22} {'FMB':>4} {'PD':>4} {'XDN':>4} {'ST':>4}")
    for i in range(fmb_b-1, xdn_b+1):
        if i < 0 or i >= n: continue
        dt = df.index[i].strftime("%Y-%m-%d")
        f = " ✓" if FMB[i] else ""
        p = " ✓" if PD[i] else ""
        x = " ✓" if XDN[i] else ""
        st = "DN" if st_trend[i] == -1 else "UP"
        print(f"  {i:>5} {dt:>12} {close[i]:>10.2f} {smi[i]:>7.1f} {smi_hist[i]:>7.1f} {hist_state[i]:>5} {S.describe_bar(i):>22} {f:>4} {p:>4} {x:>4} {st:>4}")

    # ── Price context around entry ──
    print(f"\n  PRICE CONTEXT (entry ± 5 bar):")
    print(f"  {'bar':>5} {'date':>12} {'open':>10} {'high':>10} {'low':>10} {'close':>10} {'ST':>4}")
    for i in range(max(0, eb-5), min(n, eb+6)):
        dt = df.index[i].strftime("%Y-%m-%d")
        st = "DN" if st_trend[i] == -1 else "UP"
        marker = " ← ENTRY" if i == eb else ""
        print(f"  {i:>5} {dt:>12} {df['open'].iloc[i]:>10.2f} {high[i]:>10.2f} {low[i]:>10.2f} {close[i]:>10.2f} {st:>4}{marker}")

    print()
