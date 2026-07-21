"""
indicators/python/rsi_pro_enhanced.py

Replikasi Python dari "RSI Pro Enhanced" (Pine Script v6).
Panduan replikasi: journal/stage_03_replikasi_indikator.md
Metodologi cross-check: handoff_review_indikator.md

STATUS: layer numerik + layer fase/state + divergensi sudah diimplementasikan.
        Ini BUILD PERTAMA (belum ada versi Python sebelumnya untuk indikator
        ini) - dibuat sebelum sesi deep-dive review, sekaligus SUDAH
        memasukkan temuan gotcha yang ketemu saat penulisan (lihat bagian
        CATATAN GOTCHA di bawah). Validasi numerik ke data real TradingView
        MASIH PENDING (blocked, nunggu stage 2 - fetcher Binance belum ada).

Tiga layer output:
1. Layer numerik  : rsi, rsi_ma, rsi_hist, bb_upper, bb_lower
2. Layer fase      : hist_momentum, hist_state_label, vs_ma, zone, cross_event,
                     bars_since_cross, b_cnt, a_cnt, pa_pd_state,
                     pa_pd_progress_text, signal, signal_strength,
                     marker_cross_mid_up/down, marker_enter_ob/os,
                     marker_exit_ob/os
3. Layer divergensi: divergence_event (Regular Bull/Bear saja - indikator ini
                     TIDAK punya toggle Hidden Divergence, beda dari SMI Pro v3)

=====================================================================
CATATAN GOTCHA PENTING (ditemukan waktu telusuri source Pine baris-per-baris,
sesuai mindset "lapisan mesin vs lapisan visibility" + "poin 2b" di handoff)
=====================================================================

1. DUA "TITIK TENGAH" YANG BEDA, JANGAN KETUKER
   `rsiMID` (default 40) HANYA dipakai untuk counter PA/PD (bCnt/aCnt).
   Semua elemen lain yang "kelihatannya" soal titik tengah - zona "Middle"
   di `sZone`, cabang BUY/SELL di `sSig`, DAN dua marker cross tengah
   (`cUM`/`cDM`) - semuanya pakai ANGKA HARDCODE 50, BUKAN `rsiMID`.
   Ini persis pola "poin 2b" yang disebut di handoff (SMI Pro v3 pernah
   ketemu kasus serupa dgn Zone vs Phase) - dua hal yang namanya mirip
   ("tengah") tapi definisinya beda. Direplikasi PERSIS: `rsi_mid` cuma
   dipakai di PA/PD, angka `50` di-hardcode literal di kode (lihat komentar
   inline `# literal 50, BUKAN rsi_mid`).

2. AKIBATNYA: ZONA "Middle" PRAKTIS TAK TERJANGKAU DI DEFAULT
   Cascade `sZone` = OB > rsiMID(40) > 50 > rsiOS(30) > OS. Begitu
   `rsi > rsiMID` (40) sudah TRUE, cabang jatuh ke "Upper N" - cabang
   "Middle" (butuh `rsi > 50`) cuma bisa dicek kalau cabang sebelumnya
   FALSE, yaitu kalau `rsi <= 40`. Tapi kalau `rsi <= 40`, mustahil
   `rsi > 50` di saat bersamaan. Jadi dengan default `rsiMID=40 < 50`,
   zona "Middle" adalah DEAD BRANCH - tidak akan pernah muncul di data
   real, kecuali user mengubah `rsiMID` jadi >50. Ini bukan bug replikasi
   Python, ini karakteristik source Pine aslinya - dicatat eksplisit,
   bukan "dibetulkan" diam-diam.

3. TIDAK ADA "PHASE" CASCADE GABUNGAN (beda dari SMI Pro v3 / FBF)
   SMI Pro v3 & FBF punya satu kolom teks gabungan (barStateTxt/phase_label)
   yang jadi representasi tunggal seluruh state, plus dipakai buat
   barcolor() candle. RSI Pro Enhanced TIDAK PUNYA ini - overlay=false,
   TIDAK ADA barcolor() sama sekali di source. Zone, Hist, Signal, Cross,
   PA/PD, Divergence semuanya baris dashboard TERPISAH dan INDEPENDEN,
   tidak pernah digabung jadi satu cascade prioritas. `sSig` ("Signal")
   paling dekat ke konsep "kesimpulan", tapi cascade-nya cuma pakai
   rsiOB/rsiOS + vs-MA + angka 50 - TIDAK memasukkan hist_momentum,
   cross, PA/PD, atau divergence sama sekali.

4. LAPISAN VISIBILITY: MINIMAL/TIDAK ADA GATING SIGNIFIKAN
   Beda dari FBF (filter trend Supertrend nge-gate visibility wave secara
   signifikan, default ON), indikator ini tidak punya elemen visual yang
   nge-gate sinyal. Semua toggle (`sMk`, `showLbl`, `showHist`, dst)
   murni kosmetik tampilan, tidak mengubah nilai sinyal itu sendiri.
   Jadi TIDAK ADA kolom "visibility" yang perlu direplikasi di sini
   (beda dari fbf_break_filter.py yang punya bull_wave_visible dst).

5. `maType = "None"` TETAP MEMPENGARUHI SIGNAL, BUKAN MENONAKTIFKANNYA
   Kalau MA dimatikan: `rsiH = 0` (konstan), TAPI `sAb` (above/below MA)
   di-hardcode TRUE, bukan dihapus dari perhitungan. `sSig` tetap
   memakai `sAb` ini - akibatnya kalau MA off, cabang SELL/STR SELL di
   Signal TIDAK PERNAH bisa terpicu (karena butuh `not sAb`, yg selalu
   false), cuma NEUTRAL atau BUY/STR BUY yang mungkin muncul. Direplikasi
   apa adanya (bukan dianggap "MA off = signal off").

6. `rsiLen` DEFAULT DI SOURCE INI ADALAH 5, BUKAN 14
   Beda dari konvensi RSI standar (biasanya default 14) - source Pine
   ini defaultnya RSI(5), jauh lebih sensitif/cepat. Default Python
   disamakan persis (prinsip "default Pine = default Python").

7. Flat market (up=0 DAN down=0) -> RSI = 100, BUKAN 50
   Urutan pengecekan source: `down == 0 ? 100 : up == 0 ? 0 : ...` -
   `down==0` dicek DULUAN, jadi kalau up DAN down sama-sama 0 (harga
   flat total di window RSI), hasilnya 100 (masuk cabang pertama),
   BUKAN dianggap netral 50. Directkan persis urutan prioritas ini.

Gotcha teknis tambahan (level implementasi):
- ta.rma() = Wilder smoothing, dipakai konsisten dgn fungsi sejenis di
  file lain project ini (wilder_atr, dst) - seed = SMA window pertama,
  lanjut rekursif.
- ta.stdev() default Pine = population stdev (ddof=0) - dipakai untuk BB
  band di mode "SMA + BB", konsisten dengan catatan yang sama di
  atr_percentage.py.
- ta.cross()/crossover()/crossunder() Pine: crossover = cur1>cur2 AND
  prev1<=prev2; crossunder = cur1<cur2 AND prev1>=prev2 - dipakai persis
  utk sCr (arah tetap direkonstruksi eksplisit sbg cross_event walau
  dashboard Pine aslinya cuma nampilin "N bar" tanpa arah), dan utk 6
  marker (cUM/cDM/cUO/cDO/cDB/cUS).
- Divergensi: pivot dideteksi di SERIES RSI (bukan harga), delay
  konfirmasi = div_right bar setelah titik pivot asli (bukan real-time) -
  sama prinsip dgn smi_pro_v3.py.
- Loop bar-by-bar dipakai untuk semua state persisten (b_cnt/a_cnt,
  histogram momentum, cross tracking) - BUKAN vectorized, supaya tidak
  lookahead bias, sesuai checklist stage_03.
"""

import numpy as np
import pandas as pd


# ============================================================
# HELPER: MOVING AVERAGE VARIAN
# ============================================================

def _wilder_rma(series: pd.Series, length: int) -> pd.Series:
    """Analog ta.rma() Pine = Wilder smoothing. Seed = SMA window pertama."""
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


def _vwma(src: pd.Series, volume: pd.Series, length: int) -> pd.Series:
    return (src * volume).rolling(length).sum() / volume.rolling(length).sum()


def _get_ma(src: pd.Series, length: int, ma_type: str, volume: pd.Series = None) -> pd.Series:
    """Dispatcher analog fungsi ma() di source Pine."""
    if ma_type in ("SMA", "SMA + BB"):
        return src.rolling(length).mean()
    elif ma_type == "EMA":
        return src.ewm(span=length, adjust=False).mean()
    elif ma_type == "SMMA (RMA)":
        return _wilder_rma(src, length)
    elif ma_type == "WMA":
        return _wma(src, length)
    elif ma_type == "VWMA":
        if volume is None:
            raise ValueError(
                "ma_type='VWMA' butuh kolom 'volume' di df, tapi tidak tersedia. "
                "Sediakan kolom volume, atau pakai ma_type lain."
            )
        return _vwma(src, volume, length)
    else:
        raise ValueError(f"ma_type tidak dikenal: {ma_type!r}")


def _find_pivots(series: pd.Series, left: int, right: int, mode: str) -> list:
    """
    Analog ta.pivotlow()/ta.pivothigh() Pine. Return list of
    (pivot_bar_idx, pivot_value, confirm_bar_idx). confirm_bar_idx = delay
    konfirmasi = pivot_bar_idx + right bar (baru "diketahui" di bar ini).
    Tie-break: unique min/max (sama disclaimer dgn smi_pro_v3.py - belum
    tervalidasi 100% lawan behavior asli TradingView untuk kasus seri).
    """
    n = len(series)
    vals = series.values
    pivots = []
    for i in range(left, n - right):
        if np.isnan(vals[i]):
            continue
        window = vals[i - left: i + right + 1]
        if np.any(np.isnan(window)):
            continue
        center = vals[i]
        if mode == "low":
            is_piv = center == window.min() and (window == center).sum() == 1
        else:
            is_piv = center == window.max() and (window == center).sum() == 1
        if is_piv:
            pivots.append((i, center, i + right))
    return pivots


# ============================================================
# MAIN FUNCTION
# ============================================================

def calculate_rsi_pro_enhanced(
    df: pd.DataFrame,
    src_col: str = "close",
    rsi_len: int = 5,
    ma_type: str = "EMA",          # "None"/"SMA"/"EMA"/"SMMA (RMA)"/"WMA"/"VWMA"/"SMA + BB"
    ma_len: int = 14,
    bb_mult: float = 2.0,
    rsi_ob: float = 80,
    rsi_mid: float = 40,           # HANYA dipakai PA/PD - lihat CATATAN GOTCHA #1
    rsi_os: float = 30,
    akum_candles: int = 2,
    dist_candles: int = 2,
    calc_div: bool = True,
    div_left: int = 5,             # lbL
    div_right: int = 5,            # lbR
    div_range_lower: int = 5,      # rngL
    div_range_upper: int = 60,     # rngU
) -> pd.DataFrame:
    """
    df wajib punya kolom `src_col` (default 'close'). Kalau ma_type="VWMA",
    df wajib juga punya kolom 'volume'.
    Parameter default persis sama dengan default input Pine source asli.

    Return: copy df + kolom tambahan numerik + fase/state + divergensi.
    """
    out = df.copy()
    n = len(out)
    src = out[src_col].astype(float)
    volume = out["volume"].astype(float) if "volume" in out.columns else None

    enable_ma = ma_type != "None"
    is_bb = ma_type == "SMA + BB"

    # ================================================================
    # LAYER NUMERIK
    # ================================================================
    change = src.diff()
    up_raw = change.clip(lower=0)
    down_raw = (-change).clip(lower=0)

    up = _wilder_rma(up_raw, rsi_len)
    down = _wilder_rma(down_raw, rsi_len)

    rsi = pd.Series(np.nan, index=out.index)
    valid = up.notna() & down.notna()
    u = up[valid].values
    d = down[valid].values
    # urutan prioritas PERSIS source: down==0 dicek DULUAN (lihat gotcha #7)
    rsi_valid_vals = np.where(d == 0, 100.0, np.where(u == 0, 0.0, 100 - (100 / (1 + u / d))))
    rsi.loc[valid] = rsi_valid_vals

    rsi_ma = _get_ma(rsi, ma_len, ma_type, volume) if enable_ma else pd.Series(np.nan, index=out.index)

    if enable_ma:
        rsi_h = rsi - rsi_ma
    else:
        rsi_h = pd.Series(0.0, index=out.index)
        rsi_h[rsi.isna()] = np.nan  # tetap NaN kalau rsi sendiri belum valid

    bb_upper = pd.Series(np.nan, index=out.index)
    bb_lower = pd.Series(np.nan, index=out.index)
    if is_bb:
        rsi_std = rsi.rolling(ma_len).std(ddof=0) * bb_mult  # population stdev, sesuai konvensi project
        bb_upper = rsi_ma + rsi_std
        bb_lower = rsi_ma - rsi_std

    out["rsi"] = rsi
    out["rsi_ma"] = rsi_ma
    out["rsi_hist"] = rsi_h
    out["bb_upper"] = bb_upper
    out["bb_lower"] = bb_lower

    # ================================================================
    # LAYER FASE/STATE - loop bar-by-bar (state persisten: b_cnt, a_cnt,
    # bars_since_cross)
    # ================================================================
    hist_momentum = [None] * n
    hist_state_label = [None] * n
    vs_ma = [None] * n
    zone = [None] * n
    cross_event = [None] * n
    bars_since_cross = [None] * n
    b_cnt_col = [None] * n
    a_cnt_col = [None] * n
    pa_pd_state = [None] * n
    pa_pd_progress_text = [None] * n
    signal = [None] * n
    signal_strength = [None] * n
    marker_cross_mid_up = [False] * n
    marker_cross_mid_down = [False] * n
    marker_enter_ob = [False] * n
    marker_enter_os = [False] * n
    marker_exit_ob = [False] * n
    marker_exit_os = [False] * n

    b_cnt = 0
    a_cnt = 0
    prev_rsi = np.nan
    prev_rsi_ma = np.nan
    prev_rsi_h = np.nan
    last_cross_bar = None

    for i in range(n):
        cur_rsi = rsi.iloc[i]
        cur_ma = rsi_ma.iloc[i]
        cur_h = rsi_h.iloc[i]

        # --- rsi sendiri belum valid: semuanya warmup, gak ada yg bisa dihitung ---
        if np.isnan(cur_rsi):
            hist_momentum[i] = "warmup"
            hist_state_label[i] = "warmup"
            vs_ma[i] = "warmup"
            zone[i] = "warmup"
            cross_event[i] = "warmup"
            pa_pd_state[i] = "warmup"
            pa_pd_progress_text[i] = "warmup"
            signal[i] = "warmup"
            prev_rsi, prev_rsi_ma, prev_rsi_h = cur_rsi, cur_ma, cur_h
            continue

        # --- zone: cuma butuh rsi valid, gak butuh MA (lihat gotcha #1 & #2) ---
        if cur_rsi > rsi_ob:
            zn = "OB"
        elif cur_rsi > rsi_mid:
            zn = "Upper N"
        elif cur_rsi > 50:  # literal 50, BUKAN rsi_mid - lihat gotcha #1/#2
            zn = "Middle"
        elif cur_rsi > rsi_os:
            zn = "Lower N"
        else:
            zn = "OS"
        zone[i] = zn

        # --- markers: murni fungsi rsi vs level, gak butuh MA ---
        if not np.isnan(prev_rsi):
            marker_cross_mid_up[i] = cur_rsi > 50 and prev_rsi <= 50       # literal 50
            marker_cross_mid_down[i] = cur_rsi < 50 and prev_rsi >= 50     # literal 50
            marker_enter_ob[i] = cur_rsi > rsi_ob and prev_rsi <= rsi_ob
            marker_exit_ob[i] = cur_rsi < rsi_ob and prev_rsi >= rsi_ob
            marker_enter_os[i] = cur_rsi < rsi_os and prev_rsi >= rsi_os
            marker_exit_os[i] = cur_rsi > rsi_os and prev_rsi <= rsi_os

        # --- PA/PD counter: state persisten, cuma butuh rsi vs rsi_mid ---
        if cur_rsi < rsi_mid:
            b_cnt += 1
            a_cnt = 0
        elif cur_rsi > rsi_mid:
            a_cnt += 1
            b_cnt = 0
        else:
            b_cnt = 0
            a_cnt = 0
        b_cnt_col[i] = b_cnt
        a_cnt_col[i] = a_cnt

        pre_akum = (b_cnt == akum_candles)
        pre_dist = (a_cnt == dist_candles)
        pa_pd_state[i] = "pre_akum" if pre_akum else "pre_dist" if pre_dist else "none"

        pa_prog = f"{b_cnt}/{akum_candles}"
        pd_prog = f"{a_cnt}/{dist_candles}"
        if pre_akum:
            pa_pd_progress_text[i] = "PA ON"
        elif pre_dist:
            pa_pd_progress_text[i] = "PD ON"
        elif b_cnt > 0:
            pa_pd_progress_text[i] = f"PA {pa_prog}"
        elif a_cnt > 0:
            pa_pd_progress_text[i] = f"PD {pd_prog}"
        else:
            pa_pd_progress_text[i] = "-"

        # --- ma_ready: hist_momentum/vs_ma/cross_event/signal butuh MA valid
        #     (kalau enable_ma). Kalau ma_type="None", ma_ready otomatis True
        #     (rsi_h=0 & above=True hardcode, gotcha #5). ---
        ma_ready = (not enable_ma) or (not np.isnan(cur_ma))

        if not ma_ready:
            hist_momentum[i] = "warmup"
            hist_state_label[i] = "warmup"
            vs_ma[i] = "warmup"
            cross_event[i] = "warmup"
            signal[i] = "warmup"
            prev_rsi, prev_rsi_ma, prev_rsi_h = cur_rsi, cur_ma, cur_h
            continue

        above = (cur_rsi >= cur_ma) if enable_ma else True  # sAb, hardcode True kalau MA off
        vs_ma[i] = ("Bull" if above else "Bear") if enable_ma else "N/A"

        # --- histogram momentum (strict >0 / <=0, PERSIS source) ---
        if np.isnan(prev_rsi_h):
            hm = "flat"
        elif cur_h > prev_rsi_h and cur_h > 0:
            hm = "above_up"
        elif cur_h < prev_rsi_h and cur_h > 0:
            hm = "above_down"
        elif cur_h < prev_rsi_h and cur_h <= 0:
            hm = "below_down"
        elif cur_h > prev_rsi_h and cur_h <= 0:
            hm = "below_up"
        else:
            hm = "flat"
        hist_momentum[i] = hm
        hist_state_label[i] = {
            "above_up": "Exp Bull", "above_down": "Shr Bull",
            "below_down": "Exp Bear", "below_up": "Shr Bear",
            "flat": "Neutral",
        }[hm]

        # --- cross_event (sCr, arah direkonstruksi eksplisit) ---
        if enable_ma and not np.isnan(prev_rsi_ma):
            is_cu = cur_rsi > cur_ma and prev_rsi <= prev_rsi_ma
            is_cd = cur_rsi < cur_ma and prev_rsi >= prev_rsi_ma
            cross_any = is_cu or is_cd
            ce = "cross_up" if is_cu else "cross_down" if is_cd else "none"
        else:
            cross_any = False
            ce = "none"
        cross_event[i] = ce
        if cross_any:
            last_cross_bar = i
        bars_since_cross[i] = (i - last_cross_bar) if last_cross_bar is not None else None

        # --- signal (sSig) - cascade PAKAI literal 50, bukan rsi_mid ---
        if cur_rsi > rsi_ob and not above:
            sig = "STR SELL"
        elif cur_rsi < rsi_os and above:
            sig = "STR BUY"
        elif above and cur_rsi > 50:   # literal 50
            sig = "BUY"
        elif (not above) and cur_rsi < 50:  # literal 50
            sig = "SELL"
        else:
            sig = "NEUTRAL"
        signal[i] = sig
        signal_strength[i] = 90 if sig in ("STR BUY", "STR SELL") else 70 if sig in ("BUY", "SELL") else 30

        prev_rsi, prev_rsi_ma, prev_rsi_h = cur_rsi, cur_ma, cur_h

    out["hist_momentum"] = hist_momentum
    out["hist_state_label"] = hist_state_label
    out["vs_ma"] = vs_ma
    out["zone"] = zone
    out["cross_event"] = cross_event
    out["bars_since_cross"] = bars_since_cross
    out["b_cnt"] = b_cnt_col
    out["a_cnt"] = a_cnt_col
    out["pa_pd_state"] = pa_pd_state
    out["pa_pd_progress_text"] = pa_pd_progress_text
    out["signal"] = signal
    out["signal_strength"] = signal_strength
    out["marker_cross_mid_up"] = marker_cross_mid_up
    out["marker_cross_mid_down"] = marker_cross_mid_down
    out["marker_enter_ob"] = marker_enter_ob
    out["marker_enter_os"] = marker_enter_os
    out["marker_exit_ob"] = marker_exit_ob
    out["marker_exit_os"] = marker_exit_os

    # ================================================================
    # LAYER DIVERGENSI - pivot dideteksi di series RSI, delay konfirmasi
    # = div_right bar setelah titik pivot asli. HANYA Regular (bull/bear),
    # indikator ini TIDAK punya toggle Hidden Divergence.
    # ================================================================
    divergence_event = ["none"] * n
    if calc_div:
        low_price = out["low"].values if "low" in out.columns else src.values
        high_price = out["high"].values if "high" in out.columns else src.values

        pivot_lows = _find_pivots(rsi, div_left, div_right, mode="low")
        pivot_highs = _find_pivots(rsi, div_left, div_right, mode="high")

        last_pl_osc = last_pl_price = last_pl_bar = None
        for piv_bar, piv_val, confirm_bar in pivot_lows:
            cur_price = low_price[piv_bar]
            if last_pl_bar is not None:
                gap = piv_bar - last_pl_bar
                if div_range_lower <= gap <= div_range_upper:
                    if cur_price < last_pl_price and piv_val > last_pl_osc:
                        divergence_event[confirm_bar] = "bullish"
            last_pl_osc, last_pl_price, last_pl_bar = piv_val, cur_price, piv_bar

        last_ph_osc = last_ph_price = last_ph_bar = None
        for piv_bar, piv_val, confirm_bar in pivot_highs:
            cur_price = high_price[piv_bar]
            if last_ph_bar is not None:
                gap = piv_bar - last_ph_bar
                if div_range_lower <= gap <= div_range_upper:
                    if cur_price > last_ph_price and piv_val < last_ph_osc:
                        divergence_event[confirm_bar] = "bearish"
            last_ph_osc, last_ph_price, last_ph_bar = piv_val, cur_price, piv_bar

    out["divergence_event"] = divergence_event

    return out


# ============================================================
# CATATAN VALIDASI - WAJIB DIKERJAKAN SEBELUM DIPAKAI BACKTEST
# ============================================================
#
# [ ] Layer numerik: sample beberapa titik dari data OHLCV real, bandingkan
#     rsi/rsi_ma Python vs TradingView di candle yang sama persis.
# [ ] Layer fase: cocokkan zone, signal, hist_state_label, pa_pd_progress_text
#     Python vs baris dashboard chart asli - KHUSUSNYA cek apakah zona
#     "Middle" memang gak pernah muncul di data real (sesuai gotcha #2).
# [ ] Cek kasus rsi_mid diubah user jadi >50 - apakah zona "Middle" jadi
#     reachable seperti prediksi analisis gotcha #2.
# [ ] Layer divergensi: cocokkan label Bull/Bear di chart TV vs kolom
#     divergence_event, perhatikan bar konfirmasi (bukan bar pivot asli).
# [ ] Kalau ma_type="SMA + BB" dipakai: cocokkan bb_upper/bb_lower vs
#     2 garis BB di chart (ddof=0 population stdev, sama seperti
#     atr_percentage.py - BELUM di-cross-check numerik ke TradingView asli).
# [ ] Kalau ma_type="VWMA" dipakai: pastikan kolom volume yang dipakai
#     sudah sesuai (raw volume Binance, bukan quote volume).
# [ ] Sample market beda-beda kondisi (trending, sideways, volatile).
#
# Begitu stage 2 (fetcher Binance) selesai, jalankan validasi ini sebelum
# file ini dipakai sebagai bahan strategi resmi manapun.


if __name__ == "__main__":
    rng_seed = np.random.default_rng(11)
    n_bars = 300
    close = 100 + np.cumsum(rng_seed.normal(0, 1, n_bars))
    high = close + rng_seed.uniform(0.1, 1.5, n_bars)
    low = close - rng_seed.uniform(0.1, 1.5, n_bars)
    volume = rng_seed.uniform(100, 1000, n_bars)

    df_test = pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume})

    print("=== Default (EMA, rsiLen=5) ===")
    result = calculate_rsi_pro_enhanced(df_test)
    print("Kolom hasil:", list(result.columns))
    print("\nContoh 10 baris setelah warm-up:")
    print(result[["rsi", "rsi_ma", "zone", "vs_ma", "signal", "pa_pd_state"]].iloc[30:40].to_string())
    print("\nDistribusi zone (sanity check - 'Middle' harusnya TIDAK MUNCUL sama sekali, sesuai gotcha #2):")
    print(result["zone"].value_counts())
    print("\nDistribusi signal:")
    print(result["signal"].value_counts())
    print("\nDistribusi divergence_event:")
    print(result["divergence_event"].value_counts())

    print("\n=== Test rsi_mid > 50 (harusnya zona 'Middle' JADI MUNCUL) ===")
    result_mid60 = calculate_rsi_pro_enhanced(df_test, rsi_mid=60)
    print(result_mid60["zone"].value_counts())

    print("\n=== Test ma_type='None' (signal harusnya TIDAK PERNAH 'SELL'/'STR SELL') ===")
    result_noma = calculate_rsi_pro_enhanced(df_test, ma_type="None")
    print(result_noma["signal"].value_counts())
    print("vs_ma unique:", result_noma["vs_ma"].unique())

    print("\n=== Test ma_type='SMA + BB' ===")
    result_bb = calculate_rsi_pro_enhanced(df_test, ma_type="SMA + BB")
    print(result_bb[["rsi", "rsi_ma", "bb_upper", "bb_lower"]].iloc[40:45].to_string())

    print("\n=== Test VWMA tanpa kolom volume -> harus raise ValueError ===")
    try:
        calculate_rsi_pro_enhanced(df_test.drop(columns=["volume"]), ma_type="VWMA")
        print("GAGAL - harusnya raise error tapi enggak raise")
    except ValueError as e:
        print("OK, raise seperti diharapkan:", str(e)[:70], "...")
