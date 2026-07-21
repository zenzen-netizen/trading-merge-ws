"""
indicators/python/atr_percentage.py

Replikasi Python dari "ATR Percentage" (Pine Script v4, HeWhoMustNotBeNamed).
Panduan replikasi: journal/stage_03_replikasi_indikator.md

STATUS: layer numerik + layer fase/zone sudah diimplementasikan.
        BELUM divalidasi terhadap TradingView asli.

Indikator ini simpel - single oscillator (ATR mentah atau ATR% dari
close) dibungkus Bollinger Band (SMA + stdev). Gak ada state persisten
antar-bar, gak ada cascade if-elif kompleks - jadi cocok dihitung
vectorized penuh pakai pandas, gak perlu loop bar-by-bar.

Dua layer output:
1. Layer numerik : atr, atr_percent, bb_middle, bb_top, bb_bottom
2. Layer fase     : volatility_zone (4 kategori, analog area fill
                    "High/Low Volatility Zone" di chart asli)

Gotcha yang dijaga:
- Pine v4 atr() = ta.rma(tr, length) = Wilder smoothing, SAMA dengan
  ta.atr() di v6 - dipakai fungsi wilder_atr() yang sama polanya
  dengan yang dipakai di fbf_break_filter.py
- Pine bb()/ta.stdev() default pakai population stdev (ddof=0, dibagi
  N bukan N-1) - dipakai .std(ddof=0), BUKAN default pandas (ddof=1).
  Ini gampang kelewat kalau gak hati-hati, beda dikit tapi konsisten
  beda kalau salah pilih.
- useAtrAsPercent nentuin oscillator dasar buat BB dihitung dari ATR%
  atau ATR mentah - kolom bb_* selalu ngikut basis yang aktif
  (parameter use_atr_as_percent), BUKAN dihitung dua-duanya sekaligus.
"""

import pandas as pd
import numpy as np


def wilder_atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    """Analog atr()/ta.atr() Pine = Wilder smoothing (RMA) dari True Range."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = pd.Series(np.nan, index=close.index)
    n = len(close)
    if n < length:
        return atr
    atr.iloc[length - 1] = tr.iloc[:length].mean()
    for i in range(length, n):
        atr.iloc[i] = (atr.iloc[i - 1] * (length - 1) + tr.iloc[i]) / length
    return atr


def calculate_atr_percentage(
    df: pd.DataFrame,
    atr_periods: int = 22,
    use_atr_as_percent: bool = True,
    bb_periods: int = 20,
    bb_stddev: float = 2.0,
) -> pd.DataFrame:
    """
    df wajib punya kolom: 'high', 'low', 'close'.
    Parameter default persis sama dengan default input Pine source asli.
    """
    out = df.copy()

    atr = wilder_atr(out["high"], out["low"], out["close"], atr_periods)
    atr_percent = (atr / out["close"]) * 100

    basis = atr_percent if use_atr_as_percent else atr

    bb_middle = basis.rolling(bb_periods).mean()
    bb_std = basis.rolling(bb_periods).std(ddof=0)  # population stdev, samain ke Pine
    bb_top = bb_middle + bb_std * bb_stddev
    bb_bottom = bb_middle - bb_std * bb_stddev

    out["atr"] = atr
    out["atr_percent"] = atr_percent
    out["bb_middle"] = bb_middle
    out["bb_top"] = bb_top
    out["bb_bottom"] = bb_bottom

    # --- volatility_zone: analog area fill "High/Low Volatility Zone" ---
    def _zone(row):
        if pd.isna(row["bb_middle"]):
            return "warmup"
        v = basis.loc[row.name]
        if pd.isna(v):
            return "warmup"
        if v > row["bb_top"]:
            return "above_top"       # di luar band atas, ekstrem tinggi
        elif v > row["bb_middle"]:
            return "high_zone"       # area fill merah (High Volatility Zone)
        elif v >= row["bb_bottom"]:
            return "low_zone"        # area fill hijau (Low Volatility Zone)
        else:
            return "below_bottom"    # di luar band bawah, ekstrem rendah

    out["volatility_zone"] = out.apply(_zone, axis=1)

    return out


# ============================================================
# CATATAN VALIDASI - WAJIB DIKERJAKAN SEBELUM DIPAKAI BACKTEST
# ============================================================
#
# [ ] Cocokkan atr/atr_percent Python vs plot "ATR/Percent" TradingView
#     di beberapa titik sample.
# [ ] Cocokkan bb_top/bb_middle/bb_bottom Python vs 3 garis BB di chart.
# [ ] PERHATIKAN KHUSUS: cek apakah ta.stdev/bb() Pine emang population
#     stdev (ddof=0) - asumsi ini diambil dari dokumentasi umum Pine,
#     TAPI belum dicross-check numerik lawan TradingView asli. Kalau
#     pas validasi ketemu selisih konsisten kecil, ini kandidat pertama
#     buat dicek (coba ganti ddof=1).
# [ ] Kalau use_atr_as_percent nanti dipakai False, validasi ulang basis
#     ATR mentah (bukan cuma yang persen).


if __name__ == "__main__":
    rng_seed = np.random.default_rng(3)
    n_bars = 200
    close = 100 + np.cumsum(rng_seed.normal(0, 1, n_bars))
    high = close + rng_seed.uniform(0.1, 1.5, n_bars)
    low = close - rng_seed.uniform(0.1, 1.5, n_bars)

    df_test = pd.DataFrame({"high": high, "low": low, "close": close})
    result = calculate_atr_percentage(df_test)

    print("Kolom hasil:", list(result.columns))
    print("\nContoh 10 baris setelah warm-up:")
    print(result[["atr", "atr_percent", "bb_middle", "bb_top", "bb_bottom", "volatility_zone"]].iloc[25:35].to_string())
    print("\nDistribusi volatility_zone (sanity check, data sintetis):")
    print(result["volatility_zone"].value_counts())
