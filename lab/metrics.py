"""
metrics.py
Metrics calculator untuk hasil backtest trading.

Input : list of Trade objects + equity curve (list of (timestamp, equity))
Output: dict metrics lengkap -> siap dicatat langsung ke journal (results/summary/*.json)

Semua metric di sini SATU sumber kebenaran (single source of truth).
Jangan hitung ulang manual di notebook lain -> resiko inkonsistensi antar run.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ============================================================
# DATA STRUCTURE
# ============================================================

@dataclass
class Trade:
    entry_time: str
    exit_time: str
    direction: str          # "long" / "short"
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: Optional[float]
    pnl: float               # realized profit/loss, satuan $ (atau unit akun)
    risk_amount: float       # $ yang direlakan hilang kalau kena SL (size x stop distance)
    mae: float                # Maximum Adverse Excursion, $ (selalu >= 0, jarak terjauh lawan posisi)
    mfe: float                # Maximum Favorable Excursion, $ (selalu >= 0, jarak terjauh searah profit)

    @property
    def r_multiple(self) -> float:
        """PnL dinyatakan dalam satuan risk (R). 1R = risk_amount."""
        if self.risk_amount == 0:
            return 0.0
        return self.pnl / self.risk_amount

    @property
    def is_win(self) -> bool:
        return self.pnl > 0


@dataclass
class EquityPoint:
    timestamp: str
    equity: float


# ============================================================
# CORE METRICS
# ============================================================

def net_profit(trades: List[Trade], initial_capital: float) -> Dict:
    total_pnl = sum(t.pnl for t in trades)
    return {
        "net_profit_abs": total_pnl,
        "net_profit_pct": (total_pnl / initial_capital) * 100 if initial_capital else 0.0,
    }


def win_rate(trades: List[Trade]) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.is_win)
    return wins / len(trades)


def profit_factor(trades: List[Trade]) -> float:
    gross_win = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    if gross_loss == 0:
        return float("inf") if gross_win > 0 else 0.0
    return gross_win / gross_loss


def avg_win_loss(trades: List[Trade]) -> Dict:
    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl < 0]
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0  # negatif
    realized_rr = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")
    return {
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "realized_rr": realized_rr,  # rata-rata rasio menang:kalah aktual, bukan target
    }


def expectancy(trades: List[Trade]) -> Dict:
    """Expectancy dalam $ per trade DAN dalam R per trade (lebih portable antar strategi/pair)."""
    if not trades:
        return {"expectancy_abs": 0.0, "expectancy_r": 0.0}
    exp_abs = np.mean([t.pnl for t in trades])
    exp_r = np.mean([t.r_multiple for t in trades])
    return {"expectancy_abs": exp_abs, "expectancy_r": exp_r}


def max_consecutive_losses(trades: List[Trade]) -> int:
    max_streak = streak = 0
    for t in trades:
        if not t.is_win:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


def max_consecutive_wins(trades: List[Trade]) -> int:
    max_streak = streak = 0
    for t in trades:
        if t.is_win:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


# ============================================================
# DRAWDOWN
# ============================================================

def max_drawdown(equity_curve: List[EquityPoint]) -> Dict:
    """Return max drawdown % + durasi recovery (jumlah candle/bar sampai equity balik ke peak lama)."""
    if not equity_curve:
        return {"max_drawdown_pct": 0.0, "recovery_bars": None, "in_drawdown": False}

    equities = np.array([p.equity for p in equity_curve])
    running_max = np.maximum.accumulate(equities)
    drawdown = (equities - running_max) / running_max

    trough_idx = int(np.argmin(drawdown))
    max_dd_pct = float(drawdown[trough_idx]) * 100
    peak_before_trough = running_max[trough_idx]

    # cari recovery: index pertama setelah trough di mana equity >= peak_before_trough
    recovery_idx = None
    for i in range(trough_idx, len(equities)):
        if equities[i] >= peak_before_trough:
            recovery_idx = i
            break

    return {
        "max_drawdown_pct": max_dd_pct,
        "recovery_bars": (recovery_idx - trough_idx) if recovery_idx is not None else None,
        "in_drawdown": recovery_idx is None,  # True kalau sampai akhir data belum recover
    }


def drawdown_recovery_requirement(drawdown_pct: float) -> float:
    """Gain % yang dibutuhkan buat balik ke modal awal, given drawdown_pct (positif, misal 30 utk -30%)."""
    dd = abs(drawdown_pct) / 100
    if dd >= 1:
        return float("inf")
    return (1 / (1 - dd) - 1) * 100


def recovery_factor(net_profit_abs: float, max_dd_pct: float, initial_capital: float) -> float:
    dd_abs = abs(max_dd_pct) / 100 * initial_capital
    if dd_abs == 0:
        return float("inf") if net_profit_abs > 0 else 0.0
    return net_profit_abs / dd_abs


# ============================================================
# RISK-ADJUSTED RETURN
# ============================================================

def sharpe_ratio(equity_curve: List[EquityPoint], risk_free_rate: float = 0.0, periods_per_year: int = 365) -> float:
    equities = np.array([p.equity for p in equity_curve])
    if len(equities) < 2:
        return 0.0
    returns = np.diff(equities) / equities[:-1]
    excess = returns - (risk_free_rate / periods_per_year)
    if excess.std() == 0:
        return 0.0
    return float(np.mean(excess) / excess.std() * np.sqrt(periods_per_year))


def sortino_ratio(equity_curve: List[EquityPoint], risk_free_rate: float = 0.0, periods_per_year: int = 365) -> float:
    equities = np.array([p.equity for p in equity_curve])
    if len(equities) < 2:
        return 0.0
    returns = np.diff(equities) / equities[:-1]
    excess = returns - (risk_free_rate / periods_per_year)
    downside = excess[excess < 0]
    downside_std = downside.std() if len(downside) > 0 else 0.0
    if downside_std == 0:
        return 0.0
    return float(np.mean(excess) / downside_std * np.sqrt(periods_per_year))


# ============================================================
# EXPOSURE
# ============================================================

def exposure_pct(trades: List[Trade], total_bars: int, avg_bars_per_trade: float) -> float:
    """Perkiraan waktu in-market. Butuh avg_bars_per_trade dari engine (durasi tiap trade dalam satuan bar)."""
    if total_bars == 0:
        return 0.0
    bars_in_market = len(trades) * avg_bars_per_trade
    return min(bars_in_market / total_bars, 1.0) * 100


# ============================================================
# MAE / MFE -> EDGE RATIO & TRADE EFFICIENCY
# ============================================================

def mae_mfe_analysis(trades: List[Trade]) -> Dict:
    """
    MAE: rata-rata jarak terjauh lawan posisi sebelum trade selesai -> cek SL efisien/kelonggaran.
    MFE: rata-rata jarak terjauh searah profit sebelum exit -> cek TP kecepetan/pas.
    Edge ratio: MFE/MAE rata-rata. >1 artinya secara umum profit potensial > risk potensial.
    Trade efficiency: seberapa besar realized profit dibanding max potential profit (MFE).
                       1.0 = exit persis di titik terbaik. <1 = ada profit "kebuang".
    """
    if not trades:
        return {"avg_mae": 0.0, "avg_mfe": 0.0, "edge_ratio": 0.0, "trade_efficiency_pct": 0.0}

    avg_mae = np.mean([t.mae for t in trades])
    avg_mfe = np.mean([t.mfe for t in trades])
    edge_ratio = (avg_mfe / avg_mae) if avg_mae != 0 else float("inf")

    # efficiency dihitung per-trade lalu dirata-rata (hanya trade dgn mfe > 0)
    effs = []
    for t in trades:
        if t.mfe > 0:
            realized = max(t.pnl, 0)  # kalau akhirnya loss, realized dianggap 0 dari sisi "capture profit"
            effs.append(realized / t.mfe)
    trade_efficiency = np.mean(effs) * 100 if effs else 0.0

    return {
        "avg_mae": avg_mae,
        "avg_mfe": avg_mfe,
        "edge_ratio": edge_ratio,
        "trade_efficiency_pct": trade_efficiency,
    }


# ============================================================
# EV FRAMEWORK (dari analisis video: WR x RR - (1-WR))
# ============================================================

def ev_framework(win_rate_: float, realized_rr: float) -> Dict:
    """
    EV per trade (satuan R) = WR x RR - (1 - WR)
    Breakeven WR = 1 / (RR + 1)  -> WR minimum supaya EV tidak negatif pada RR tsb.
    """
    ev_per_trade_r = win_rate_ * realized_rr - (1 - win_rate_)
    breakeven_wr = 1 / (realized_rr + 1) if realized_rr > -1 else float("inf")
    return {
        "ev_per_trade_r": ev_per_trade_r,
        "breakeven_win_rate": breakeven_wr,
        "wr_vs_breakeven_gap": win_rate_ - breakeven_wr,  # positif = strategi punya margin aman
    }


def ruin_probability_table(win_rate_: float, streaks: Tuple[int, ...] = (5, 7, 10)) -> Dict:
    """P(n loss beruntun) per kejadian = (1 - WR)^n. Dipakai buat kesiapan mental + sizing, bukan metric per-run."""
    loss_rate = 1 - win_rate_
    return {f"p_loss_streak_{n}": (loss_rate ** n) * 100 for n in streaks}


def annual_fee_funding_drag(
    trades_per_year: float,
    avg_position_size: float,
    fee_pct_round_trip: float,
    initial_capital: float,
    funding_pct_per_8h: float = 0.0,
    avg_holding_hours: float = 0.0,
) -> Dict:
    """
    Fee drag: biaya trading murni (entry+exit).
    Funding drag: khusus posisi leverage/perpetual yang diinapkan -> biaya sewa tiap 8 jam.
    Total drag dibandingkan ke modal awal -> aturan umum: idealnya < 20% modal/tahun.
    """
    annual_fee = trades_per_year * avg_position_size * (fee_pct_round_trip / 100)

    if avg_holding_hours > 0 and funding_pct_per_8h > 0:
        funding_periods_per_trade = avg_holding_hours / 8
        annual_funding = trades_per_year * avg_position_size * (funding_pct_per_8h / 100) * funding_periods_per_trade
    else:
        annual_funding = 0.0

    total_drag = annual_fee + annual_funding
    return {
        "annual_fee_abs": annual_fee,
        "annual_funding_abs": annual_funding,
        "annual_total_drag_abs": total_drag,
        "annual_total_drag_pct_capital": (total_drag / initial_capital) * 100 if initial_capital else 0.0,
    }


# ============================================================
# MASTER FUNCTION -> dipanggil sekali per run, hasil langsung dump ke journal
# ============================================================

def calculate_all_metrics(
    trades: List[Trade],
    equity_curve: List[EquityPoint],
    initial_capital: float,
    total_bars: int = 0,
    avg_bars_per_trade: float = 0.0,
    trades_per_year: Optional[float] = None,
    fee_pct_round_trip: float = 0.0,
    funding_pct_per_8h: float = 0.0,
    avg_holding_hours: float = 0.0,
) -> Dict:
    if not trades:
        return {"error": "no_trades", "total_trades": 0}

    n_profit = net_profit(trades, initial_capital)
    wr = win_rate(trades)
    pf = profit_factor(trades)
    awl = avg_win_loss(trades)
    exp = expectancy(trades)
    dd = max_drawdown(equity_curve)
    mae_mfe = mae_mfe_analysis(trades)
    ev = ev_framework(wr, awl["realized_rr"])
    ruin = ruin_probability_table(wr)

    result = {
        # --- core ---
        **n_profit,
        "win_rate_pct": wr * 100,
        "profit_factor": pf,
        "total_trades": len(trades),
        **awl,
        **exp,

        # --- consecutive ---
        "max_consecutive_losses": max_consecutive_losses(trades),
        "max_consecutive_wins": max_consecutive_wins(trades),

        # --- drawdown ---
        **dd,
        "drawdown_recovery_required_pct": drawdown_recovery_requirement(dd["max_drawdown_pct"]),
        "recovery_factor": recovery_factor(n_profit["net_profit_abs"], dd["max_drawdown_pct"], initial_capital),

        # --- risk adjusted ---
        "sharpe_ratio": sharpe_ratio(equity_curve),
        "sortino_ratio": sortino_ratio(equity_curve),

        # --- exposure ---
        "exposure_pct": exposure_pct(trades, total_bars, avg_bars_per_trade) if total_bars else None,

        # --- MAE/MFE ---
        **mae_mfe,

        # --- EV framework ---
        **ev,
        **ruin,

        # --- sample size flag ---
        "sample_size_warning": len(trades) < 30,
    }

    if trades_per_year:
        avg_position_size = np.mean([t.risk_amount for t in trades]) if trades else 0.0
        drag = annual_fee_funding_drag(
            trades_per_year=trades_per_year,
            avg_position_size=avg_position_size,
            fee_pct_round_trip=fee_pct_round_trip,
            initial_capital=initial_capital,
            funding_pct_per_8h=funding_pct_per_8h,
            avg_holding_hours=avg_holding_hours,
        )
        result.update(drag)

    return result
