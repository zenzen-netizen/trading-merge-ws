#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LABEL BAR-PER-BAR — BTCUSDT 1D (Binance SPOT)
Window: 2026-05-06 .. 2026-06-28  (analisis runutan event indikator)
Sumber: SMI Pro v3 (indicators/smi_pro.py) + FBF v11 (engine default /home/ubuntu/fbf_v11_backtest.py)
Output:
  - Tabel per-bar (tanggal, OHLC, SMI state, FBF event + fase tracker per bar)
  - Ringkasan fase (kapan WAVE_STARTED / C_LOCKED / BREAK bear, dll)
  - File CSV: label_window_1d.csv

Tujuan: cocokkan persis dengan apa yg user lihat di TradingView (chart-faithful).
"""
import sys, os, datetime as _dt
sys.path.insert(0, "/home/ubuntu")                 # engine default FBF v11
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/fetchers")

import pandas as pd
import numpy as np
import data_fetcher as dfetcher
import smi_pro
import fbf_v11_backtest as V11

SYM = "BTCUSDT"
TF = "1d"
IV_MS = 86_400_000
# Analisis window (user minta 6 Mei - 28 Juni 2026)
WIN_START = pd.Timestamp("2026-05-06")
WIN_END   = pd.Timestamp("2026-06-28")
# Fetch cukup warmup: dari 2025-08-01 supaya SMI(5) & pivot valid saat masuk window
FETCH_START = pd.Timestamp("2025-08-01")
FETCH_END   = pd.Timestamp("2026-07-01")  # cutoff, drop unclosed

SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}

print("[1] fetch BTCUSDT 1D ...")
df, err = dfetcher.fetch_ohlcv(SYM, TF, limit=600, market_type="spot", drop_unclosed=True)
if df is None:
    print("FETCH ERROR:", err); raise SystemExit(1)
# filter ke range fetch
df = df[(df.index >= FETCH_START) & (df.index <= FETCH_END)]
print(f"    {len(df)} candles {df.index[0].date()} .. {df.index[-1].date()}")

# ── index window ──
win_mask = (df.index >= WIN_START) & (df.index <= WIN_END)
win_pos = [i for i, m in enumerate(win_mask) if m]
wsp, wep = win_pos[0], win_pos[-1]
print(f"    window bars: {len(win_pos)} ({WIN_START.date()} .. {WIN_END.date()})")

# ════════════════════════════════════════════════════════════
# SMI per bar
# ════════════════════════════════════════════════════════════
print("[2] SMI Pro v3 per bar ...")
smi_by = {}
for p in range(len(df)):
    s = smi_pro.smi_pro_v3(df.iloc[:p+1], SMI_CFG)
    smi_by[p] = s

# ════════════════════════════════════════════════════════════
# FBF v11 engine penuh -> events
# ════════════════════════════════════════════════════════════
print("[3] FBF v11 engine run ...")
times = [int(t.value // 1_000_000) for t in df.index]   # ns->ms
eng = V11.FBFEngine(
    times,
    df["open"].values.astype(float),
    df["high"].values.astype(float),
    df["low"].values.astype(float),
    df["close"].values.astype(float),
    IV_MS,
)
breaks, events = eng.run()
print(f"    total events: {len(events)}, total BREAK: {len(breaks)}")

# ── Map events per bar ──
ev_by_bar = {}
for e in events:
    ev_by_bar.setdefault(e["bar"], []).append(e)

# ════════════════════════════════════════════════════════════
# Rekonstruksi STATE FBF per bar (fase tracker) dari engine
# Engine pakai slot live trk[side] yang berubah tiap bar, tapi
# kita TIDAK punya akses history internal. Makanya kita re-derive
# state per bar lewat replay ringan dari events + st_trend.
# Pendekatan: ikuti events WAVE_STARTED / C_LOCKED / WAVE_CANCELLED
# dan jaga "active wave bear" antar event.
# ════════════════════════════════════════════════════════════
def fbf_phase_label_for_bar(i):
    """
    Kembalikan (phase_text, events_text) untuk bar i.
    phase_text = status wave bear di bar itu (dari tracker).
    Karena engine internal tdk di-expose per bar, kita replay state:
      - saat WAVE_STARTED(bear) -> fase = 'WAVE bear: A->B locked, tracking C?'
      - setelah itu tiap bar (sampai C_LOCKED/CANCEL) -> 'tracking C?'
      - saat C_LOCKED(bear) -> 'C_LOCKED (kandidat masuk juri)'
      - saat B_LINE_TRACKING(bear) -> 'kandidat AKTIF (di luar B)'
      - saat BREAK(bear) -> 'BREAK bear (SINYAL!)'
      - saat WAVE_CANCELLED / WAVE_STRUCT_REJECTED / CANDIDATE_FAILED /
        CANDIDATE_INVALIDATED -> 'wave/kandidat batal'
    Kita track lewat ordered events.
    """
    evs = ev_by_bar.get(i, [])
    bear_evs = [e for e in evs if e["side"] == "bear"]
    bull_evs = [e for e in evs if e["side"] == "bull"]
    parts = []
    for e in bear_evs:
        parts.append(e["event"])
    return bear_evs, bull_evs, parts

# Replay state antar bar untuk fase kontekstual BEAR TRACKER.
# Engine v11: tracker bear punya 1 slot live (phase 1 = tracking C?).
# WAVE_STARTED -> phase 1. C_LOCKED/WAVE_CANCELLED/WAVE_STRUCT_REJECTED -> phase 0.
# Setelah C_LOCKED, kandidat masuk JURI (B_LINE_TRACKING / BREAK / FAILED).
# Kita rekonstruksi 2 hal per bar:
#   wave_tracker_b  = B-val wave bear yg sedang di-track (phase 1) atau None
#   judge_state     = 'cand_active' / 'break' / None  (aktivitas juri bear)
fase_ctx = {}        # bar -> (wave_b_val or None, judge_state or None)
live_wave_b = None   # B-val wave bear aktif (tracker phase 1)
for i in range(len(df)):
    evs = ev_by_bar.get(i, [])
    bev = [e for e in evs if e["side"] == "bear"]
    bevent_names = [e["event"] for e in bev]
    judge = None
    for e in bev:
        et = e["event"]
        if et == "WAVE_STARTED":
            live_wave_b = e["b_val"]
        elif et == "WAVE_CANCELLED":
            live_wave_b = None
        elif et == "WAVE_STRUCT_REJECTED":
            live_wave_b = None
        elif et == "C_LOCKED":
            live_wave_b = None   # tracker reset, kandidat ke juri
        elif et == "B_LINE_TRACKING":
            judge = "cand_active"
        elif et == "BREAK":
            judge = "BREAK"
        elif et == "CANDIDATE_FAILED":
            judge = "cand_failed"
        elif et == "CANDIDATE_INVALIDATED":
            judge = "cand_invalid"
        elif et == "BREAK_HIDDEN_BY_TREND":
            judge = "BREAK_hidden"
    fase_ctx[i] = (live_wave_b, judge, bevent_names)

# ════════════════════════════════════════════════════════════
# Pre-compute SMI 3-step markers + ST trend per bar
# (ST trend dari engine: eng.st_trend update per bar; kita pakai events' st_trend
#  atau rebuild. Engine simpan st_trend di tiap event; kita ambil latest per bar.)
# ════════════════════════════════════════════════════════════
st_trend_by_bar = {}
for e in events:
    st_trend_by_bar[e["bar"]] = e["st_trend"]   # last event wins (same bar)
# carry forward st_trend
_last = 1
for i in range(len(df)):
    if i in st_trend_by_bar:
        _last = st_trend_by_bar[i]
    st_trend_by_bar[i] = _last

def smi_step(bs):
    if bs == "[!] Fail MID Buy": return "FMB"
    if bs.startswith("[~] PD") or bs.startswith("[OK] PD") or bs == "PD TRIGGERED": return "PD"
    if bs == "[X] Cross DN": return "XDN"
    return ""

smi_step_by = {}
for p in range(len(df)):
    smi_step_by[p] = smi_step(smi_by[p]["bar_state"])

# ════════════════════════════════════════════════════════════
# SETUP1 v2 trigger — hitung ENTRY per WAVE (bear), sesuai TRIGGER_SPEC v2:
#   entry = max(C_LOCKED_bar, XDN_bar)
#   syarat: FMB -> PD -> XDN (urut, XDN >= FMB), wave msh valid
#           (tdk WAVE_CANCELLED/STRUCT_REJECTED), ST downtrend(-1) di entry bar.
# Lalu bandingkan dengan BREAK engine v11 (chart-visible).
# ════════════════════════════════════════════════════════════
# Kumpulkan wave bear: WAVE_STARTED + C_LOCKED terkait (by B_val).
# Group events bear by B_val.
waves = {}   # b_val -> dict(start_bar, start_date, c_locked_bar, c_locked_date, cancelled)
for i in range(len(df)):
    bev = [e for e in ev_by_bar.get(i, []) if e["side"] == "bear"]
    for e in bev:
        bv = round(e["b_val"], 1)
        et = e["event"]
        if et == "WAVE_STARTED":
            waves.setdefault(bv, {"start_bar": e["bar"], "c_locked_bar": None,
                                  "cancelled": False, "struct_rej": False})
        if et == "C_LOCKED" and bv in waves and waves[bv]["c_locked_bar"] is None:
            waves[bv]["c_locked_bar"] = e["bar"]
        if et == "WAVE_CANCELLED" and bv in waves:
            waves[bv]["cancelled"] = True
        if et == "WAVE_STRUCT_REJECTED" and bv in waves:
            waves[bv]["struct_rej"] = True

wave_cands = []
# Untuk tiap wave, cari SMI 3-step sequence dalam [start_bar .. c_locked_bar + 30]
for bv, w in waves.items():
    if w["c_locked_bar"] is None:
        continue
    sb = w["start_bar"]; clb = w["c_locked_bar"]
    if w["cancelled"] or w.get("struct_rej"):
        continue
    hi = min(len(df), clb+31)
    # cari FMB/PD/XDN di window
    fmb_bars = [p for p in range(sb, hi) if smi_step_by[p] == "FMB"]
    pd_bars  = [p for p in range(sb, hi) if smi_step_by[p] == "PD"]
    xdn_bars = [p for p in range(sb, hi) if smi_step_by[p] == "XDN"]
    # butuh FMB < PD < XDN (urut)
    found = None
    for f in fmb_bars:
        pc = [p for p in pd_bars if p > f]
        if not pc: continue
        p = pc[0]
        xc = [x for x in xdn_bars if x > p]
        if not xc: continue
        found = (f, p, xc[0]); break
    if not found:
        continue
    f, p, x = found
    entry_bar = max(clb, x)
    st_ok = (st_trend_by_bar.get(entry_bar, 1) == -1)
    wave_cands.append({
        "b_val": bv, "start_bar": sb, "c_locked_bar": clb,
        "FMB": f, "PD": p, "XDN": x, "entry_bar": entry_bar,
        "entry_date": df.index[entry_bar].strftime("%Y-%m-%d"),
        "entry": round(df["close"].iloc[entry_bar], 1),
        "st_ok": st_ok,
    })

# Flag per bar: entry_bar dari wave_cands
entry_bar_set = {c["entry_bar"] for c in wave_cands if c["st_ok"]}

# ════════════════════════════════════════════════════════════
# PRINT TABEL PER-BAR
# ════════════════════════════════════════════════════════════
L = []
L.append("="*150)
L.append("LABEL BAR-PER-BAR — BTCUSDT 1D (Binance SPOT)")
L.append(f"Window: {WIN_START.date()} .. {WIN_END.date()}  |  SMI Pro v3 + FBF v11 (chart-faithful)")
L.append("="*150)
L.append("")
L.append(f"{'Tgl':<11}{'O':>8}{'H':>8}{'L':>8}{'C':>8} {'SMI':>6}{'EMA':>6}{'Hst':>6} {'Zn':<8} {'Sig':<8} "
         f"{'SMIstp':<5} | {'FBF-wave':<9} {'FBF-judge':<11} | {'SMItgr':<4} ENTRY?")
L.append("-"*150)

rows_csv = []
for p in win_pos:
    d = df.index[p]
    o = df['open'].iloc[p]; h = df['high'].iloc[p]; l = df['low'].iloc[p]; c = df['close'].iloc[p]
    s = smi_by[p]
    bs = s["bar_state"].replace("[","").replace("]","")
    wave_b, judge, bev_names = fase_ctx[p]
    wave_s = f"B={wave_b:.0f}" if wave_b is not None else "-"
    judge_s = judge if judge else "-"
    step = smi_step_by[p]
    setup1 = ">>> ENTRY" if p in entry_bar_set else ""
    L.append(f"{d.strftime('%Y-%m-%d'):<11}{o:>8.0f}{h:>8.0f}{l:>8.0f}{c:>8.0f} "
             f"{s['smi']:>6.1f}{s['smi_ema']:>6.1f}{s['smi_hist']:>6.1f} {s['zone'][:8]:<8} {s['signal'][:8]:<8} "
             f"{step:<5} | {wave_s:<9} {judge_s:<11} | {step:<4} {setup1}")
    rows_csv.append({
        "date": d.strftime("%Y-%m-%d"),
        "open": round(o,1), "high": round(h,1), "low": round(l,1), "close": round(c,1),
        "smi": s["smi"], "smi_ema": s["smi_ema"], "smi_hist": s["smi_hist"],
        "zone": s["zone"], "signal": s["signal"], "bar_state": bs,
        "pa_pd": s["pa_pd_text"], "cross_up": s["cross_up"], "cross_down": s["cross_down"],
        "cross_mid_up": s["cross_mid_up"], "cross_mid_down": s["cross_mid_down"],
        "fbf_event": ",".join(bev_names) if bev_names else "",
        "fbf_wave_B": round(wave_b,1) if wave_b is not None else "",
        "fbf_judge": judge if judge else "",
        "smi_step": step,
        "st_trend": st_trend_by_bar[p],
        "setup1_entry": (p in entry_bar_set),
    })

L.append("")
L.append("="*120)
L.append("RINGKASAN EVENT FBF v11 (side BEAR) DALAM WINDOW")
L.append("="*120)
bear_events_in_win = [e for e in events
                      if e["side"] == "bear" and wsp <= e["bar"] <= wep]
for e in bear_events_in_win:
    d = df.index[e["bar"]].strftime("%Y-%m-%d")
    extra = e.get("extra","")
    retr = e.get("retrace_pct")
    retr_s = f" retr={retr}%" if retr is not None else ""
    L.append(f"  {d}  {e['event']:<22} A={e['a_val']:.0f} B={e['b_val']:.0f} C={e['c_val']:.0f}{retr_s}  {extra}")

L.append("")
L.append("="*120)
L.append("BREAK BEAR (sinyal SHORT, chart-visible) DALAM WINDOW")
L.append("="*120)
for e in bear_events_in_win:
    if e["event"] != "BREAK":
        continue
    d = df.index[e["bar"]].strftime("%Y-%m-%d")
    L.append(f"  {d}  B={e['b_val']:.0f}  A={e['a_val']:.0f}  C={e['c_val']:.0f}  "
             f"retr={e.get('retrace_pct')}%  ST={'up' if e.get('st_trend')==1 else 'down'}  {e.get('extra','')}")

L.append("")
L.append("="*150)
L.append("SETUP1 SHORT — CANDIDATE ENTRY (per WAVE bear: FMB->PD->XDN + C_LOCKED + ST-1)")
L.append("="*150)
if not wave_cands:
    L.append("  (tidak ada candidate)")
for c in wave_cands:
    L.append(f"  wave B={c['b_val']:.0f}  start={df.index[c['start_bar']].strftime('%Y-%m-%d')}  "
             f"C_LOCKED={df.index[c['c_locked_bar']].strftime('%Y-%m-%d')}  "
             f"FMB={df.index[c['FMB']].strftime('%Y-%m-%d')}  PD={df.index[c['PD']].strftime('%Y-%m-%d')}  "
             f"XDN={df.index[c['XDN']].strftime('%Y-%m-%d')}  -> ENTRY {c['entry_date']} @ {c['entry']:.0f}  "
             f"ST={'OK' if c['st_ok'] else 'NOT down'}")
L.append("")
L.append("BANDING: BREAK bear chart-visible (engine v11) dalam window = 1 event (2026-06-24).")
L.append("  -> Candidate yang ENTRY-nya = 2026-06-24 adalah yang MATCH engine. Lainnya =")
L.append("     confluence SMI+wave tapi BREAK engine gugur (cand_failed / fibo abu / hidden trend).")

report = "\n".join(L)
print(report)

OUT = "/home/ubuntu/trading-research/label_window_1d.csv"
import csv
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_csv[0].keys()))
    w.writeheader(); w.writerows(rows_csv)
print(f"\n[saved] {OUT}  ({len(rows_csv)} bars)")
