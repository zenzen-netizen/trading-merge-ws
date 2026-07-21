"""
Binance data fetcher — pulls OHLCV from spot, futures (perp), 
and quarterly contract endpoints.
Filters out unclosed candles by default (close_time <= now).
"""

import requests
import pandas as pd
import time


SPOT_BASE = "https://api.binance.com"
FUTURES_BASE = "https://fapi.binance.com"


def _get_klines(base_url, symbol, interval, limit, is_futures=False, drop_unclosed=True):
    """Fetch klines from given endpoint.
    
    Args:
        drop_unclosed: If True, remove the last candle if it hasn't closed yet
                      (close_time > now). This ensures all indicators are
                      calculated from finalized candle data only.
    """
    endpoint = "/fapi/v1/klines" if is_futures else "/api/v3/klines"
    url = base_url + endpoint
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, f"API error: {e}"

    if not data:
        return None, "Empty response"

    # Columns: open_time, open, high, low, close, volume, close_time, ...
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])
    # Convert types
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df["close_time_ms"] = df["close_time"].astype(int)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df.set_index("open_time")

    # Filter out unclosed candles
    if drop_unclosed:
        now_ms = int(time.time() * 1000)
        before = len(df)
        df = df[df["close_time_ms"] <= now_ms]
        dropped = before - len(df)
        if dropped > 0:
            pass  # silently drop unclosed candle

    df = df[["open", "high", "low", "close", "volume", "close_time_ms"]]
    return df, None


def fetch_ohlcv(symbol, interval, limit=400, market_type="spot", drop_unclosed=True):
    """
    Fetch OHLCV data from Binance.
    
    Args:
        symbol: e.g. "BTCUSDT"
        interval: "15m", "1h", "4h", "1d", etc.
        limit: number of candles
        market_type: "spot", "perp", "futures"
        drop_unclosed: if True, only return candles that have closed
    
    Returns:
        (df, error) — df is DataFrame or None, error is str or None
    """
    if market_type == "spot":
        return _get_klines(SPOT_BASE, symbol, interval, limit, is_futures=False, drop_unclosed=drop_unclosed)
    elif market_type in ("perp", "futures"):
        return _get_klines(FUTURES_BASE, symbol, interval, limit, is_futures=True, drop_unclosed=drop_unclosed)
    else:
        return None, f"Unknown market type: {market_type}"


def fetch_all(watchlist, timeframes, limit=400, drop_unclosed=True):
    """
    Fetch OHLCV for all pairs across all timeframes.
    
    Args:
        watchlist: dict with keys "spot", "perp", "futures" (lists of symbols)
        timeframes: list of interval strings
        limit: candles per fetch
        drop_unclosed: if True, only return candles that have closed
    
    Returns:
        dict: { "BTCUSDT_spot": { "1h": df, "4h": df, ... }, ... }
        errors: list of (symbol, tf, error_msg)
    """
    results = {}
    errors = []
    
    pairs = []
    for sym in watchlist.get("spot", []):
        pairs.append((sym, "spot"))
    for sym in watchlist.get("perp", []):
        pairs.append((sym, "perp"))
    for sym in watchlist.get("futures", []):
        pairs.append((sym, "futures"))
    
    for symbol, mtype in pairs:
        key = f"{symbol}_{mtype}"
        results[key] = {}
        for tf in timeframes:
            df, err = fetch_ohlcv(symbol, tf, limit, mtype, drop_unclosed=drop_unclosed)
            if err:
                errors.append((key, tf, err))
                results[key][tf] = None
            else:
                results[key][tf] = df
            # Small delay to be nice to API
            time.sleep(0.05)
    
    return results, errors


# Cache: simple in-memory cache to avoid re-fetching within 60s
_cache = {}
_cache_ts = {}
CACHE_TTL = 60  # seconds


def fetch_cached(symbol, interval, limit=400, market_type="spot"):
    """Cached fetch — avoids re-pulling data within CACHE_TTL seconds."""
    cache_key = f"{symbol}_{market_type}_{interval}_{limit}"
    now = time.time()
    
    if cache_key in _cache and (now - _cache_ts.get(cache_key, 0)) < CACHE_TTL:
        return _cache[cache_key], None
    
    df, err = fetch_ohlcv(symbol, interval, limit, market_type)
    if df is not None:
        _cache[cache_key] = df
        _cache_ts[cache_key] = now
    return df, err