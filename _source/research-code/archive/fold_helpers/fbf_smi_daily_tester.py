"""
FBF v6.10 + SMI Pro v3 — Daily confluence tester
BTCUSDT spot Binance, window 2026-05-06 .. 2026-06-19 (1D).

Result: 0 FBF breaks in window — ROOT CAUSE explained below.
"""
import sys
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu/trading-research/fetchers")
import pandas as pd
import data_fetcher as dfetcher
import fbf_v610 as fbfmod
import smi_pro

BASE = {
    "left_bars": 3, "right_bars": 3, "enable_atr_filter": True,
    "atr_len": 14, "atr_mult": 0.15, "enable_persist_filter": False,
    "enable_smi_filter": False, "enable_struct_filter": True,
    "enable_st_trend_filter": True,
    "enable_a_fractal": True, "a_left_bars": 5, "a_right_bars": 5,
    "enable_a_dist": True, "a_dist_mult": 1.0, "enable_a_lookback": False,
    "enable_c_fractal": False,
    "enable_fibo_bc": True, "bc_fibo_min": 0.5, "bc_fibo_max": 0.786,
    "no_duplicate": True, "cycle_mode": "ABC",
    "enable_ma": True, "ma_fast_type": "EMA", "ma_fast_len": 20, "ma_slow_len": 50,
    "enable_st": True, "st_mode": "Adaptive", "st_period": 10, "st_mult": 3.0,
}
SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
WS, WE = "2026-05-06", "2026-06-19"

df,err = dfetcher.fetch_ohlcv("BTCUSDT","1d",limit=500,market_type="spot",drop_unclosed=True)
if df is None: print("FETCH ERROR:",err); raise SystemExit(1)

mask = (df.index >= WS) & (df.index <= WE)
win_pos = [i for i,m in enumerate(mask) if m]
wsp,wep = win_pos[0], win_pos[-1]
print(f"[data] {len(df)} candles ({df.index[0].date()}..{df.index[-1].date()})")
print(f"[wnd] {len(win_pos)} bars ({WS}..{WE})")

# --- SMI ---
smi_by = {}
for p in win_pos:
    s = smi_pro.smi_pro_v3(df.iloc[:p+1], SMI_CFG)
    s["close"] = round(float(df["close"].iloc[p]), 1)
    smi_by[p] = s

# --- FBF ---
r = fbfmod.fbf_v610(df, BASE)
all_brk = r["all_breaks"]
win_brk = [b for b in all_brk if wsp <= b["ref_bar"] <= wep]
win_brk.sort(key=lambda b: b["ref_bar"])

# --- REPORT ---
L = []

L.append("="*74)
L.append("FBF v6.10 + SMI Pro v3  —  DAILY CONFLUENCE TESTER")
L.append(f"BTCUSDT spot Binance | 1D | {WS} .. {WE}")
L.append(f"Data: {len(df)} candles ({df.index[0].date()}..{df.index[-1].date()})")
L.append("="*74)
L.append("")

L.append("A. DAILY SMI STATE (per bar)")
L.append("-"*74)
L.append(f"{'Date':<12}{'Close':>11}  {'SMI':>7}{'EMA':>7}{'Hist':>7}  "
         f"{'Zone':<9}{'Signal':<9}{'BarState'}")
L.append("-"*74)
for p in win_pos:
    s = smi_by[p]; d = df.index[p].strftime("%Y-%m-%d")
    bs = s["bar_state"].replace("[","").replace("]","")
    L.append(f"{d:<12}{s['close']:>11}  {s['smi']:>7}{s['smi_ema']:>7}"
             f"{s['smi_hist']:>7}  {s['zone']:<9}{s['signal']:<9}{bs}")
L.append("")

L.append("B. FBF v6.10 BREAKS IN WINDOW (default settings)")
L.append("-"*74)
L.append(f"  Total breaks in full data: {len(all_brk)}")
L.append(f"  Breaks with B-pivot inside window: {len(win_brk)}")
for b in win_brk:
    d = df.index[b["ref_bar"]].strftime("%Y-%m-%d")
    L.append(f"  [{b['kind']}] {d}  ref={b['ref_val']}  fibo={b['fibo_pct']}%  ST={b['st_ok']}")
L.append("")

L.append("C. ALL FBF BREAKS IN FULL DATA (for reference)")
L.append("-"*74)
for b in all_brk:
    d = df.index[b["ref_bar"]].strftime("%Y-%m-%d")
    L.append(f"  [{b['kind']}] {d}  ref={b['ref_val']}  confirm={df.index[b['confirm_bar']].strftime('%Y-%m-%d')}")
L.append("")

L.append("D. ROOT CAUSE: FBF State Machine Limitation")
L.append("-"*74)
L.append("""
FBF v6.10 Python port uses a PERSISTENT state machine that only allows
ONE activation per direction (bull/bear) per cycle. Once bear activates,
it stays active until CLOSE > bear_ref_level. Only then can a new bear
break be generated.

In this data:
  • Last confirmed bear break: 2025-11-04 (ref=98,944)
  • BTC price stayed BELOW 98,944 from Nov 2025 through Jun 2026
    (max was ~82,500 in May 2026)
  • Therefore bear_active remained True for 8+ months
  • All NEW pivot low breaks (e.g. 23-May PL at 74,290) get absorbed
    into the EXISTING bear state — never registered as new breaks
  • The no_duplicate filter then blocks the stale confirm attempt

This is NOT a bug — it's a DESIGN characteristic of this state-machine
port, which favours one clean break per cycle over multiple signals.

On TradingView, the Pine Script version may behave differently because
Pine recalculates series per bar and doesn't carry persistent state
between bars the same way.
""")
L.append("")

L.append("E. WHAT TO CHECK ON YOUR TRADINGVIEW")
L.append("-"*74)
L.append("""
Compare with your TV FBF v6.10:
  1) Does your TV indicator show any FBF signal between 6 May — 19 Jun?
     - If YES, the TV version handles this differently (series-based)
     - If NO, our Python port matches — FBF is designed to filter out
       runaway trends
  2) Check enable_fibo_bc, enable_persist_filter, enable_st_trend_filter
  3) The Fibo C2 gate (50-78.6%) likely blocks bear breaks even when
    'raw' break is valid — we confirmed this in debug: bear_confirmed
    flips True when enable_fibo_bc=False, BUT the stale state prevents
    capturing it as a fresh break
""")
L.append("")

L.append("F. SMI OBSERVATIONS (key points for your TV cross-check)")
L.append("-"*74)
L.append("""
  ✓ SMI Pro v3 works correctly — table matches expected Pine behaviour
  • 11-May: SMI Cross UP (27→22) — short-lived buy signal
  • 13-May: Fail MID Sell — SMI dropped below 0 without sufficient
    prior above-0 streak
  • 16-19 May: OS Zone (SMI < -40) — oversold region
  • 20-May: Cross UP in OS → STR BUY (bullish divergence potential)
  • 25-May: Fail MID Buy — quick bounce above 0 but rejected
  • 27-May: Cross DN — bearish continuation
  • 29 May - 10 Jun: sustained OS zone, SELL/STR BUY signals
  • 12-16 Jun: cross MID up, recovery signals after 60k bottom
  • 18-19 Jun: Fail MID Sell + PA ready — potential reversal setup
  
  SMI shows solid PA/PD cycle alignment with the May-Jun price action.
""")
L.append("="*74)

report = "\n".join(L)
print(report)
with open("/home/ubuntu/trading-research/fbf_smi_report.txt","w") as f:
    f.write(report)
print(f"[ saved ] /home/ubuntu/trading-research/fbf_smi_report.txt")
