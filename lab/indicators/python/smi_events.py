"""
smi_events.py — VECTORIZED SMI Pro v3 EVENT DICTIONARY (faithful to
TradingView Pine Script "TOP SMI Pro Enhanced v3" shared by user).

Single source of truth untuk semua backtest SETUP1 ke depan.
Menghasilkan per-bar event flags (numpy bool array) untuk SELURUH seri,
bukan cuma 1 bar terakhir.

Kamus event (mapping ke Pine variable):
  CROSS markers (plotshape):
    cUM  = crossover(smi, MID)       -> "M" up
    cDM  = crossunder(smi, MID)      -> "M" down
    cUO  = crossover(smi, OB)        -> "EO" Enter OB
    cDO  = crossunder(smi, OS)       -> "ES" Enter OS
    cDB  = crossunder(smi, OB)       -> "XO" Exit OB
    cUS  = crossover(smi, OS)        -> "XS" Exit OS
  EMA cross:
    cross_up   = crossover(smi, smiEma)  -> bcCrossUp (cyan)
    cross_down = crossunder(smi, smiEma) -> bcCrossDown (white)  [= XDN trigger step-3]
  PA / PD (preAkum / preDist, distCandles=akumCandles=2):
    pa_dip  = preAkum & hist melemah     -> bcPADip  (PA - Dip Mungkin, dashed)
    pa_ready= preAkum & hist menguat     -> bcPAReady (PA - Siap Balik, solid)
    pd_dip  = preDist & hist naik        -> bcPDDip  (PD - Dip Mungkin, dashed)
    pd_ready= preDist & hist melemah     -> bcPDReady (PD - Siap Balik, solid)  [= PD step-2 flavour Siap Balik]
  Failed MID (fakeout):
    fail_mid_buy  = bcFailMIDBuy  (SMI cross MID up lalu balik turun; PA batal)
    fail_mid_sell = bcFailMIDSell (SMI cross MID down lalu balik naik; PD batal)
  Bias (background):
    bias_bull  = smi>mid & no special event
    bias_bear  = smi<mid & no special event
    bias_neutral = smi==mid / edge case

SETUP1 3-step short trigger (lock di modul, reusable):
    STEP1 = FMB = fail MID buy initiation (SMI cross UP through MID setelah bear stretch)
    STEP2 = PD  = PD "Siap Balik" (preDist & hist melemah 2 bar)  -- puncak momentum
    STEP3 = XDN = cross DOWN (SMI crossunder EMA)
  (definisi ini = yg udah divalidasi ke 4 window rujukan -> 47 sinyal daily)

Semua array di-return sbg numpy bool 1D, index = bar ke-i.
"""

import numpy as np
import pandas as pd


def _ema_ema(series, length):
    return series.ewm(span=length, adjust=False).mean().ewm(span=length, adjust=False).mean()


def _consecutive_run(mask):
    """Hitung streak berturut-turut (inclusive bar saat ini) di mana mask True.
    Reset ke 0 saat mask False. Vectorized via loop (n aman ~3000)."""
    n = len(mask)
    out = np.zeros(n, dtype=int)
    c = 0
    for i in range(n):
        c = c + 1 if mask[i] else 0
        out[i] = c
    return out


def compute_smi_events(df, cfg):
    len_k = cfg.get("len_k", 5)
    len_d = cfg.get("len_d", 3)
    len_e = cfg.get("len_e", 3)
    ob = cfg.get("ob", 80)
    mid = cfg.get("mid", 0)
    os_ = cfg.get("os", -40)
    akum_candles = cfg.get("akum_candles", 2)
    dist_candles = cfg.get("dist_candles", 2)

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    n = len(df)

    # ---- SMI core ----
    hh = high.rolling(window=len_k, min_periods=len_k).max()
    ll = low.rolling(window=len_k, min_periods=len_k).min()
    rel = close - (hh + ll) / 2.0
    rng = hh - ll
    rng_safe = rng.replace(0, np.nan)
    smi = 200.0 * (_ema_ema(rel, len_d) / _ema_ema(rng_safe, len_d))
    smi_ema = smi.ewm(span=len_e, adjust=False).mean()
    smi_hist = smi - smi_ema
    smi = smi.values
    smi_ema = smi_ema.values
    h = smi_hist.values

    # ---- MID / OB / OS crosses ----
    smi_prev = np.concatenate([[mid], smi[:-1]])
    ema_prev = np.concatenate([[smi_ema[0]], smi_ema[:-1]])
    h_prev = np.concatenate([[h[0]], h[:-1]])

    cross_mid_up = (smi > mid) & (smi_prev <= mid)
    cross_mid_down = (smi < mid) & (smi_prev >= mid)
    cross_up = (smi > smi_ema) & (smi_prev <= ema_prev)   # EMA crossover (cyan)
    cross_down = (smi < smi_ema) & (smi_prev >= ema_prev)  # EMA crossunder (white) = XDN
    entered_ob = (smi > ob) & (smi_prev <= ob)
    entered_os = (smi < os_) & (smi_prev >= os_)
    exited_ob = (smi <= ob) & (smi_prev > ob)
    exited_os = (smi >= os_) & (smi_prev < os_)

    # ---- consecutive above/below MID ----
    consec_above = _consecutive_run(smi > mid)
    consec_below = _consecutive_run(smi < mid)
    pre_akum = consec_below == akum_candles   # akumulasi bear terkonfirmasi
    pre_dist = consec_above == dist_candles   # distribusi bull terkonfirmasi

    # ---- PA / PD flavours ----
    hist_rising = h > h_prev
    hist_falling = h < h_prev
    pa_dip = pre_akum & hist_falling            # bcPADip
    pa_ready = pre_akum & hist_rising           # bcPAReady
    pd_dip = pre_dist & hist_rising             # bcPDDip
    pd_ready = pre_dist & hist_falling          # bcPDReady

    # ---- Failed MID (fakeout) ----
    # fail_mid_buy: bar ini cross DOWN through MID (cDM) SETELAH sebelumnya
    #   pernah cross UP (cUM) dlm window dekat -> PA batal / jebakan naik.
    # fail_mid_sell: bar ini cross UP through MID (cUM) SETELAH sebelumnya
    #   pernah cross DOWN (cDM) -> PD batal / jebakan turun.
    # Window dicari mundur sampai ditemukan cross berlawanan (atau 2*dist_candles).
    fail_mid_buy = np.zeros(n, dtype=bool)
    fail_mid_sell = np.zeros(n, dtype=bool)
    win = max(2 * dist_candles, 5)
    for i in range(n):
        if cross_mid_down[i]:
            # cari cUM terdekat ke belakang
            for j in range(i - 1, max(-1, i - 1 - win), -1):
                if cross_mid_up[j]:
                    fail_mid_buy[i] = True
                    break
                if cross_mid_down[j]:
                    break
        elif cross_mid_up[i]:
            for j in range(i - 1, max(-1, i - 1 - win), -1):
                if cross_mid_down[j]:
                    fail_mid_sell[i] = True
                    break
                if cross_mid_up[j]:
                    break

    # ---- hist-state (AU/AD/BD/BU) ----
    above = smi > smi_ema
    hist_state = np.where(above & hist_rising, "AU",
                 np.where(above & hist_falling, "AD",
                 np.where(~above & hist_rising, "BD", "BU")))

    # ---- zone ----
    zone = np.where(smi > ob, "OB",
            np.where(smi > mid, "Upper",
            np.where(smi > 0, "Mid",
            np.where(smi > os_, "Lower", "OS"))))

    # ---- dominant bar-state cascade (priority = Pine bar color) ----
    bar_state = np.empty(n, dtype=object)
    for i in range(n):
        if cross_up[i]:
            bar_state[i] = "Cross UP"
        elif cross_down[i]:
            bar_state[i] = "Cross DN"
        elif smi[i] > ob:
            bar_state[i] = "OB Zone"
        elif smi[i] < os_:
            bar_state[i] = "OS Zone"
        elif pa_dip[i]:
            bar_state[i] = "PA - Dip Mungkin"
        elif pa_ready[i]:
            bar_state[i] = "PA - Siap Balik"
        elif pd_dip[i]:
            bar_state[i] = "PD - Dip Mungkin"
        elif pd_ready[i]:
            bar_state[i] = "PD - Siap Balik"
        elif fail_mid_buy[i]:
            bar_state[i] = "Fail MID Buy"
        elif fail_mid_sell[i]:
            bar_state[i] = "Fail MID Sell"
        elif smi[i] < mid:
            bar_state[i] = "Bias Bawah"
        elif smi[i] > mid:
            bar_state[i] = "Bias Atas"
        else:
            bar_state[i] = "Netral"

    # ---- SETUP1 3-step trigger arrays ----
    # STEP1 FMB = fail MID buy INITIATION (cross UP through MID setelah bear stretch).
    #   Definisi = cross_mid_up & ada below-streak sebelumnya (bear stretch) ->
    #   sama dgn fail_mid_sell's prerequisite tapi kita pakai cross-up sbg inisiator.
    #   Untuk SETUP1 short, FMB = bar SMI cross UP lewati MID setelah di bawah
    #   (mirror dg Pine: PA dimulai saat close <MID, lalu SMI cross up = attempt).
    below_run_prev = np.concatenate([[0], consec_below[:-1]])  # streak below sblm bar i
    FMB = cross_mid_up & (below_run_prev >= 1)
    # STEP2 PD = PD Siap Balik (hist melemah 2 bar) -> puncak momentum
    PD = (smi > mid) & (h < h_prev) & (h < np.concatenate([[h[0], h[0]], h[:-2]]))
    # STEP3 XDN = cross DOWN (sudah = cross_down)
    XDN = cross_down

    return {
        "n": n,
        "smi": smi, "smi_ema": smi_ema, "smi_hist": h,
        "hist_state": hist_state, "zone": zone, "bar_state": bar_state,
        "cross_mid_up": cross_mid_up, "cross_mid_down": cross_mid_down,
        "cross_up": cross_up, "cross_down": cross_down,
        "entered_ob": entered_ob, "entered_os": entered_os,
        "exited_ob": exited_ob, "exited_os": exited_os,
        "consec_above": consec_above, "consec_below": consec_below,
        "pre_akum": pre_akum, "pre_dist": pre_dist,
        "pa_dip": pa_dip, "pa_ready": pa_ready,
        "pd_dip": pd_dip, "pd_ready": pd_ready,
        "fail_mid_buy": fail_mid_buy, "fail_mid_sell": fail_mid_sell,
        "FMB": FMB, "PD": PD, "XDN": XDN,
    }


def describe_bar(E, i):
    """Human-readable 1-line event descriptor for bar i (no emoji, terminal-safe)."""
    parts = [f"SMI={E['smi'][i]:.1f}", f"hist={E['smi_hist'][i]:.1f}",
             f"[{E['hist_state'][i]}]", f"zone={E['zone'][i]}",
             f"state={E['bar_state'][i]}"]
    return " ".join(parts)
