"""
indicators/python/robust_momcand.py

Replikasi Python dari "Robust + MomCand Signal" (Pine Script v6).
Panduan replikasi: journal/stage_03_replikasi_indikator.md

STATUS: layer numerik + layer fase/sinyal sudah diimplementasikan untuk
        3 dari 4 mode Momentum Candle (Fixed Pips, Dynamic ATR, Smart
        Stats). Mode CRT (2-Candle) SENGAJA BELUM digarap - keputusan
        eksplisit dari Zenlol (skip CRT dulu). BELUM divalidasi
        terhadap TradingView asli.

=====================================================================
KEPUTUSAN SCOPE (disepakati sebelum coding)
=====================================================================
1. HTF (higher timeframe) Robust Lines - section 2 & HTF Cross Labels
   di source asli DIBUANG TOTAL dari replikasi ini. ALASAN (ditelusuri
   dari kode, bukan tebakan): htf_fast/htf_main/htf_slow/htf_cls cuma
   dipakai buat plot garis + label cross (htf_xup_*/htf_xdn_*) - GAK
   ADA satupun yang nyambung ke rob_trend_up/rob_trend_dn atau ke
   sig_bull/sig_bear final. Robust Direction Filter (rob_dir_on) juga
   cuma pakai rob_trend_up/dn dari CURRENT TF. Jadi HTF section itu
   100% visual/informational, gak mengubah sinyal tradeable sama
   sekali - konsisten dengan alasan skip section 6 di FBF kemarin.
   BONUS: ini juga otomatis menghindari kebutuhan data multi-timeframe
   (yang butuh timestamp asli utk alignment "closed HTF candle" -
   belum ada infrastrukturnya karena stage 2 fetcher belum dibangun).
2. Mode Momentum Candle: Fixed Pips, Dynamic ATR, Smart Stats
   diimplementasikan. CRT (2-Candle) SKIP - keputusan eksplisit dari
   Zenlol pas ditanya. Kalau mom_mode="CRT (2-Candle)" dipanggil,
   function raise NotImplementedError (fail fast, bukan silent wrong
   result).
3. Ketiga mode yang digarap (fp_ok/atr_ok/smt_ok) dihitung SEKALIGUS
   di tiap bar terlepas dari mom_mode yang aktif - biar bisa
   dibandingkan langsung tanpa run ulang 3x kalau nanti mau eksperimen
   pilih mode mana yang paling masuk akal buat setup.

=====================================================================
CATATAN STRUKTUR: GAK PERLU LOOP BAR-BY-BAR
=====================================================================
Beda dari smi_pro_v3.py & fbf_break_filter.py: indikator ini GAK PUNYA
state persisten antar-bar (gak ada var/counter Pine, gak ada candidate
array). Semua kolom murni fungsi dari nilai-nilai di bar itu sendiri
+ rolling window biasa. Makanya seluruh replikasi ini vectorized penuh
pakai pandas/numpy, TANPA loop eksplisit - ini bukan pelanggaran
prinsip stage_03 (yang ngewajibin loop CUMA buat kasus ada state
persisten/referensi antar-bar yang berisiko lookahead), karena memang
gak ada state semacam itu di sini.

=====================================================================
OBSERVASI TRANSPARAN (bukan keputusan, cuma flag ke Zenlol)
=====================================================================
rob_dir_mode punya 2 pilihan ("Only One Direction" vs "Both Direction
(Reverse)") - ditelusuri source-nya, DUA-DUANYA MENGHASILKAN OUTPUT
MATEMATIS IDENTIK. Ini karena bull_raw & bear_raw gak pernah true
bareng (candle cuma bisa bull ATAU bear, gak dua-duanya), dan
rob_trend_up/rob_trend_dn saling eksklusif waktu salah satunya true
(bukan neutral). Jadi "not rob_trend_up" == "rob_trend_dn" persis di
kondisi non-neutral, bikin kedua cabang logic ketemu hasil yang sama.
Kemungkinan ini opsi redundant di source asli, bukan bug replikasi.
Tetap direplikasi 2-2 nya PERSIS sesuai source (fungsi ini gak
"membetulkan" source, cuma mencerminkan), lihat fungsi
`_apply_direction_filter` di bawah.

Gotcha lain yang dijaga:
- Pine v4/v6 atr()/ta.atr() default = Wilder smoothing (RMA) - dipakai
  fungsi rma() generik yang juga dukung EMA/SMA/WMA sesuai pilihan
  atr_smooth (dipakai mode Dynamic ATR)
- f_mad (dipakai Smart Stats) = ROLLING MAD dua tahap: rolling median
  body dulu, baru rolling median dari |body - rolling_median| -
  BUKAN MAD sekali jalan, jangan disederhanakan
- f_robust (Robust Lines) = MAD CROSS-SECTIONAL (antar beberapa nilai
  EMA di satu bar yang sama), BEDA KONSEP dari f_mad yang rolling
  antar-waktu - dua-duanya sama-sama "MAD" tapi dimensi beda, jangan
  ketuker
- Stack filter (rob_stack_on) béda urutan cek dari align_mode - align
  mode dulu, baru stack filter meng-AND-kan hasilnya belakangan
"""

import numpy as np
import pandas as pd


MAD_MULT = 2.5  # konstanta f_robust, hardcoded persis di source Pine


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)


def _rma(series: pd.Series, length: int) -> pd.Series:
    """Wilder smoothing generik - dipakai basis default ta.atr()."""
    out = pd.Series(np.nan, index=series.index)
    n = len(series)
    if n < length:
        return out
    out.iloc[length - 1] = series.iloc[:length].mean()
    for i in range(length, n):
        out.iloc[i] = (out.iloc[i - 1] * (length - 1) + series.iloc[i]) / length
    return out


def _wma(series: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def _f_atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int, smooth: str) -> pd.Series:
    tr = _true_range(high, low, close)
    if smooth == "EMA":
        return tr.ewm(span=length, adjust=False).mean()
    elif smooth == "SMA":
        return tr.rolling(length).mean()
    elif smooth == "WMA":
        return _wma(tr, length)
    else:  # "RMA" default
        return _rma(tr, length)


def _f_mad_rolling(src: pd.Series, length: int) -> pd.Series:
    """
    Analog f_mad() Pine - MAD dua-tahap ROLLING ANTAR-WAKTU (bukan
    cross-sectional). Dipakai Smart Stats mode.
    """
    med = src.rolling(length).median()
    dev = (src - med).abs()
    return dev.rolling(length).median()


def _f_robust(emas: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    Analog f_robust() Pine - MAD CROSS-SECTIONAL (antar beberapa nilai
    EMA DI BAR YANG SAMA, bukan rolling antar-waktu). emas shape
    (n_bars, n_periods). Return shape (n_bars,).
    """
    med = np.median(emas, axis=1)
    devs = np.abs(emas - med[:, None])
    mad = np.median(devs, axis=1)
    lo = med - mad * MAD_MULT
    hi = med + mad * MAD_MULT
    clipped = np.clip(emas, lo[:, None], hi[:, None])
    w = weights / weights.sum()
    return (clipped * w[None, :]).sum(axis=1)


def _apply_direction_filter(
    bull_raw: np.ndarray, bear_raw: np.ndarray,
    trend_up: np.ndarray, trend_dn: np.ndarray,
    rob_dir_mode: str,
) -> tuple:
    """
    Analog blok `if rob_dir_on ...` Pine. Lihat OBSERVASI TRANSPARAN
    di docstring modul - 2 mode di rob_dir_mode matematis identik,
    tapi tetap direplikasi 2-2nya persis sesuai source.
    """
    bull_out = bull_raw.copy()
    bear_out = bear_raw.copy()
    neutral = ~(trend_up | trend_dn)
    bull_out[neutral] = False
    bear_out[neutral] = False
    nonneutral = ~neutral
    if rob_dir_mode == "Only One Direction":
        bull_out[nonneutral] = bull_out[nonneutral] & trend_up[nonneutral]
        bear_out[nonneutral] = bear_out[nonneutral] & trend_dn[nonneutral]
    else:  # "Both Direction (Reverse)"
        bull_out[nonneutral] = bull_out[nonneutral] & (~trend_dn[nonneutral])
        bear_out[nonneutral] = bear_out[nonneutral] & (~trend_up[nonneutral])
    return bull_out, bear_out


def calculate_robust_momcand(
    df: pd.DataFrame,
    # 1. Robust Lines
    rob_show_fast: bool = True,
    rob_show_main: bool = True,
    rob_show_slow: bool = True,
    rob_align_mode: str = "AND (semua harus align)",
    rob_stack_on: bool = True,
    rob_stack_eq_ok: bool = False,
    # 3. Momentum Candle
    mom_mode: str = "Smart Stats",
    fp_min_pips: float = 20.0,
    fp_pip_size: float = 0.0001,
    atr_len: int = 14,
    atr_mult: float = 1.5,
    atr_smooth: str = "RMA",
    qt_look: int = 200,
    qt_dev: float = 2.0,
    qt_max_wick: float = 0.30,
    # 4. Signal & Filter
    side_mode: str = "Both",
    rob_dir_on: bool = False,
    rob_dir_mode: str = "Only One Direction",
) -> pd.DataFrame:
    """
    df wajib punya kolom: 'open', 'high', 'low', 'close'.
    Parameter default persis sama dengan default input Pine source asli.

    mom_mode="CRT (2-Candle)" akan raise NotImplementedError - mode ini
    sengaja belum digarap (keputusan Zenlol).
    """
    if mom_mode == "CRT (2-Candle)":
        raise NotImplementedError(
            "Mode CRT (2-Candle) sengaja belum direplikasi - keputusan "
            "eksplisit skip CRT. Pilih mode lain (Fixed Pips / Dynamic "
            "ATR / Smart Stats), atau minta digarap dulu kalau memang "
            "mau dipakai."
        )

    out = df.copy()
    close = out["close"]
    high = out["high"]
    low = out["low"]
    open_ = out["open"]

    # ================================================================
    # ROBUST LINES (current TF)
    # ================================================================
    e1 = close.ewm(span=8, adjust=False).mean()
    e2 = close.ewm(span=13, adjust=False).mean()
    e3 = close.ewm(span=21, adjust=False).mean()
    e4 = close.ewm(span=34, adjust=False).mean()
    e5 = close.ewm(span=50, adjust=False).mean()
    e6 = close.ewm(span=100, adjust=False).mean()
    e7 = close.ewm(span=150, adjust=False).mean()
    e8 = close.ewm(span=200, adjust=False).mean()

    fast_stack = np.column_stack([e1, e2, e3, e4])
    main_stack = np.column_stack([e1, e2, e3, e4, e5, e6, e7, e8])
    slow_stack = np.column_stack([e5, e6, e7, e8])

    rob_fast = _f_robust(fast_stack, np.array([1.0, 1.5, 2.0, 2.5]))
    rob_main = _f_robust(main_stack, np.array([1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 4.5, 5.0]))
    rob_slow = _f_robust(slow_stack, np.array([3.0, 4.0, 4.5, 5.0]))

    out["rob_fast"] = rob_fast
    out["rob_main"] = rob_main
    out["rob_slow"] = rob_slow

    close_v = close.values
    up_fast = close_v > rob_fast
    up_main = close_v > rob_main
    up_slow = close_v > rob_slow
    dn_fast = close_v < rob_fast
    dn_main = close_v < rob_main
    dn_slow = close_v < rob_slow

    rob_up_and = (up_fast if rob_show_fast else True) & (up_main if rob_show_main else True) & (up_slow if rob_show_slow else True)
    rob_dn_and = (dn_fast if rob_show_fast else True) & (dn_main if rob_show_main else True) & (dn_slow if rob_show_slow else True)
    rob_up_any = (up_fast if rob_show_fast else False) | (up_main if rob_show_main else False) | (up_slow if rob_show_slow else False)
    rob_dn_any = (dn_fast if rob_show_fast else False) | (dn_main if rob_show_main else False) | (dn_slow if rob_show_slow else False)

    up_pri_f = up_fast if rob_show_fast else (up_main if rob_show_main else up_slow)
    up_pri_m = up_main if rob_show_main else (up_fast if rob_show_fast else up_slow)
    up_pri_s = up_slow if rob_show_slow else (up_main if rob_show_main else up_fast)
    dn_pri_f = dn_fast if rob_show_fast else (dn_main if rob_show_main else dn_slow)
    dn_pri_m = dn_main if rob_show_main else (dn_fast if rob_show_fast else dn_slow)
    dn_pri_s = dn_slow if rob_show_slow else (dn_main if rob_show_main else dn_fast)

    align_map_up = {
        "AND (semua harus align)": rob_up_and,
        "OR (salah satu cukup)": rob_up_any,
        "Priority FAST": up_pri_f,
        "Priority MAIN": up_pri_m,
        "Priority SLOW": up_pri_s,
    }
    align_map_dn = {
        "AND (semua harus align)": rob_dn_and,
        "OR (salah satu cukup)": rob_dn_any,
        "Priority FAST": dn_pri_f,
        "Priority MAIN": dn_pri_m,
        "Priority SLOW": dn_pri_s,
    }
    rob_trend_up = align_map_up.get(rob_align_mode, rob_up_and).copy()
    rob_trend_dn = align_map_dn.get(rob_align_mode, rob_dn_and).copy()

    if rob_stack_on and rob_show_fast and rob_show_main and rob_show_slow:
        if rob_stack_eq_ok:
            st_bull = (rob_fast >= rob_main) & (rob_main >= rob_slow)
            st_bear = (rob_fast <= rob_main) & (rob_main <= rob_slow)
        else:
            st_bull = (rob_fast > rob_main) & (rob_main > rob_slow)
            st_bear = (rob_fast < rob_main) & (rob_main < rob_slow)
        rob_trend_up = rob_trend_up & st_bull
        rob_trend_dn = rob_trend_dn & st_bear

    out["rob_trend_up"] = rob_trend_up
    out["rob_trend_dn"] = rob_trend_dn
    out["rob_dir_text"] = np.where(rob_trend_up, "BULL UP", np.where(rob_trend_dn, "BEAR DN", "NEUTRAL"))

    # ================================================================
    # MOMENTUM CANDLE - 3 mode digarap (fp/atr/smart), semua dihitung
    # sekaligus biar bisa dibandingkan
    # ================================================================
    body = (close - open_).abs()
    full_rng = high - low
    wick_rat = np.where(full_rng > 0, (full_rng - body) / full_rng, np.nan)
    is_bull_c = (close > open_).values
    is_bear_c = (close < open_).values

    out["body"] = body
    out["full_rng"] = full_rng
    out["wick_rat"] = wick_rat
    out["is_bull_c"] = is_bull_c
    out["is_bear_c"] = is_bear_c

    # -- Fixed Pips --
    fp_thresh = fp_min_pips * fp_pip_size
    fp_ok = (body >= fp_thresh).values
    out["fp_ok"] = fp_ok

    # -- Dynamic ATR --
    atr_val = _f_atr(high, low, close, atr_len, atr_smooth) * atr_mult
    atr_ok = (body >= atr_val).values
    out["atr_threshold"] = atr_val
    out["atr_ok"] = atr_ok

    # -- Smart Stats --
    smart_median = body.rolling(qt_look).median()
    smart_mad = _f_mad_rolling(body, qt_look)
    smart_threshold = smart_median + smart_mad * qt_dev
    smart_mom_pass = (body >= smart_threshold).values
    smart_wick_ok = ((full_rng > 0) & (pd.Series(wick_rat) <= qt_max_wick)).values
    smt_ok = smart_mom_pass & smart_wick_ok
    out["smart_median"] = smart_median
    out["smart_mad"] = smart_mad
    out["smart_threshold"] = smart_threshold
    out["smart_wick_ok"] = smart_wick_ok
    out["smt_ok"] = smt_ok

    # -- pilih mode aktif --
    pass_mode = {"Fixed Pips": fp_ok, "Dynamic ATR": atr_ok, "Smart Stats": smt_ok}[mom_mode]
    mom_bull = pass_mode & is_bull_c
    mom_bear = pass_mode & is_bear_c
    out["mom_bull"] = mom_bull
    out["mom_bear"] = mom_bear

    # ================================================================
    # SIGNAL GENERATION
    # ================================================================
    bull_raw = mom_bull.copy()
    bear_raw = mom_bear.copy()

    if rob_dir_on:
        trend_up_arr = rob_trend_up.values if hasattr(rob_trend_up, "values") else np.asarray(rob_trend_up)
        trend_dn_arr = rob_trend_dn.values if hasattr(rob_trend_dn, "values") else np.asarray(rob_trend_dn)
        bull_raw, bear_raw = _apply_direction_filter(
            bull_raw, bear_raw, trend_up_arr, trend_dn_arr, rob_dir_mode,
        )

    sig_bull = bull_raw & (side_mode in ("Both", "Buy Only"))
    sig_bear = bear_raw & (side_mode in ("Both", "Sell Only"))

    out["bull_raw"] = bull_raw
    out["bear_raw"] = bear_raw
    out["sig_bull"] = sig_bull
    out["sig_bear"] = sig_bear
    out["signal_text"] = np.where(sig_bull, "BULL", np.where(sig_bear, "BEAR", "--"))

    return out


# ============================================================
# CATATAN VALIDASI - WAJIB DIKERJAKAN SEBELUM DIPAKAI BACKTEST
# ============================================================
#
# [ ] Robust Lines: cocokkan rob_fast/rob_main/rob_slow Python vs 3
#     garis di TradingView, di beberapa titik sample.
# [ ] Momentum Candle: cocokkan fp_ok/atr_ok/smt_ok Python vs marker
#     sinyal (segitiga/label) di chart TV, UNTUK MODE YANG AKTIF di
#     config Pine saat itu - inget mode di TV cuma 1 aktif per waktu,
#     jadi validasi harus dicocokkan mode-per-mode gonta-ganti di TV.
# [ ] rob_dir_text ("BULL UP"/"BEAR DN"/"NEUTRAL") cocokkan ke baris
#     dashboard "Rob Dir" di chart.
# [ ] signal_text cocokkan ke baris dashboard "Signal" DAN ke posisi
#     marker segitiga bull/bear di chart.
# [ ] KHUSUS smart_mad: pastikan Python ambil MAD dua-tahap yang benar
#     (median dulu, baru median dari deviasi) - bukan std dev biasa.
# [ ] Sample market beda-beda kondisi (trending, sideways, volatile),
#     terutama buat qt_max_wick filter yang bisa nolak banyak sinyal
#     di kondisi wick panjang (news spike, dsb).
#
# BELUM DIGARAP (nunggu keputusan lanjutan):
# [ ] Mode CRT (2-Candle) - skip, keputusan eksplisit.
# [ ] HTF Robust Lines + HTF Cross Label - skip permanen, murni visual
#     (lihat penjelasan di docstring modul), TIDAK perlu digarap lagi
#     kecuali suatu saat sig_bull/sig_bear diubah buat ikut baca HTF.


if __name__ == "__main__":
    rng_seed = np.random.default_rng(21)
    n_bars = 500
    close = 100 + np.cumsum(rng_seed.normal(0, 1, n_bars))
    open_ = close - rng_seed.normal(0, 0.5, n_bars)
    high = np.maximum(close, open_) + rng_seed.uniform(0.05, 1.2, n_bars)
    low = np.minimum(close, open_) - rng_seed.uniform(0.05, 1.2, n_bars)

    df_test = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})

    for mode in ["Fixed Pips", "Dynamic ATR", "Smart Stats"]:
        result = calculate_robust_momcand(df_test, mom_mode=mode)
        n_bull = int(result["sig_bull"].sum())
        n_bear = int(result["sig_bear"].sum())
        print(f"Mode {mode}: sig_bull={n_bull}, sig_bear={n_bear}")

    print("\nContoh 10 baris (mode Smart Stats):")
    result = calculate_robust_momcand(df_test, mom_mode="Smart Stats")
    print(result[["rob_fast", "rob_main", "rob_slow", "rob_dir_text", "signal_text"]].iloc[250:260].to_string())

    print("\nTest CRT harus raise NotImplementedError:")
    try:
        calculate_robust_momcand(df_test, mom_mode="CRT (2-Candle)")
        print("GAGAL - harusnya raise error tapi gak raise")
    except NotImplementedError as e:
        print("OK, raise seperti diharapkan:", str(e)[:60], "...")

    print("\nTest rob_dir_on=True (Robust Direction Filter):")
    result_filtered = calculate_robust_momcand(df_test, mom_mode="Smart Stats", rob_dir_on=True, rob_dir_mode="Only One Direction")
    result_filtered2 = calculate_robust_momcand(df_test, mom_mode="Smart Stats", rob_dir_on=True, rob_dir_mode="Both Direction (Reverse)")
    same = (result_filtered["sig_bull"] == result_filtered2["sig_bull"]).all() and (result_filtered["sig_bear"] == result_filtered2["sig_bear"]).all()
    print("Kedua rob_dir_mode hasilnya identik (sesuai observasi di docstring)?", same)
