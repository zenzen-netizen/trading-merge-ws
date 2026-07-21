"""
Core Backtest Engine — loop bar-by-bar, entry/exit/MAE/MFE tracking.

Stage 4c implementation. Follows stage_04c_core_eksekusi_trade.md.
Generic: any strategy plugs in via entry_signal() / exit_signal() functions.

Key decisions (explicit):
  - SL/TP ambiguitas satu candle: SL diasumsikan kena duluan (konservatif)
  - Posisi sizing: fixed fractional (risk % dari modal awal)
  - Entry price: open candle SETELAH candle sinyal (bukan close candle sinyal)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Tuple
import numpy as np
import pandas as pd

# Import Trade + EquityPoint from metrics.py (single source of truth)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from metrics import Trade, EquityPoint, calculate_all_metrics


def run_backtest(
    df: pd.DataFrame,
    entry_signal: Callable[[pd.DataFrame, int], bool],
    exit_signal: Callable[[pd.DataFrame, int, Dict], bool],
    sl_price_fn: Callable[[pd.DataFrame, int, float], float],
    tp_price_fn: Optional[Callable[[pd.DataFrame, int, float], float]] = None,
    risk_pct: float = 1.0,
    initial_capital: float = 10000.0,
    direction: str = "short",
    fixed_fractional: bool = True,
    max_bars: int = 240,
    fee_pct: float = 0.0,
    sl_first: bool = True,
) -> Dict:
    """
    Run backtest engine.

    Args:
        df: OHLCV DataFrame (index = datetime). Must have: open, high, low, close.
            Plus any indicator columns needed by signal functions.
        entry_signal(df, i) -> bool: True jika ada sinyal entry di bar i.
            NOTE: entry terjadi di open bar i+1 (setelah sinyal confirmed).
        exit_signal(df, i, position) -> bool: True jika sinyal exit di bar i.
        sl_price_fn(df, i, entry_price) -> float: harga stop loss.
        tp_price_fn(df, i, entry_price) -> float | None: harga take profit.
        risk_pct: % risk per trade dari modal (default 1%).
        initial_capital: modal awal.
        direction: "long" atau "short".
        fixed_fractional: True = risk dari modal awal tetap. False = compounding.
        max_bars: max bar posisi dibiarkan hidup (EXP setelah ini).
        fee_pct: fee round-trip dalam % (mis. 0.1 untuk spot).
        sl_first: True = SL diasumsikan kena duluan kalau SL+TP satu candle.

    Returns:
        dict with keys: trades, equity_curve, metrics, summary
    """
    n = len(df)
    capital = initial_capital
    trades: List[Trade] = []
    equity_curve: List[EquityPoint] = []

    # State
    in_position = False
    pos: Dict = {}  # current position state

    # Warmup: cari bar pertama dengan data valid (bukan NaN close)
    first_valid = 0
    for i in range(n):
        if not pd.isna(df["close"].iloc[i]) and df["close"].iloc[i] > 0:
            first_valid = i
            break

    for i in range(first_valid, n - 1):  # -1 karena entry di i+1
        close_i = df["close"].iloc[i]
        high_i = df["high"].iloc[i]
        low_i = df["low"].iloc[i]

        if pd.isna(close_i) or close_i <= 0:
            continue

        # Record equity point
        equity_curve.append(EquityPoint(
            timestamp=str(df.index[i]),
            equity=capital,
        ))

        if not in_position:
            # ── Cek sinyal entry ──
            if entry_signal(df, i):
                # Entry di open candle i+1
                if i + 1 >= n:
                    continue
                entry_price = df["open"].iloc[i + 1]
                if pd.isna(entry_price) or entry_price <= 0:
                    continue

                sl = sl_price_fn(df, i, entry_price)
                tp = tp_price_fn(df, i, entry_price) if tp_price_fn else None

                if direction == "short":
                    if sl <= entry_price:
                        continue  # SL invalid untuk short (harus di atas entry)
                    size_r = abs(sl - entry_price)
                    risk_amount = (risk_pct / 100) * (initial_capital if fixed_fractional else capital)
                    size = risk_amount / size_r if size_r > 0 else 0
                else:  # long
                    if sl >= entry_price:
                        continue  # SL invalid untuk long (harus di bawah entry)
                    size_r = abs(entry_price - sl)
                    risk_amount = (risk_pct / 100) * (initial_capital if fixed_fractional else capital)
                    size = risk_amount / size_r if size_r > 0 else 0

                if size <= 0:
                    continue

                in_position = True
                pos = {
                    "entry_bar": i + 1,
                    "entry_price": entry_price,
                    "direction": direction,
                    "sl": sl,
                    "tp": tp,
                    "size": size,
                    "risk_amount": risk_amount,
                    "mae": 0.0,   # selisih harga (akan dikonversi ke $)
                    "mfe": 0.0,
                    "bars_held": 0,
                }

        else:
            # ── Dalam posisi: cek exit ──
            pos["bars_held"] += 1

            # Update MAE/MFE (dalam selisih harga)
            if direction == "short":
                mae_move = high_i - pos["entry_price"]   # harga naik = rugi untuk short
                mfe_move = pos["entry_price"] - low_i    # harga turun = untung
            else:
                mae_move = pos["entry_price"] - low_i    # harga turun = rugi untuk long
                mfe_move = high_i - pos["entry_price"]   # harga naik = untung

            pos["mae"] = max(pos["mae"], mae_move)
            pos["mfe"] = max(pos["mfe"], mfe_move)

            # Cek SL dan TP di candle ini
            sl_hit = False
            tp_hit = False
            exit_price = None
            exit_reason = ""

            if direction == "short":
                if high_i >= pos["sl"]:
                    sl_hit = True
                if pos["tp"] and low_i <= pos["tp"]:
                    tp_hit = True
            else:  # long
                if low_i <= pos["sl"]:
                    sl_hit = True
                if pos["tp"] and high_i >= pos["tp"]:
                    tp_hit = True

            if sl_hit and tp_hit:
                # Ambiguitas SL+TP satu candle — kebijakan eksplisit
                if sl_first:
                    exit_price = pos["sl"]
                    exit_reason = "SL"
                else:
                    exit_price = pos["tp"]
                    exit_reason = "TP"
            elif sl_hit:
                exit_price = pos["sl"]
                exit_reason = "SL"
            elif tp_hit:
                exit_price = pos["tp"]
                exit_reason = "TP"

            # Cek sinyal exit dari strategi
            signal_exit = exit_signal(df, i, pos)

            # Cek EXP (max bars)
            expired = pos["bars_held"] >= max_bars

            if exit_price is not None or signal_exit or expired:
                if exit_price is None:
                    exit_price = close_i
                    if signal_exit:
                        exit_reason = "SIGNAL"
                    elif expired:
                        exit_reason = "EXP"

                # Hitung PnL
                if direction == "short":
                    pnl = (pos["entry_price"] - exit_price) * pos["size"]
                else:
                    pnl = (exit_price - pos["entry_price"]) * pos["size"]

                # Fee
                fee_cost = pos["size"] * pos["entry_price"] * (fee_pct / 100) * 2
                pnl -= fee_cost

                # MAE/MFE dalam $
                mae_dollar = pos["mae"] * pos["size"]
                mfe_dollar = pos["mfe"] * pos["size"]

                trade = Trade(
                    entry_time=str(df.index[pos["entry_bar"]]),
                    exit_time=str(df.index[i]),
                    direction=pos["direction"],
                    entry_price=pos["entry_price"],
                    exit_price=exit_price,
                    stop_loss=pos["sl"],
                    take_profit=pos["tp"],
                    pnl=pnl,
                    risk_amount=pos["risk_amount"],
                    mae=mae_dollar,
                    mfe=mfe_dollar,
                )
                trades.append(trade)
                capital += pnl
                in_position = False
                pos = {}

    # Close any remaining open position at last bar
    if in_position:
        last_close = df["close"].iloc[-1]
        if direction == "short":
            pnl = (pos["entry_price"] - last_close) * pos["size"]
        else:
            pnl = (last_close - pos["entry_price"]) * pos["size"]

        fee_cost = pos["size"] * pos["entry_price"] * (fee_pct / 100) * 2
        pnl -= fee_cost

        trade = Trade(
            entry_time=str(df.index[pos["entry_bar"]]),
            exit_time=str(df.index[-1]),
            direction=pos["direction"],
            entry_price=pos["entry_price"],
            exit_price=last_close,
            stop_loss=pos["sl"],
            take_profit=pos["tp"],
            pnl=pnl,
            risk_amount=pos["risk_amount"],
            mae=pos["mae"] * pos["size"],
            mfe=pos["mfe"] * pos["size"],
        )
        trades.append(trade)
        capital += pnl

        equity_curve.append(EquityPoint(
            timestamp=str(df.index[-1]),
            equity=capital,
        ))

    # Count actual bars held
    total_bars = n
    bars_held_list = []
    for t in trades:
        try:
            entry_dt = pd.Timestamp(t.entry_time)
            exit_dt = pd.Timestamp(t.exit_time)
            bars_held_list.append(len(df[entry_dt:exit_dt]) - 1)
        except:
            bars_held_list.append(0)
    avg_bars_per_trade = float(np.mean(bars_held_list)) if bars_held_list else 0.0

    metrics = calculate_all_metrics(
        trades=trades,
        equity_curve=equity_curve,
        initial_capital=initial_capital,
        total_bars=total_bars,
        avg_bars_per_trade=avg_bars_per_trade,
    )

    # Summary
    summary = {
        "total_trades": len(trades),
        "net_profit_pct": metrics.get("net_profit_pct", 0),
        "win_rate_pct": metrics.get("win_rate_pct", 0),
        "ev_per_trade_r": metrics.get("ev_per_trade_r", 0),
        "max_drawdown_pct": metrics.get("max_drawdown_pct", 0),
        "profit_factor": metrics.get("profit_factor", 0),
        "sample_size_warning": metrics.get("sample_size_warning", True),
        "final_capital": capital,
        "exit_reasons": {},
    }

    # Count exit reasons
    for t in trades:
        reason = "UNKNOWN"
        if t.pnl <= -t.risk_amount * 0.99:
            reason = "SL"
        elif t.take_profit and abs(t.exit_price - t.take_profit) < 0.01 * t.entry_price:
            reason = "TP"
        else:
            reason = "OTHER"
        summary["exit_reasons"][reason] = summary["exit_reasons"].get(reason, 0) + 1

    return {
        "trades": trades,
        "equity_curve": equity_curve,
        "metrics": metrics,
        "summary": summary,
    }
