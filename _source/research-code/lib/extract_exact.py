import sys, time, requests, pandas as pd, numpy as np
TF=sys.argv[1]; ENTRY=float(sys.argv[2])
SYM="BTCUSDT"
START=pd.Timestamp("2026-05-01",tz="UTC")
END=pd.Timestamp.now("UTC").normalize()+pd.Timedelta(days=1)
url="https://api.binance.com/api/v3/klines"
params={"symbol":SYM,"interval":TF,"startTime":int(START.timestamp()*1000),
        "endTime":int(END.timestamp()*1000),"limit":1000}
allr=[]
while True:
    r=requests.get(url,params=params,timeout=20); d=r.json()
    if not d: break
    allr+=d; params["startTime"]=d[-1][0]+1
    if len(d)<1000: break
    time.sleep(0.2)
df=pd.DataFrame(allr,columns=["t","o","h","l","c","v","ct","q","n","vb","qb","x"])
df["t"]=pd.to_datetime(df["t"],unit="ms",utc=True)
df["ct"]=pd.to_datetime(df["ct"],unit="ms",utc=True)
df["c"]=df["c"].astype(float)
# cari bar dgn close == entry (toleransi 0.5)
m=df[abs(df["c"]-ENTRY)<0.5]
if len(m):
    for _,row in m.iterrows():
        print(f"[{TF}] MATCH entry={ENTRY}: open={row['t']} close={row['ct']} o={row['o']} c={row['c']}")
else:
    # cari terdekat
    df["diff"]=abs(df["c"]-ENTRY)
    row=df.nsmallest(1,"diff").iloc[0]
    print(f"[{TF}] nearest entry={ENTRY}: close={row['ct']} c={row['c']} diff={row['diff']}")
