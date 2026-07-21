"""
fetch_data_tf.py
================
Fetch & cache BTCUSDT kline sekali saja untuk TF 2H & 4H.
Output: data_BTCUSDT_<tf>_2021now.csv di folder masing-masing.
Format identik dgn 1D (ot,open,high,low,close,volume; index=datetime UTC).
Setelah file ada, engine tinggal baca CSV — gak perlu fetch ulang.

Jalan: python3 fetch_data_tf.py
"""
import os, time, requests, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SYM = "BTCUSDT"
START = pd.Timestamp("2021-01-01", tz="UTC")
END = pd.Timestamp.now("UTC").normalize()
URL = "https://api.binance.com/api/v3/klines"
STEP = 895 * 24 * 60 * 60 * 1000  # ~895 hari per chunk (limit 1000)

def fetch_full(tf):
    cur = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)
    rows = []
    while cur < end_ms:
        nxt = min(cur + STEP, end_ms)
        r = requests.get(URL, params={"symbol": SYM, "interval": tf,
                     "startTime": cur, "endTime": nxt, "limit": 1000}, timeout=30).json()
        if r:
            rows.extend(r)
            cur = r[-1][0] + 1
        else:
            cur = nxt
        time.sleep(0.2)
    df = pd.DataFrame(rows, columns=["ot","o","h","l","c","v","ct","q","t","tb","tq","ig"])
    for c2 in ["o","h","l","c","v"]:
        df[c2] = df[c2].astype(float)
    df["ot"] = pd.to_datetime(df["ot"], unit="ms", utc=True)
    df = df.set_index("ot").sort_index()
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    return df[["open","high","low","close","volume"]]

for tf in ["2h", "4h"]:
    folder = os.path.join(HERE, tf.upper())
    os.makedirs(folder, exist_ok=True)
    out = os.path.join(folder, f"data_BTCUSDT_{tf}_2021now.csv")
    if os.path.exists(out):
        print(f"[skip] {tf}: {out} sudah ada ({os.path.getsize(out)} bytes)")
        continue
    print(f"[*] fetching {SYM} {tf} ...")
    df = fetch_full(tf)
    df.to_csv(out)
    print(f"[ok] {tf}: {len(df)} candles -> {out}")
print("DONE")
