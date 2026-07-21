"""
detail_rawbrk_samples.py — O6 (ATR% 1D) + RAWBRK, 4H & 2H, 2026 only.
Extracts DETAILED rawbreak event timeline for RAWBRK_HIT trades.
Shows: entry, every rawbreak candle (close/PL/rb_sl), final HIT.
"""
import sys, os
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu")
import pandas as pd, numpy as np
from datetime import timezone, timedelta

WIB = timezone(timedelta(hours=7))
def fmt_wib(ts):
    return ts.tz_convert(WIB).strftime("%d %b %Y %H:%M")

SMI_CFG = {
    "len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
    "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
    "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60
}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

BASE = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1"

# ── PHASE 0: Preload 1D ──
import atr_percentage as atrp
df1d = pd.read_csv(f"{BASE}/1D/data_BTCUSDT_1d_2019now.csv", index_col=0, parse_dates=True)
daily_atr_pct = np.full(len(df1d), np.nan)
for i in range(30, len(df1d)):
    daily_atr_pct[i] = atrp.atr_percentage(df1d.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]

def get_daily_atr_pct(ts):
    for i in range(len(df1d)-1, -1, -1):
        if df1d.index[i] <= ts:
            val = daily_atr_pct[i]
            if np.isnan(val):
                for j in range(i+1, len(df1d)):
                    if not np.isnan(daily_atr_pct[j]):
                        return daily_atr_pct[j]
                return None
            return val
    return None

# ── Helpers ──
import smi_events as SM
import fbf_v11_backtest as V11

def supertrend_full(high, low, close, period=10, mult=3.0):
    n = len(close); h,l,c = high,low,close
    hl2=(h+l)/2.0
    tr=np.zeros(n); tr[0]=h[0]-l[0]
    for i in range(1,n):
        tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    atr=np.zeros(n); atr[0]=tr[0]; alpha=1.0/period
    for i in range(1,n): atr[i]=atr[i-1]+alpha*(tr[i]-atr[i-1])
    up_raw=hl2-mult*atr; dn_raw=hl2+mult*atr
    up_f=np.zeros(n); dn_f=np.zeros(n); trend=np.ones(n,dtype=int)
    up_f[0]=up_raw[0]; dn_f[0]=dn_raw[0]
    for i in range(1,n):
        up_f[i]=max(up_raw[i],up_f[i-1]) if c[i-1]>up_f[i-1] else up_raw[i]
        dn_f[i]=min(dn_raw[i],dn_f[i-1]) if c[i-1]<dn_f[i-1] else dn_raw[i]
        trend[i]=trend[i-1]
        if trend[i-1]==-1 and c[i]>dn_f[i-1]: trend[i]=1
        elif trend[i-1]==1 and c[i]<up_f[i-1]: trend[i]=-1
    return trend

def find_pivot_lows(arr, left=3, right=3):
    out=[]
    for ii in range(left,len(arr)-right):
        v=arr[ii]; ok=True
        for j in range(ii-left,ii):
            if arr[j]<=v: ok=False; break
        if ok:
            for j in range(ii+1,ii+right+1):
                if arr[j]<=v: ok=False; break
        if ok: out.append((v,ii))
    return out

def atr_pct_at(df_slice, idx):
    return atrp.atr_percentage(df_slice.iloc[:idx+1], ATR_PCT_CFG)["atr_pct"]

def sim_rawbrk_detailed(entry, eb, sl, tp_mult, high, low, close, n, pl_dict, df, allow_exp_max=240):
    """RAWBRK sim returning FULL event timeline."""
    risk = sl - entry
    tp = entry - tp_mult * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    rb_sl = None
    rb_events = []  # list of {bar_offset, bi, date_wib, close, pivot_low, rb_sl_set}
    final_outcome = None
    
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        # TP hit
        if fwd_l[k] <= tp:
            final_outcome = dict(out="TP", ex=tp, bars=k+1, R=tp_mult, rb_events=rb_events)
            return final_outcome
        # SL hit
        if fwd_h[k] >= sl:
            final_outcome = dict(out="SL", ex=sl, bars=k+1, R=-1.0, rb_events=rb_events)
            return final_outcome
        # RAWBRK_HIT (from PREVIOUS trigger)
        if rb_sl is not None and fwd_h[k] >= rb_sl:
            final_outcome = dict(out="RAWBRK_HIT", ex=rb_sl, bars=k+1, R=(entry-rb_sl)/risk, rb_events=rb_events, rawbreak_price=rb_sl)
            return final_outcome
        # RAWBRK trigger — only SET rb_sl
        cur_pl = None
        for bi2 in sorted(pl_dict.keys(), reverse=True):
            if bi2 <= bi: cur_pl = pl_dict[bi2]; break
        if cur_pl is not None and close[bi] < cur_pl:
            old_rb_sl = rb_sl
            rb_sl = high[bi]  # OVERWRITE — tiap rawbreak baru, SL = high candle TERBARU
            rb_events.append(dict(
                bar=bi,
                date_wib=fmt_wib(df.index[bi]),
                close=close[bi],
                pivot_low=cur_pl,
                rb_sl_old=old_rb_sl,
                rb_sl_new=rb_sl,
                high=high[bi],
            ))
        # EXP cap
        if k >= allow_exp_max:
            lastc = fwd_l[k]
            final_outcome = dict(out="EXP", ex=lastc, bars=k+1, R=(entry-lastc)/risk, rb_events=rb_events)
            return final_outcome
    
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    final_outcome = dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk, rb_events=rb_events)
    return final_outcome

# ── RUN ──
TF_CONFIGS = [
    ("4H", f"{BASE}/4H/data_BTCUSDT_4h_2019now.csv", 14400000),
    ("2H", f"{BASE}/2H/data_BTCUSDT_2h_2019now.csv",  7200000),
]

CUTOFF = pd.Timestamp("2026-01-01", tz="UTC")

for tf_name, csv_path, iv_ms in TF_CONFIGS:
    print(f"\n{'='*70}")
    print(f"  {tf_name} — RAWBRK DETAIL TIMELINE — O6 (ATR% 1D) — 2026 (WIB)")
    print(f"{'='*70}")
    
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    high = df["high"].values.astype(float)
    low  = df["low"].values.astype(float)
    close = df["close"].values.astype(float)
    n = len(df)
    
    st_trend = supertrend_full(high, low, close)
    E = SM.compute_smi_events(df, SMI_CFG)
    FMB = E["FMB"]; PD = E["PD"]; XDN = E["XDN"]
    
    times = [int(t.value // 1_000_000) for t in df.index]
    eng = V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, iv_ms)
    breaks, events = eng.run()
    ev_by_bar = {}
    for e in events: ev_by_bar.setdefault(e["bar"], []).append(e)
    
    # v2.b trigger
    samples = []
    pos_open = False; clear_bar = -1
    fmb_b = None; pd_b = None; wave_entry_done = False
    for i in range(n):
        if pos_open:
            if i >= clear_bar: pos_open = False; clear_bar = -1
            else: continue
        for e in ev_by_bar.get(i, []):
            if e["side"] != "bear": continue
            if e["event"] == "WAVE_STARTED":
                wave_entry_done = False
                if pd_b is None: fmb_b = None
            elif e["event"] in ("WAVE_CANCELLED", "WAVE_STRUCT_REJECTED",
                                "CANDIDATE_INVALIDATED", "CANDIDATE_EVICTED"):
                fmb_b = None; pd_b = None; wave_entry_done = False
        if not wave_entry_done:
            if FMB[i] and fmb_b is None: fmb_b = i
            if fmb_b is not None and pd_b is None and PD[i] and i >= fmb_b: pd_b = i
            if fmb_b is not None and pd_b is not None and XDN[i] and i >= pd_b:
                if st_trend[i] == -1:
                    entry = close[i]
                    daily_apct = get_daily_atr_pct(df.index[i])
                    samples.append(dict(bar=i, entry=entry, daily_apct=daily_apct, date=df.index[i]))
                    apct = atr_pct_at(df, i)
                    sl0 = entry * (1 + apct/100.0)
                    tp0 = entry - (sl0 - entry)
                    fwd_h2 = high[i+1:]; fwd_l2 = low[i+1:]
                    ck = 240
                    for k in range(len(fwd_h2)):
                        if fwd_l2[k] <= tp0 or fwd_h2[k] >= sl0 or k >= 240:
                            ck = k; break
                    clear_bar = i + 1 + ck
                    pos_open = True; wave_entry_done = True
                fmb_b = None; pd_b = None
    
    recent = [s for s in samples if s["date"] >= CUTOFF]
    
    pl_arr = find_pivot_lows(low, 3, 3)
    pl_dict = {bar: val for val, bar in pl_arr}
    
    def sl_o6(s):
        da = s.get("daily_apct")
        if da is None or np.isnan(da) or da <= 0: return None
        return s["entry"] * (1 + da/100.0)
    
    valid = []
    for s in recent:
        sl_val = sl_o6(s)
        if sl_val is not None and sl_val > s["entry"]:
            valid.append((s, sl_val))
    
    if len(valid) == 0:
        print("  NO VALID O6 SIGNALS\n")
        continue
    
    # Find all RAWBRK_HIT trades first
    rb_hits = []
    for idx, (s, sl) in enumerate(valid, 1):
        r = sim_rawbrk_detailed(s["entry"], s["bar"], sl, 3.0, high, low, close, n, pl_dict, df)
        if r["out"] == "RAWBRK_HIT":
            rb_hits.append((idx, s, sl, r))
    
    print(f"  Total signals: {len(valid)} | RAWBRK_HIT: {len(rb_hits)}\n")
    
    # Show up to 3 samples
    show_n = min(3, len(rb_hits))
    for sample_num, (orig_idx, s, sl, r) in enumerate(rb_hits[:show_n], 1):
        risk = sl - s["entry"]
        tp3 = s["entry"] - 3.0 * risk
        da_str = f"{s['daily_apct']:.1f}%" if s["daily_apct"] else "N/A"
        entry_wib = fmt_wib(s["date"])
        exit_idx = min(s["bar"] + r["bars"], n - 1)
        exit_wib = fmt_wib(df.index[exit_idx])
        
        print(f"  ═══ SAMPLE #{sample_num} (signal #{orig_idx}) ═══")
        print(f"  Entry  : {entry_wib} @ {s['entry']:.1f}")
        print(f"  SL O6  : {sl:.1f}  (ATR% 1D = {da_str})")
        print(f"  Risk   : {risk:.1f}  ({(risk/s['entry']*100):.1f}%)")
        print(f"  TP3x   : {tp3:.1f}  ({((s['entry']-tp3)/s['entry']*100):.1f}% dari entry)")
        print(f"  Exit   : {exit_wib} @ {r['ex']:.1f}  → RAWBRK_HIT")
        print(f"  Bars   : {r['bars']}  |  R = {r['R']:+.2f}")
        print()
        
        if len(r["rb_events"]) == 0:
            print(f"  ⚠️  NO RAW EVENTS — ini aneh. Seharusnya ada rawbreak sebelum HIT.")
        else:
            print(f"  RAW BREAK EVENT TIMELINE ({len(r['rb_events'])} events):")
            print(f"  {'':->3} {'':->17} {'':>10} {'':>10} {'':>10} {'':>8} {'':>8}")
            print(f"  {'#':>3} {'DATE WIB':>17} {'CLOSE':>10} {'PIVOT_LOW':>10} {'HIGH':>10} {'SL OLD':>8} {'SL NEW':>8}")
            print(f"  {'':->3} {'':->17} {'':>10} {'':>10} {'':>10} {'':>8} {'':>8}")
            
            for ei, ev in enumerate(r["rb_events"], 1):
                old_str = f"{ev['rb_sl_old']:.0f}" if ev['rb_sl_old'] else "None"
                print(f"  {ei:>3} {ev['date_wib']:>17} {ev['close']:>10.1f} {ev['pivot_low']:>10.1f} {ev['high']:>10.1f} {old_str:>8} {ev['rb_sl_new']:>8.0f}")
            
            # Show SL evolution
            print(f"\n  SL RAWBRK EVOLUTION:")
            print(f"  Initial SL O6 = {sl:.0f}")
            for ei, ev in enumerate(r["rb_events"], 1):
                arrow = "→" if ev['rb_sl_old'] else "→"
                print(f"    RB #{ei} {ev['date_wib']}: close={ev['close']:.0f} < PL={ev['pivot_low']:.0f}  {arrow} rb_sl={ev['rb_sl_new']:.0f}")
            print(f"  Final HIT  {exit_wib}: high={high[exit_idx]:.0f} >= rb_sl={r['rawbreak_price']:.0f}")
            print(f"  Profit saved: {s['entry'] - r['ex']:.0f} pts ({(s['entry']-r['ex'])/s['entry']*100:.1f}%)")
        print()

print("="*70)
print("  DONE")
print("="*70)
