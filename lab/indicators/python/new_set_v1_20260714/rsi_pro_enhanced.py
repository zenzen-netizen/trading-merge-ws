"""
rsi_pro_enhanced.py — Python port of TradingView Pine "RSI Pro Enhanced".

Batch: new_set_v1 (2026-07-14). Sumber kebenaran:
    indicators/pine_source/new_set_v1_20260714/rsi_pro_enhanced.pine (@version=6)

Struktur paralel dengan SMI Pro v3 (lihat indicators/python/smi_pro.py + smi_events.py).

Dua layer (stage_03):
  - Numerik : rsi (Wilder rma), rsiMA (7 tipe smoothing, default EMA14), histogram, BB band opsional.
  - Fase    : zone (OB/Upper N/Middle/Lower N/OS), histogram 4-state (Exp/Shr Bull/Bear),
              cross, PA/PD counter (pulse == threshold), signal (STR BUY/BUY/SELL/STR SELL/NEUTRAL),
              divergence pivot (delay konfirmasi lbR bar), + teks-fase gabungan.

Replikasi krusial:
  - PA/PD nyala pas counter PERSIS == threshold (pulse 1-bar), BUKAN >=.
  - Divergence pakai pivot rsi (lbL kiri, lbR kanan) -> TERKONFIRMASI delay lbR bar,
    tidak dianggap muncul di bar pivot (no lookahead).
  - Histogram 4-state banding hist vs hist[1] + tanda -> urutan if-elif dijaga.
  - Cascade sZone/sSig dijaga urutannya.
"""

import numpy as np
import pandas as pd


def _rma(s, length):
    """Wilder RMA == Pine ta.rma."""
    return s.ewm(alpha=1.0 / length, adjust=False).mean()


def _wma(s, length):
    w = np.arange(1, length + 1)
    return s.rolling(length).apply(lambda x: np.dot(x, w) / w.sum(), raw=True)


def _ma(s, length, typ, volume=None):
    if typ in ("SMA", "SMA + BB"):
        return s.rolling(length).mean()
    if typ == "EMA":
        return s.ewm(span=length, adjust=False).mean()
    if typ == "SMMA (RMA)":
        return _rma(s, length)
    if typ == "WMA":
        return _wma(s, length)
    if typ == "VWMA":
        if volume is None:
            raise ValueError("VWMA butuh volume")
        return (s * volume).rolling(length).sum() / volume.rolling(length).sum()
    raise ValueError(f"MA type tak dikenal: {typ}")


def _pivots(series, lbL, lbR, kind):
    """Return (found[t], pivot_bar[t], pivot_val[t]) — dikonfirmasi di bar t (delay lbR).
    kind='low' cari pivot low, 'high' cari pivot high. found True saat window center = ekstrem."""
    n = len(series)
    v = series.values
    found = np.zeros(n, dtype=bool)
    pbar = np.full(n, -1, dtype=int)
    pval = np.full(n, np.nan)
    for t in range(n):
        c = t - lbR  # kandidat pivot bar (center)
        if c - lbL < 0 or t >= n:
            continue
        lo = c - lbL
        hi = c + lbR
        if hi >= n:
            continue
        win = v[lo:hi + 1]
        cv = v[c]
        if np.isnan(win).any():
            continue
        if kind == "low":
            if cv == win.min() and (win < cv).sum() == 0:
                # pivot low: center <= semua (Pine pakai strict-ish; pakai center==min)
                if cv <= win.min():
                    found[t] = True
                    pbar[t] = c
                    pval[t] = cv
        else:
            if cv >= win.max():
                found[t] = True
                pbar[t] = c
                pval[t] = cv
    return found, pbar, pval


DEFAULTS = dict(
    rsiLen=5, rsiOB=80, rsiMID=40, rsiOS=30,
    maType="EMA", maLen=14, bbMult=2.0,
    calcDiv=True, lbR=5, lbL=5, rngU=60, rngL=5,
    extLvl=90, extLow=10,
    akumCandles=2, distCandles=2,
)


def rsi_pro(df, cfg=None):
    c = dict(DEFAULTS)
    if cfg:
        c.update(cfg)
    df = df.reset_index(drop=True).copy()
    n = len(df)
    src = df["close"].astype(float)
    high, low = df["high"].astype(float), df["low"].astype(float)
    vol = df["volume"].astype(float) if "volume" in df else None

    # ── RSI ──
    change = src.diff()
    up = _rma(change.clip(lower=0), c["rsiLen"])
    down = _rma((-change).clip(lower=0), c["rsiLen"])
    rsi = np.where(down == 0, 100.0, np.where(up == 0, 0.0, 100.0 - (100.0 / (1.0 + up / down))))
    rsi = pd.Series(rsi, index=df.index)

    # ── MA smoothing ──
    enableMA = c["maType"] != "None"
    isBB = c["maType"] == "SMA + BB"
    rsiMA = _ma(rsi, c["maLen"], c["maType"], vol) if enableMA else pd.Series(np.nan, index=df.index)
    rsiStd = (rsi.rolling(c["maLen"]).std(ddof=0) * c["bbMult"]) if isBB else pd.Series(np.nan, index=df.index)

    rsiH = (rsi - rsiMA) if enableMA else pd.Series(0.0, index=df.index)
    hprev = rsiH.shift(1)
    sAb = (rsi >= rsiMA) if enableMA else pd.Series(True, index=df.index)
    sHAU = (rsiH > hprev) & (rsiH > 0)
    sHAD = (rsiH < hprev) & (rsiH > 0)
    sHBD = (rsiH < hprev) & (rsiH <= 0)
    sHBU = (rsiH > hprev) & (rsiH <= 0)

    # cross (ta.cross = either direction)
    ma_prev = rsiMA.shift(1)
    rsi_prev = rsi.shift(1)
    cross = enableMA & (((rsi > rsiMA) & (rsi_prev <= ma_prev)) | ((rsi < rsiMA) & (rsi_prev >= ma_prev)))

    OB, MID, OS = c["rsiOB"], c["rsiMID"], c["rsiOS"]

    # ── PA/PD counter (per-bar, pulse ==) ──
    bCnt = np.zeros(n, dtype=int)
    aCnt = np.zeros(n, dtype=int)
    for i in range(n):
        pb = bCnt[i - 1] if i > 0 else 0
        pa = aCnt[i - 1] if i > 0 else 0
        r = rsi.iloc[i]
        if r < MID:
            bCnt[i] = pb + 1
            aCnt[i] = 0
        elif r > MID:
            aCnt[i] = pa + 1
            bCnt[i] = 0
        else:
            bCnt[i] = 0
            aCnt[i] = 0
    preAkum = bCnt == c["akumCandles"]   # pulse
    preDist = aCnt == c["distCandles"]

    # cross bars-ago tracking
    sBA = np.zeros(n, dtype=int)
    last_cross = 0
    for i in range(n):
        if bool(cross.iloc[i]):
            last_cross = i
        sBA[i] = i - last_cross

    # ── zone / hist-state / signal (cascade) ──
    def zone(r):
        if r > OB: return "OB"
        if r > MID: return "Upper N"
        if r > 50: return "Middle"
        if r > OS: return "Lower N"
        return "OS"
    sZone = rsi.apply(zone)

    sHSt = np.where(sHAU, "Exp Bull", np.where(sHAD, "Shr Bull",
           np.where(sHBD, "Exp Bear", np.where(sHBU, "Shr Bear", "Neutral"))))

    def sig(r, ab):
        if r > OB and not ab: return "STR SELL"
        if r < OS and ab: return "STR BUY"
        if ab and r > 50: return "BUY"
        if (not ab) and r < 50: return "SELL"
        return "NEUTRAL"
    sSig = pd.Series([sig(rsi.iloc[i], bool(sAb.iloc[i])) for i in range(n)], index=df.index)

    def paPd(i):
        if preAkum[i]: return "PA ON"
        if preDist[i]: return "PD ON"
        if bCnt[i] > 0: return f"PA {bCnt[i]}/{c['akumCandles']}"
        if aCnt[i] > 0: return f"PD {aCnt[i]}/{c['distCandles']}"
        return "-"
    paPdTxt = [paPd(i) for i in range(n)]

    # ── Divergence (pivot, delay lbR) ──
    divText = ["None"] * n
    if c["calcDiv"]:
        lbL, lbR, rngL, rngU = c["lbL"], c["lbR"], c["rngL"], c["rngU"]
        plF, plBar, plVal = _pivots(rsi, lbL, lbR, "low")
        phF, phBar, phVal = _pivots(rsi, lbL, lbR, "high")
        # valuewhen helpers berjalan sekuensial
        last_pl = None  # (bar, rsiVal, lowVal)
        last_ph = None
        for t in range(n):
            if plF[t]:
                cbar = plBar[t]
                curRsi = rsi.iloc[cbar]
                curLow = low.iloc[cbar]
                if last_pl is not None:
                    gap = cbar - last_pl[0]
                    if rngL <= gap <= rngU:
                        # bullish: price LL, rsi HL
                        if curLow < last_pl[2] and curRsi > last_pl[1]:
                            divText[t] = "Bull Div"
                last_pl = (cbar, curRsi, curLow)
            if phF[t]:
                cbar = phBar[t]
                curRsi = rsi.iloc[cbar]
                curHigh = high.iloc[cbar]
                if last_ph is not None:
                    gap = cbar - last_ph[0]
                    if rngL <= gap <= rngU:
                        # bearish: price HH, rsi LH
                        if curHigh > last_ph[2] and curRsi < last_ph[1]:
                            divText[t] = "Bear Div"
                last_ph = (cbar, curRsi, curHigh)

    out = pd.DataFrame({
        "timestamp": df["open_time"] if "open_time" in df else df.index,
        "close": src,
        # numerik
        "rsi": rsi, "rsi_ma": rsiMA, "rsi_hist": rsiH,
        "bb_std": rsiStd,
        # fase/state
        "zone": sZone.values,
        "vs_ma": np.where(enableMA, np.where(sAb, "Bull", "Bear"), "N/A"),
        "hist_state": sHSt,
        "cross": cross.values, "bars_since_cross": sBA,
        "pa_cnt": bCnt, "pd_cnt": aCnt,
        "pre_akum": preAkum, "pre_dist": preDist,
        "pa_pd": paPdTxt,
        "signal": sSig.values,
        "divergence": divText,
    })
    out["phase_text"] = [
        f"{z} | {sg} | hist={hs} | {pp} | div={dv}"
        for z, sg, hs, pp, dv in zip(out["zone"], out["signal"], out["hist_state"],
                                     out["pa_pd"], out["divergence"])
    ]
    return out


if __name__ == "__main__":
    import os

    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    csv = os.path.join(ROOT, "data", "raw", "BTCUSDT_1d_20260705_20260713.csv")
    out_dir = os.path.join(ROOT, "results", "new_set_v1_20260714")
    os.makedirs(out_dir, exist_ok=True)

    df = pd.read_csv(csv)
    res = rsi_pro(df)
    out_csv = os.path.join(out_dir, "rsi_pro_enhanced_percandle.csv")
    res.to_csv(out_csv, index=False)

    print(f"[rsi_pro_enhanced] rows={len(res)}  ->  {out_csv}")
    print("Catatan: divergence butuh lbL+lbR=10 bar -> di data 8-candle kosong (warm-up wajar).")
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(res[["timestamp", "close", "rsi", "rsi_ma", "zone", "signal",
                   "pa_pd", "phase_text"]].to_string(index=False))
