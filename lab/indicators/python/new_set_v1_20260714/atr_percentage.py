"""
ATR Percentage + Bollinger Bands — Python port of TradingView Pine Script (@version=4).

Sumber kebenaran (Pine):
  indicators/pine_source/new_set_v1_20260714/atr_percentage.pine
Batch: new_set_v1 (2026-07-14).

Dibangun mengikuti stage_01_struktur_folder.md + stage_03_replikasi_indikator.md.
File lama indicators/python/atr_percentage.py TIDAK disentuh — ini port terpisah
dengan output PER-CANDLE (2 layer) untuk validasi visual.

Logika Pine asli:
  useAtrAsPercent = input(true)
  ATRPeriods      = input(22)
  showBollingerBands = input(true)
  BBPeriods       = input(20)
  StdDev          = input(2)
  atr        = atr(ATRPeriods)              -> Wilder RMA dari True Range
  atrPercent = (atr / close) * 100
  [middle, top, bottom] = bb(useAtrAsPercent ? atrPercent : atr, BBPeriods, StdDev)
    -> middle = SMA(source, BBPeriods)
    -> dev    = StdDev * stdev(source, BBPeriods)   (stdev = populasi, ddof=0)
    -> top    = middle + dev ; bottom = middle - dev
  fill(top, middle)    = "High Volatility Zone"  (di atas mid)
  fill(bottom, middle) = "Low Volatility Zone"   (di bawah mid)

2 LAYER (stage_03):
  1. numerik : atr, atr_pct (source line), bb_middle, bb_top, bb_bottom
  2. fase    : vol_zone  (HIGH_VOL kalau source di atas mid, LOW_VOL kalau di bawah)
               band_pos  (ABOVE_TOP / INSIDE / BELOW_BOTTOM — posisi relatif band)
  + phase    : kolom teks-fase gabungan (target validasi visual utama)

Proses aman, no lookahead: RMA (ewm) + rolling SMA/stdev semuanya kausal.
Warm-up wajar NaN di awal (BB butuh BBPeriods bar penuh).
"""

import pandas as pd
import numpy as np


def _rma(series, length):
    """Wilder's RMA (sama seperti Pine rma / atr built-in). Kausal."""
    return series.ewm(alpha=1 / length, adjust=False).mean()


def _sma(series, length):
    """Simple Moving Average (basis bb Pine)."""
    return series.rolling(window=length, min_periods=length).mean()


def _stddev(series, length):
    """Population std dev (ddof=0) matching Pine stdev()."""
    return series.rolling(window=length, min_periods=length).std(ddof=0)


def atr_percentage(df, cfg=None):
    """
    Replikasi ATR Percentage + BB, output PER-CANDLE (semua deret).

    Args:
        df: DataFrame kolom ['high','low','close'] (index/urutan per-candle).
        cfg: dict opsional:
            atr_period      (default 22)   — ATRPeriods
            use_atr_pct     (default True)  — useAtrAsPercent (BB pada atrPercent vs atr mentah)
            show_bb         (default True)  — showBollingerBands
            bb_period       (default 20)    — BBPeriods
            bb_stddev       (default 2.0)   — StdDev

    Returns:
        DataFrame (index sama dgn df) berisi:
            atr, atr_pct,
            bb_source (= nilai yang di-BB: atr_pct kalau use_atr_pct else atr),
            bb_middle, bb_top, bb_bottom, bb_std,
            vol_zone, band_pos, phase
    """
    if cfg is None:
        cfg = {}

    atr_period = cfg.get("atr_period", 22)
    use_atr_pct = cfg.get("use_atr_pct", True)
    show_bb = cfg.get("show_bb", True)
    bb_period = cfg.get("bb_period", 20)
    bb_stddev = cfg.get("bb_stddev", 2.0)

    high = df["high"]
    low = df["low"]
    close = df["close"]

    # --- True Range (Pine ta.tr / atr internal) ---
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    # --- ATR (Wilder RMA) & ATR% ---
    atr = _rma(tr, atr_period)
    atr_pct = (atr / close) * 100.0

    # Layer numerik: source garis yang diplot & di-BB
    source = atr_pct if use_atr_pct else atr

    out = pd.DataFrame(index=df.index)
    out["atr"] = atr
    out["atr_pct"] = atr_pct
    out["bb_source"] = source

    if show_bb:
        middle = _sma(source, bb_period)
        std = _stddev(source, bb_period)
        dev = bb_stddev * std
        top = middle + dev
        bottom = middle - dev

        out["bb_middle"] = middle
        out["bb_top"] = top
        out["bb_bottom"] = bottom
        out["bb_std"] = std

        # --- Layer fase/state (proses per-candle, no lookahead) ---
        vol_zone = []
        band_pos = []
        phase = []
        for i in range(len(out)):
            s = source.iloc[i]
            m = middle.iloc[i]
            t = top.iloc[i]
            b = bottom.iloc[i]

            # Zona volatilitas: relatif ke mid (fill Pine High/Low Vol Zone)
            if np.isnan(s) or np.isnan(m):
                vz = "NaN"
            elif s >= m:
                vz = "HIGH_VOL"
            else:
                vz = "LOW_VOL"

            # Posisi relatif band
            if np.isnan(s) or np.isnan(t) or np.isnan(b):
                bp = "NaN"
            elif s > t:
                bp = "ABOVE_TOP"
            elif s < b:
                bp = "BELOW_BOTTOM"
            else:
                bp = "INSIDE"

            # Teks-fase gabungan (target validasi visual)
            if vz == "NaN" or bp == "NaN":
                ph = "Warmup"
            else:
                vz_txt = "High Vol" if vz == "HIGH_VOL" else "Low Vol"
                bp_txt = {
                    "ABOVE_TOP": "Above Top",
                    "INSIDE": "Inside Band",
                    "BELOW_BOTTOM": "Below Bottom",
                }[bp]
                ph = f"{vz_txt} | {bp_txt}"

            vol_zone.append(vz)
            band_pos.append(bp)
            phase.append(ph)

        out["vol_zone"] = vol_zone
        out["band_pos"] = band_pos
        out["phase"] = phase
    else:
        out["bb_middle"] = np.nan
        out["bb_top"] = np.nan
        out["bb_bottom"] = np.nan
        out["bb_std"] = np.nan
        out["vol_zone"] = "N/A"
        out["band_pos"] = "N/A"
        out["phase"] = "N/A"

    return out


if __name__ == "__main__":
    import os

    RAW = "data/raw/BTCUSDT_1d_20260705_20260713.csv"
    OUT_DIR = "results/new_set_v1_20260714"
    OUT_CSV = os.path.join(OUT_DIR, "atr_percentage_percandle.csv")

    df = pd.read_csv(RAW)
    df["timestamp"] = df["open_time"]

    ind = atr_percentage(df, cfg=None)  # default Pine params

    result = pd.DataFrame({"timestamp": df["timestamp"]})
    result["close"] = df["close"]
    for col in [
        "atr",
        "atr_pct",
        "bb_source",
        "bb_middle",
        "bb_top",
        "bb_bottom",
        "bb_std",
        "vol_zone",
        "band_pos",
        "phase",
    ]:
        result[col] = ind[col].values

    os.makedirs(OUT_DIR, exist_ok=True)
    result.to_csv(OUT_CSV, index=False)

    print(f"[atr_percentage] rows={len(result)}  ->  {OUT_CSV}")
    print("Catatan: data cuma 8 candle 1D, warm-up (BBPeriods=20) dominan -> NaN wajar.")
    print(result.tail(8).to_string(index=False))
