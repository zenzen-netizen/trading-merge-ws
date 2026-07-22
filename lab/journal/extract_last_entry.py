import sys, time, requests, pandas as pd, numpy as np
sys.path.insert(0,"/home/ubuntu/trading-merge-ws")
sys.path.insert(0,"/home/ubuntu/trading-merge-ws/lab/data")
import csv

TF=sys.argv[1]; JOURNAL=sys.argv[2]
# ambil entry_date terbaru + detail dari journal
rows=list(csv.DictReader(open(JOURNAL)))
rows.sort(key=lambda r:r["entry_date"],reverse=True)
latest=rows[0]
ed=latest["entry_date"]
print(f"[{TF}] journal latest entry_date={ed} opt={latest['opt']} combo={latest['tp_ratio']} mode={latest['mode']}")
print(f"[{TF}] entry={latest['entry']} SL={latest['sl']}({latest['sl_pct']}%) TP%={latest['tp_pct']}% outcome={latest['outcome']} R={latest['R']} bars={latest['bars']}")

SYM="BTCUSDT"
START=pd.Timestamp(ed,tz="UTC")-pd.Timedelta(days=2)
END=pd.Timestamp(ed,tz="UTC")+pd.Timedelta(days=2)
url="https://api.binance.com/api/v3/klines"
params={"symbol":SYM,"interval":TF,"startTime":int(START.timestamp()*1000),
        "endTime":int(END.timestamp()*1000),"limit":1000}
r=requests.get(url,params=params,timeout=20); d=r.json()
df=pd.DataFrame(d,columns=["t","o","h","l","c","v","ct","q","n","vb","qb","x"])
df["t"]=pd.to_datetime(df["t"],unit="ms",utc=True)
df["ct"]=pd.to_datetime(df["ct"],unit="ms",utc=True)
# cari candle yg close date == ed
match=df[df["ct"].dt.strftime("%Y-%m-%d")==ed]
if len(match):
    row=match.iloc[0]
    print(f"[{TF}] EXACT entry candle: open={row['t']} close={row['ct']} o={float(row['o']):.2f} c={float(row['c']):.2f}")
    # derive exit time
    bars=int(latest["bars"])
    tfdelta={"1d":pd.Timedelta(days=1),"4h":pd.Timedelta(hours=4),"2h":pd.Timedelta(hours=2)}[TF]
    exit_t=row["ct"]+bars*tfdelta
    print(f"[{TF}] exit ~ {exit_t} (after {bars} bars)")
else:
    print(f"[{TF}] no candle match for {ed}")
