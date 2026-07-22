import sys, csv, time, requests, pandas as pd

JPATH=sys.argv[1]; TF=sys.argv[2]
rows=list(csv.DictReader(open(JPATH)))
rows.sort(key=lambda r:r["entry_date"],reverse=True)
picks={}
for mode in ["GATED","RAW"]:
    for r in rows:
        if r["mode"]!=mode: continue
        if r["outcome"] in ("TP","SL"):
            picks[mode]=r; break

def exact_time(TF, entry):
    SYM="BTCUSDT"
    START=pd.Timestamp("2026-05-01",tz="UTC")
    END=pd.Timestamp.now("UTC").normalize()+pd.Timedelta(days=1)
    url="https://api.binance.com/api/v3/klines"
    params={"symbol":SYM,"interval":TF,"startTime":int(START.timestamp()*1000),
            "endTime":int(END.timestamp()*1000),"limit":1000}
    allr=[]
    while True:
        r=requests.get(url,params=params,timeout=20); d=r.json()
        if not d or not isinstance(d,list): break
        allr+=d; params["startTime"]=d[-1][0]+1
        if len(d)<1000: break
        time.sleep(0.2)
    df=pd.DataFrame(allr,columns=["t","o","h","l","c","v","ct","q","n","vb","qb","x"])
    df["t"]=pd.to_datetime(df["t"],unit="ms",utc=True)
    df["ct"]=pd.to_datetime(df["ct"],unit="ms",utc=True)
    df["c"]=df["c"].astype(float)
    m=df[abs(df["c"]-entry)<0.5]
    if len(m): return m.iloc[0]["ct"]
    return None

for mode,r in picks.items():
    entry=float(r["entry"]); sl=float(r["sl"]); sl_pct=float(r["sl_pct"])
    tp_pct=float(r["tp_pct"]); opt=r["opt"]; combo=r["tp_ratio"]; out=r["outcome"]
    R=float(r["R"]); bars=int(r["bars"])
    tp_price=entry*(1+tp_pct/100) if abs(tp_pct)>0 else 0.0
    exit_price = tp_price if out=="TP" else (sl if out=="SL" else None)
    exit_chg=((exit_price-entry)/entry*100) if exit_price else None
    ct=exact_time(TF,entry)
    ct_str=ct.strftime("%Y-%m-%d %H:%M UTC") if ct is not None else r["entry_date"]+" (no exact)"
    print(f"===== {TF} | {mode} =====")
    print(f"SL type (opt): {opt}")
    print(f"TP type/combo: {combo}  (tp_pct={tp_pct:+.1f}%)")
    print(f"Entry: {ct_str}")
    print(f"  price: {entry:.2f}")
    print(f"SL: {sl:.2f}  ({sl_pct:+.1f}% from entry)")
    if tp_price: print(f"TP: {tp_price:.2f}  ({tp_pct:+.1f}% from entry)")
    else: print(f"TP: none (exit by signal {combo})")
    print(f"Outcome: {out}")
    if exit_price: print(f"Exit: {exit_price:.2f}  ({exit_chg:+.2f}% from entry)  R={R:.3f}")
    print(f"Hold: {bars} bars")
    print()
