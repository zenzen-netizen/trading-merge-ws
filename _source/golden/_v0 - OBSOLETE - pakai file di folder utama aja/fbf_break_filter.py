"""
indicators/python/fbf_break_filter.py

Replikasi Python dari "Fractal Break Filter v11.1" (Pine Script v6).
Panduan replikasi: journal/stage_03_replikasi_indikator.md

STATUS: layer numerik (pivot/ATR) + layer state (tracker wave A-B-C) +
        layer event (judge -> BREAK/FAIL) sudah diimplementasikan.
        BELUM divalidasi terhadap TradingView asli.

=====================================================================
KEPUTUSAN SCOPE (disepakati sebelum coding, lihat obrolan)
=====================================================================
1. SEMUA elemen visual-only DIBUANG dari replikasi ini: filter trend
   EMA/Supertrend buat nyembunyiin wave (section 6), kalkulasi MA/
   Supertrend/HTF (section 7-9), gambar wave/fibo-box/break-line/label/
   fade-lookback (section 10-13). ALASAN: ditelusuri baris
   `confirmed = barstate.isconfirmed and timeOk and smiOk and structOk
   and distAOk and cFrOk and fiboOk` di source asli - variabel
   `bullWaveVisible`/`bearWaveVisible` TIDAK ikut nentuin apakah event
   BREAK terjadi, cuma dipakai buat warna/tampil-gaknya di chart.
   Konsekuensi: kode ini gak butuh hitung EMA/Supertrend/HTF sama
   sekali - event BREAK yang dihasilkan identik dengan atau tanpa
   filter trend visual itu di source asli.
2. Tag "BREAK↺" (break dari wave pasca-flip trend) juga DIBUANG,
   karena itu murni cosmetic label text, gak mengubah apakah event
   terjadi atau parameter event-nya. Kalau nanti butuh info ini
   (misal buat filter tambahan di strategi), kasih tau - bisa ditambah.
3. Output BUKAN 1 kolom per bar (beda dari SMI) - dipakai TABEL EVENT
   LOG terpisah karena bisa ada beberapa kandidat wave jalan paralel
   (sampai 8 slot per sisi). Tiap kejadian (BREAK atau FAIL/gugur)
   dicatat 1 baris. Plus 2 kolom ringkas opsional ditempel ke df utama
   (n_active_bull_candidates, n_active_bear_candidates) buat gambaran
   cepat tanpa buka tabel event.
4. SEMUA filter (termasuk yang default OFF di Pine: A3 lookback, C1
   fractal, persistence filter, SMI filter) dijadikan parameter
   function, default value disamain persis dgn Pine - biar gampang
   eksperimen kombinasi lain tanpa ubah kode.

Gotcha yang dijaga presisi:
- Loop bar-by-bar wajib (state candidate + pivot confirm delay),
  BUKAN vectorized - sama alasan dengan smi_pro.py (lookahead bias)
- Pivot (ta.pivothigh/pivotlow) py delay konfirmasi = right_bars bar
  SETELAH titik pivot asli, persis prinsip di stage_03
- A2/dist-ATR pakai >= (bukan >), persis source
- C2 fibo pakai ratio (b-c)/(b-a) buat bull, (c-b)/(a-b) buat bear,
  bounds inclusive [bcFiboMin, bcFiboMax]
- barstate.isconfirmed di Pine SELALU true untuk data historis closed
  candle -> gak direplikasi eksplisit, otomatis true di backtest
- Max 8 kandidat per sisi (bull/bear), evict paling lama kalau penuh
- no_duplicate: 1 level B cuma boleh confirm BREAK sekali
"""

import numpy as np
import pandas as pd


def double_ema(series: pd.Series, length: int) -> pd.Series:
    first = series.ewm(span=length, adjust=False).mean()
    second = first.ewm(span=length, adjust=False).mean()
    return second


def wilder_atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    """Analog ta.atr() Pine = ta.rma(ta.tr(true), length) -> Wilder smoothing."""
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


def _find_pivots(values: np.ndarray, left: int, right: int, mode: str) -> dict:
    """
    Analog ta.pivothigh()/ta.pivotlow() Pine. Return dict
    confirm_bar_idx -> (pivot_bar_idx, pivot_value).
    confirm_bar_idx = pivot_bar_idx + right (delay konfirmasi).
    Tie-break: unique min/max (lihat disclaimer sama di smi_pro_v3.py).
    """
    n = len(values)
    out = {}
    for i in range(left, n - right):
        if np.isnan(values[i]):
            continue
        window = values[i - left: i + right + 1]
        if np.any(np.isnan(window)):
            continue
        center = values[i]
        if mode == "low":
            is_piv = center == window.min() and (window == center).sum() == 1
        else:
            is_piv = center == window.max() and (window == center).sum() == 1
        if is_piv:
            out[i + right] = (i, center)
    return out


def calculate_fbf(
    df: pd.DataFrame,
    # 1. Fractal & memori
    left_bars: int = 3,
    right_bars: int = 3,
    # 3. Filter leg A
    enable_a_fractal: bool = True,
    a_left_bars: int = 5,
    a_right_bars: int = 5,
    enable_a_dist: bool = True,
    a_dist_mult: float = 1.0,
    enable_a_lookback: bool = False,
    a_lookback_bars: int = 50,
    # 4. Filter leg C
    enable_c_fractal: bool = False,
    c_left_bars: int = 5,
    c_right_bars: int = 5,
    enable_fibo_bc: bool = True,
    bc_fibo_min: float = 0.5,
    bc_fibo_max: float = 0.786,
    enable_struct_filter: bool = True,
    # 5. Filter break
    enable_atr_filter: bool = True,
    atr_len: int = 14,
    atr_mult: float = 0.15,
    enable_persist_filter: bool = False,
    persist_n: int = 2,
    enable_smi_filter: bool = False,
    smi_len_k: int = 5,
    smi_len_d: int = 3,
    smi_len_e: int = 3,
    no_duplicate: bool = True,
    max_candidates: int = 8,
) -> dict:
    """
    df wajib punya kolom: 'high', 'low', 'close'.
    Parameter default persis sama dengan default input Pine source asli.

    Return dict:
      "bars": copy df + kolom ringkas per-bar (n_active_bull_candidates,
              n_active_bear_candidates, event_bull_break, event_bear_break)
      "events": DataFrame event log (1 baris = 1 kejadian BREAK atau FAIL)
    """
    out = df.copy()
    n = len(out)
    high = out["high"].values.astype(float)
    low = out["low"].values.astype(float)
    close = out["close"].values.astype(float)

    atr = wilder_atr(out["high"], out["low"], out["close"], atr_len).values

    # SMI internal (instance terpisah dari indikator SMI Pro - scope beda)
    if enable_smi_filter:
        hh_s = out["high"].rolling(smi_len_k).max()
        ll_s = out["low"].rolling(smi_len_k).min()
        rel_s = out["close"] - (hh_s + ll_s) / 2
        rng_s = hh_s - ll_s
        smi_int = (200 * (double_ema(rel_s, smi_len_d) / double_ema(rng_s, smi_len_d))).values
        smi_ema_int = pd.Series(smi_int).ewm(span=smi_len_e, adjust=False).mean().values
    else:
        smi_int = np.full(n, np.nan)
        smi_ema_int = np.full(n, np.nan)

    # ---- pivot confirm maps ----
    ph_map = _find_pivots(high, left_bars, right_bars, "high")
    pl_map = _find_pivots(low, left_bars, right_bars, "low")
    phA_map = _find_pivots(high, a_left_bars, a_right_bars, "high") if enable_a_fractal else {}
    plA_map = _find_pivots(low, a_left_bars, a_right_bars, "low") if enable_a_fractal else {}
    phC_map = _find_pivots(high, c_left_bars, c_right_bars, "high") if enable_c_fractal else {}
    plC_map = _find_pivots(low, c_left_bars, c_right_bars, "low") if enable_c_fractal else {}

    # ---- state pivot persisten ----
    last_ph = last_ph_bar = None
    last_pl = last_pl_bar = None
    last_a_ph = last_a_ph_bar = None
    last_a_pl = last_a_pl_bar = None
    last_c_ph_bar = None  # dipakai cBearFractalOk
    last_c_pl_bar = None  # dipakai cBullFractalOk
    snap_low_at_high_val = snap_low_at_high_bar = None
    snap_high_at_low_val = snap_high_at_low_bar = None

    # ---- state tracker (Otak 1) ----
    tb_phase = 0
    tb_a = tb_a_bar = tb_b = tb_b_bar = tb_c = tb_c_bar = None
    tr_phase = 0
    tr_a = tr_a_bar = tr_b = tr_b_bar = tr_c = tr_c_bar = None

    bull_cands = []  # list of dict
    bear_cands = []
    last_confirmed_bull_b = None
    last_confirmed_bear_b = None

    n_active_bull = [0] * n
    n_active_bear = [0] * n
    event_bull_break = [False] * n
    event_bear_break = [False] * n
    events = []  # list of dict -> jadi DataFrame event log

    def new_cand(a_val, a_bar, b_val, b_bar, c_val, c_bar):
        return {
            "a_val": a_val, "a_bar": a_bar, "b_val": b_val, "b_bar": b_bar,
            "c_val": c_val, "c_bar": c_bar, "active": False, "persist": 0,
        }

    def push_cand(arr, cand):
        arr.append(cand)
        if len(arr) > max_candidates:
            arr.pop(0)  # evict paling lama (analog f_pushCand shift array)

    for i in range(n):
        # -------- update pivot A-fractal (urutan persis source) --------
        if enable_a_fractal:
            if i in phA_map:
                pb, val = phA_map[i]
                last_a_ph, last_a_ph_bar = val, pb
            if i in plA_map:
                pb, val = plA_map[i]
                last_a_pl, last_a_pl_bar = val, pb

        if enable_c_fractal:
            if i in phC_map:
                pb, _val = phC_map[i]
                last_c_ph_bar = pb
            if i in plC_map:
                pb, _val = plC_map[i]
                last_c_pl_bar = pb

        ph_here = i in ph_map
        pl_here = i in pl_map

        if ph_here:
            pb, val = ph_map[i]
            snap_low_at_high_val = last_a_pl if enable_a_fractal else last_pl
            snap_low_at_high_bar = last_a_pl_bar if enable_a_fractal else last_pl_bar
            last_ph, last_ph_bar = val, pb
        if pl_here:
            pb, val = pl_map[i]
            snap_high_at_low_val = last_a_ph if enable_a_fractal else last_ph
            snap_high_at_low_bar = last_a_ph_bar if enable_a_fractal else last_ph_bar
            last_pl, last_pl_bar = val, pb

        # ================= TRACKER BULL (Otak 1) =================
        tb_b_new = last_ph if ph_here else None
        tb_b_new_bar = (i - right_bars) if ph_here else None
        tb_a_new = snap_low_at_high_val
        tb_a_new_bar = snap_low_at_high_bar

        tb_start_ok = (
            tb_phase == 0 and ph_here and tb_a_new is not None
            and tb_a_new < tb_b_new and tb_a_new_bar < tb_b_new_bar
        )

        if tb_start_ok:
            tb_a, tb_a_bar = tb_a_new, tb_a_new_bar
            tb_b, tb_b_bar = tb_b_new, tb_b_new_bar
            tb_c, tb_c_bar = None, None
            for k in range(right_bars):
                idx = i - k
                if idx > tb_b_bar:
                    if tb_c is None or low[idx] < tb_c:
                        tb_c, tb_c_bar = low[idx], idx
            tb_phase = 1
        elif tb_phase > 0:
            if close[i] < tb_a:
                tb_phase = 0
            else:
                if tb_phase == 1:
                    if tb_c is None or low[i] < tb_c:
                        tb_c, tb_c_bar = low[i], i
                    tb_lock_pivot = pl_here and (i - right_bars) > tb_b_bar
                    tb_lock_break = close[i] > tb_b
                    if tb_lock_pivot or tb_lock_break:
                        if tb_lock_pivot:
                            tb_c_val, tb_c_bar_f = pl_map[i][1], i - right_bars
                        else:
                            tb_c_val, tb_c_bar_f = tb_c, tb_c_bar
                        tb_ok = (not enable_struct_filter) or (tb_c_val > tb_a)
                        if tb_ok:
                            tb_c, tb_c_bar = tb_c_val, tb_c_bar_f
                            push_cand(bull_cands, new_cand(tb_a, tb_a_bar, tb_b, tb_b_bar, tb_c, tb_c_bar))
                        tb_phase = 0

        # ================= TRACKER BEAR (Otak 1, mirror) =================
        tr_b_new = last_pl if pl_here else None
        tr_b_new_bar = (i - right_bars) if pl_here else None
        tr_a_new = snap_high_at_low_val
        tr_a_new_bar = snap_high_at_low_bar

        tr_start_ok = (
            tr_phase == 0 and pl_here and tr_a_new is not None
            and tr_a_new > tr_b_new and tr_a_new_bar < tr_b_new_bar
        )

        if tr_start_ok:
            tr_a, tr_a_bar = tr_a_new, tr_a_new_bar
            tr_b, tr_b_bar = tr_b_new, tr_b_new_bar
            tr_c, tr_c_bar = None, None
            for k in range(right_bars):
                idx = i - k
                if idx > tr_b_bar:
                    if tr_c is None or high[idx] > tr_c:
                        tr_c, tr_c_bar = high[idx], idx
            tr_phase = 1
        elif tr_phase > 0:
            if close[i] > tr_a:
                tr_phase = 0
            else:
                if tr_phase == 1:
                    if tr_c is None or high[i] > tr_c:
                        tr_c, tr_c_bar = high[i], i
                    tr_lock_pivot = ph_here and (i - right_bars) > tr_b_bar
                    tr_lock_break = close[i] < tr_b
                    if tr_lock_pivot or tr_lock_break:
                        if tr_lock_pivot:
                            tr_c_val, tr_c_bar_f = ph_map[i][1], i - right_bars
                        else:
                            tr_c_val, tr_c_bar_f = tr_c, tr_c_bar
                        tr_ok = (not enable_struct_filter) or (tr_c_val < tr_a)
                        if tr_ok:
                            tr_c, tr_c_bar = tr_c_val, tr_c_bar_f
                            push_cand(bear_cands, new_cand(tr_a, tr_a_bar, tr_b, tr_b_bar, tr_c, tr_c_bar))
                        tr_phase = 0

        # ================= JUDGE BULL (Otak 2) =================
        for c in list(bull_cands):
            if not c["active"] and close[i] < c["a_val"]:
                bull_cands.remove(c)
                continue

            just_act = False
            if not c["active"] and close[i] > c["b_val"]:
                atr_i = atr[i]
                dist_ok = (not enable_atr_filter) or (
                    not np.isnan(atr_i) and (close[i] - c["b_val"]) >= atr_mult * atr_i
                )
                if dist_ok:
                    c["active"], c["persist"], just_act = True, 1, True
                    if enable_a_lookback:
                        j = i - right_bars
                        start = max(0, j - a_lookback_bars + 1)
                        if j >= 0:
                            window = low[start: j + 1]
                            wmin = window.min()
                            wbar = start + int(window.argmin())
                            c["a_val"], c["a_bar"] = wmin, wbar
                        else:
                            c["a_val"], c["a_bar"] = np.nan, None

            if c["active"] and not just_act:
                atr_i = atr[i]
                still_beyond = close[i] > c["b_val"]
                dist_ok2 = (not enable_atr_filter) or (
                    not np.isnan(atr_i) and (close[i] - c["b_val"]) >= atr_mult * atr_i
                )
                if still_beyond and dist_ok2:
                    c["persist"] += 1
                else:
                    events.append({
                        "bar": i, "side": "bull", "event_type": "FAIL",
                        "a_val": c["a_val"], "a_bar": c["a_bar"],
                        "b_val": c["b_val"], "b_bar": c["b_bar"],
                        "c_val": c["c_val"], "c_bar": c["c_bar"],
                        "retrace_pct": None, "persist_bars": c["persist"],
                    })
                    c["active"], c["persist"] = False, 0

            if c["active"]:
                req_n = persist_n if enable_persist_filter else 1
                smi_ok = (not enable_smi_filter) or (smi_int[i] >= smi_ema_int[i])
                time_ok = c["persist"] >= req_n
                c_valid = c["c_bar"] is not None and c["c_bar"] > c["b_bar"] and c["c_bar"] < i
                a_valid = c["a_bar"] is not None and not (isinstance(c["a_val"], float) and np.isnan(c["a_val"]))
                dist_a_ok = (not enable_a_dist) or (
                    a_valid and not np.isnan(atr[i]) and (c["b_val"] - c["a_val"]) >= a_dist_mult * atr[i]
                )
                struct_ok = (not enable_struct_filter) or (a_valid and c_valid and c["c_val"] > c["a_val"])
                c_fr_ok = (not c_valid) or (not enable_c_fractal) or (
                    last_c_pl_bar is not None and abs(last_c_pl_bar - c["c_bar"]) <= (c_right_bars - right_bars)
                )
                retr = None
                fibo_ok = True
                if enable_fibo_bc and a_valid and c_valid:
                    leg_ab = c["b_val"] - c["a_val"]
                    retr = (c["b_val"] - c["c_val"]) / leg_ab if leg_ab > 0 else 0.0
                    fibo_ok = bc_fibo_min <= retr <= bc_fibo_max

                confirmed = time_ok and smi_ok and struct_ok and dist_a_ok and c_fr_ok and fibo_ok
                if confirmed:
                    is_dup = no_duplicate and last_confirmed_bull_b is not None and c["b_bar"] == last_confirmed_bull_b
                    if is_dup:
                        bull_cands.remove(c)
                        continue
                    last_confirmed_bull_b = c["b_bar"]
                    events.append({
                        "bar": i, "side": "bull", "event_type": "BREAK",
                        "a_val": c["a_val"], "a_bar": c["a_bar"],
                        "b_val": c["b_val"], "b_bar": c["b_bar"],
                        "c_val": c["c_val"], "c_bar": c["c_bar"],
                        "retrace_pct": (retr * 100) if retr is not None else None,
                        "persist_bars": c["persist"],
                    })
                    event_bull_break[i] = True
                    bull_cands.remove(c)
                    continue

        # ================= JUDGE BEAR (Otak 2, mirror) =================
        for c in list(bear_cands):
            if not c["active"] and close[i] > c["a_val"]:
                bear_cands.remove(c)
                continue

            just_act = False
            if not c["active"] and close[i] < c["b_val"]:
                atr_i = atr[i]
                dist_ok = (not enable_atr_filter) or (
                    not np.isnan(atr_i) and (c["b_val"] - close[i]) >= atr_mult * atr_i
                )
                if dist_ok:
                    c["active"], c["persist"], just_act = True, 1, True
                    if enable_a_lookback:
                        j = i - right_bars
                        start = max(0, j - a_lookback_bars + 1)
                        if j >= 0:
                            window = high[start: j + 1]
                            wmax = window.max()
                            wbar = start + int(window.argmax())
                            c["a_val"], c["a_bar"] = wmax, wbar
                        else:
                            c["a_val"], c["a_bar"] = np.nan, None

            if c["active"] and not just_act:
                atr_i = atr[i]
                still_beyond = close[i] < c["b_val"]
                dist_ok2 = (not enable_atr_filter) or (
                    not np.isnan(atr_i) and (c["b_val"] - close[i]) >= atr_mult * atr_i
                )
                if still_beyond and dist_ok2:
                    c["persist"] += 1
                else:
                    events.append({
                        "bar": i, "side": "bear", "event_type": "FAIL",
                        "a_val": c["a_val"], "a_bar": c["a_bar"],
                        "b_val": c["b_val"], "b_bar": c["b_bar"],
                        "c_val": c["c_val"], "c_bar": c["c_bar"],
                        "retrace_pct": None, "persist_bars": c["persist"],
                    })
                    c["active"], c["persist"] = False, 0

            if c["active"]:
                req_n = persist_n if enable_persist_filter else 1
                smi_ok = (not enable_smi_filter) or (smi_int[i] <= smi_ema_int[i])
                time_ok = c["persist"] >= req_n
                c_valid = c["c_bar"] is not None and c["c_bar"] > c["b_bar"] and c["c_bar"] < i
                a_valid = c["a_bar"] is not None and not (isinstance(c["a_val"], float) and np.isnan(c["a_val"]))
                dist_a_ok = (not enable_a_dist) or (
                    a_valid and not np.isnan(atr[i]) and (c["a_val"] - c["b_val"]) >= a_dist_mult * atr[i]
                )
                struct_ok = (not enable_struct_filter) or (a_valid and c_valid and c["c_val"] < c["a_val"])
                c_fr_ok = (not c_valid) or (not enable_c_fractal) or (
                    last_c_ph_bar is not None and abs(last_c_ph_bar - c["c_bar"]) <= (c_right_bars - right_bars)
                )
                retr = None
                fibo_ok = True
                if enable_fibo_bc and a_valid and c_valid:
                    leg_ab = c["a_val"] - c["b_val"]
                    retr = (c["c_val"] - c["b_val"]) / leg_ab if leg_ab > 0 else 0.0
                    fibo_ok = bc_fibo_min <= retr <= bc_fibo_max

                confirmed = time_ok and smi_ok and struct_ok and dist_a_ok and c_fr_ok and fibo_ok
                if confirmed:
                    is_dup = no_duplicate and last_confirmed_bear_b is not None and c["b_bar"] == last_confirmed_bear_b
                    if is_dup:
                        bear_cands.remove(c)
                        continue
                    last_confirmed_bear_b = c["b_bar"]
                    events.append({
                        "bar": i, "side": "bear", "event_type": "BREAK",
                        "a_val": c["a_val"], "a_bar": c["a_bar"],
                        "b_val": c["b_val"], "b_bar": c["b_bar"],
                        "c_val": c["c_val"], "c_bar": c["c_bar"],
                        "retrace_pct": (retr * 100) if retr is not None else None,
                        "persist_bars": c["persist"],
                    })
                    event_bear_break[i] = True
                    bear_cands.remove(c)
                    continue

        n_active_bull[i] = sum(1 for c in bull_cands if c["active"])
        n_active_bear[i] = sum(1 for c in bear_cands if c["active"])

    out["n_active_bull_candidates"] = n_active_bull
    out["n_active_bear_candidates"] = n_active_bear
    out["event_bull_break"] = event_bull_break
    out["event_bear_break"] = event_bear_break

    events_df = pd.DataFrame(events, columns=[
        "bar", "side", "event_type", "a_val", "a_bar", "b_val", "b_bar",
        "c_val", "c_bar", "retrace_pct", "persist_bars",
    ])

    return {"bars": out, "events": events_df}


# ============================================================
# CATATAN VALIDASI - WAJIB DIKERJAKAN SEBELUM DIPAKAI BACKTEST
# ============================================================
#
# [ ] Pivot: cocokkan marker segitiga pivot high/low Python vs TradingView
#     di beberapa titik, termasuk delay konfirmasi (right_bars).
# [ ] Wave A-B-C: cocokkan koordinat A/B/C tiap event BREAK di events_df
#     vs garis zigzag + label A/B/C yang tampil di chart TradingView -
#     WAJIB pas showAbcd on & filter trend visual OFF di TV (karena kode
#     ini gak simulasikan visibility gating, representasi paling adil
#     buat dibandingkan adalah kondisi trend-filter OFF di chart asli).
# [ ] Event BREAK: cocokkan bar & harga breakout tiap event vs label
#     "BREAK" di chart, PERHATIKAN retrace_pct dari kolom C2 fibo.
# [ ] Event FAIL: cocokkan vs tanda ✖ (kalau showFailMark on) di chart.
# [ ] ATR: cocokkan nilai Wilder ATR Python vs ta.atr(atrLen) TV di
#     beberapa titik sample.
# [ ] Kalau enable_smi_filter dipakai nanti: validasi SMI internal di
#     sini sama persis caranya dengan validasi smi_pro_v3.py.
# [ ] Kalau enable_c_fractal dipakai nanti: cek ulang formula
#     cBullFractalOk/cBearFractalOk toleransi jarak bar - INI PALING
#     RUMIT buat divalidasi manual, prioritaskan sample banyak titik.
#
# ASUMSI/KEPUTUSAN YANG DIAMBIL TANPA TANYA (flag transparan, low-level,
# bukan keputusan strategis):
# - Tie-break pivot: unique min/max, sama seperti smi_pro_v3.py.
# - Evict kandidat penuh (>8 slot): kandidat PALING LAMA dibuang
#   (analog array.shift Pine yg buang elemen index 0 = paling lama).


if __name__ == "__main__":
    rng_seed = np.random.default_rng(7)
    n_bars = 500
    close = 100 + np.cumsum(rng_seed.normal(0, 1.2, n_bars))
    high = close + rng_seed.uniform(0.1, 1.8, n_bars)
    low = close - rng_seed.uniform(0.1, 1.8, n_bars)

    df_test = pd.DataFrame({"high": high, "low": low, "close": close})
    result = calculate_fbf(df_test)

    bars = result["bars"]
    events = result["events"]

    print("Kolom bars:", list(bars.columns))
    print("\nTotal event:", len(events))
    print("\nDistribusi event_type x side:")
    if len(events):
        print(events.groupby(["side", "event_type"]).size())
    print("\nContoh 5 event BREAK pertama:")
    print(events[events["event_type"] == "BREAK"].head(5).to_string())
    print("\nMax kandidat aktif bersamaan (bull/bear):",
          bars["n_active_bull_candidates"].max(), "/", bars["n_active_bear_candidates"].max())
