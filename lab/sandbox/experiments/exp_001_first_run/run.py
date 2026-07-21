"""
Exp 001 — Demo: SMI CrossDown Entry (Short) + Fixed SL/TP

Pakai BTCUSDT 1D data dari trading-research.
Sinyal entry: SMI cross_down (XDN) dengan zone Upper atau Mid.
SL: fixed 6%, TP: 2x risk (12%).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../indicators/python"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../backtest_engine"))

import pandas as pd
import numpy as np
from typing import Dict

from indicators.python.smi_events import compute_smi_events
from backtest_engine.engine import run_backtest


# ── Load data ────────────────────────────────────
DATA = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D/data_BTCUSDT_1d_2021now.csv"
df = pd.read_csv(DATA, index_col=0, parse_dates=True)
print(f"Data loaded: {len(df)} bars, {df.index[0]} → {df.index[-1]}")

# ── Compute SMI events ───────────────────────────
cfg_smi = {
    "len_k": 5, "len_d": 3, "len_e": 3,
    "ob": 80, "os": -40, "mid": 0,
    "akum_candles": 2, "dist_candles": 2,
}
E = compute_smi_events(df, cfg_smi)
print(f"SMI events: {E['n']} bars computed")

# Gabungin kolom indikator ke df
for key in ["smi", "smi_ema", "smi_hist", "hist_state", "zone",
            "bar_state", "cross_up", "cross_down", "FMB", "PD", "XDN"]:
    df[key] = E[key]


# ── Strategy: Simple SMI CrossDown ───────────────
def entry_signal(df: pd.DataFrame, i: int) -> bool:
    """Entry short saat SMI cross_down di zone Upper/Mid."""
    if i <= 0 or pd.isna(df["cross_down"].iloc[i]):
        return False
    cross = df["cross_down"].iloc[i]
    zone = df["zone"].iloc[i] if "zone" in df.columns else "Unknown"
    return bool(cross) and zone in ("Upper", "Mid", "OB")


def exit_signal(df: pd.DataFrame, i: int, pos: Dict) -> bool:
    """No exit signal — rely on SL/TP only."""
    return False


def sl_price_fn(df: pd.DataFrame, i: int, entry_price: float) -> float:
    """Fixed 6% SL (short: di atas entry)."""
    return entry_price * 1.06


def tp_price_fn(df: pd.DataFrame, i: int, entry_price: float) -> float:
    """2x risk TP (12% di bawah entry)."""
    return entry_price * 0.88


# ── RUN ──────────────────────────────────────────
print("\nRunning backtest...")
result = run_backtest(
    df=df,
    entry_signal=entry_signal,
    exit_signal=exit_signal,
    sl_price_fn=sl_price_fn,
    tp_price_fn=tp_price_fn,
    risk_pct=1.0,
    initial_capital=10000.0,
    direction="short",
    fixed_fractional=True,
    max_bars=240,
    fee_pct=0.1,
    sl_first=True,
)

# ── RESULTS ──────────────────────────────────────
print("\n" + "=" * 55)
print("EXP 001 — SMI CrossDown Short Demo")
print("=" * 55)

m = result["metrics"]
s = result["summary"]

print(f"\n  Total trades     : {s['total_trades']}")
print(f"  Win rate         : {s['win_rate_pct']:.1f}%")
print(f"  Net profit       : {s['net_profit_pct']:.1f}%")
print(f"  Final capital    : ${s['final_capital']:,.0f}")
print(f"  EV per trade (R) : {s['ev_per_trade_r']:+.3f}R")
print(f"  Profit factor    : {s['profit_factor']:.2f}")
print(f"  Max drawdown     : {s['max_drawdown_pct']:.1f}%")

if m.get("sample_size_warning"):
    print(f"  ⚠  Sample < 30 — hasil sementara")

print(f"\n  Breakeven WR     : {m.get('breakeven_win_rate', 0)*100:.1f}%")
print(f"  WR vs BE gap     : {m.get('wr_vs_breakeven_gap', 0)*100:+.1f}%")
print(f"  Avg win          : ${m.get('avg_win', 0):,.0f}")
print(f"  Avg loss         : ${m.get('avg_loss', 0):,.0f}")
print(f"  Max consec loss  : {m.get('max_consecutive_losses', 0)}")
print(f"  Sharpe           : {m.get('sharpe_ratio', 0):.2f}")
print(f"  Edge ratio       : {m.get('edge_ratio', 0):.2f}")

if s["exit_reasons"]:
    print(f"\n  Exit reasons:")
    for reason, count in sorted(s["exit_reasons"].items()):
        print(f"    {reason}: {count}")

# Trade list
print(f"\n  Trade list ({len(result['trades'])} trades):")
print(f"  {'Entry':>12s}  {'Exit':>12s}  {'PnL':>8s}  R-Mult  Reason")
print(f"  {'-'*12}  {'-'*12}  {'-'*8}  {'-'*6}  {'-'*10}")
for t in result["trades"][:10]:
    reason = "SL" if t.pnl < 0 else "TP" if t.take_profit and abs(t.exit_price - t.take_profit) < t.entry_price*0.01 else "OTHER"
    rm = t.r_multiple
    print(f"  {t.entry_time[:10]:>12s}  {t.exit_time[:10]:>12s}  ${t.pnl:>7,.0f}  {rm:+5.2f}R  {reason}")
if len(result["trades"]) > 10:
    print(f"  ... + {len(result['trades'])-10} more trades")
