"""
fbf_v11_signal.py — bridge FBF v11 -> Setup1 SHORT signals

Ambil sinyal SHORT dari FBF v11 (engine default /home/ubuntu/fbf_v11_backtest.py,
UTUH tidak diubah). Sinyal = event BREAK sisi BEAR (karena kita SHORT).
Entry = close bar BREAK (persis label "BREAK" yg user lihat di chart TradingView).

Engine v11 SUDAH menerapkan ST-gate (enableStTrendFilter=True):
BREAK bear cuma tercatat kalau Supertrend Adaptive sedang DOWNTREND saat
close bar itu. Jadi sinyal yg dikembalikan = sudah ST-gated by definition.

Return: (df, signals)
  df       = OHLC (pandas, index=open-time UTC) yg SAMA dipakai engine ->
            langsung bisa dipakai simulate Setup1 tanpa re-fetch.
  signals  = list dict:
     entry_bar (int, index ke df), entry (close), 
     B_bar, B_val, C_bar, C_val, A_bar, A_val (dr wave ABC beku),
     st_trend (1/-1), retrace_pct, date (pd.Timestamp open bar entry)
"""
import sys, os
sys.path.insert(0, "/home/ubuntu")                 # engine default ada di sini
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/fetchers")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")

import datetime as _dt
import pandas as pd
import numpy as np
import requests
import fbf_v11_backtest as V11                       # ENGINE DEFAULT (utuh)

SYM = "BTCUSDT"
IV_MS = {"1d": 86400000, "4h": 14400000, "2h": 7200000,
         "1h": 3600000, "15m": 900000}

# ---------- fetch (sama persis dgn backtest.py lama) ----------
def fetch_full(sym, tf, start_ts, end_ts):
    url = "https://api.binance.com/api/v3/klines"
    all_rows = []
    cur = int(start_ts.timestamp() * 1000)
    end_ms = int(end_ts.timestamp() * 1000)
    step = 895 * 24 * 60 * 60 * 1000
    while cur < end_ms:
        nxt = min(cur + step, end_ms)
        r = requests.get(url, params={"symbol": sym, "interval": tf,
                         "startTime": cur, "endTime": nxt, "limit": 1000},
                       timeout=30).json()
        if r:
            all_rows.extend(r); cur = r[-1][0] + 1
        else:
            cur = nxt
        import time as _t; _t.sleep(0.2)
    df = pd.DataFrame(all_rows, columns=[
        "ot", "o", "h", "l", "c", "v", "ct", "q", "t", "tb", "tq", "ig"])
    for c2 in ["o", "h", "l", "c", "v"]:
        df[c2] = df[c2].astype(float)
    df["ot"] = pd.to_datetime(df["ot"], unit="ms", utc=True)
    df = df.set_index("ot").sort_index()
    df.rename(columns={"o": "open", "h": "high", "l": "low",
                       "c": "close", "v": "volume"}, inplace=True)
    return df[["open", "high", "low", "close", "volume"]]


def get_short_signals(symbol="BTCUSDT", interval="1d", months=3):
    """Kembalikan (df, signals) dalam window = `months` bulan terakhir
    (dihitung dari hari ini). Engine butuh ~120 bar warmup -> kita fetch
    months*30 + 120 bar, lalu PARSE cuma yg close dlm window."""
    now = pd.Timestamp.now("UTC").normalize()
    end = now + _dt.timedelta(days=1)          # sampai candle hari ini
    warmup = 120
    total_bars = months * 30 + warmup
    start = now - _dt.timedelta(days=total_bars * IV_MS.get(interval, 86400000) / 86400000 + 1)

    print(f"[v11] fetch {symbol} {interval} ~{total_bars} bar (window {months}bln)")
    df = fetch_full(symbol, interval, start, end)
    print(f"[v11] {len(df)} candle {df.index[0].date()} .. {df.index[-1].date()}")

    # build engine v11 (default, utuh)
    times = [int(t.value // 1_000_000) for t in df.index]   # ns->ms
    eng = V11.FBFEngine(
        times,
        df["open"].values.astype(float),
        df["high"].values.astype(float),
        df["low"].values.astype(float),
        df["close"].values.astype(float),
        IV_MS.get(interval, 86400000),
    )
    breaks, events = eng.run()

    # Ambil BREAK bear dari EVENTS (punya "bar" = entry close index).
    # NB: list `breaks` tdk punya field bar-index -> pakai events.
    win_start = now - _dt.timedelta(days=months * 30)
    signals = []
    for e in events:
        if e["event"] != "BREAK" or e["side"] != "bear":
            continue
        eb = e["bar"]                         # entry close bar (index ke df)
        if eb < 0 or eb >= len(df):
            continue
        close_dt = df.index[eb]
        if close_dt < win_start:
            continue                        # di luar window -> buang
        signals.append({
            "entry_bar": eb,
            "entry": float(df["close"].iloc[eb]),
            "B_bar": e["b_bar"], "B_val": float(e["b_val"]),
            "C_bar": e["c_bar"], "C_val": float(e["c_val"]),
            "A_bar": e.get("a_bar"),
            "A_val": (float(e["a_val"]) if e.get("a_val") is not None else None),
            "st_trend": e["st_trend"],
            "retrace_pct": e.get("retrace_pct"),
            "date": close_dt,
        })
    signals.sort(key=lambda x: x["entry_bar"])
    print(f"[v11] BREAK bear dlm window ({months}bln): {len(signals)}")
    return df, signals


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default=SYM)
    ap.add_argument("--interval", default="1d")
    ap.add_argument("--months", type=int, default=3)
    a = ap.parse_args()
    df, sig = get_short_signals(a.symbol, a.interval, a.months)
    for s in sig:
        print(f"  {s['date'].date()}  entry={s['entry']:.0f}  "
              f"B={s['B_val']:.0f}@bar{s['B_bar']}  C={s['C_val']:.0f}@bar{s['C_bar']}  "
              f"C:{s['retrace_pct']}%  ST={'up' if s['st_trend']==1 else 'down'}")
