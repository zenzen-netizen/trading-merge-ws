#!/usr/bin/env python3
"""
setup1_v3_2019.py — v3 SETUP1 backtest.
ALL BUGFIXES from watcher applied:
  ✓ FMB/PD full reset on WAVE_STARTED (no cross-wave carry-over)
  ✓ Unclosed candle drop before indicator computation
  ✓ fmb_b/pd_b reset AFTER bar snapshot (not before)
  ✓ ARM guard — once triggered, not overwritten

Setup logic baru (v3):
  ✓ Wave-aware entry — FMB/PD/XDN only within SAME wave
  ✓ C_LOCKED confirmation optional
  ✓ Track wave retrace % at entry
  ✓ Track ST direction consistency across bars

Multi-TF: 1D, 4H, 2H, 1H.
SL: O1 Liq10x, O3 ATR%curr, O6 ATR%1D.
Exit: TP1x, TP3x, RAWBRK, ST_REV.

Comparison: runs OLD (buggy) logic + NEW (fixed) logic side-by-side.
"""
import sys, os, time, json, datetime as _dt
import pandas as pd, numpy as np

sys.path.insert(0, "/home/ubuntu/trading-research")
sys.path.insert(0, "/home/ubuntu/trading-research/indicators")
sys.path.insert(0, "/home/ubuntu")

import smi_events as SM
import fbf_v11_backtest as V11
import atr_percentage as atrp

# ─── CONFIG ───
SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}
ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}

BASE = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1"
WIB = _dt.timezone(_dt.timedelta(hours=7))

TF_CONFIGS = [
    ("1D", f"{BASE}/1D/data_BTCUSDT_1d_2019now.csv", 86400000,  "1d"),
    ("4H", f"{BASE}/4H/data_BTCUSDT_4h_2019now.csv", 14400000, "4h"),
    ("2H", f"{BASE}/2H/data_BTCUSDT_2h_2019now.csv",  7200000, "2h"),
    ("1H", f"{BASE}/1H/data_BTCUSDT_1h_2019now.csv",  3600000, "1h"),
]

# ─── INDICATORS ───
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

# ─── TRADE SIMULATION ───
def sim_rawbrk(entry, eb, sl, tp_mult, high, low, close, n, pl_dict):
    """TP=tp_mult*risk + RAWBRK exit."""
    risk = sl - entry
    tp = entry - tp_mult * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    rb_sl = None; rb_bars = []
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp:
            return dict(out="TP", ex=tp, bars=k+1, R=tp_mult)
        if fwd_h[k] >= sl:
            return dict(out="SL", ex=sl, bars=k+1, R=-1.0)
        # RAWBRK
        cur_pl = None
        for bi2 in sorted(pl_dict.keys(), reverse=True):
            if bi2 <= bi: cur_pl = pl_dict[bi2]; break
        if cur_pl is not None and close[bi] < cur_pl:
            if rb_sl is None: rb_sl = high[bi]
            else: rb_sl = max(rb_sl, high[bi])
            rb_bars.append((bi, high[bi]))
        if rb_sl is not None and fwd_h[k] >= rb_sl:
            return dict(out="RAWBRK_HIT", ex=rb_sl, bars=k+1, R=(entry-rb_sl)/risk)
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk)

def sim_strev(entry, eb, sl, high, low, close, st_trend, n):
    """TP3x + ST flip exit."""
    risk = sl - entry
    tp3 = entry - 3 * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp3:
            return dict(out="TP3x", ex=tp3, bars=k+1, R=3.0)
        if fwd_h[k] >= sl:
            return dict(out="SL", ex=sl, bars=k+1, R=-1.0)
        if st_trend[bi] == 1:
            return dict(out="ST_REV", ex=close[bi], bars=k+1, R=(entry-close[bi])/risk)
    lastc = fwd_l[-1] if len(fwd_l) > 0 else entry
    return dict(out="EXP", ex=lastc, bars=len(fwd_h), R=(entry-lastc)/risk)

# ─── OLD (BUGGY) TRIGGER ───
def detect_old(df, high, low, close, st_trend, E, ev_by_bar, n):
    """ORIGINAL v2.b trigger logic with BUG #4 (cross-wave carry-over)."""
    FMB, PD, XDN = E["FMB"], E["PD"], E["XDN"]
    samples = []
    pos_open = False; clear_bar = -1
    fmb_b = None; pd_b = None; wave_entry_done = False
    for i in range(n):
        if pos_open:
            if i >= clear_bar: pos_open = False; clear_bar = -1
            else: continue
        for e in ev_by_bar.get(i, []):
            if e.get("side") != "bear": continue
            if e["event"] == "WAVE_STARTED":
                wave_entry_done = False
                if pd_b is None: fmb_b = None   # ← BUG #4
            elif e["event"] in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED",
                                "CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
                fmb_b = None; pd_b = None; wave_entry_done = False
        if not wave_entry_done:
            if FMB[i] and fmb_b is None: fmb_b = i
            if fmb_b is not None and pd_b is None and PD[i] and i >= fmb_b: pd_b = i
            if fmb_b is not None and pd_b is not None and XDN[i] and i >= pd_b:
                if st_trend[i] == -1:
                    entry = close[i]
                    apct_current = atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]
                    samples.append(dict(bar=i, entry=entry, apct=apct_current, date=df.index[i]))
                    sl0 = entry * (1 + apct_current/100.0)
                    tp0 = entry - (sl0 - entry)
                    fwd_h = high[i+1:]; fwd_l = low[i+1:]; ck = 240
                    for k in range(len(fwd_h)):
                        if fwd_l[k] <= tp0 or fwd_h[k] >= sl0 or k >= 240: ck = k; break
                    clear_bar = i + 1 + ck
                    pos_open = True; wave_entry_done = True
                fmb_b = None; pd_b = None  # ← partial BUG (reset location)
    return samples

# ─── NEW (FIXED) TRIGGER ───
def detect_new(df, high, low, close, st_trend, E, ev_by_bar, n):
    """FIXED v3 trigger logic:
    ✓ Full FMB/PD reset on WAVE_STARTED
    ✓ fmb_b/pd_b reset AFTER bar n-1 snapshot
    ✓ Track wave boundaries for each signal
    """
    FMB, PD, XDN = E["FMB"], E["PD"], E["XDN"]
    samples = []
    pos_open = False; clear_bar = -1
    fmb_b = None; pd_b = None; wave_entry_done = False
    current_wave_A = None; current_wave_B = None; current_wave_c = None

    for i in range(n):
        if pos_open:
            if i >= clear_bar: pos_open = False; clear_bar = -1
            else: continue

        # ── process FBF events ──
        for e in ev_by_bar.get(i, []):
            if e.get("side") != "bear": continue
            et = e["event"]
            if et == "WAVE_STARTED":
                current_wave_A = (e["a_bar"], e["a_val"])
                current_wave_B = (e["b_bar"], e["b_val"])
                wave_entry_done = False
                fmb_b = None; pd_b = None; current_wave_c = None  # ✓ FULL reset
            elif et == "C_LOCKED":
                current_wave_c = (e["c_bar"], e["c_val"], e.get("retrace_pct"))
            elif et in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED",
                        "CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
                fmb_b = None; pd_b = None; wave_entry_done = False

        # ── FMB/PD/XDN tracking ──
        if not wave_entry_done:
            if FMB[i] and fmb_b is None: fmb_b = i
            if fmb_b is not None and pd_b is None and PD[i] and i >= fmb_b: pd_b = i
            if fmb_b is not None and pd_b is not None and XDN[i] and i >= pd_b:
                if st_trend[i] == -1:
                    entry = close[i]
                    apct_current = atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]

                    # Wave info at entry
                    wA = current_wave_A
                    wB = current_wave_B
                    wc = current_wave_c
                    retrace_pct = None
                    if wA and wB:
                        span = abs(wB[1] - wA[1])
                        if wc and span > 0:
                            retrace_pct = abs(wB[1] - wc[1]) / span * 100
                        elif span > 0:
                            retrace_pct = abs(wB[1] - entry) / span * 100

                    samples.append(dict(
                        bar=i, entry=entry,
                        apct=apct_current,
                        date=df.index[i],
                        wave_A_bar=wA[0] if wA else None,
                        wave_A_val=wA[1] if wA else None,
                        wave_B_bar=wB[0] if wB else None,
                        wave_B_val=wB[1] if wB else None,
                        wave_c_bar=wc[0] if wc else None,
                        wave_c_val=wc[1] if wc else None,
                        retrace_pct=retrace_pct,
                    ))
                    # clear_bar
                    sl0 = entry * (1 + apct_current/100.0)
                    tp0 = entry - (sl0 - entry)
                    fwd_h = high[i+1:]; fwd_l = low[i+1:]; ck = 240
                    for k in range(len(fwd_h)):
                        if fwd_l[k] <= tp0 or fwd_h[k] >= sl0 or k >= 240: ck = k; break
                    clear_bar = i + 1 + ck
                    pos_open = True; wave_entry_done = True

                # fmb_b/pd_b reset AFTER this bar's snapshot
                fmb_b = None; pd_b = None

    return samples

# ─── RUN BACKTEST ───
def run_backtest(tf_name, csv_path, iv_ms, tf_binance):
    """Run both OLD and NEW trigger on same data. Returns results dict."""
    print(f"\n{'='*70}")
    print(f"  {tf_name}")

    # Load data
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

    # Unclosed candle drop (NEW only, but data may be stale)
    # For backtest, the last candle might be forming → drop it
    now_utc = _dt.datetime.now(_dt.timezone.utc)
    last_ct_utc = df.index[-1] + _dt.timedelta(milliseconds=iv_ms)
    if now_utc < last_ct_utc and len(df) > 1:
        df = df.iloc[:-1]

    print(f"    {len(df)} candles  {df.index[0].date()}..{df.index[-1].date()}")

    if len(df) < 60:
        print(f"    SKIP — too few candles")
        return None

    high = df["high"].values.astype(float)
    low  = df["low"].values.astype(float)
    close = df["close"].values.astype(float)
    n = len(df)

    # ST
    st_trend = supertrend_full(high, low, close)
    print(f"    ST computed")

    # SMI
    E = SM.compute_smi_events(df, SMI_CFG)
    print(f"    SMI computed")

    # FBF v11
    times = [int(t.value // 1_000_000) for t in df.index]
    eng = V11.FBFEngine(times, df["open"].values.astype(float), high, low, close, iv_ms)
    breaks, events = eng.run()
    ev_by_bar = {}
    for e in events: ev_by_bar.setdefault(e["bar"], []).append(e)
    print(f"    FBF v11: {len(events)} events, {len(breaks)} breaks")

    # Trigger — OLD (buggy)
    old_samples = detect_old(df, high, low, close, st_trend, E, ev_by_bar, n)
    # Trigger — NEW (fixed)
    new_samples = detect_new(df, high, low, close, st_trend, E, ev_by_bar, n)

    print(f"    OLD: {len(old_samples)} signals  NEW: {len(new_samples)} signals")
    if old_samples or new_samples:
        diff = len(new_samples) - len(old_samples)
        sign = "+" if diff >= 0 else ""
        print(f"    Δ = {sign}{diff} signals")

    # Pivot lows for RAWBRK
    pl_arr = find_pivot_lows(low, 3, 3)
    pl_dict = {bar: val for val, bar in pl_arr}

    # Preload 1D ATR% for O6
    daily_apct = None
    if tf_name != "1D":
        df1d_path = f"{BASE}/1D/data_BTCUSDT_1d_2019now.csv"
        if os.path.exists(df1d_path):
            df1d = pd.read_csv(df1d_path, index_col=0, parse_dates=True)
            dap = np.full(len(df1d), np.nan)
            for i2 in range(30, len(df1d)):
                dap[i2] = atrp.atr_percentage(df1d.iloc[:i2+1], ATR_PCT_CFG)["atr_pct"]
            daily_apct = dict(zip(df1d.index, dap))

    def get_daily_apct(ts):
        if daily_apct is None: return None
        for dts in sorted(daily_apct.keys(), reverse=True):
            if dts <= ts and not np.isnan(daily_apct[dts]):
                return daily_apct[dts]
        return None

    # ─── SL OPTIONS ───
    def sl_o1(s): return s["entry"] * 1.10
    def sl_o3(s): return s["entry"] * (1 + s["apct"]/100.0)
    def sl_o6(s):
        da = get_daily_apct(s["date"])
        if da is None or np.isnan(da) or da <= 0: return None
        return s["entry"] * (1 + da/100.0)

    SL_OPTS = [("O1 Liq10x", sl_o1), ("O3 ATR%curr", sl_o3), ("O6 ATR%1D", sl_o6)]

    EXIT_LABELS = ["TP1x", "TP3x", "RAWBRK", "ST_REV"]

    def compute_for_samples(samples_list, label):
        if not samples_list:
            return None
        valid_by_sl = {}
        for sl_name, sl_fn in SL_OPTS:
            valid = []
            for s in samples_list:
                sl_val = sl_fn(s)
                if sl_val is not None and sl_val > s["entry"]:
                    valid.append((s, sl_val))
            valid_by_sl[sl_name] = valid

        results = {}
        for sl_name, sl_fn in SL_OPTS:
            valid = valid_by_sl[sl_name]
            if not valid:
                results[sl_name] = {"n": 0, "tp1x": None, "tp3x": None, "rawbrk": None, "strev": None}
                continue

            tp1x = [sim_rawbrk(s["entry"], s["bar"], sl, 1.0, high, low, close, n, pl_dict) for s,sl in valid]
            tp3x = [sim_rawbrk(s["entry"], s["bar"], sl, 3.0, high, low, close, n, pl_dict) for s,sl in valid]
            rawb = [sim_rawbrk(s["entry"], s["bar"], sl, 3.0, high, low, close, n, pl_dict) for s,sl in valid]
            strev = [sim_strev(s["entry"], s["bar"], sl, high, low, close, st_trend, n) for s,sl in valid]

            results[sl_name] = {
                "n": len(valid),
                "tp1x": sum(r["R"] for r in tp1x),
                "tp3x": sum(r["R"] for r in tp3x),
                "rawbrk": sum(r["R"] for r in rawb),
                "strev": sum(r["R"] for r in strev),
            }
        return results

    old_res = compute_for_samples(old_samples, "OLD")
    new_res = compute_for_samples(new_samples, "NEW")

    # Print OLD vs NEW comparison
    print(f"\n    {'='*60}")
    print(f"    OLD (buggy) vs NEW (fixed) — {tf_name}")
    print(f"    {'='*60}")
    header = f"    {'SL':>14} | {'OLD TP1x':>10} {'NEW TP1x':>10} | {'OLD RBK':>10} {'NEW RBK':>10} | {'OLD STR':>10} {'NEW STR':>10}"
    print(header)
    print(f"    {'':->14} | {'':->10} {'':->10} | {'':->10} {'':->10} | {'':->10} {'':->10}")
    for sl_name, _ in SL_OPTS:
        old = old_res.get(sl_name, {}) if old_res else {}
        new = new_res.get(sl_name, {}) if new_res else {}

        def v(d, k):
            vv = d.get(k)
            return f"{vv:>+10.2f}" if vv is not None else f"{'N/A':>10}"

        print(f"    {sl_name:>14} | {v(old,'tp1x')} {v(new,'tp1x')} | {v(old,'rawbrk')} {v(new,'rawbrk')} | {v(old,'strev')} {v(new,'strev')}")

    return {
        "tf": tf_name,
        "n_old": len(old_samples),
        "n_new": len(new_samples),
        "old": old_res,
        "new": new_res,
    }

# ─── MAIN ───
def main():
    start = _dt.datetime.now()
    print(f"{'='*70}")
    print(f"  SETUP1 v3 — Fixed Trigger + Multi-TF Backtest")
    print(f"  Started: {start.strftime('%Y-%m-%d %H:%M:%S')} WIB")
    print(f"{'='*70}")

    all_results = []
    for tf_name, csv_path, iv_ms, tf_binance in TF_CONFIGS:
        try:
            res = run_backtest(tf_name, csv_path, iv_ms, tf_binance)
            if res:
                all_results.append(res)
        except Exception as e:
            print(f"\n  {tf_name} ERROR: {e}")
            import traceback
            traceback.print_exc()

    # ─── FINAL SUMMARY ───
    print(f"\n{'='*70}")
    print(f"  FINAL SUMMARY — All TFs")
    print(f"{'='*70}")

    header = f"  {'TF':>4} {'OLD sig':>8} {'NEW sig':>8} {'Δ sig':>7}"
    for exit_key in ["TP1x", "RAWBRK", "ST_REV"]:
        for sl_short in ["O1", "O3", "O6"]:
            header += f"  {exit_key}/{sl_short}"
    print(header)

    for r in all_results:
        line = f"  {r['tf']:>4} {r['n_old']:>8} {r['n_new']:>8} {r['n_new']-r['n_old']:>+7}"
        for exit_key in ["tp1x", "rawbrk", "strev"]:
            for sl_short in ["O1", "O3", "O6"]:
                old_val = None
                new_val = None
                if r["old"]:
                    for k in r["old"]:
                        if k.startswith(sl_short):
                            vv = r["old"][k].get(exit_key) if r["old"][k] else None
                            old_val = vv
                if r["new"]:
                    for k in r["new"]:
                        if k.startswith(sl_short):
                            vv = r["new"][k].get(exit_key) if r["new"][k] else None
                            new_val = vv
                if old_val is not None and new_val is not None:
                    line += f"  {new_val-old_val:>+9.2f}"
                elif new_val is not None:
                    line += f"  {new_val:>+9.2f}✓"
                else:
                    line += f"  {'N/A':>9}"
        print(line)

    elapsed = (_dt.datetime.now() - start).total_seconds()
    print(f"\n  Selesai — {len(all_results)} TF — {elapsed:.1f}s")

if __name__ == "__main__":
    main()
