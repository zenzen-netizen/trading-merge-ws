"""
Bybit data fetcher — pulls OHLCV from Bybit for TradeFi pairs (e.g. XAUUSDT).
Interval mapping: Binance format → Bybit format
  15m → 15, 1h → 60, 2h → 120, 4h → 240, 1d → D, 1w → W
"""

import requests
import pandas as pd
import time

BYBIT_BASE = "https://api.bybit.com"
BYBIT_INTERVAL_MAP = {
    "15m": "15", "1h": "60", "2h": "120", "4h": "240", "1d": "D", "1w": "W",
}


def _bybit_klines(symbol, interval, limit=400, category="linear", drop_unclosed=True):
    """Fetch klines from Bybit.
    
    Args:
        symbol: e.g. "XAUUSDT"
        interval: Binance format ("15m", "1h", etc.)
        category: "linear" (perp) or "spot"
        drop_unclosed: if True, remove unclosed candles
    """
    bybit_interval = BYBIT_INTERVAL_MAP.get(interval, interval)
    url = f"{BYBIT_BASE}/v5/market/kline"
    params = {
        "category": category,
        "symbol": symbol,
        "interval": bybit_interval,
        "limit": str(limit),
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, f"Bybit API error: {e}"

    if data.get("retCode") != 0:
        return None, f"Bybit error: {data.get('retMsg', 'unknown')}"

    klines = data.get("result", {}).get("list", [])
    if not klines:
        return None, "Empty response"

    # Bybit klines: [start_time, open, high, low, close, volume, turnover]
    # Note: Bybit returns newest first, need to reverse
    klines = list(reversed(klines))

    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume", "turnover"
    ])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df["open_time"] = pd.to_numeric(df["open_time"], errors="coerce")
    # Bybit doesn't provide close_time, calculate from interval
    interval_ms = {
        "15": 15*60*1000, "60": 60*60*1000, "120": 2*60*60*1000,
        "240": 4*60*60*1000, "D": 24*60*60*1000, "W": 7*24*60*60*1000,
    }
    dur = interval_ms.get(bybit_interval, 60*60*1000)
    df["close_time_ms"] = df["open_time"].astype("int64") + dur - 1
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df.set_index("open_time")

    # Filter unclosed candles
    if drop_unclosed:
        now_ms = int(time.time() * 1000)
        df = df[df["close_time_ms"] <= now_ms]

    df = df[["open", "high", "low", "close", "volume", "close_time_ms"]]
    return df, None


def fetch_bybit(symbol, interval, limit=400, category="linear", drop_unclosed=True):
    """Fetch OHLCV from Bybit.
    
    Args:
        symbol: e.g. "XAUUSDT"
        interval: "15m", "1h", "4h", "1d", etc.
        limit: number of candles
        category: "linear" (perp) or "spot"
        drop_unclosed: if True, only return closed candles
    
    Returns:
        (df, error) — df is DataFrame or None, error is str or None
    """
    return _bybit_klines(symbol, interval, limit, category, drop_unclosed)


def fetch_all_bybit(symbols, timeframes, limit=400, category="linear", drop_unclosed=True):
    """Fetch OHLCV for all Bybit symbols across all timeframes.
    
    Args:
        symbols: list of symbol strings (e.g. ["XAUUSDT"])
        timeframes: list of interval strings
        limit: candles per fetch
        category: "linear" or "spot"
        drop_unclosed: if True, only return closed candles
    
    Returns:
        dict: { "XAUUSDT_bybit": { "1h": df, "4h": df, ... }, ... }
        errors: list of (symbol, tf, error_msg)
    """
    results = {}
    errors = []

    for symbol in symbols:
        key = f"{symbol}_bybit"
        results[key] = {}
        for tf in timeframes:
            df, err = fetch_bybit(symbol, tf, limit, category, drop_unclosed=drop_unclosed)
            if err:
                errors.append((key, tf, err))
                results[key][tf] = None
            else:
                results[key][tf] = df
            time.sleep(0.05)

    return results, errors