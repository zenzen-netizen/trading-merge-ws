"""
indicators/python/ema_ribbon_krypt_v11.py

Replikasi Python dari "EMA Ribbon Pro [Krypt v11 - High Contrast]" (Pine Script v6).
Source asli: indicators/pine_source/ema_ribbon_pro_krypt_v11.pine
Panduan replikasi: journal/stage_03_replikasi_indikator.md
Metodologi review: handoff_review_indikator.md

STATUS: layer numerik + layer fase/state (termasuk 4 trend method,
        ribbon strength, dashboard-context labels) + layer event (alert)
        sudah diimplementasikan. BELUM divalidasi terhadap TradingView
        asli (butuh data OHLCV real dari stage 2, yang belum dibangun).

=====================================================================
CATATAN PENTING - GOTCHA VISIBILITY (baca sebelum pakai file ini)
=====================================================================
Indikator ini BEDA KARAKTER dari SMI Pro / FBF yang sudah direview
duluan: dia TIDAK PUNYA `barcolor()` atau plot per-bar untuk fase
tren. Dashboard (table.cell) di source Pine cuma digambar ulang saat
`barstate.islast` - artinya trend_label/verdict_label di TradingView
HANYA kelihatan untuk BAR TERAKHIR/live, bukan tercatat historis di
tiap candle di masa lalu. Kalau mau lihat state di tanggal tertentu
di masa lalu langsung dari chart TV, satu-satunya cara adalah scrub
playback bar-by-bar (yang mahal & gak praktis untuk kalibrasi setup).

Konsekuensi: kolom-kolom fase (trend_label, verdict_label, dst) di
file ini DIHITUNG untuk SETIAP bar (supaya berguna untuk backtest/
kalibrasi setup historis), padahal source Pine aslinya cuma pernah
menampilkan itu untuk bar paling akhir. Ini bukan salah replikasi -
justru diperlukan supaya data historis bisa dipakai - tapi WAJIB
dicatat sebagai perbedaan mode "live-only display" vs "computed for
every historical bar", supaya saat validasi manual ke TV, jangan kaget
kalau candle expired gak bisa dicek ulang labelnya kecuali via replay.

showDashboard DEFAULT = False di source Pine. Artinya kalaupun
scrubbing dilakukan, dashboard TIDAK otomatis kelihatan kecuali user
eksplisit nyalain toggle-nya dulu.

=====================================================================
KLASIFIKASI EVENT vs DASHBOARD-ONLY (penting untuk kalibrasi setup)
=====================================================================
8 alertcondition() di source Pine TIDAK BERGANTUNG pada trend_label/
dashboard sama sekali - mereka dihitung dari variabel numerik mentah
(ma1+dev, ma10, isAlignedBull/Bear, divPct/overextThresh) yang SELALU
dihitung terlepas dari trendMethod yang dipilih atau showDashboard
on/off. Artinya "alert" indikator ini independen dari opsi tampilan
apa pun - beda dari trend_label yang bentuknya cuma representasi
tampilan (dashboard) dan gak dipakai alertcondition manapun.
Kolom event di output (kolom akhiran `_event`) = representasi 8
alertcondition tersebut, aman dipakai sebagai sinyal mentah.

=====================================================================
GOTCHA LAIN YANG DIJAGA PRESISI
=====================================================================
- KAMA: rekursif dgn smoothing constant (sc) yang BERUBAH tiap bar
  (bukan alpha konstan seperti EMA/RMA biasa) - WAJIB loop, gak bisa
  ewm() langsung. direction & noise divectorized, cuma langkah akhir
  (prev + sc*(src-prev)) yang loop.
- RMA (dipakai kalau maType="RMA" ATAU untuk ATR(14) & SMA(ATR,20)
  filter): Wilder smoothing asli Pine seed pakai SMA(length) bar
  pertama, BUKAN ewm(alpha=1/length, adjust=False) langsung dari bar
  pertama - pola sama seperti wilder_atr() di fbf_break_filter.py /
  atr_percentage.py.
- MAD di sini (fungsi `mad()` Pine) SATU TAHAP:
  sma(abs(source - sma(source,length)), length) - BEDA dari `f_mad()`
  di robust_momcand.py yang dua tahap (median dari |x - rolling
  median|). JANGAN DITUKAR, dua indikator beda punya definisi MAD
  yang beda persis.
- stdev (dipakai kalau useMAD=False): diasumsikan population stdev
  (ddof=0) mengikuti asumsi yang sama dengan atr_percentage.py -
  BELUM tervalidasi numerik lawan TradingView, sama-sama pending.
- getMA(): fallback eksplisit ke EMA kalau maType gak dikenali (ikut
  komentar "FIX" di source Pine - fallback ini sudah eksplisit di
  source, bukan tebakan/interpretasi Python).
- Cascade prioritas getTrend(): filter ATR (useATRFilter, default
  OFF) dicek PALING PERTAMA sebelum masuk ke logic trendMethod
  manapun - urutan ini dijaga persis (bukan diperiksa independen).
- 4 trendMethod TIDAK semuanya kasih kategori yang sama: MA200 Cross
  & Short vs Long Ribbon SELALU BINARY (Bullish/Bearish, gak ada
  Choppy). Ribbon Divergence (7 kategori) & Ribbon Alignment
  (3 kategori) punya state Choppy/OverExt. Ini perbedaan DESAIN di
  source asli, bukan bug - jangan disamaratakan strukturnya.
- divPct/overextThresh dihitung SELALU (gak digate showLongMA atau
  trendMethod) - dipakai alertcondition div overext independen dari
  tampilan.
- ta.crossover/ta.crossunder pakai definisi resmi: crossover(a,b) =
  a>b AND a[1]<=b[1]; crossunder(a,b) = a<b AND a[1]>=b[1] - konsisten
  dengan koreksi yang sudah dipakai di smi_pro_v3.py.
"""

import numpy as np
import pandas as pd


# ============================================================
# HELPER: MOVING AVERAGE VARIANTS
# ============================================================

def _wma(series: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def _rma_wilder(series: pd.Series, length: int) -> pd.Series:
    """Analog ta.rma() Pine - Wilder smoothing, seed = SMA(length) bar pertama."""
    out = pd.Series(np.nan, index=series.index)
    n = len(series)
    if n < length:
        return out
    out.iloc[length - 1] = series.iloc[:length].mean()
    for i in range(length, n):
        out.iloc[i] = (out.iloc[i - 1] * (length - 1) + series.iloc[i]) / length
    return out


def _hma(series: pd.Series, length: int) -> pd.Series:
    half = max(1, round(length / 2))
    sqrtl = max(1, round(np.sqrt(length)))
    return _wma(2.0 * _wma(series, half) - _wma(series, length), sqrtl)


def _dema(series: pd.Series, length: int) -> pd.Series:
    e = series.ewm(span=length, adjust=False).mean()
    return 2.0 * e - e.ewm(span=length, adjust=False).mean()


def _tema(series: pd.Series, length: int) -> pd.Series:
    e1 = series.ewm(span=length, adjust=False).mean()
    e2 = e1.ewm(span=length, adjust=False).mean()
    e3 = e2.ewm(span=length, adjust=False).mean()
    return 3.0 * e1 - 3.0 * e2 + e3


def _kama(series: pd.Series, length: int) -> pd.Series:
    """
    Analog kamaCalc() Pine - rekursif dgn smoothing constant per-bar.
    direction & noise divectorized, langkah rekursif akhir WAJIB loop
    (sc berubah tiap bar, gak bisa didekati ewm konstan).
    """
    fast_sc = 2.0 / 3.0
    slow_sc = 2.0 / 31.0

    direction = series.diff(length).abs()
    abs_diff = series.diff().abs()
    noise = abs_diff.rolling(length).sum()
    er = np.where(noise.values != 0, direction.values / noise.values, 0.0)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    src_v = series.values
    valid = ~direction.isna().values
    n = len(src_v)
    out = np.full(n, np.nan)
    prev = np.nan
    for i in range(n):
        if not valid[i]:
            continue
        if np.isnan(prev):
            out[i] = src_v[i]
        else:
            out[i] = prev + sc[i] * (src_v[i] - prev)
        prev = out[i]
    return pd.Series(out, index=series.index)


def _get_ma(series: pd.Series, length: int, ma_type: str) -> pd.Series:
    """Analog getMA() Pine. Fallback eksplisit ke EMA (persis komentar 'FIX' source)."""
    if ma_type == "SMA":
        return series.rolling(length).mean()
    elif ma_type == "EMA":
        return series.ewm(span=length, adjust=False).mean()
    elif ma_type == "WMA":
        return _wma(series, length)
    elif ma_type == "RMA":
        return _rma_wilder(series, length)
    elif ma_type == "HMA":
        return _hma(series, length)
    elif ma_type == "DEMA":
        return _dema(series, length)
    elif ma_type == "TEMA":
        return _tema(series, length)
    else:
        return series.ewm(span=length, adjust=False).mean()  # fallback, KAMA di-handle terpisah


def _mad_pine_single_tier(series: pd.Series, length: int) -> pd.Series:
    """Analog mad() Pine (SATU TAHAP) - BEDA dari f_mad() dua-tahap robust_momcand.py."""
    return (series - series.rolling(length).mean()).abs().rolling(length).mean()


def _crossover(a: pd.Series, b: pd.Series) -> pd.Series:
    """Definisi resmi ta.crossover: a>b AND a[1]<=b[1]."""
    return (a > b) & (a.shift(1) <= b.shift(1))


def _crossunder(a: pd.Series, b: pd.Series) -> pd.Series:
    """Definisi resmi ta.crossunder: a<b AND a[1]>=b[1]."""
    return (a < b) & (a.shift(1) >= b.shift(1))


# ============================================================
# MAIN FUNCTION
# ============================================================

def calculate_ema_ribbon_krypt(
    df: pd.DataFrame,
    src_col: str = "close",
    ma_type: str = "EMA",
    # Short ribbon (8 MA)
    len1: int = 20, len2: int = 25, len3: int = 30, len4: int = 35,
    len5: int = 40, len6: int = 45, len7: int = 50, len8: int = 55,
    # Long ribbon (4 MA)
    show_long_ma: bool = True,
    len9: int = 100, len10: int = 200, len11: int = 300, len12: int = 365,
    # Deviation bands
    mult: float = 1.0,
    dev_period: int = 20,
    use_mad: bool = True,
    # ATR SL
    mult_atr: float = 1.5,
    # Trend & Robust settings
    trend_method: str = "Ribbon Divergence",
    div_bull_strong: float = 3.0,
    div_bull_weak: float = 1.0,
    div_overext_mult: float = 5.0,
    use_atr_filter: bool = False,
) -> pd.DataFrame:
    """
    df wajib punya kolom: 'open', 'high', 'low', 'close' (untuk ATR).
    Parameter default persis sama dengan default input Pine source asli.

    trend_method salah satu dari:
      "MA200 Cross", "Ribbon Divergence", "Short vs Long Ribbon", "Ribbon Alignment"
      (default "Ribbon Divergence", sama dengan Pine).

    CATATAN: showDeviationBands & showATRSL & showDashboard di source
    Pine murni TOGGLE TAMPILAN - nilai yang mendasarinya (dev, ATR SL,
    dashboard label) SELALU dihitung terlepas toggle itu. Makanya
    parameter itu SENGAJA TIDAK ADA di function ini - kolom hasil
    selalu lengkap, tinggal pilih mau dipakai atau tidak di sisi
    pemanggil/strategi.
    """
    out = df.copy()
    src = out[src_col]
    high = out["high"]
    low = out["low"]
    close = out["close"]

    lens = [len1, len2, len3, len4, len5, len6, len7, len8, len9, len10, len11, len12]

    # ================================================================
    # LAYER NUMERIK - 12 MA
    # ================================================================
    if ma_type == "KAMA":
        mas = [_kama(src, l) for l in lens]
    else:
        mas = [_get_ma(src, l, ma_type) for l in lens]

    (ma1, ma2, ma3, ma4, ma5, ma6, ma7, ma8, ma9, ma10, ma11, ma12) = mas
    for idx, ma in enumerate(mas, start=1):
        out[f"ma{idx}"] = ma

    # ================================================================
    # DEVIATION & ATR
    # ================================================================
    raw_dev = _mad_pine_single_tier(src, dev_period) if use_mad else src.rolling(dev_period).std(ddof=0)
    dev = raw_dev * mult

    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = _rma_wilder(tr, 14)  # ta.atr(14) fixed, bukan input
    sl_dist = atr * mult_atr

    dev_pct = np.where(close != 0, (dev / close) * 100.0, 0.0)
    atr_pct = np.where(close != 0, (atr / close) * 100.0, 0.0)
    dev_pct = pd.Series(dev_pct, index=out.index)
    atr_pct = pd.Series(atr_pct, index=out.index)

    out["dev"] = dev
    out["atr"] = atr
    out["dev_pct"] = dev_pct
    out["atr_pct"] = atr_pct
    out["atr_sl_long"] = close - sl_dist
    out["atr_sl_short"] = close + sl_dist

    # deviation bands (short ribbon only, ma1-ma8) - dihitung selalu
    for i, ma in enumerate([ma1, ma2, ma3, ma4, ma5, ma6, ma7, ma8], start=1):
        out[f"dev_upper_{i}"] = ma + dev
        out[f"dev_lower_{i}"] = ma - dev

    # normalisasi self-calibrating
    norm_len = max(2, dev_period * 2)
    dev_pct_avg = dev_pct.rolling(norm_len).mean()
    atr_pct_avg = atr_pct.rolling(norm_len).mean()
    dev_ratio = np.where(dev_pct_avg != 0, dev_pct / dev_pct_avg, 1.0)
    atr_ratio = np.where(atr_pct_avg != 0, atr_pct / atr_pct_avg, 1.0)
    dev_ratio = pd.Series(dev_ratio, index=out.index)
    atr_ratio = pd.Series(atr_ratio, index=out.index)
    out["dev_ratio"] = dev_ratio
    out["atr_ratio"] = atr_ratio

    def _vol_label(ratio: pd.Series) -> pd.Series:
        return np.where(ratio < 0.7, "RENDAH", np.where(ratio > 1.3, "TINGGI", "NORMAL"))

    out["dev_vol_label"] = _vol_label(dev_ratio)
    out["atr_vol_label"] = _vol_label(atr_ratio)

    # ================================================================
    # TREND & STRENGTH
    # ================================================================
    atr_sma_filter = atr.rolling(20).mean()  # ta.sma(atr, 20)
    is_trending = atr > atr_sma_filter

    div_pct = np.where(ma12 != 0, (ma1 - ma12) / ma12 * 100.0, 0.0)
    div_pct = pd.Series(div_pct, index=out.index)
    overext_thresh = div_bull_strong * div_overext_mult
    out["div_pct"] = div_pct
    out["overext_thresh"] = overext_thresh

    avg_short = (ma1 + ma2 + ma3 + ma4 + ma5 + ma6 + ma7 + ma8) / 8.0
    avg_long = (ma9 + ma10 + ma11 + ma12) / 4.0
    out["avg_short"] = avg_short
    out["avg_long"] = avg_long

    is_aligned_bull = (ma1 > ma2) & (ma2 > ma3) & (ma3 > ma4) & (ma4 > ma5) & (ma5 > ma6) & (ma6 > ma7) & (ma7 > ma8)
    is_aligned_bear = (ma1 < ma2) & (ma2 < ma3) & (ma3 < ma4) & (ma4 < ma5) & (ma5 < ma6) & (ma6 < ma7) & (ma7 < ma8)
    out["is_aligned_bull"] = is_aligned_bull
    out["is_aligned_bear"] = is_aligned_bear

    strength_count = sum((close > ma).astype(int) for ma in [ma1, ma2, ma3, ma4, ma5, ma6, ma7, ma8])
    ribbon_strength = (strength_count / 8.0) * 100.0
    long_str_count = sum((close > ma).astype(int) for ma in [ma9, ma10, ma11, ma12])
    out["strength_count"] = strength_count
    out["ribbon_strength"] = ribbon_strength
    out["long_str_count"] = long_str_count

    # ---- getTrend() cascade: filter ATR dicek PALING PERTAMA ----
    n = len(out)
    trend_label = np.empty(n, dtype=object)

    div_ge_overext = (div_pct >= overext_thresh).values
    div_ge_strong = (div_pct >= div_bull_strong).values
    div_ge_weak = (div_pct >= div_bull_weak).values
    div_le_overext = (div_pct <= -overext_thresh).values
    div_le_strong = (div_pct <= -div_bull_strong).values
    div_le_weak = (div_pct <= -div_bull_weak).values

    close_v = close.values
    ma10_v = ma10.values
    avg_short_v = avg_short.values
    avg_long_v = avg_long.values
    is_al_bull_v = is_aligned_bull.values
    is_al_bear_v = is_aligned_bear.values
    is_trending_v = is_trending.values

    for i in range(n):
        if use_atr_filter and not is_trending_v[i]:
            trend_label[i] = "Ranging ↔"
            continue

        if trend_method == "MA200 Cross":
            trend_label[i] = "Bullish ▲" if close_v[i] >= ma10_v[i] else "Bearish ▼"

        elif trend_method == "Ribbon Divergence":
            if div_ge_overext[i]:
                trend_label[i] = "OverExt ▲▲▲"
            elif div_ge_strong[i]:
                trend_label[i] = "Strong Bull ▲▲"
            elif div_ge_weak[i]:
                trend_label[i] = "Bull ▲"
            elif div_le_overext[i]:
                trend_label[i] = "OverExt ▼▼▼"
            elif div_le_strong[i]:
                trend_label[i] = "Strong Bear ▼▼"
            elif div_le_weak[i]:
                trend_label[i] = "Bear ▼"
            else:
                trend_label[i] = "Choppy ↔"

        elif trend_method == "Short vs Long Ribbon":
            trend_label[i] = "Bullish ▲" if avg_short_v[i] >= avg_long_v[i] else "Bearish ▼"

        elif trend_method == "Ribbon Alignment":
            if is_al_bull_v[i]:
                trend_label[i] = "Strong Bull ▲▲"
            elif is_al_bear_v[i]:
                trend_label[i] = "Strong Bear ▼▼"
            else:
                trend_label[i] = "Choppy ↔"
        else:
            trend_label[i] = "N/A"

    out["trend_label"] = trend_label

    # ---- context labels (dashboard-only di source, dihitung tiap bar di sini) ----
    bull_ctx_set = {"Bull ▲", "Strong Bull ▲▲", "OverExt ▲▲▲", "Bullish ▲"}
    bear_ctx_set = {"Bear ▼", "Strong Bear ▼▼", "OverExt ▼▼▼", "Bearish ▼"}

    is_bull_ctx = np.isin(trend_label, list(bull_ctx_set))
    is_bear_ctx = np.isin(trend_label, list(bear_ctx_set))

    short_str_ctx = np.empty(n, dtype=object)
    rs_v = ribbon_strength.values
    for i in range(n):
        if is_bull_ctx[i]:
            if rs_v[i] >= 87.5:
                short_str_ctx[i] = "MOMENTUM"
            elif rs_v[i] >= 50.0:
                short_str_ctx[i] = "PULLBACK?"
            else:
                short_str_ctx[i] = "LEMAH"
        elif is_bear_ctx[i]:
            if rs_v[i] >= 75.0:
                short_str_ctx[i] = "RETEST!"
            elif rs_v[i] >= 50.0:
                short_str_ctx[i] = "BOUNCE?"
            else:
                short_str_ctx[i] = "KONFIRM"
        else:
            short_str_ctx[i] = "SIDEWAYS"
    out["short_str_ctx"] = short_str_ctx

    def _long_str_ctx(cnt):
        if cnt == 4:
            return "MACRO BULL"
        elif cnt == 3:
            return "ABOVE 3/4"
        elif cnt == 2:
            return "MIXED"
        elif cnt == 1:
            return "NEARLY BEAR"
        else:
            return "MACRO BEAR"

    out["long_str_ctx_label"] = long_str_count.apply(_long_str_ctx)

    # ---- verdictLabel (dashboard-only, cascade string-match ke trend_label) ----
    verdict_label = np.empty(n, dtype=object)
    lsc_v = long_str_count.values
    sc_v = strength_count.values
    for i in range(n):
        tl = trend_label[i]
        if tl == "OverExt ▲▲▲":
            verdict_label[i] = "PARABOLIC - TRAIL SL"
        elif tl == "OverExt ▼▼▼":
            verdict_label[i] = "CAPITULATE - WAIT"
        elif tl in ("Strong Bull ▲▲", "Bull ▲", "Bullish ▲"):
            if sc_v[i] >= 6 and lsc_v[i] >= 3:
                verdict_label[i] = "STRONG BUY"
            elif sc_v[i] >= 6 and lsc_v[i] < 3:
                verdict_label[i] = "HOLD - MACRO LEMAH"
            else:
                verdict_label[i] = "BUY DIP - TUNGGU"
        elif tl in ("Strong Bear ▼▼", "Bear ▼", "Bearish ▼"):
            if rs_v[i] >= 75.0:
                verdict_label[i] = "AVOID - RETEST"
            else:
                verdict_label[i] = "SELL / SHORT"
        elif tl in ("Choppy ↔", "Ranging ↔"):
            verdict_label[i] = "WAIT - NO TRADE"
        else:
            verdict_label[i] = "WAIT"
    out["verdict_label"] = verdict_label

    # ================================================================
    # LAYER EVENT (8 alertcondition Pine, independen dari trend_label/dashboard)
    # ================================================================
    out["break_upper_band1_event"] = _crossover(close, ma1 + dev)
    out["break_lower_band1_event"] = _crossunder(close, ma1 - dev)
    out["cross_above_ma200_event"] = _crossover(close, ma10)
    out["cross_below_ma200_event"] = _crossunder(close, ma10)
    # CATATAN BUG-FIX: .shift(1) pada Series bool bikin dtype jadi 'object'
    # (NaN di bar pertama) - kalau langsung di-`~` tanpa .astype(bool) dulu,
    # negasi jadi salah (bitwise invert Python bool: ~True=-2, ~False=-1,
    # DUA-DUANYA truthy!). WAJIB .astype(bool) eksplisit setelah fillna.
    prev_aligned_bull = is_aligned_bull.shift(1).fillna(False).astype(bool)
    prev_aligned_bear = is_aligned_bear.shift(1).fillna(False).astype(bool)
    out["ribbon_aligned_bull_event"] = is_aligned_bull & ~prev_aligned_bull
    out["ribbon_aligned_bear_event"] = is_aligned_bear & ~prev_aligned_bear
    div_pct_prev = div_pct.shift(1)
    out["div_enter_overext_bull_event"] = (div_pct >= overext_thresh) & (div_pct_prev < overext_thresh)
    out["div_enter_overext_bear_event"] = (div_pct <= -overext_thresh) & (div_pct_prev > -overext_thresh)

    # ================================================================
    # EMA SLOPE/ANGLE (ported dari _source/research-code/indicators/ema_ribbon.py
    # fungsi ema_ribbon_pro, blok "EMA Slope/Angle (compare EMA20 3 candles back)".
    # basis = ma1 (EMA20 by-posisi), 3 bar ke belakang. slope_pct versi lama DEAD, diabaikan.
    # ================================================================
    ma1_past3 = ma1.shift(3)
    ema_slope = ma1 - ma1_past3
    ema_slope_angle = pd.Series(
        np.where(
            ma1_past3.eq(0),
            0.0,
            np.degrees(np.arctan2(ema_slope, 3 * (ma1_past3 / 100))),
        ),
        index=out.index,
    )
    abs_slope_angle = ema_slope_angle.abs()

    slope_conditions = [
        abs_slope_angle < 2,
        (abs_slope_angle < 10) & (ema_slope > 0),
        (abs_slope_angle < 10) & (ema_slope <= 0),
        (abs_slope_angle < 25) & (ema_slope > 0),
        (abs_slope_angle < 25) & (ema_slope <= 0),
        (abs_slope_angle < 45) & (ema_slope > 0),
        (abs_slope_angle < 45) & (ema_slope <= 0),
        ema_slope > 0,
    ]
    slope_labels = [
        "Flat/Netral",
        "Rising Bull", "Falling Bear",
        "Steep Bull", "Steep Bear",
        "Very Steep Bull", "Very Steep Bear",
        "Parabolic Bull",
    ]
    slope_emojis = [
        "➡️",
        "↗️", "↘️",
        "📈", "📉",
        "🚀", "💀",
        "🚀🚀",
    ]
    ema_slope_label = pd.Series(np.select(slope_conditions, slope_labels, default="Cliff Drop Bear"), index=out.index)
    ema_slope_emoji = pd.Series(np.select(slope_conditions, slope_emojis, default="💀💀"), index=out.index)

    slope_warmup = ema_slope.isna()
    ema_slope_label = ema_slope_label.mask(slope_warmup, "warmup")
    ema_slope_emoji = ema_slope_emoji.mask(slope_warmup, "")

    out["ema_slope"] = ema_slope
    out["ema_slope_angle"] = ema_slope_angle
    out["ema_slope_label"] = ema_slope_label
    out["ema_slope_emoji"] = ema_slope_emoji

    return out


# ============================================================
# CATATAN VALIDASI - WAJIB DIKERJAKAN SEBELUM DIPAKAI BACKTEST
# ============================================================
#
# [ ] Layer numerik: cocokkan ma1..ma12 Python vs 12 garis ribbon di
#     TradingView di beberapa titik sample, UNTUK SETIAP maType kalau
#     memang berencana ganti-ganti tipe MA (default EMA dulu cukup).
# [ ] KAMA (kalau dipakai): validasi ekstra hati-hati karena rekursif
#     dgn sc dinamis - paling gampang meleset kalau ada salah index.
# [ ] Deviation bands: cocokkan garis upper/lower band 1 di chart
#     (kalau showDeviationBands dinyalain di TV) vs dev_upper_1/
#     dev_lower_1 Python.
# [ ] stdev ddof=0 assumption (kalau useMAD=False dipakai): SAMA
#     seperti pending item di atr_percentage.py, belum tervalidasi.
# [ ] trend_label: KARENA TV cuma nampilin dashboard di bar terakhir
#     (barstate.islast), validasi harus dilakukan dengan REPLAY/scrub
#     manual TradingView per-bar, bukan cuma screenshot kondisi
#     sekarang - lihat catatan gotcha visibility di atas docstring.
# [ ] Event (8 alertcondition): ini paling gampang divalidasi karena
#     independen dashboard - cocokkan waktu trigger vs alert log TV
#     kalau alert pernah di-set, atau vs titik crossover manual di chart.
# [ ] Sampling representasi kondisi market berbeda (trending, sideways,
#     volatile), terutama buat 4 trend_method yang beda karakter.
#
# Begitu stage 2 (fetcher Binance) selesai dibangun, jalankan validasi
# ini sebelum file ini dipakai sebagai bahan strategi resmi manapun.


if __name__ == "__main__":
    rng_seed = np.random.default_rng(11)
    n_bars = 500
    close = 100 + np.cumsum(rng_seed.normal(0, 1, n_bars))
    open_ = close - rng_seed.normal(0, 0.5, n_bars)
    high = np.maximum(close, open_) + rng_seed.uniform(0.05, 1.2, n_bars)
    low = np.minimum(close, open_) - rng_seed.uniform(0.05, 1.2, n_bars)

    df_test = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})

    result = calculate_ema_ribbon_krypt(df_test)
    print("Kolom hasil:", list(result.columns))
    print("\nContoh 10 baris setelah warm-up (trend_method default Ribbon Divergence):")
    print(result[["ma1", "ma10", "div_pct", "trend_label", "verdict_label", "ribbon_strength"]].iloc[400:410].to_string())
    print("\nDistribusi trend_label (sanity check, data sintetis):")
    print(result["trend_label"].value_counts())

    print("\nTest 4 trend_method (harus jalan tanpa error, distribusi beda karakter):")
    for tm in ["MA200 Cross", "Ribbon Divergence", "Short vs Long Ribbon", "Ribbon Alignment"]:
        r = calculate_ema_ribbon_krypt(df_test, trend_method=tm)
        print(f"  {tm}: {dict(r['trend_label'].value_counts())}")

    print("\nTest tiap maType (harus jalan tanpa error):")
    for mt in ["SMA", "EMA", "WMA", "RMA", "HMA", "DEMA", "TEMA", "KAMA"]:
        r = calculate_ema_ribbon_krypt(df_test, ma_type=mt)
        print(f"  {mt}: ma1 terakhir = {r['ma1'].iloc[-1]:.4f}, NaN count ma1 = {r['ma1'].isna().sum()}")

    print("\nTotal event per kolom:")
    event_cols = [c for c in result.columns if c.endswith("_event")]
    print(result[event_cols].sum())
