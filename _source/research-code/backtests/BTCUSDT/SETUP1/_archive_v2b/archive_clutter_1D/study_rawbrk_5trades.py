"""
study_rawbrk_5trades.py
Study mendalam RAWBRK buat SETUP1 SHORT v2.b (Variant E / reset-only).
Basis engine = sample_v2a.py (sudah berisi baris reset => = v2.b yg di-lock).
RAWBRK dibangun PERSIS spt backtest.py (fbf_v610.find_pivots, atr_mult=0.15).

Output:
  - 5 entry DAILY paling recent (dari sinyal v2.b)
  - per trade: FBF chain, SMI 3-step (FMB/PD/XDN), RAWBRK mechanic
    (pre-entry state, trigger bar, trailing ratchet, exit + DIMANA terjadi)
  - combo: 3 SL (O1/O3/O5) x RAWBRK, LALU 5 SL (O1-O5) x RAWBRK
"""
import sys, io, contextlib
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D")
import pandas as pd
import numpy as np
import fbf_v610 as fbfmod

# ---- load engine v2.b (sample_v2a = reset-only) ----
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import sample_v2a as S

df = S.df; high = S.high; low = S.low; close = S.close; n = S.n
st_trend = S.st_trend; events = S.events; ev_by_bar = S.ev_by_bar
E = S.E
FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]
smi = E["smi"]; smi_hist = E["smi_hist"]; hist_state = E["hist_state"]
samples_all = S.samples

# ============================================================
# RAWBRK engine — PERSIS backtest.py lines 124-197
# ============================================================
ph_arr, pl_arr = fbfmod.find_pivots(high, low, 3, 3)
pl_by_idx = dict(pl_arr)
ph_map = dict(ph_arr)
running_last_pl = np.full(n, np.nan)
for i in range(n):
    if i in pl_by_idx:
        running_last_pl[i] = pl_by_idx[i]

tr = np.zeros(n); tr[0] = high[0] - low[0]
for i in range(1, n):
    tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
atr_arr = np.zeros(n); atr_arr[0] = tr[0]; alpha = 1.0/14
for i in range(1, n):
    atr_arr[i] = atr_arr[i-1] + alpha*(tr[i]-atr_arr[i-1])

bear_active = np.zeros(n, dtype=bool)
bear_ref_val = np.full(n, np.nan)
bear_ref_bar = np.full(n, -1, dtype=int)
bear_active_high = np.full(n, np.nan)
bear_last_high = np.nan
_active = False; _ref_val = np.nan; _ref_bar = -1; _base_high = np.nan
for i in range(n):
    rpl = running_last_pl[i]
    if not np.isnan(rpl):
        raw_bear = close[i] < rpl
    else:
        raw_bear = False
    if not _active and raw_bear:
        dist_ok = (rpl - close[i]) >= 0.15 * atr_arr[i]
        if dist_ok:
            _active = True; _ref_val = rpl; _ref_bar = i; _base_high = high[i]
    elif _active:
        still_beyond = close[i] < _ref_val
        dist_ok2 = (_ref_val - close[i]) >= 0.15 * atr_arr[i] if not np.isnan(_ref_val) else False
        if still_beyond and dist_ok2:
            pass
        else:
            _active = False
    bear_active[i] = _active
    bear_ref_val[i] = _ref_val
    bear_ref_bar[i] = _ref_bar
    if _active:
        bear_last_high = bear_last_high if not np.isnan(bear_last_high) else _base_high
        if high[i] > bear_last_high: bear_last_high = high[i]
        bear_active_high[i] = bear_last_high
    else:
        bear_last_high = np.nan

bear_trigger = np.zeros(n, dtype=bool)
for i in range(1, n):
    if bear_active[i] and not bear_active[i-1]:
        bear_trigger[i] = True

# ============================================================
# helpers
# ============================================================
def atr_pct_at(i):
    return S.atr_pct_at(i)
def atr14_at(i):
    return S.atr14_at(i)
def get_sl_tp(entry, Ch, atr14, apct, opt, entry_bar):
    if opt == "O1": return (entry*1.1, entry*0.9)
    if opt == "O2": sl = Ch + atr14; return (sl, 2*entry - sl)
    if opt == "O3": sl = entry*(1+apct/100.0); return (sl, entry*(1-apct/100.0))
    if opt == "O4": return (entry*1.06, entry*0.94)
    if opt == "O5" and entry_bar is not None:
        conf_hi = high[entry_bar]; sl = conf_hi + atr14; return (sl, 2*entry - sl)
    return (None, None)

OPT_NAMES = {"O1":"Liq10x","O2":"C+ATR14","O3":"ATR%30","O4":"Fix6%","O5":"ConfHi+ATR"}

# ============================================================
# RAWBRK forward sim for ONE trade + ONE SL opt (MODE C: SL + RB only)
# returns dict with mechanic trace + outcome
# ============================================================
def simulate_rb(s, opt):
    eb = s["bar"]; entry = s["entry"]; Ch = s["Ch"]
    atr14 = atr14_at(eb); apct = atr_pct_at(eb)
    sl, tp1 = get_sl_tp(entry, Ch, atr14, apct, opt, eb)
    if sl is None or sl <= entry:
        return {"inv": True}
    risk = sl - entry
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    tr_active = False; anchor_high = None
    trace = []
    exited = False; out = None; ex_pr = None; ex_bar = None; R = 0
    for k in range(len(fwd_h)):
        bar_idx = eb + 1 + k
        if bar_idx >= n: break
        # SL check (all modes)
        if fwd_h[k] >= sl:
            out = "SL"; ex_pr = sl; ex_bar = bar_idx; R = -1.0; exited = True; break
        # RB trailing
        if not tr_active and bear_trigger[bar_idx]:
            tr_active = True; anchor_high = high[bar_idx]
            trace.append(("TRIGGER", bar_idx, high[bar_idx], close[bar_idx]))
        if tr_active:
            if high[bar_idx] > anchor_high:
                anchor_high = high[bar_idx]
                trace.append(("RATCHET", bar_idx, high[bar_idx], close[bar_idx]))
            if fwd_h[k] >= anchor_high:
                out = "RAWTRL"; ex_pr = anchor_high; ex_bar = bar_idx
                R = (entry - anchor_high)/risk; exited = True; break
            prev_active = bear_active[bar_idx-1] if bar_idx-1 >= 0 else False
            cur_active = bear_active[bar_idx]
            if prev_active and not cur_active:
                exit_pr = min(fwd_l[k], close[bar_idx]) if close[bar_idx] < entry else entry
                out = "RAWBRK"; ex_pr = exit_pr; ex_bar = bar_idx
                R = (entry - exit_pr)/risk; exited = True; break
    if not exited:
        lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
        out = "EXP"; ex_pr = lastc; ex_bar = eb+len(fwd_h); R = (entry-lastc)/risk
    return {"inv": False, "sl": sl, "risk": risk, "out": out, "ex_pr": ex_pr,
            "ex_bar": ex_bar, "R": R, "bars": (ex_bar-eb), "trace": trace,
            "atr14": atr14, "apct": apct}

# ============================================================
# Pilih 5 entry DAILY paling recent
# ============================================================
sel = samples_all[-5:]
print("="*100)
print("STUDY RAWBRK — SETUP1 SHORT v2.b (Variant E / reset-only)")
print(f"Engine: sample_v2a (reset-only). Total sinyal v2.b (START=2021): {len(samples_all)}")
print(f"Ditampilkan: 5 entry DAILY paling RECENT")
print("="*100)

for idx, s in enumerate(sel, 1):
    eb = s["bar"]; entry = s["entry"]
    A = s["A"]; B = s["B"]; C = s["C"]
    fmb_b = s["fmb_b"]; pd_b = s["pd_b"]; xdn_b = s["xdn_b"]
    print("\n" + "="*100)
    print(f"TRADE #{idx}  |  ENTRY {df.index[eb].strftime('%Y-%m-%d')}  |  close = {entry:.2f}")
    print("="*100)

    # ---- FBF v11 BEAR WAVE ----
    print("\n  [FBF v11 BEAR WAVE]")
    print(f"    WAVE_STARTED: A={A[1]:.2f} @ {df.index[A[0]].strftime('%Y-%m-%d')}")
    print(f"                   B={B[1]:.2f} @ {df.index[B[0]].strftime('%Y-%m-%d')}")
    if C:
        print(f"    C_LOCKED:     C={C[1]:.2f} @ {df.index[C[0]].strftime('%Y-%m-%d')}  retrace={C[2]:.1f}%")
    else:
        print(f"    C_LOCKED:     BELUM (no-wait C — entry valid tanpa C)")
    ws_bar = A[0]
    fbf_events = []
    for i in range(ws_bar, eb+1):
        for e in ev_by_bar.get(i, []):
            if e["side"] == "bear":
                fbf_events.append((i, e["event"], e))
    if fbf_events:
        print(f"    FBF EVENT CHAIN (bar {ws_bar} → {eb}):")
        for bar_i, evt, evd in fbf_events:
            cv = evd.get('c_val'); c_val = f" C={cv:.0f}" if cv is not None else ""
            bv = evd.get('b_val'); b_val = f" B={bv:.0f}" if bv is not None else ""
            rp = evd.get('retrace_pct'); retr = f" ret={rp:.1f}%" if rp is not None else ""
            print(f"      bar {bar_i:>5} {df.index[bar_i].strftime('%Y-%m-%d'):>12}  {evt:28s}{c_val}{b_val}{retr}")
    else:
        print("    FBF: no events in window")

    # ---- SMI 3-STEP ----
    print("\n  [SMI 3-STEP]")
    print(f"    STEP1 FMB = bar {fmb_b} ({df.index[fmb_b].strftime('%Y-%m-%d')})  SMI={smi[fmb_b]:.1f} hist={smi_hist[fmb_b]:.1f} [{hist_state[fmb_b]}] ST={'DN' if st_trend[fmb_b]==-1 else 'UP'}")
    print(f"    STEP2 PD  = bar {pd_b} ({df.index[pd_b].strftime('%Y-%m-%d')})  SMI={smi[pd_b]:.1f} hist={smi_hist[pd_b]:.1f} [{hist_state[pd_b]}] ST={'DN' if st_trend[pd_b]==-1 else 'UP'}")
    if E["pd_ready"][pd_b]: flav="Siap Balik (hist melemah)"
    elif E["pd_dip"][pd_b]: flav="Dip Mungkin (hist naik)"
    else: flav="triggered"
    print(f"            flavour: {flav}")
    print(f"    STEP3 XDN = bar {xdn_b} ({df.index[xdn_b].strftime('%Y-%m-%d')})  ← ENTRY  SMI={smi[xdn_b]:.1f} hist={smi_hist[xdn_b]:.1f} [{hist_state[xdn_b]}] ST={'DN' if st_trend[xdn_b]==-1 else 'UP'}")

    # ---- RAWBRK MECHANIC ----
    print("\n  [RAWBRK MECHANIC — fbf_v610 pivot, atr_mult=0.15]")
    pre_active = bear_active[eb] if eb < n else False
    # quantify pre-entry break state
    if eb > 0:
        look = 0
        for j in range(eb-1, max(-1, eb-60), -1):
            if bear_active[j]:
                look += 1
            else:
                break
    else:
        look = 0
    print(f"    Pre-entry: bear_active@{eb-1}? {'YA' if (bear_active[eb-1] if eb>0 else False) else 'TIDAK'}  (break berlangsung {look} bar sebelum entry)")
    # run sim to get trace + exit
    sim = simulate_rb(s, "O3")  # pakai O3 sbg repr utk trace (RAWBRK exit tdk bergantung SL)
    if sim["inv"]:
        print("    INV (SL invalid)")
    else:
        print(f"    ATR14={sim['atr14']:.2f}  ATR%={sim['apct']:.2f}%  (syarat trigger: close < PL terakhir, jarak >= 0.15*ATR14 = {0.15*sim['atr14']:.2f})")
        # locate the trigger
        if sim["trace"]:
            trig = [t for t in sim["trace"] if t[0]=="TRIGGER"]
            if trig:
                tbar, th, tc = trig[0][1], trig[0][2], trig[0][3]
                print(f"    TRIGGER (bear_active False→True) = bar {tbar} ({df.index[tbar].strftime('%Y-%m-%d')})  close={tc:.2f}  high(anchor awal)={th:.2f}")
            rats = [t for t in sim["trace"] if t[0]=="RATCHET"]
            if rats:
                print(f"    TRAILING RATCHET (anchor naik) di {len(rats)} bar:")
                for t in rats:
                    print(f"        bar {t[1]} ({df.index[t[1]].strftime('%Y-%m-%d')})  anchor_high={t[2]:.2f}  close={t[3]:.2f}")
        exb = sim["ex_bar"]
        print(f"    EXIT: {sim['out']} @ bar {exb} ({df.index[exb].strftime('%Y-%m-%d')})  price={sim['ex_pr']:.2f}  R(O3)={sim['R']:+.2f}  bars={sim['bars']}")

        # ---- BREAK ATTEMPT: di forward window, bar mana harga nyaris break PL ----
        fwd_end = min(n, eb+241)
        first_break_attempt = None
        best_attempt = None  # (bar, dist_ratio, pl_val, close_val)
        lowest_fwd = None; lowest_fwd_bar = None
        for i in range(eb+1, fwd_end):
            rpl = running_last_pl[i]
            if np.isnan(rpl):
                continue
            c = close[i]
            if lowest_fwd is None or low[i] < lowest_fwd:
                lowest_fwd = low[i]; lowest_fwd_bar = i
            if c < rpl:  # raw break attempt (turun di bawah PL)
                if first_break_attempt is None:
                    first_break_attempt = (i, c, rpl)
                dist_ratio = (rpl - c) / atr_arr[i] if atr_arr[i] > 0 else 0
                if best_attempt is None or dist_ratio > best_attempt[1]:
                    best_attempt = (i, dist_ratio, rpl, c)
        print(f"    BREAK-ATTEMPT (forward window):")
        if first_break_attempt is None:
            print(f"      TIDAK ADA bar di mana close < PL terakhir → RAWBRK state TIDAK PERNAH aktif (trigger gak nyala).")
            if lowest_fwd is not None:
                print(f"      Lowest forward low = {lowest_fwd:.2f} @ bar {lowest_fwd_bar} ({df.index[lowest_fwd_bar].strftime('%Y-%m-%d')})  (vs entry {entry:.2f})")
            else:
                print(f"      (tidak ada PL valid di forward window)")
        else:
            fb, fc, fpl = first_break_attempt
            print(f"      Pertama kali close<PL: bar {fb} ({df.index[fb].strftime('%Y-%m-%d')})  close={fc:.2f}  PL={fpl:.2f}")
            if best_attempt:
                bb, br, bpl, bc = best_attempt
                print(f"      Break terdalam: bar {bb} ({df.index[bb].strftime('%Y-%m-%d')})  close={bc:.2f}  jarak/ATR={br:.3f}  (butuh >=0.15 utk trigger)")
                if br < 0.15:
                    print(f"      → jarak {br:.3f} < 0.15 → TIDAK cukup → RAWBRK gak ke-trigger. Harga naik balik.")
        print(f"    >> KESIMPULAN RAWBRK utk trade ini: {'TRIGGER NYALA → trailing jalan' if sim['trace'] else 'TRIGGER TIDAK NYALA → exit jatuh ke '+sim['out']}")

# ============================================================
# COMBO TABLES
# ============================================================
print("\n\n" + "#"*100)
print("# COMBO: SL x RAWBRK (MODE C: SL + trailing RawBreak ONLY, no TP target)")
print("#"*100)

def fmt_r(x): return f"{x:+.2f}"

# Table 1: 3 SL x RAWBRK
print("\n--- TABEL 1: 3 SL (O1 Liq10x / O3 ATR%30 / O5 ConfHi+ATR) x RAWBRK ---")
hdr = f"  {'#':>2} {'ENTRY':>12} {'entry':>10} | {'SL':>4} {'SL$':>10} | {'OUT':>7} {'exit$':>10} {'bars':>5} | {'R_O1':>6} {'R_O3':>6} {'R_O5':>6}"
print(hdr); print("  " + "-"*len(hdr))
for idx, s in enumerate(sel, 1):
    eb = s["bar"]; entry = s["entry"]
    res = {}
    for opt in ["O1","O3","O5"]:
        res[opt] = simulate_rb(s, opt)
    r1 = res["O1"]; r3 = res["O3"]; r5 = res["O5"]
    if r3["inv"]:
        continue
    sl3 = r3["sl"]
    row = (f"  {idx:>2} {df.index[eb].strftime('%Y-%m-%d'):>12} {entry:>10.2f} | "
           f"{'O3':>4} {sl3:>10.2f} | "
           f"{r3['out']:>7} {r3['ex_pr']:>10.2f} {r3['bars']:>5} | "
           f"{fmt_r(r1['R']):>6} {fmt_r(r3['R']):>6} {fmt_r(r5['R']):>6}")
    print(row)
print("  (R = (entry - exit)/risk, risk = SL - entry; RAWBRK exit sama utk ke-3 SL,")
print("   beda cuma di risk & kemungkinan SL kecekik duluan)")

# Table 2: 5 SL x RAWBRK
print("\n--- TABEL 2: 5 SL (O1-O5) x RAWBRK ---")
hdr2 = f"  {'#':>2} {'ENTRY':>12} | {'O1':>6} {'O2':>6} {'O3':>6} {'O4':>6} {'O5':>6} | OUT@O3"
print(hdr2); print("  " + "-"*len(hdr2))
for idx, s in enumerate(sel, 1):
    eb = s["bar"]; entry = s["entry"]
    rs = {opt: simulate_rb(s, opt) for opt in ["O1","O2","O3","O4","O5"]}
    if rs["O3"]["inv"]:
        continue
    rr = " ".join([f"{fmt_r(rs[o]['R']):>6}" for o in ["O1","O2","O3","O4","O5"]])
    print(f"  {idx:>2} {df.index[eb].strftime('%Y-%m-%d'):>12} | {rr} | {rs['O3']['out']}")
print("\nKeterangan OUT (RAWBRK exit type):")
print("  RAWTRL  = trailing kena: high bar tembus anchor_high (high tertinggi sejak trigger)")
print("  RAWBRK  = break LOST: bear_active active→inactive (harga naik balik di atas pivot low)")
print("  SL      = stop-loss kena duluan sblm RB trigger/exit")
print("  EXP     = max 240 bar, msh open")
print("\nSELESAI")
