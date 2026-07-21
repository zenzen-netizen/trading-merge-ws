"""
robust_momcand.py — Python port of TradingView Pine "Robust + MomCand Signal".

Batch: new_set_v1 (2026-07-14). Sumber kebenaran:
    indicators/pine_source/new_set_v1_20260714/robust_momcand.pine (@version=6)

Dua layer (stage_03):
  - Layer numerik : 8 EMA (8/13/21/34/50/100/150/200), robust FAST/MAIN/SLOW
                    (median + MAD-clip MULT=2.5 lalu weighted mean), body/wick/ATR.
  - Layer fase    : rob_trend (up/dn/neutral), mom_bull/bear per mode,
                    crt_t1/t2, sig_bull/sig_bear, + teks-fase gabungan (mirror dashboard).

Catatan replikasi:
  - f_robust dihitung LINTAS-baris pada nilai EMA di bar yang sama (cross-sectional),
    bukan rolling waktu -> bisa row-wise.
  - ta.ema == pandas ewm(span=len, adjust=False), seed = nilai pertama (sama Pine).
  - Smart Stats pakai ta.median(body,200)+MAD*dev -> butuh 200 bar; di data pendek = NaN (warm-up).
  - HTF default "D": kalau TF chart == HTF (data 1D), is_ltf=False -> HTF = current TF (sesuai pine).
  - == vs >= dijaga; cascade switch/if-elif dijaga urutannya; per-bar, no lookahead.
"""

import numpy as np
import pandas as pd

MAD_MULT = 2.5


# ── helpers ────────────────────────────────────────────────────────────────
def _ema(s, length):
    """Pine ta.ema: alpha=2/(len+1), adjust=False, seed=first value."""
    return s.ewm(span=length, adjust=False).mean()


def _true_range(df):
    """Pine ta.tr(true): max(high-low, |high-prevclose|, |low-prevclose|); bar0 = high-low."""
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    tr.iloc[0] = (h.iloc[0] - l.iloc[0])
    return tr


def _smooth(s, length, method):
    if method == "EMA":
        return _ema(s, length)
    if method == "SMA":
        return s.rolling(length).mean()
    if method == "WMA":
        w = np.arange(1, length + 1)
        return s.rolling(length).apply(lambda x: np.dot(x, w) / w.sum(), raw=True)
    # RMA (Wilder) default
    return s.ewm(alpha=1.0 / length, adjust=False).mean()


def _robust_row(vals, wgts):
    """f_robust: median -> MAD -> clip [med-MAD*MULT, med+MAD*MULT] -> weighted mean."""
    vals = np.asarray(vals, dtype=float)
    wgts = np.asarray(wgts, dtype=float)
    med = np.median(vals)
    mad = np.median(np.abs(vals - med))
    lo, hi = med - mad * MAD_MULT, med + mad * MAD_MULT
    clipped = np.clip(vals, lo, hi)
    den = wgts.sum()
    return float(np.dot(clipped, wgts) / den) if den > 0 else float(med)


DEFAULTS = dict(
    rob_show_fast=True, rob_show_main=True, rob_show_slow=True,
    rob_align_mode="AND (semua harus align)",
    rob_stack_on=True, rob_stack_eq_ok=False,
    htf_on=True, htf_tf="D", htf_cross_which="FAST",
    mom_mode="Smart Stats",
    fp_min_pips=20.0, fp_pip_size=0.0001,
    atr_len=14, atr_mult=1.5, atr_smooth="RMA",
    qt_look=200, qt_dev=2.0, qt_max_wick=0.30,
    crt_c1_body_pct=60.0, crt_c2_body_pct=60.0, crt_c2_max_ratio=0.5,
    crt_close_inside=True, crt_dir="Both", crt_t1_on=True, crt_t2_on=True,
    side_mode="Both", rob_dir_on=False, rob_dir_mode="Only One Direction",
    chart_tf="1D",
)

_TF_SEC = {"1": 60, "5": 300, "15": 900, "60": 3600, "1H": 3600,
           "240": 14400, "4H": 14400, "1D": 86400, "D": 86400, "1W": 604800, "W": 604800}


def robust_momcand(df, cfg=None):
    """Return DataFrame per-candle: numerik + fase/state + teks-fase gabungan."""
    c = dict(DEFAULTS)
    if cfg:
        c.update(cfg)
    df = df.reset_index(drop=True).copy()
    o, h, l, cl = df["open"], df["high"], df["low"], df["close"]
    n = len(df)

    # ── EMA stack ──
    e = {
        1: _ema(cl, 8), 2: _ema(cl, 13), 3: _ema(cl, 21), 4: _ema(cl, 34),
        5: _ema(cl, 50), 6: _ema(cl, 100), 7: _ema(cl, 150), 8: _ema(cl, 200),
    }
    E = pd.DataFrame({k: v for k, v in e.items()})

    w_fast = [1.0, 1.5, 2.0, 2.5]
    w_main = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 4.5, 5.0]
    w_slow = [3.0, 4.0, 4.5, 5.0]

    rob_fast = E[[1, 2, 3, 4]].apply(lambda r: _robust_row(r.values, w_fast), axis=1)
    rob_main = E[[1, 2, 3, 4, 5, 6, 7, 8]].apply(lambda r: _robust_row(r.values, w_main), axis=1)
    rob_slow = E[[5, 6, 7, 8]].apply(lambda r: _robust_row(r.values, w_slow), axis=1)

    # ── HTF (data 1D + htf "D" -> is_ltf False -> current TF) ──
    sec_chart = _TF_SEC.get(str(c["chart_tf"]), 86400)
    sec_htf = _TF_SEC.get(str(c["htf_tf"]), 86400)
    is_ltf = c["htf_on"] and (sec_chart < sec_htf)
    # Data pendek: tanpa resample -> degrade ke current TF (pine behaviour saat not is_ltf)
    htf_fast, htf_main, htf_slow, htf_cls = rob_fast, rob_main, rob_slow, cl

    # ── Robust direction (current TF) ──
    sf, sm, ss = c["rob_show_fast"], c["rob_show_main"], c["rob_show_slow"]
    up_f, up_m, up_s = cl > rob_fast, cl > rob_main, cl > rob_slow
    dn_f, dn_m, dn_s = cl < rob_fast, cl < rob_main, cl < rob_slow
    T, F = pd.Series(True, index=df.index), pd.Series(False, index=df.index)

    up_and = (up_f if sf else T) & (up_m if sm else T) & (up_s if ss else T)
    dn_and = (dn_f if sf else T) & (dn_m if sm else T) & (dn_s if ss else T)
    up_any = (up_f if sf else F) | (up_m if sm else F) | (up_s if ss else F)
    dn_any = (dn_f if sf else F) | (dn_m if sm else F) | (dn_s if ss else F)

    up_pri_f = up_f if sf else (up_m if sm else up_s)
    up_pri_m = up_m if sm else (up_f if sf else up_s)
    up_pri_s = up_s if ss else (up_m if sm else up_f)
    dn_pri_f = dn_f if sf else (dn_m if sm else dn_s)
    dn_pri_m = dn_m if sm else (dn_f if sf else dn_s)
    dn_pri_s = dn_s if ss else (dn_m if sm else dn_f)

    am = c["rob_align_mode"]
    pick = {
        "AND (semua harus align)": (up_and, dn_and),
        "OR (salah satu cukup)": (up_any, dn_any),
        "Priority FAST": (up_pri_f, dn_pri_f),
        "Priority MAIN": (up_pri_m, dn_pri_m),
        "Priority SLOW": (up_pri_s, dn_pri_s),
    }.get(am, (up_and, dn_and))
    rob_trend_up, rob_trend_dn = pick[0].copy(), pick[1].copy()

    if c["rob_stack_on"] and sf and sm and ss:
        if c["rob_stack_eq_ok"]:
            st_bull = (rob_fast >= rob_main) & (rob_main >= rob_slow)
            st_bear = (rob_fast <= rob_main) & (rob_main <= rob_slow)
        else:
            st_bull = (rob_fast > rob_main) & (rob_main > rob_slow)
            st_bear = (rob_fast < rob_main) & (rob_main < rob_slow)
        rob_trend_up = rob_trend_up & st_bull
        rob_trend_dn = rob_trend_dn & st_bear

    # ── Momentum candle ──
    body = (cl - o).abs()
    full_rng = h - l
    wick_rat = np.where(full_rng > 0, (full_rng - body) / full_rng, np.nan)
    is_bull_c, is_bear_c = cl > o, cl < o

    mode = c["mom_mode"]
    crt_is_t1 = pd.Series(False, index=df.index)
    crt_is_t2 = pd.Series(False, index=df.index)
    mom_bull = pd.Series(False, index=df.index)
    mom_bear = pd.Series(False, index=df.index)

    if mode == "Fixed Pips":
        thresh = c["fp_min_pips"] * c["fp_pip_size"]
        pass_ = body >= thresh
        mom_bull, mom_bear = pass_ & is_bull_c, pass_ & is_bear_c
    elif mode == "Dynamic ATR":
        atr_val = _smooth(_true_range(df), c["atr_len"], c["atr_smooth"]) * c["atr_mult"]
        pass_ = body >= atr_val
        mom_bull, mom_bear = pass_ & is_bull_c, pass_ & is_bear_c
    elif mode == "CRT (2-Candle)":
        o1, h1, l1, c1 = o.shift(1), h.shift(1), l.shift(1), cl.shift(1)
        r1, b1 = (h1 - l1), (c1 - o1).abs()
        r2, b2 = (h - l), (cl - o).abs()
        b1pct = np.where(r1 > 0, b1 * 100.0 / r1, 0.0)
        b2pct = np.where(r2 > 0, b2 * 100.0 / r2, 0.0)
        c1_bull, c1_bear = c1 > o1, c1 < o1
        c2_bull, c2_bear = cl > o, cl < o
        if c["crt_dir"] == "Same Direction":
            dir_ok = (c1_bull & c2_bull) | (c1_bear & c2_bear)
        elif c["crt_dir"] == "Opposite":
            dir_ok = (c1_bull & c2_bear) | (c1_bear & c2_bull)
        else:
            dir_ok = pd.Series(True, index=df.index)
        body_ratio = np.where(r1 > 0, b2 <= r1 * c["crt_c2_max_ratio"], False)
        close_in = ((cl >= l1) & (cl <= h1)) if c["crt_close_inside"] else pd.Series(True, index=df.index)
        shared = (h1.notna() & (b1pct >= c["crt_c1_body_pct"]) & (b2pct >= c["crt_c2_body_pct"])
                  & dir_ok & body_ratio & close_in)
        t1 = shared & c["crt_t1_on"] & ((c1_bear & (l < l1)) | (c1_bull & (h > h1)))
        t2 = shared & c["crt_t2_on"] & ((c1_bear & (l >= l1)) | (c1_bull & (h <= h1)))
        crt_is_t1, crt_is_t2 = t1.fillna(False), t2.fillna(False)
        mom_bull = (t1 | t2) & c1_bear
        mom_bear = (t1 | t2) & c1_bull
        mom_bull, mom_bear = mom_bull.fillna(False), mom_bear.fillna(False)
    else:  # Smart Stats (default)
        med_b = body.rolling(c["qt_look"]).median()
        dev = (body - body.rolling(c["qt_look"]).median()).abs()
        mad_b = dev.rolling(c["qt_look"]).median()
        thr_s = med_b + mad_b * c["qt_dev"]
        mom_pass = body >= thr_s
        wick_pass = (full_rng > 0) & (pd.Series(wick_rat, index=df.index) <= c["qt_max_wick"])
        pass_ = (mom_pass & wick_pass).fillna(False)
        mom_bull, mom_bear = pass_ & is_bull_c, pass_ & is_bear_c

    # ── Signal generation (cascade, urutan dijaga) ──
    bull_raw, bear_raw = mom_bull.copy(), mom_bear.copy()
    if c["rob_dir_on"]:
        no_trend = ~(rob_trend_up | rob_trend_dn)
        bull_raw = bull_raw & ~no_trend
        bear_raw = bear_raw & ~no_trend
        if c["rob_dir_mode"] == "Only One Direction":
            bull_raw = bull_raw & ~(bull_raw & ~rob_trend_up)
            bear_raw = bear_raw & ~(bear_raw & ~rob_trend_dn)
        else:  # Both Direction (Reverse)
            bear_raw = bear_raw & ~rob_trend_up
            bull_raw = bull_raw & ~rob_trend_dn

    sig_bull = bull_raw & (c["side_mode"] in ("Both", "Buy Only"))
    sig_bear = bear_raw & (c["side_mode"] in ("Both", "Sell Only"))

    # ── Fase text ──
    rob_dir_txt = np.where(rob_trend_up, "BULL UP",
                  np.where(rob_trend_dn, "BEAR DN", "NEUTRAL"))
    sig_txt = np.where(sig_bull, "BULL", np.where(sig_bear, "BEAR", "--"))
    htf_dir = np.where(htf_cls > htf_fast, "above FAST",
              np.where(htf_cls < htf_fast, "below FAST", "at FAST"))

    out = pd.DataFrame({
        "timestamp": df["open_time"] if "open_time" in df else df.index,
        "close": cl,
        # numerik
        "rob_fast": rob_fast, "rob_main": rob_main, "rob_slow": rob_slow,
        "body": body, "wick_rat": pd.Series(wick_rat, index=df.index),
        # fase/state
        "rob_trend": rob_dir_txt,
        "mom_bull": mom_bull.values, "mom_bear": mom_bear.values,
        "crt_t1": crt_is_t1.values, "crt_t2": crt_is_t2.values,
        "sig_bull": sig_bull.values, "sig_bear": sig_bear.values,
        "signal": sig_txt,
        "htf_dir": htf_dir,
    })
    # teks-fase gabungan (mirror dashboard) — target validasi visual utama
    out["phase_text"] = [
        f"Mode={mode} | RobDir={rd} | Sig={sg} | HTF={hd}"
        for rd, sg, hd in zip(out["rob_trend"], out["signal"], out["htf_dir"])
    ]
    return out


if __name__ == "__main__":
    import os

    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    csv = os.path.join(ROOT, "data", "raw", "BTCUSDT_1d_20260705_20260713.csv")
    out_dir = os.path.join(ROOT, "results", "new_set_v1_20260714")
    os.makedirs(out_dir, exist_ok=True)

    df = pd.read_csv(csv)
    res = robust_momcand(df)
    out_csv = os.path.join(out_dir, "robust_momcand_percandle.csv")
    res.to_csv(out_csv, index=False)

    print(f"[robust_momcand] rows={len(res)}  ->  {out_csv}")
    print("Catatan: Smart Stats butuh 200 bar (ta.median/MAD) -> di data 8-candle sinyal kosong (warm-up wajar).")
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(res[["timestamp", "close", "rob_fast", "rob_main", "rob_slow",
                   "rob_trend", "signal", "phase_text"]].to_string(index=False))
