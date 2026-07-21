import sys, csv
from datetime import datetime
import pandas as pd

JPATH=sys.argv[1]; TF=sys.argv[2]
rows=list(csv.DictReader(open(JPATH)))
# cari terbaru dgn outcome TP atau SL (bukan EXP/ST_REV/RAWBRK)
rows.sort(key=lambda r:r["entry_date"],reverse=True)
picks={}
for mode in ["GATED","RAW"]:
    for r in rows:
        if r["mode"]!=mode: continue
        if r["outcome"] in ("TP","SL"):
            picks[mode]=r; break
for mode,r in picks.items():
    entry=float(r["entry"]); sl=float(r["sl"]); sl_pct=float(r["sl_pct"])
    tp_pct=float(r["tp_pct"]); apct=float(r["apct"])
    opt=r["opt"]; combo=r["tp_ratio"]; out=r["outcome"]; R=float(r["R"]); bars=int(r["bars"])
    # tp price (fixed) or 0 for ST_REV/RAWBRK
    if abs(tp_pct)>0:
        tp_price=entry*(1+tp_pct/100)
    else:
        tp_price=0.0
    # exit price
    if out=="TP":
        exit_price=tp_price
    elif out=="SL":
        exit_price=sl
    else:
        exit_price=None
    exit_chg=((exit_price-entry)/entry*100) if exit_price else None
    print(f"===== {TF} | {mode} =====")
    print(f"Opt (SL type): {opt}")
    print(f"TP type/combo: {combo}  (tp_pct={tp_pct}%)")
    print(f"Entry date: {r['entry_date']}")
    print(f"Entry price: {entry:.2f}")
    print(f"SL price: {sl:.2f}  ({sl_pct:+.1f}% from entry)")
    if tp_price: print(f"TP price: {tp_price:.2f}  ({tp_pct:+.1f}% from entry)")
    else: print(f"TP: none (exit by signal: {combo})")
    print(f"Outcome: {out}")
    if exit_price: print(f"Exit price: {exit_price:.2f}  ({exit_chg:+.2f}% from entry)  R={R:.3f}")
    print(f"Hold: {bars} bars")
    print()
