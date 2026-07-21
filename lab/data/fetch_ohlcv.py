"""
Fetch OHLCV data dari Binance, simpan ke data/raw/.

Adaptasi dari trading-research/fetchers/data_fetcher.py.
Tambah kolom open_time_wib (UTC+7) untuk jurnal/laporan.
UTC tetap sumber utama sesuai stage_02_data_dan_waktu.md.

Usage:
    python3 data/fetch_ohlcv.py BTCUSDT 1d
    python3 data/fetch_ohlcv.py BTCUSDT 1d --market perp --limit 1000
    python3 data/fetch_ohlcv.py --list  # lihat cache yg sudah ada
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

# ── Config ─────────────────────────────────────────────
SPOT_BASE = "https://api.binance.com"
FUTURES_BASE = "https://fapi.binance.com"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

WIB = timezone(timedelta(hours=7))  # UTC+7


def _get_klines(base_url, symbol, interval, limit, is_futures=False, drop_unclosed=True):
    """Fetch klines from Binance REST endpoint."""
    endpoint = "/fapi/v1/klines" if is_futures else "/api/v3/klines"
    url = base_url + endpoint
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, f"API error: {e}"

    if not data:
        return None, "Empty response"

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore",
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["close_time_ms"] = df["close_time"].astype(int)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df.set_index("open_time")

    # Drop unclosed candle
    if drop_unclosed:
        now_ms = int(time.time() * 1000)
        df = df[df["close_time_ms"] <= now_ms]

    df = df[["open", "high", "low", "close", "volume", "close_time_ms"]]

    # Tambah kolom WIB untuk display/journal (UTC+7)
    df["open_time_wib"] = df.index + pd.Timedelta(hours=7)

    return df, None


def fetch_ohlcv(symbol, interval, limit=400, market_type="spot", drop_unclosed=True):
    """
    Fetch OHLCV from Binance.

    Returns: (DataFrame | None, error: str | None)
    """
    if market_type == "spot":
        return _get_klines(SPOT_BASE, symbol, interval, limit,
                           is_futures=False, drop_unclosed=drop_unclosed)
    elif market_type in ("perp", "futures"):
        return _get_klines(FUTURES_BASE, symbol, interval, limit,
                           is_futures=True, drop_unclosed=drop_unclosed)
    else:
        return None, f"Unknown market type: {market_type}"


def save_to_cache(df, symbol, interval):
    """Simpan CSV ke data/raw/PAIR_TF_daterange.csv."""
    os.makedirs(DATA_DIR, exist_ok=True)

    start = df.index[0].strftime("%Y%m%d")
    end = df.index[-1].strftime("%Y%m%d")
    fname = f"{symbol}_{interval}_{start}_{end}.csv"
    path = os.path.join(DATA_DIR, fname)

    df.to_csv(path)
    return path


def list_cache():
    """List file CSV yang sudah ada di data/raw/."""
    if not os.path.isdir(DATA_DIR):
        print("data/raw/ belum ada — belum ada data yang di-cache.")
        return

    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".csv"))
    if not files:
        print("data/raw/ kosong.")
        return

    print(f"Cache di {DATA_DIR}/:")
    for f in files:
        full = os.path.join(DATA_DIR, f)
        size_kb = os.path.getsize(full) / 1024
        print(f"  {f}  ({size_kb:.0f} KB)")


# ── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch OHLCV Binance → data/raw/")
    parser.add_argument("symbol", nargs="?", help="e.g. BTCUSDT")
    parser.add_argument("interval", nargs="?", help="e.g. 1h, 4h, 1d")
    parser.add_argument("--market", default="spot", choices=["spot", "perp", "futures"])
    parser.add_argument("--limit", type=int, default=400)
    parser.add_argument("--list", action="store_true", help="List cached data")
    parser.add_argument("--no-drop-unclosed", action="store_true",
                        help="Keep unclosed candle (not recommended for backtest)")
    args = parser.parse_args()

    if args.list:
        list_cache()
        sys.exit(0)

    if not args.symbol or not args.interval:
        parser.print_help()
        sys.exit(1)

    print(f"Fetching {args.symbol} {args.interval} ({args.market}, limit={args.limit})...")
    df, err = fetch_ohlcv(args.symbol, args.interval, args.limit,
                          args.market, drop_unclosed=not args.no_drop_unclosed)

    if err:
        print(f"ERROR: {err}")
        sys.exit(1)

    path = save_to_cache(df, args.symbol, args.interval)
    print(f"OK — {len(df)} candles saved to {path}")
    print(f"  Range : {df.index[0]} → {df.index[-1]}")
    print(f"  WIB   : {df['open_time_wib'].iloc[0]} → {df['open_time_wib'].iloc[-1]}")
    print(f"  Cols  : {list(df.columns)}")
