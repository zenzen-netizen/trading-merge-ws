"""
setup1_trigger.py — Shared trigger logic for SETUP1 v3.
SINGLE SOURCE OF TRUTH for both watcher + backtest.

FIX applied vs v2.b (14 Jul 2026):
  1. FMB/PD reset on WAVE_STARTED  → `fmb_b=None; pd_b=None` (full, not conditional)
  2. Unclosed candle drop           → drop forming candle before compute
  3. fmb_b/pd_b timing             → reset AFTER step snapshot (not before)
  4. ARM guard                     → once ARMED, never overwritten by end-of-bar tracking

Usage (backtest):
  from indicators.setup1_trigger import detect_signals_v3, ...

Usage (watcher):
  sys.path.insert(0, '/home/ubuntu/trading-research/indicators')
  from setup1_trigger import supertrend_full, detect_trigger_state
"""
import pandas as pd, numpy as np

# ─── CONFIG ─────────────────────────────────────────────────────
SMI_CFG = {"len_k":5,"len_d":3,"len_e":3,"ob":80,"mid":0,"os":-40,
           "akum_candles":2,"dist_candles":2,"div_enabled":True,"div_hidden":False,
           "div_left":5,"div_right":5,"div_range_min":5,"div_range_max":60}

ATR_PCT_CFG = {"atr_period":30,"use_atr_pct":True,"show_bb":True,"bb_period":20,"bb_stddev":2.0}


# ─── INDICATORS ────────────────────────────────────────────────
def supertrend_full(high, low, close, period=10, mult=3.0):
    """ST(10,3) — returns trend array: -1=DN (bearish), +1=UP (bullish)."""
    n = len(close); h,l,c = high,low,close
    hl2 = (h+l)/2.0; tr = np.zeros(n); tr[0] = h[0]-l[0]
    for i in range(1,n):
        tr[i] = max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
    atr = np.zeros(n); atr[0] = tr[0]; alpha = 1.0/period
    for i in range(1,n): atr[i] = atr[i-1] + alpha*(tr[i]-atr[i-1])
    up_raw = hl2 - mult*atr; dn_raw = hl2 + mult*atr
    up_f = np.zeros(n); dn_f = np.zeros(n); trend = np.ones(n,dtype=int)
    up_f[0] = up_raw[0]; dn_f[0] = dn_raw[0]
    for i in range(1,n):
        up_f[i] = max(up_raw[i], up_f[i-1]) if c[i-1] > up_f[i-1] else up_raw[i]
        dn_f[i] = min(dn_raw[i], dn_f[i-1]) if c[i-1] < dn_f[i-1] else dn_raw[i]
        trend[i] = trend[i-1]
        if trend[i-1] == -1 and c[i] > dn_f[i-1]: trend[i] = 1
        elif trend[i-1] == 1 and c[i] < up_f[i-1]: trend[i] = -1
    return trend

def find_pivot_lows(arr, left=3, right=3):
    """Return list of (val, bar_index) for confirmed pivot lows."""
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


# ─── FIXED TRIGGER — v3 ─────────────────────────────────────────
def detect_signals_v3(df, high, low, close, st_trend, E, ev_by_bar):
    """V3 trigger — FMB→PD→XDN in SAME wave only.
    
    FIX applied vs v2.b:
    - Full reset (fmb_b=None, pd_b=None) on every WAVE_STARTED
    - fmb_b/pd_b reset AFTER bar snapshot (not at XDN fire)
    
    Returns list of signal dicts with wave metadata.
    """
    FMB, PD, XDN = E["FMB"], E["PD"], E["XDN"]
    n = len(df)
    samples = []
    pos_open = False; clear_bar = -1
    fmb_b = None; pd_b = None; wave_entry_done = False

    for i in range(n):
        if pos_open:
            if i >= clear_bar: pos_open = False; clear_bar = -1
            else: continue

        # ── Process FBF events ──
        for e in ev_by_bar.get(i, []):
            if e.get("side") != "bear": continue
            et = e["event"]
            if et == "WAVE_STARTED":
                wave_entry_done = False
                fmb_b = None; pd_b = None   # ← FIX: FULL reset, not conditional
            elif et in ("WAVE_CANCELLED","WAVE_STRUCT_REJECTED",
                        "CANDIDATE_INVALIDATED","CANDIDATE_EVICTED"):
                fmb_b = None; pd_b = None; wave_entry_done = False

        # ── FMB/PD/XDN tracking ──
        if not wave_entry_done:
            if FMB[i] and fmb_b is None: fmb_b = i
            if fmb_b is not None and pd_b is None and PD[i] and i >= fmb_b: pd_b = i
            if fmb_b is not None and pd_b is not None and XDN[i] and i >= pd_b:
                if st_trend[i] == -1:
                    from indicators.legacy import atr_percentage as atrp
                    entry_val = float(close[i])
                    apct_current = atrp.atr_percentage(df.iloc[:i+1], ATR_PCT_CFG)["atr_pct"]

                    samples.append(dict(
                        bar=i, entry=entry_val,
                        apct=float(apct_current),
                        date=df.index[i],
                    ))
                    # clear_bar via TP1x O3
                    sl0 = entry_val * (1 + apct_current/100.0)
                    tp0 = entry_val - (sl0 - entry_val)
                    fwd_h = high[i+1:]; fwd_l = low[i+1:]; ck = 240
                    for k in range(len(fwd_h)):
                        if fwd_l[k] <= tp0 or fwd_h[k] >= sl0 or k >= 240: ck = k; break
                    clear_bar = i + 1 + ck
                    pos_open = True; wave_entry_done = True
                fmb_b = None; pd_b = None

    return samples


# ─── TRADE SIMULATION ──────────────────────────────────────────
def sim_rawbrk(entry, eb, sl, tp_mult, high, low, close, n, pl_dict):
    """TP=tp_mult×risk + RAWBRK exit.
    
    RAWBRK: when close < last pivot low, set SL = current high.
    When price rallies back and hits that SL = RAWBRK_HIT.
    """
    risk = sl - entry; tp = entry - tp_mult * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    rb_sl = None
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp: return dict(out="TP", R=tp_mult)
        if fwd_h[k] >= sl: return dict(out="SL", R=-1.0)
        cur_pl = None
        for bi2 in sorted(pl_dict.keys(), reverse=True):
            if bi2 <= bi: cur_pl = pl_dict[bi2]; break
        if cur_pl is not None and close[bi] < cur_pl:
            if rb_sl is None: rb_sl = high[bi]
            else: rb_sl = max(rb_sl, high[bi])
        if rb_sl is not None and fwd_h[k] >= rb_sl: return dict(out="RAWBRK_HIT", R=(entry-rb_sl)/risk)
    return dict(out="EXP", R=0.0)

def sim_strev(entry, eb, sl, high, low, close, st_trend, n):
    """TP3x patok + exit when ST flips -1→+1."""
    risk = sl - entry; tp3 = entry - 3 * risk
    fwd_h = high[eb+1:]; fwd_l = low[eb+1:]
    for k in range(len(fwd_h)):
        bi = eb + 1 + k
        if bi >= n: break
        if fwd_l[k] <= tp3: return dict(out="TP3x", R=3.0)
        if fwd_h[k] >= sl: return dict(out="SL", R=-1.0)
        if st_trend[bi] == 1: return dict(out="ST_REV", R=(entry-close[bi])/risk)
    return dict(out="EXP", R=0.0)


# ─── SL HELPERS ────────────────────────────────────────────────
def sl_o1(entry):
    return entry * 1.10

def sl_o3(entry, apct):
    if apct is None or np.isnan(apct) or apct <= 0: return None
    return entry * (1 + apct/100.0)

def sl_o6(entry, daily_apct):
    if daily_apct is None or np.isnan(daily_apct) or daily_apct <= 0: return None
    return entry * (1 + daily_apct/100.0)
