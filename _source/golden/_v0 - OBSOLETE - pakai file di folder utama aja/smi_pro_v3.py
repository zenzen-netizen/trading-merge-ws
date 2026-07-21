"""
indicators/python/smi_pro_v3.py

Replikasi Python dari "TOP SMI Pro Enhanced v3" (Pine Script v6) - VERSI PENUH.
Menggantikan indicators/python/smi_pro.py lama (yang cuma replikasi sebagian,
dan punya 3 selisih vs source Pine asli - lihat "CATATAN KOREKSI" di bawah).

Panduan replikasi: journal/stage_03_replikasi_indikator.md

STATUS: layer numerik + layer fase/state + divergensi sudah diimplementasikan.
        BELUM divalidasi terhadap TradingView asli (butuh data OHLCV real
        dari stage 2, yang belum dibangun).

Tiga layer output:
1. Layer numerik : smi, smi_ema, smi_hist
2. Layer fase     : hist_momentum, hist_state_label, zone, vs_ema, cross_event,
                    bars_since_cross, b_cnt, a_cnt, pa_pd_state,
                    pa_pd_progress_text, failed_mid_hold, signal, phase_label,
                    marker_* (6 kolom event pulse)
3. Layer divergensi: divergence_event (delay konfirmasi via pivot, lihat bawah)

=====================================================================
CATATAN KOREKSI vs indicators/python/smi_pro.py (versi lama)
=====================================================================
Dicek ulang lawan source Pine asli, ketemu 3 selisih - sudah diperbaiki
di file ini (ikut Pine, karena Pine itu sumber kebenaran):

1. hist_momentum: source asli pakai smiH > 0 (strict) buat AU/AD,
   smiH <= 0 buat BD/BU - BUKAN smi >= smiEma seperti versi lama.
   Konsekuensi: kasus smiH == 0 sekarang jatuh ke kategori "below",
   bukan "above". Efek juga nular ke definisi hist_state_label.

2. cross_event: source asli pakai ta.crossover/ta.crossunder resmi
   (cur > cur2 AND prev <= prev2 untuk crossover; cur < cur2 AND
   prev >= prev2 untuk crossunder). Versi lama pakai prev < prev2
   (strict) - beda di kasus prev pas sama dengan prev2.

3. Label zone: source asli teksnya "Upper N" / "Lower N", bukan
   "Upper" / "Lower" polos - dicocokkan biar gampang validasi ke
   dashboard chart asli.

Gotcha lain yang dijaga (sama seperti versi lama):
- emaEma() = EMA dari EMA (double smoothing), bukan EMA tunggal
- ta.highest/lowest tanpa argumen source = pakai high/low, bukan close
- Counter PA/PD pakai exact equality (==), bukan >=
- momentum rising/falling utk PA-PD pakai >=/< - operator BEDA dari
  hist_momentum strict >/<, sesuai source asli
- failed_mid_hold pakai counter SATU BAR SEBELUMNYA
- phase_label adalah cascade if-elif berurutan, urutan dijaga persis

=====================================================================
CATATAN DIVERGENCE (belum ada di versi lama, ditambah di sini)
=====================================================================
- Pivot dideteksi di SERIES SMI (bukan di harga) - persis source Pine:
  plFound = ta.pivotlow(smi, divLbL, divLbR), phFound = ta.pivothigh(...)
- Harga pembanding diambil dari bar pivot yang sama (low/high candle
  di bar itu), bukan pivot harga independen.
- Event divergence dicatat di CONFIRM BAR (pivot_bar + divLbR), bukan
  di pivot_bar itu sendiri - ini delay konfirmasi wajib biar gak
  lookahead bias, sesuai checklist stage_03.
- ASUMSI BELUM TERVALIDASI: tie-break pivot (kalau ada 2 bar dgn nilai
  smi identik dalam 1 window) di sini pakai aturan "unique minimum/
  maximum" (kalau ada seri, gak dianggap pivot). Perilaku ta.pivotlow/
  pivothigh Pine yang PERSIS untuk kasus seri ini gak terdokumentasi
  jelas - WAJIB dicek manual lawan TradingView pas validasi data real.
- Kalau collision (event bullish & bearish confirm di bar yang sama
  persis) - kasus jarang, saat ini bearish akan menimpa (overwrite)
  bullish di kolom yang sama. Flag sebagai known limitation, bukan bug.
"""

import numpy as np
import pandas as pd


def double_ema(series: pd.Series, length: int) -> pd.Series:
    """EMA dari EMA - analog emaEma() di Pine. Bukan EMA tunggal."""
    first = series.ewm(span=length, adjust=False).mean()
    second = first.ewm(span=length, adjust=False).mean()
    return second


def _find_pivots(series: pd.Series, left: int, right: int, mode: str) -> list:
    """
    Analog ta.pivotlow()/ta.pivothigh() Pine. Return list of
    (pivot_bar_idx, pivot_value, confirm_bar_idx) - confirm_bar_idx
    = pivot_bar_idx + right (baru "diketahui" di bar ini, delay
    konfirmasi pivot).

    CATATAN: tie-break pakai unique min/max - lihat disclaimer di
    docstring modul, belum tervalidasi 100% lawan TradingView.
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


def calculate_smi_pro_v3(
    df: pd.DataFrame,
    len_k: int = 5,
    len_d: int = 3,
    len_e: int = 3,
    smi_ob: float = 80,
    smi_mid: float = 0,
    smi_os: float = -40,
    akum_candles: int = 2,
    dist_candles: int = 2,
    enable_div: bool = True,
    enable_hidden_div: bool = False,
    div_left: int = 5,
    div_right: int = 5,
    div_range_min: int = 5,
    div_range_max: int = 60,
) -> pd.DataFrame:
    """
    df wajib punya kolom: 'high', 'low', 'close'.
    Parameter default persis sama dengan default input Pine source asli.

    Return: copy df dengan kolom tambahan numerik + fase/state + divergensi.
    """
    out = df.copy()
    n = len(out)

    # ================================================================
    # LAYER NUMERIK
    # ================================================================
    hh = out["high"].rolling(len_k).max()
    ll = out["low"].rolling(len_k).min()
    rel = out["close"] - (hh + ll) / 2
    rng = hh - ll

    smi = 200 * (double_ema(rel, len_d) / double_ema(rng, len_d))
    smi_ema = smi.ewm(span=len_e, adjust=False).mean()  # ta.ema tunggal, BUKAN emaEma
    smi_hist = smi - smi_ema

    out["smi"] = smi
    out["smi_ema"] = smi_ema
    out["smi_hist"] = smi_hist

    # ATR-free di sini (SMI gak butuh ATR), tapi butuh true range? Tidak.

    # ================================================================
    # LAYER FASE/STATE - loop bar-by-bar (state persisten: b_cnt, a_cnt,
    # last pivot utk divergence, bars_since_cross)
    # ================================================================
    hist_momentum = [None] * n
    hist_state_label = [None] * n
    zone = [None] * n
    vs_ema = [None] * n
    cross_event = [None] * n
    bars_since_cross = [None] * n
    b_cnt_col = [None] * n
    a_cnt_col = [None] * n
    pa_pd_state = [None] * n
    pa_pd_progress_text = [None] * n
    failed_mid_hold = [None] * n
    signal = [None] * n
    phase_label = [None] * n
    marker_cross_zero_up = [False] * n
    marker_cross_zero_down = [False] * n
    marker_enter_ob = [False] * n
    marker_enter_os = [False] * n
    marker_exit_ob = [False] * n
    marker_exit_os = [False] * n
    divergence_event = ["none"] * n

    b_cnt = 0
    a_cnt = 0
    prev_smi = np.nan
    prev_smi_ema = np.nan
    prev_hist = np.nan
    last_cross_bar = None  # var int sLB, mulai 0 di Pine tapi 0 gak valid bar -> pakai None

    for i in range(n):
        cur_smi = smi.iloc[i]
        cur_ema = smi_ema.iloc[i]
        cur_hist = smi_hist.iloc[i]

        if np.isnan(cur_smi) or np.isnan(cur_ema):
            hist_momentum[i] = "warmup"
            hist_state_label[i] = "warmup"
            zone[i] = "warmup"
            vs_ema[i] = "warmup"
            cross_event[i] = "warmup"
            pa_pd_state[i] = "warmup"
            pa_pd_progress_text[i] = "warmup"
            failed_mid_hold[i] = "warmup"
            signal[i] = "warmup"
            phase_label[i] = "Warm-up"
            prev_smi, prev_smi_ema, prev_hist = cur_smi, cur_ema, cur_hist
            continue

        above = cur_smi >= cur_ema  # sAb - dipakai vs_ema & signal, BUKAN hist_momentum
        vs_ema[i] = "Bull" if above else "Bear"

        # --- KOREKSI #1: hist momentum pakai smiH > 0 / smiH <= 0, BUKAN sAb ---
        if np.isnan(prev_hist):
            hm = "flat"
        elif cur_hist > prev_hist and cur_hist > 0:
            hm = "above_up"
        elif cur_hist < prev_hist and cur_hist > 0:
            hm = "above_down"
        elif cur_hist < prev_hist and cur_hist <= 0:
            hm = "below_down"
        elif cur_hist > prev_hist and cur_hist <= 0:
            hm = "below_up"
        else:
            hm = "flat"  # smiH == smiH[1], analog color.gray / "Neutral"
        hist_momentum[i] = hm
        hist_state_label[i] = {
            "above_up": "Exp Bull", "above_down": "Shr Bull",
            "below_down": "Exp Bear", "below_up": "Shr Bear",
            "flat": "Neutral",
        }[hm]

        # --- zone (KOREKSI #3: teks "Upper N" / "Lower N") ---
        if cur_smi > smi_ob:
            zn = "OB"
        elif cur_smi > smi_mid:
            zn = "Upper N"
        elif cur_smi > 0:
            zn = "Middle"
        elif cur_smi > smi_os:
            zn = "Lower N"
        else:
            zn = "OS"
        zone[i] = zn

        # --- cross_event (KOREKSI #2: definisi resmi crossover/crossunder) ---
        if np.isnan(prev_smi):
            ce = "none"
            cross_any = False
        else:
            is_cu = (cur_smi > cur_ema) and (prev_smi <= prev_smi_ema)
            is_cd = (cur_smi < cur_ema) and (prev_smi >= prev_smi_ema)
            cross_any = is_cu or is_cd
            ce = "cross_up" if is_cu else "cross_down" if is_cd else "none"
        cross_event[i] = ce

        if cross_any:
            last_cross_bar = i
        bars_since_cross[i] = (i - last_cross_bar) if last_cross_bar is not None else None

        # --- marker pulse (cross level, official crossover/crossunder def) ---
        if not np.isnan(prev_smi):
            marker_cross_zero_up[i] = cur_smi > 0 and prev_smi <= 0
            marker_cross_zero_down[i] = cur_smi < 0 and prev_smi >= 0
            marker_enter_ob[i] = cur_smi > smi_ob and prev_smi <= smi_ob
            marker_enter_os[i] = cur_smi < smi_os and prev_smi >= smi_os
            marker_exit_ob[i] = cur_smi < smi_ob and prev_smi >= smi_ob
            marker_exit_os[i] = cur_smi > smi_os and prev_smi <= smi_os

        # --- PA/PD counter (persisten, exact equality) ---
        prev_b_cnt, prev_a_cnt = b_cnt, a_cnt
        if cur_smi < smi_mid:
            b_cnt += 1
            a_cnt = 0
        elif cur_smi > smi_mid:
            a_cnt += 1
            b_cnt = 0
        else:
            b_cnt = 0
            a_cnt = 0
        b_cnt_col[i] = b_cnt
        a_cnt_col[i] = a_cnt

        pre_akum = (b_cnt == akum_candles)
        pre_dist = (a_cnt == dist_candles)

        momentum_rising = True if np.isnan(prev_hist) else (cur_hist >= prev_hist)
        momentum_falling = not momentum_rising

        if pre_akum and momentum_falling:
            pps = "pa_dip"
        elif pre_akum and momentum_rising:
            pps = "pa_ready"
        elif pre_dist and momentum_rising:
            pps = "pd_dip"
        elif pre_dist and momentum_falling:
            pps = "pd_ready"
        else:
            pps = "none"
        pa_pd_state[i] = pps

        # --- pa_pd_progress_text, mirip dashboard row "PA/PD" (paPdTxt) ---
        pa_prog = f"{b_cnt}/{akum_candles}" if (0 < b_cnt < akum_candles) else ("TRIGGERED" if pre_akum else "-")
        pd_prog = f"{a_cnt}/{dist_candles}" if (0 < a_cnt < dist_candles) else ("TRIGGERED" if pre_dist else "-")
        if pps == "pa_ready":
            pa_pd_progress_text[i] = "PA - Siap Balik"
        elif pps == "pa_dip":
            pa_pd_progress_text[i] = "PA - Dip Mungkin"
        elif pps == "pd_ready":
            pa_pd_progress_text[i] = "PD - Siap Balik"
        elif pps == "pd_dip":
            pa_pd_progress_text[i] = "PD - Dip Mungkin"
        elif b_cnt > 0:
            pa_pd_progress_text[i] = f"PA {pa_prog}"
        elif a_cnt > 0:
            pa_pd_progress_text[i] = f"PD {pd_prog}"
        else:
            pa_pd_progress_text[i] = "-"

        # --- failed mid hold (counter SATU BAR SEBELUMNYA) ---
        if np.isnan(prev_smi):
            fmh = "none"
        elif (cur_smi > smi_mid) and (prev_smi < smi_mid) and (prev_b_cnt > 0):
            fmh = "fail_buy"
        elif (cur_smi < smi_mid) and (prev_smi > smi_mid) and (prev_a_cnt > 0):
            fmh = "fail_sell"
        else:
            fmh = "none"
        failed_mid_hold[i] = fmh

        # --- signal (sSig dashboard) ---
        if cur_smi > smi_ob and not above:
            sig = "STR SELL"
        elif cur_smi < smi_os and above:
            sig = "STR BUY"
        elif above and cur_smi > 0:
            sig = "BUY"
        elif (not above) and cur_smi < 0:
            sig = "SELL"
        else:
            sig = "NEUTRAL"
        signal[i] = sig

        # --- phase_label: CASCADE prioritas, urutan persis source asli ---
        if ce == "cross_up":
            pl = "Cross UP"
        elif ce == "cross_down":
            pl = "Cross DOWN"
        elif zn == "OB":
            pl = "OB Zone"
        elif zn == "OS":
            pl = "OS Zone"
        elif pps == "pa_dip":
            pl = "PA - Dip Mungkin"
        elif pps == "pa_ready":
            pl = "PA - Siap Balik"
        elif pps == "pd_dip":
            pl = "PD - Dip Mungkin"
        elif pps == "pd_ready":
            pl = "PD - Siap Balik"
        elif fmh == "fail_buy":
            pl = "Fail MID Buy"
        elif fmh == "fail_sell":
            pl = "Fail MID Sell"
        elif cur_smi < smi_mid:
            pl = "Bias Bawah"
        elif cur_smi > smi_mid:
            pl = "Bias Atas"
        else:
            pl = "Netral"
        phase_label[i] = pl

        prev_smi, prev_smi_ema, prev_hist = cur_smi, cur_ema, cur_hist

    out["hist_momentum"] = hist_momentum
    out["hist_state_label"] = hist_state_label
    out["zone"] = zone
    out["vs_ema"] = vs_ema
    out["cross_event"] = cross_event
    out["bars_since_cross"] = bars_since_cross
    out["b_cnt"] = b_cnt_col
    out["a_cnt"] = a_cnt_col
    out["pa_pd_state"] = pa_pd_state
    out["pa_pd_progress_text"] = pa_pd_progress_text
    out["failed_mid_hold"] = failed_mid_hold
    out["signal"] = signal
    out["phase_label"] = phase_label
    out["marker_cross_zero_up"] = marker_cross_zero_up
    out["marker_cross_zero_down"] = marker_cross_zero_down
    out["marker_enter_ob"] = marker_enter_ob
    out["marker_enter_os"] = marker_enter_os
    out["marker_exit_ob"] = marker_exit_ob
    out["marker_exit_os"] = marker_exit_os

    # ================================================================
    # LAYER DIVERGENSI - pivot dideteksi di series SMI, delay konfirmasi
    # = divLbR bar setelah titik pivot asli (bukan real-time)
    # ================================================================
    pivot_lows = _find_pivots(smi, div_left, div_right, mode="low")
    pivot_highs = _find_pivots(smi, div_left, div_right, mode="high")

    low_price = out["low"].values
    high_price = out["high"].values

    last_pl_osc = last_pl_price = last_pl_bar = None
    for piv_bar, piv_val, confirm_bar in pivot_lows:
        cur_price = low_price[piv_bar]
        if last_pl_bar is not None:
            gap = piv_bar - last_pl_bar
            if div_range_min <= gap <= div_range_max:
                if enable_div and cur_price < last_pl_price and piv_val > last_pl_osc:
                    divergence_event[confirm_bar] = "bullish"
                if enable_hidden_div and cur_price > last_pl_price and piv_val < last_pl_osc:
                    divergence_event[confirm_bar] = "hidden_bullish"
        last_pl_osc, last_pl_price, last_pl_bar = piv_val, cur_price, piv_bar

    last_ph_osc = last_ph_price = last_ph_bar = None
    for piv_bar, piv_val, confirm_bar in pivot_highs:
        cur_price = high_price[piv_bar]
        if last_ph_bar is not None:
            gap = piv_bar - last_ph_bar
            if div_range_min <= gap <= div_range_max:
                if enable_div and cur_price > last_ph_price and piv_val < last_ph_osc:
                    divergence_event[confirm_bar] = "bearish"
                if enable_hidden_div and cur_price < last_ph_price and piv_val > last_ph_osc:
                    divergence_event[confirm_bar] = "hidden_bearish"
        last_ph_osc, last_ph_price, last_ph_bar = piv_val, cur_price, piv_bar

    out["divergence_event"] = divergence_event

    return out


# ============================================================
# CATATAN VALIDASI - WAJIB DIKERJAKAN SEBELUM DIPAKAI BACKTEST
# ============================================================
#
# [ ] Layer numerik: sample beberapa titik dari data OHLCV real, bandingkan
#     smi/smi_ema Python vs TradingView di candle yang sama persis.
# [ ] Layer fase: cocokkan phase_label, pa_pd_progress_text, signal,
#     hist_state_label Python dengan dashboard/warna bar chart asli -
#     KHUSUSNYA di kasus smiH == smiH[1] dan smi == smiEma (edge case
#     dari 3 koreksi di atas), pastikan Python ambil cabang yang sama
#     kayak Pine.
# [ ] Layer divergensi: cocokkan garis/label Bull/Bear/H.Bull/H.Bear di
#     chart TradingView vs kolom divergence_event, PERHATIKAN bar
#     konfirmasi (bukan bar pivot asli) - dan validasi tie-break pivot
#     (lihat disclaimer di docstring _find_pivots).
# [ ] Sampling representasi kondisi market berbeda (trending, sideways,
#     volatile), bukan cuma 1-2 titik random.
#
# Begitu stage 2 (fetcher Binance) selesai, jalankan validasi ini sebelum
# file ini dipakai sebagai bahan strategi resmi manapun.


if __name__ == "__main__":
    rng_seed = np.random.default_rng(42)
    n_bars = 400
    close = 100 + np.cumsum(rng_seed.normal(0, 1, n_bars))
    high = close + rng_seed.uniform(0.1, 1.5, n_bars)
    low = close - rng_seed.uniform(0.1, 1.5, n_bars)

    df_test = pd.DataFrame({"high": high, "low": low, "close": close})
    result = calculate_smi_pro_v3(df_test)

    print("Kolom hasil:", list(result.columns))
    print("\nContoh 10 baris setelah warm-up:")
    print(
        result[
            ["smi", "smi_ema", "smi_hist", "zone", "cross_event",
             "pa_pd_state", "phase_label", "signal"]
        ].iloc[30:40].to_string()
    )
    print("\nDistribusi phase_label (sanity check, data sintetis):")
    print(result["phase_label"].value_counts())
    print("\nDistribusi divergence_event (sanity check, data sintetis):")
    print(result["divergence_event"].value_counts())
    print("\nJumlah bar dengan hist_momentum 'flat' (edge case smiH==smiH[1]):")
    print((result["hist_momentum"] == "flat").sum())
