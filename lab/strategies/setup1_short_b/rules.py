"""
SETUP1 SHORT B — Rules
SHORT, multi position. Entry di SETIAP valid trigger, tanpa tunggu posisi clear.
Trigger logic = detect_signals_v3() dengan multi_position=True.

Perbedaan dari A: tidak ada gate "1 wave = 1 posisi".
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Set

from indicators.python.setup1_trigger import (
    detect_signals_v3,
    supertrend_full,
    sl_o1, sl_o3, sl_o6,
)

_signal_bars: Optional[Set[int]] = None
_df_ref: Optional[pd.DataFrame] = None


def _init_signals(df: pd.DataFrame):
    """Precompute sinyal — multi position (free fire)."""
    import config as cfg
    globals()["_df_ref"] = df

    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    close = df["close"].values.astype(float)

    st = supertrend_full(high, low, close, cfg.ST_PERIOD, cfg.ST_MULTIPLIER)
    E = {
        "FMB": df["SMI_FMB"].values.astype(bool),
        "PD":  df["SMI_PD"].values.astype(bool),
        "XDN": df["SMI_XDN"].values.astype(bool),
    }
    ev_by_bar: Dict[int, list] = {}
    if "FBF_EVENT" in df.columns:
        for i in range(len(df)):
            ev = df["FBF_EVENT"].iloc[i]
            if isinstance(ev, str) and ev:
                ev_by_bar[i] = [{"event": ev, "side": "bear"}]

    # Beda dari A: multi_position=True — tidak ada gate 1-wave-1-posisi
    from indicators.python import setup1_trigger as trig
    # detect_signals_v3 default multi_position=False.
    # Untuk B, kita panggil dengan multi_position=True
    # TAPI fungsi asli belum punya param itu. Workaround:
    # copy logic tanpa wave_entry_done flag
    samples = _detect_free_fire(df, high, low, close, st, E, ev_by_bar)

    globals()["_signal_bars"] = {s["bar"] for s in samples}
    print(f"[setup1_short_b] Precomputed {len(samples)} signals ({len(_signal_bars)} unique bars)")


def _detect_free_fire(df, high, low, close, st_trend, E, ev_by_bar):
    """Versi detect_signals tanpa 1-wave-1-position gate.

    Setiap FMB->PD->XDN valid langsung fire, tanpa nunggu posisi clear.
    """
    FMB, PD, XDN = E["FMB"], E["PD"], E["XDN"]
    n = len(df)
    samples = []
    fmb_b = None; pd_b = None

    for i in range(n):
        # Reset on wave events
        for e in ev_by_bar.get(i, []):
            if e.get("side") != "bear": continue
            et = e["event"]
            if et == "WAVE_STARTED":
                fmb_b = None; pd_b = None
            elif et in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED",
                        "CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
                fmb_b = None; pd_b = None

        # FMB/PD/XDN tracking — NO wave_entry_done guard
        if FMB[i] and fmb_b is None:
            fmb_b = i
        if fmb_b is not None and pd_b is None and PD[i] and i >= fmb_b:
            pd_b = i
        if fmb_b is not None and pd_b is not None and XDN[i] and i >= pd_b:
            if st_trend[i] == -1:
                import config as cfg
                from indicators.python.setup1_trigger import ATR_PCT_CFG
                from indicators.legacy import atr_percentage as atrp

                entry_val = float(close[i])
                apct_current = atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]

                samples.append(dict(
                    bar=i, entry=entry_val,
                    apct=float(apct_current),
                    date=df.index[i],
                ))
                # NO pos_open / clear_bar — free fire
                fmb_b = None; pd_b = None

    return samples


def entry_signal(df: pd.DataFrame, i: int) -> bool:
    """True kalau bar i adalah sinyal entry — multi position."""
    global _signal_bars
    if _signal_bars is None:
        _init_signals(df)
    return i in _signal_bars


def exit_signal(df: pd.DataFrame, i: int, position: Dict) -> bool:
    """Sinyal exit dinamis — ST_REV flip."""
    import config as cfg
    if cfg.EXIT_METHOD == "st_rev":
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        close = df["close"].values.astype(float)
        if i <= 0: return False
        st = supertrend_full(
            high[:i+1], low[:i+1], close[:i+1],
            cfg.ST_PERIOD, cfg.ST_MULTIPLIER,
        )
        return len(st) > 1 and st[-2] == -1 and st[-1] == 1
    return False


def sl_price(df: pd.DataFrame, i: int, entry_price: float) -> float:
    """SL price — SHORT, di atas entry."""
    import config as cfg
    from indicators.python.setup1_trigger import ATR_PCT_CFG

    if cfg.SL_METHOD == "liq10x":
        return sl_o1(entry_price)
    if cfg.SL_METHOD == "atr_pct":
        apct = _get_atr_pct(df, i, cfg)
        sl = sl_o3(entry_price, apct)
        return sl if sl else entry_price * 1.10
    if cfg.SL_METHOD == "atr_1d":
        apct = _get_atr_pct(df, i, cfg)
        sl = sl_o6(entry_price, apct)
        return sl if sl else entry_price * 1.10
    return entry_price * 1.10


def tp_price(df: pd.DataFrame, i: int, entry_price: float) -> Optional[float]:
    """TP price — fixed multiplier."""
    import config as cfg
    if cfg.TP_MULTIPLIER is None:
        return None
    risk = abs(entry_price - sl_price(df, i, entry_price))
    return entry_price - cfg.TP_MULTIPLIER * risk


def _get_atr_pct(df: pd.DataFrame, i: int, cfg) -> float:
    from indicators.python.setup1_trigger import ATR_PCT_CFG
    if cfg.SL_ATR_TIMEFRAME == "1d":
        return _get_daily_atr_pct(i)
    sub = df.iloc[:i+1]
    if len(sub) < 2: return 1.0
    try:
        from indicators.legacy.atr_percentage import atr_percentage
        result = atr_percentage(sub, ATR_PCT_CFG)
        vals = result["atr_pct"]
        return float(vals.iloc[-1]) if len(vals) > 0 else 1.0
    except Exception:
        return 1.0


def _get_daily_atr_pct(i: int) -> float:
    return 2.0  # TODO: daily ATR anchor
