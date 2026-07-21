"""
sample_o6_rawbrk_2025.py — O6 (ATR% 1D) + RAWBRK, TP1x & TP3x, 4H & 2H, >= 2025 only.
Shows per-trade details: date, entry, SL, TP, daily_atr%, outcome, bars, R.
"""
import sys, os
sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu")
import pandas as pd, numpy as np

SMI_CFG = {
    "len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
    "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
    "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60
}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

BASE = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1"

# ────────────────────────────────────────────
# UTC → WIB converter (UTC+7)
# ────────────────────────────────────────────
from datetime import timezone, timedelta
WIB = timezone(timedelta(hours=7))

def fmt_wib(ts):
    """Format pandas Timestamp in WIB timezone."""
    return ts.tz_convert(WIB).strftime("%d %b %Y %H:%M")

# ────────────────────────────────────────────
# PHASE 0: Preload 1D data for O6 anchor
# ────────────────────────────────────────────
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

# ────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────
import smi_events as SM
import fbf_v11_backtest as V11

def supertrend_full(high, low, close, period=10, mult=3.0):
    n = len(close)
    h, l, c = high, low, close
    hl2 = (h+l)/2.0
    tr = np.zeros(n); tr[0] = h[0]-l[0]
    for i in range(1,n):
        tr[i] = max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
    atr = np.zeros(n); atr[0] = tr[0]; alpha = 1.0/period
    for i in range(1,n): atr[i] = atr[i-1] + alpha*(tr[i]-atr[i-1])
    up_raw = hl2 - mult*atr
    dn_raw = hl2 + mult*atr
    up_f = np.zeros(n); dn_f = np.zeros(n); trend = np.ones(n, dtype=int)
    up_f[0] = up_raw[0]; dn_f[0] = dn_raw[0]
    for i in range(1,n):
        up_f[i] = max(up_raw[i], up_f[i-1]) if c[i-1] > up_f[i-1] else up_raw[i]
        dn_f[i] = min(dn_raw[i], dn_f[i-1]) if c[i-1] < dn_f[i-1] else dn_raw[i]
        trend[i] = trend[i-1]
        if trend[i-1] == -1 and c[i] > dn_f[i-1]: trend[i] = 1
        elif trend[i-1] == 1 and c[i] < up_f[i-1]: trend[i] = -1
    return trend

def find_pivot_lows(arr, left=3, right=3):
    out = []
    for ii in range(left, len(arr)-right):
        v = arr[ii]; ok = True
        for j in range(ii-left, ii):
            if arr[j] <= v: ok = False; break
        if ok:
            for j in range(ii+1, ii+right+1):
                if arr[j] <= v: ok = False; break
        if ok: out.append((v, ii))
    return out

def atr_pct_at(df_slice, idx):
    return atrp.atr_percentage(df_slice.iloc[:idx+1], ATR_PCT_CFG)["atr_pct"]

def sim_rawbrk(entry, eb, sl, tp_mult, high, low, close, n, pl_dict):
    """RAWBRK sim for a single trade."""
    risk = sl - entry
    tp = entry - tp_mult * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    rb_sl = None; rb_count = 0
    
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        # TP hit
        if fwd_l[k] <= tp:
            return dict(out="TP", ex=tp, bars=k+1, R=tp_mult, rawbreak_count=rb_count)
        # SL hit
        if fwd_h[k] >= sl:
            return dict(out="SL", ex=sl, bars=k+1, R=-1.0, rawbreak_count=rb_count)
        # RAWBRK_HIT (from PREVIOUS trigger, not this candle's trigger)
        if rb_sl is not None and fwd_h[k] >= rb_sl:
            return dict(out="RAWBRK_HIT", ex=rb_sl, bars=k+1, R=(entry-rb_sl)/risk, rawbreak_count=rb_count, rawbreak_price=rb_sl)
        # RAWBRK trigger — only SET rb_sl, don't check hit this candle
        cur_pl = None
        for bi2 in sorted(pl_dict.keys(), reverse=True):
            if bi2 <= bi: cur_pl = pl_dict[bi2]; break
        if cur_pl is not None and close[bi] < cur_pl:
            if rb_sl is None: rb_sl = high[bi]
            else: rb_sl = max(rb_sl, high[bi])
            rb_count += 1
    
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk, rawbreak_count=rb_count)

def sim_pure(entry, eb, sl, tp_mult, high, low, close, n):
    """Pure TP vs SL, NO rawbreak."""
    risk = sl - entry
    tp = entry - tp_mult * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp:
            return dict(out="TP", ex=tp, bars=k+1, R=tp_mult)
        if fwd_h[k] >= sl:
            return dict(out="SL", ex=sl, bars=k+1, R=-1.0)
    
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk)

def sim_st_rev(entry, eb, sl, high, low, close, st_trend, n):
    """ST_REV: TP3x patok, exit when ST flips -1→+1."""
    risk = sl - entry
    tp3 = entry - 3 * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp3:
            return dict(out="TP", ex=tp3, bars=k+1, R=3.0)
        if fwd_h[k] >= sl:
            return dict(out="SL", ex=sl, bars=k+1, R=-1.0)
        if st_trend[bi] == 1:  # ST flipped UP
            return dict(out="ST_REV", ex=close[bi], bars=k+1, R=(entry-close[bi])/risk)
    
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk)

# ────────────────────────────────────────────
# RUN per TF
# ────────────────────────────────────────────
TF_CONFIGS = [
    ("4H", f"{BASE}/4H/data_BTCUSDT_4h_2019now.csv", 14400000),
    ("2H", f"{BASE}/2H/data_BTCUSDT_2h_2019now.csv",  7200000),
]

CUTOFF = pd.Timestamp("2026-01-01", tz="UTC")

for tf_name, csv_path, iv_ms in TF_CONFIGS:
    print(f"\n{'='*70}")
    print(f"  {tf_name} — O6 (ATR% 1D) — 2026 only (WIB)")
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
                    apct_current = atr_pct_at(df, i)
                    daily_apct = get_daily_atr_pct(df.index[i])
                    samples.append(dict(
                        bar=i, entry=entry,
                        apct=apct_current,
                        daily_apct=daily_apct,
                        date=df.index[i]
                    ))
                    sl0 = entry * (1 + apct_current/100.0)
                    tp0 = entry - (sl0 - entry)
                    fwd_h = high[i+1:]; fwd_l = low[i+1:]
                    ck = 240
                    for k in range(len(fwd_h)):
                        if fwd_l[k] <= tp0 or fwd_h[k] >= sl0 or k >= 240:
                            ck = k; break
                    clear_bar = i + 1 + ck
                    pos_open = True; wave_entry_done = True
                fmb_b = None; pd_b = None
    
    recent = [s for s in samples if s["date"] >= CUTOFF]
    
    if len(recent) == 0:
        print("  NO 2026+ SIGNALS\n")
        continue
    
    # Pivot lows (for RAWBRK only)
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
        print("  O6 SL invalid for all samples\n")
        continue
    
    N = len(valid)
    print(f"  Total sinyal: {len(samples)} | 2026: {N}\n")
    
    # ============================================================
    # A. TP1x STANDALONE (no RAWBRK)
    # ============================================================
    HEADER_A = f"  {'#':>3} {'DATE':>17} {'EXIT':>17} {'ENTRY':>10} {'SL O6':>10} {'ATR%1D':>7} {'TP1x':>10} {'OUT':>6} {'bars':>5} {'R':>8}"
    SEP_A    = f"  {'':->3} {'':->17} {'':->17} {'':->10} {'':->10} {'':->7} {'':->10} {'':->6} {'':->5} {'':->8}"
    
    print("  ── A. TP1x standalone (no RAWBRK) ──")
    print(HEADER_A)
    print(SEP_A)
    
    a_results = []
    a_dist = {}
    for idx, (s, sl) in enumerate(valid, 1):
        r = sim_pure(s["entry"], s["bar"], sl, 1.0, high, low, close, n)
        a_results.append(r)
        a_dist[r["out"]] = a_dist.get(r["out"], 0) + 1
        risk = sl - s["entry"]
        tp1 = s["entry"] - 1.0 * risk
        date_str = fmt_wib(s["date"])
        exit_idx = min(s["bar"] + r["bars"], n - 1)
        exit_str = fmt_wib(df.index[exit_idx])
        da_str = f"{s['daily_apct']:.1f}%"
        print(f"  {idx:>3} {date_str:>17} {exit_str:>17} {s['entry']:>10.1f} {sl:>10.1f} {da_str:>7} {tp1:>10.1f} {r['out']:>6} {r['bars']:>5} {r['R']:>+8.2f}")
    
    a_tot = sum(r["R"] for r in a_results)
    a_tp = sum(1 for r in a_results if r["out"]=="TP")
    a_sl = sum(1 for r in a_results if r["out"]=="SL")
    a_exp = sum(1 for r in a_results if r["out"]=="EXP")
    
    print(SEP_A)
    print(f"  {'':>3} {'':>17} {'':>10} {'':>10} {'':>7} {'':>10} WIN:{a_tp:>2}/{N:<3} {'':>5} {a_tot:>+8.2f}")
    
    parts_a = []
    if a_tp > 0: parts_a.append(f"TP {a_tp}× +{a_tp*1.0:+.2f}")
    if a_sl > 0: parts_a.append(f"SL {a_sl}× {a_sl*-1.0:+.2f}")
    if a_exp > 0: parts_a.append(f"EXP {a_exp}×")
    print(f"  Breakdown: {' | '.join(parts_a)} → SumR {a_tot:+.2f}")
    
    # ============================================================
    # B. TP3x STANDALONE (no RAWBRK)
    # ============================================================
    HEADER_B = f"\n  {'#':>3} {'DATE':>17} {'EXIT':>17} {'ENTRY':>10} {'SL O6':>10} {'ATR%1D':>7} {'TP3x':>10} {'OUT':>6} {'bars':>5} {'R':>8}"
    SEP_B    = f"  {'':->3} {'':->17} {'':->17} {'':->10} {'':->10} {'':->7} {'':->10} {'':->6} {'':->5} {'':->8}"
    
    print("  ── B. TP3x standalone (no RAWBRK) ──")
    print(HEADER_B)
    print(SEP_B)
    
    b_results = []
    b_dist = {}
    for idx, (s, sl) in enumerate(valid, 1):
        r = sim_pure(s["entry"], s["bar"], sl, 3.0, high, low, close, n)
        b_results.append(r)
        b_dist[r["out"]] = b_dist.get(r["out"], 0) + 1
        risk = sl - s["entry"]
        tp3 = s["entry"] - 3.0 * risk
        date_str = fmt_wib(s["date"])
        exit_idx = min(s["bar"] + r["bars"], n - 1)
        exit_str = fmt_wib(df.index[exit_idx])
        da_str = f"{s['daily_apct']:.1f}%"
        print(f"  {idx:>3} {date_str:>17} {exit_str:>17} {s['entry']:>10.1f} {sl:>10.1f} {da_str:>7} {tp3:>10.1f} {r['out']:>6} {r['bars']:>5} {r['R']:>+8.2f}")
    
    b_tot = sum(r["R"] for r in b_results)
    b_tp = sum(1 for r in b_results if r["out"]=="TP")
    b_sl = sum(1 for r in b_results if r["out"]=="SL")
    b_exp = sum(1 for r in b_results if r["out"]=="EXP")
    
    print(SEP_B)
    print(f"  {'':>3} {'':>17} {'':>10} {'':>10} {'':>7} {'':>10} WIN:{b_tp:>2}/{N:<3} {'':>5} {b_tot:>+8.2f}")
    
    parts_b = []
    if b_tp > 0: parts_b.append(f"TP {b_tp}× +{b_tp*3.0:+.2f}")
    if b_sl > 0: parts_b.append(f"SL {b_sl}× {b_sl*-1.0:+.2f}")
    if b_exp > 0: parts_b.append(f"EXP {b_exp}×")
    print(f"  Breakdown: {' | '.join(parts_b)} → SumR {b_tot:+.2f}")
    
    # ============================================================
    # C. TP3x + RAWBRK
    # ============================================================
    HEADER_C = f"\n  {'#':>3} {'DATE':>17} {'EXIT':>17} {'ENTRY':>10} {'SL O6':>10} {'ATR%1D':>7} {'TP3x':>10} {'OUT':>12} {'bars':>5} {'R':>8} {'RB#':>4}"
    SEP_C    = f"  {'':->3} {'':->17} {'':->17} {'':->10} {'':->10} {'':->7} {'':->10} {'':->12} {'':->5} {'':->8} {'':->4}"
    
    print("  ── C. TP3x + RAWBRK ──")
    print(HEADER_C)
    print(SEP_C)
    
    c_results = []
    c_dist = {}
    for idx, (s, sl) in enumerate(valid, 1):
        r = sim_rawbrk(s["entry"], s["bar"], sl, 3.0, high, low, close, n, pl_dict)
        c_results.append(r)
        c_dist[r["out"]] = c_dist.get(r["out"], 0) + 1
        risk = sl - s["entry"]
        tp3 = s["entry"] - 3.0 * risk
        date_str = fmt_wib(s["date"])
        exit_idx = min(s["bar"] + r["bars"], n - 1)
        exit_str = fmt_wib(df.index[exit_idx])
        da_str = f"{s['daily_apct']:.1f}%"
        print(f"  {idx:>3} {date_str:>17} {exit_str:>17} {s['entry']:>10.1f} {sl:>10.1f} {da_str:>7} {tp3:>10.1f} {r['out']:>12} {r['bars']:>5} {r['R']:>+8.2f} {r['rawbreak_count']:>4}")
    
    c_tot = sum(r["R"] for r in c_results)
    c_tp = sum(1 for r in c_results if r["out"]=="TP")
    c_sl = sum(1 for r in c_results if r["out"]=="SL")
    c_rb = sum(1 for r in c_results if r["out"]=="RAWBRK_HIT")
    c_exp = sum(1 for r in c_results if r["out"]=="EXP")
    c_rb_total = sum(r["rawbreak_count"] for r in c_results)
    
    print(SEP_C)
    print(f"  {'':>3} {'':>17} {'':>10} {'':>10} {'':>7} {'':>10} WIN:{c_tp:>2}/{N:<3} {'':>5} {c_tot:>+8.2f}")
    
    parts_c = []
    if c_tp > 0: parts_c.append(f"TP {c_tp}× +{c_tp*3.0:+.2f}")
    if c_sl > 0: parts_c.append(f"SL {c_sl}× {c_sl*-1.0:+.2f}")
    if c_rb > 0: parts_c.append(f"RAWBRK_HIT {c_rb}× (total +{sum(r['R'] for r in c_results if r['out']=='RAWBRK_HIT'):+.2f})")
    if c_exp > 0: parts_c.append(f"EXP {c_exp}×")
    print(f"  Breakdown: {' | '.join(parts_c)} → SumR {c_tot:+.2f}")
    
    # ============================================================
    # D. TP3x + ST_REV
    # ============================================================
    HEADER_D = f"\n  ── D. TP3x + ST_REV ──"
    HEADER_D2 = f"  {'#':>3} {'DATE':>17} {'EXIT':>17} {'ENTRY':>10} {'SL O6':>10} {'ATR%1D':>7} {'TP3x':>10} {'OUT':>8} {'bars':>5} {'R':>8}"
    SEP_D     = f"  {'':->3} {'':->17} {'':->17} {'':->10} {'':->10} {'':->7} {'':->10} {'':->8} {'':->5} {'':->8}"
    
    print(HEADER_D)
    print(HEADER_D2)
    print(SEP_D)
    
    d_results = []
    for idx, (s, sl) in enumerate(valid, 1):
        r = sim_st_rev(s["entry"], s["bar"], sl, high, low, close, st_trend, n)
        d_results.append(r)
        risk = sl - s["entry"]
        tp3 = s["entry"] - 3.0 * risk
        date_str = fmt_wib(s["date"])
        exit_idx = min(s["bar"] + r["bars"], n - 1)
        exit_str = fmt_wib(df.index[exit_idx])
        da_str = f"{s['daily_apct']:.1f}%"
        print(f"  {idx:>3} {date_str:>17} {exit_str:>17} {s['entry']:>10.1f} {sl:>10.1f} {da_str:>7} {tp3:>10.1f} {r['out']:>8} {r['bars']:>5} {r['R']:>+8.2f}")
    
    d_tot = sum(r["R"] for r in d_results)
    d_tp = sum(1 for r in d_results if r["out"]=="TP")
    d_sl = sum(1 for r in d_results if r["out"]=="SL")
    d_rev = sum(1 for r in d_results if r["out"]=="ST_REV")
    d_exp = sum(1 for r in d_results if r["out"]=="EXP")
    
    print(SEP_D)
    print(f"  {'':>3} {'':>17} {'':>10} {'':>10} {'':>7} {'':>10} WIN:{d_tp:>2}/{N:<3} {'':>5} {d_tot:>+8.2f}")
    
    d_strev_r = sum(r["R"] for r in d_results if r["out"]=="ST_REV")
    parts_d = []
    if d_tp > 0: parts_d.append(f"TP {d_tp}× +{d_tp*3.0:+.2f}")
    if d_sl > 0: parts_d.append(f"SL {d_sl}× {d_sl*-1.0:+.2f}")
    if d_rev > 0: parts_d.append(f"ST_REV {d_rev}× (total +{d_strev_r:+.2f})")
    if d_exp > 0: parts_d.append(f"EXP {d_exp}×")
    print(f"  Breakdown: {' | '.join(parts_d)} → SumR {d_tot:+.2f}")
    
    # ============================================================
    # CROSS-COMPARISON
    # ============================================================
    print(f"\n  ── COMPARISON ──")
    print(f"  {'Combo':<25} {'TP':>5} {'SL':>5} {'RB':>5} {'ST_REV':>7} {'SumR':>8}")
    print(f"  {'':->25} {'':->5} {'':->5} {'':->5} {'':->7} {'':->8}")
    print(f"  {'A. TP1x standalone':<25} {a_tp:>5} {a_sl:>5} {'-':>5} {'-':>7} {a_tot:>+8.2f}")
    print(f"  {'B. TP3x standalone':<25} {b_tp:>5} {b_sl:>5} {'-':>5} {'-':>7} {b_tot:>+8.2f}")
    print(f"  {'C. TP3x + RAWBRK':<25} {c_tp:>5} {c_sl:>5} {c_rb:>5} {'-':>7} {c_tot:>+8.2f}")
    print(f"  {'D. TP3x + ST_REV':<25} {d_tp:>5} {d_sl:>5} {'-':>5} {d_rev:>7} {d_tot:>+8.2f}")

print(f"\n{'='*70}")
print("  DONE")
print(f"{'='*70}")
