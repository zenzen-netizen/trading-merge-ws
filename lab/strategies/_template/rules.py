"""
Strategy rules template.
Copy ke strategies/[nama_strategi]/rules.py dan sesuaikan.

Entry signal dan exit signal — dipanggil oleh backtest engine.
Harus mengikuti kontrak yang sama untuk semua strategi.
"""

import pandas as pd
from typing import Dict


def entry_signal(df: pd.DataFrame, i: int) -> bool:
    """
    Sinyal entry di bar i. Engine akan entry di open bar i+1.

    Args:
        df: DataFrame dengan kolom OHLCV + indikator.
        i: indeks bar yang dicek.

    Returns:
        True jika sinyal entry valid.
    """
    # TODO: implement logic entry
    # Contoh: SMI cross_down + zone di Upper
    return False


def exit_signal(df: pd.DataFrame, i: int, position: Dict) -> bool:
    """
    Sinyal exit di bar i. Dipanggil tiap bar selama posisi terbuka.

    Args:
        df: DataFrame dengan kolom OHLCV + indikator.
        i: indeks bar saat ini.
        position: dict posisi (entry_price, sl, tp, direction, ...)

    Returns:
        True jika sinyal exit valid.
    """
    # TODO: implement logic exit
    return False


def sl_price(df: pd.DataFrame, i: int, entry_price: float) -> float:
    """
    Harga stop loss berdasarkan konfigurasi.

    Args:
        df: DataFrame.
        i: indeks bar sinyal entry.
        entry_price: harga entry (open bar i+1).

    Returns:
        Harga stop loss.
    """
    from config import SL_METHOD, SL_PCT, DIRECTION

    if SL_METHOD == "fixed_pct":
        if DIRECTION == "short":
            return entry_price * (1 + SL_PCT / 100)
        else:
            return entry_price * (1 - SL_PCT / 100)

    # TODO: ATR-based, structure-based
    return entry_price * (1 + SL_PCT / 100)  # default


def tp_price(df: pd.DataFrame, i: int, entry_price: float) -> float:
    """
    Harga take profit berdasarkan konfigurasi.

    Args:
        df: DataFrame.
        i: indeks bar sinyal entry.
        entry_price: harga entry (open bar i+1).

    Returns:
        Harga take profit, atau None kalau tidak pakai TP.
    """
    from config import TP_MULTIPLIER, SL_PCT, DIRECTION
    import config as cfg

    if TP_MULTIPLIER is None:
        return None

    tp_pct = SL_PCT * TP_MULTIPLIER
    if DIRECTION == "short":
        return entry_price * (1 - tp_pct / 100)
    else:
        return entry_price * (1 + tp_pct / 100)
