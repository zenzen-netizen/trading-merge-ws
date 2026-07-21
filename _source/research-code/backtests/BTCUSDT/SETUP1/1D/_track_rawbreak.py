"""Track raw fractal breaks for Trade #2 (entry 2026-06-17 bar 1993).
RAW BREAK = close < lastPivotLow (no filter).
"""
import sys, os
sys.path.insert(0, '/home/ubuntu/trading-research')
sys.path.insert(0, '/home/ubuntu/trading-research/indicators')
sys.path.insert(0, '/home/ubuntu')
import pandas as pd, numpy as np

HERE = '/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1/1D'
CACHE = os.path.join(HERE, 'data_BTCUSDT_1d_2021now.csv')
IV_MS = 86400000

df = pd.read_csv(CACHE, index_col=0, parse_dates=True)
h=df['high'].values.astype(float); l=df['low'].values.astype(float); c=df['close'].values.astype(float)
n=len(df)

import fbf_v11_backtest as V11
times=[int(t.value//1_000_000) for t in df.index]
eng = V11.FBFEngine(times, df['open'].values.astype(float), h, l, c, IV_MS, debug_raw=True)
_, events = eng.run()

# Filter RAW_CANDIDATE events, bear side only
raws = [e for e in events if e['event']=='RAW_CANDIDATE' and e['side']=='bear']

# Trade #2 entry bar = 1993 (2026-06-17)
eb = 1993
entry = 64509.40

print('='*80)
print(f'TRADE #2: entry {df.index[eb].strftime("%Y-%m-%d")} bar{eb} price={entry:.2f}')
print(f'DEFINISI RAW BREAK: close < lastPivotLow (fractal break mentah, tanpa filter)')
print('='*80)

# Compute pivot lows: LEFT_BARS=3, RIGHT_BARS=3
def find_pivot_lows(arr, left=3, right=3):
    out = []
    for i in range(left, len(arr) - right):
        p = i  # bar pivot = i (the convention: pivot at the low point itself)
        v = arr[p]
        ok = True
        for j in range(p - left, p):
            if arr[j] <= v: ok = False; break
        if ok:
            for j in range(p + 1, p + right + 1):
                if arr[j] <= v: ok = False; break
        if ok: out.append((v, p))
    return out

pl_arr = find_pivot_lows(l, 3, 3)
pl_dict = {bar: val for val, bar in pl_arr}

# Show last pivot low at entry
print()
print(f'[STATE SAAT ENTRY bar {eb}]')
last_pl_val = None; last_pl_bar = None
for bi in sorted(pl_dict.keys()):
    if bi <= eb:
        last_pl_val = pl_dict[bi]; last_pl_bar = bi
print(f'  lastPivotLow = {last_pl_val:.2f} @ bar{last_pl_bar} ({df.index[last_pl_bar].strftime("%Y-%m-%d")})')
print(f'  entry close  = {c[eb]:.2f}')
print(f'  close < PL?  = {c[eb] < last_pl_val}')

print()
print('='*80)
print(f'ALL RAW_CANDIDATE (bear) after entry (bar {eb})')
print('='*80)
print(f'{"bar":>5} {"date":>12} {"close":>10} {"high":>10} {"PL_val":>10} {"PL_bar":>7} {"gap%":>8}')
for e in raws:
    if e['bar'] >= eb:
        b_val = e.get('b_val','?')
        b_bar = e.get('b_bar','?')
        gap = (b_val - c[e['bar']]) / c[e['bar']] * 100 if b_val else 0
        print(f'{e["bar"]:>5} {df.index[e["bar"]].strftime("%Y-%m-%d"):>12} {c[e["bar"]]:>10.2f} {h[e["bar"]]:>10.2f} {b_val:>10} {b_bar:>7} {gap:>+7.2f}%')

# Now full forward track with rawbreak info
print()
print('='*80)
print('TRADE #2 FORWARD TRACK (entry -> rawbreaks -> exit)')
print('='*80)
print(f'{"bar":>5} {"date":>12} {"close":>10} {"high":>10} {"PL":>10} {"RAW?" :>6} {"RAW_HIGH":>10}')

# Track pivot lows as we go
for i in range(eb, min(n, eb+30)):
    # find current lastPivotLow
    cur_pl_val = None; cur_pl_bar = None
    for bi in sorted(pl_dict.keys()):
        if bi <= i: cur_pl_val = pl_dict[bi]; cur_pl_bar = bi
    
    is_raw = c[i] < cur_pl_val if cur_pl_val else False
    raw_str = 'RAW!' if is_raw else ''
    raw_high = f'{h[i]:.2f}' if is_raw else ''
    mark = ' <=E' if i==eb else ''
    
    print(f'{i:>5} {df.index[i].strftime("%Y-%m-%d"):>12} {c[i]:>10.2f} {h[i]:>10.2f} {cur_pl_val if cur_pl_val else 0:>10.2f} {raw_str:>6} {raw_high:>10}{mark}')

# Summary: count raw breaks per pivot
print()
print('='*80)
print('RAW BREAK SUMMARY')
print('='*80)
last_pl = None
for e in raws:
    if e['bar'] >= eb:
        b_val = e.get('b_val'); b_bar = e.get('b_bar')
        if b_bar != last_pl:
            last_pl = b_bar
            bars_for_this_pl = [e2 for e2 in raws if e2['bar']>=eb and e2.get('b_bar')==b_bar]
            first = bars_for_this_pl[0]
            print(f'  PL={b_val:.2f} bar{b_bar} ({df.index[b_bar].strftime("%Y-%m-%d")}) -> {len(bars_for_this_pl)} raw breaks')
            for e2 in bars_for_this_pl:
                print(f'    bar{e2["bar"]:>5} {df.index[e2["bar"]].strftime("%Y-%m-%d")} close={c[e2["bar"]]:.2f} high={h[e2["bar"]]:.2f}')
