#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FBF v11 — ALTERNATIF backtest engine (chart-faithful dari FBF_v11.pine, DEFAULT SETTING)

VERSI INI = "fbf_v11_mhermes" — alternatif buatan mhermes, terpisah dari
fbf_v11_backtest.py (default engine yang sudah ada sebelumnya).
Sama-sama basis brief + FBF_v11.pine, tapi di sini saya teruskan jadi
varian STRICT:
  (a) aktifkan 2 filter opsional brief yang di default OFF:
        Persistence = 2  (kandidat harus bertahan ≥2 bar di luar level B)
        SMI agreement  (arah SMI harus searah break)
      → hasil = SUBSET lebih ketat dari default, alat crosscheck false-positive.
  (b) ST-ATR: gate Supertrend pakai ATR sendiri (stAdaptPeriod=10, RMA),
      BUKAN ATR(14) utama (netral di BTC, tapi lebih benar secara intern).
  (c) seed ATR/ST-ATR RMA benar (bar-0 tidak double-count TR).

Sumber kebenaran: FBF_v11.pine. Output = APA YANG USER LIHAT di chart TradingView.
- Non-repaint: semua keputusan pada candle CLOSED (candle terakhir Binance yang masih jalan dibuang).
- Gate visual Supertrend (enableStTrendFilter=True) ditaruh di LAPISAN OUTPUT, bukan di mesin:
  BREAK lawan trend tetap update state mesin (last_confirmed, hapus kandidat) tapi dicatat
  sebagai BREAK_HIDDEN_BY_TREND (debug), BUKAN data backtest.

Event (istilah visual chart):
  WAVE_STARTED, C_LOCKED, WAVE_CANCELLED, WAVE_STRUCT_REJECTED,
  CANDIDATE_INVALIDATED, B_LINE_TRACKING, CANDIDATE_FAILED (tanda ✖),
  CANDIDATE_EVICTED, BREAK_DUPLICATE_SKIPPED, BREAK_HIDDEN_BY_TREND,
  BREAK  <-- data utama
  RAW_CANDIDATE (opsional, --debug-raw)

Pakai:
  python3 fbf_v11_backtest.py --symbol BTCUSDT --interval 1h --bars 1000
  python3 fbf_v11_backtest.py --symbol BTCUSDT --interval 1h --bars 1000 --explain "2026-07-01T12:00"
  python3 fbf_v11_backtest.py --csv data.csv --interval 1h        # offline (kolom: open_time_ms,open,high,low,close)

Output:
  - tabel BREAK di stdout (waktu UTC = saat candle CLOSE, cocokkan dengan bar close TradingView)
  - fbf_breaks_<SYMBOL>_<TF>.csv   (data utama)
  - fbf_events_<SYMBOL>_<TF>.csv   (semua event, buat crosscheck/diagnosa)
"""

import argparse
import csv
import json
import sys
import time as _time
import datetime as dt
import urllib.request
import urllib.parse

# ═══════════════════════════════════════════════════════════════
# PARAMETER DEFAULT (§2 brief — SATU-SATUNYA konfigurasi)
# ═══════════════════════════════════════════════════════════════
LEFT_BARS   = 3      # pivot utama; lag deteksi = RIGHT_BARS
RIGHT_BARS  = 3
ENABLE_A_FRACTAL = True   # A1
A_LEFT_BARS = 5
A_RIGHT_BARS = 5
ENABLE_C_FRACTAL = False  # C1 OFF -> cek fractal C auto-lolos
ENABLE_A_DIST = True      # A2
A_DIST_MULT   = 1.0
ENABLE_A_LOOKBACK = False # A3 OFF -> A tidak diganti scan ekstrem
ENABLE_FIBO_BC = True     # C2
BC_FIBO_MIN = 0.5
BC_FIBO_MAX = 0.786
ENABLE_STRUCT_FILTER = True  # C3

ENABLE_ATR_FILTER = True
ATR_LEN  = 14             # ta.atr = RMA/Wilder (BUKAN SMA) — jebakan #1
ATR_MULT = 0.15
# ══ ALT-STRICT: aktifkan 2 filter opsional brief yg default OFF ══
# Persistence(2): kandidat harus BERTAHAN ≥2 bar di luar level B
#   (nyaring fakeout 1-candle). SMI agreement: arah SMI harus searah break.
# Hasilnya = subset lebih ketat dari default → alat crosscheck false-positive.
ENABLE_PERSIST_FILTER = True
PERSIST_N = 2
REQ_N = PERSIST_N
ENABLE_SMI_FILTER = True
SMI_LEN_K = 5
SMI_LEN_D = 3
SMI_LEN_E = 3
NO_DUPLICATE = True       # 1 BREAK per level B (per b_bar) per sisi
MAX_CAND = 8              # kapasitas kandidat per sisi; ke-9 -> tertua digusur

ENABLE_ST_TREND_FILTER = True   # gate visual: BREAK bull hanya saat ST uptrend
# enableEmaTrendFilter=False -> EMA gate tidak dipakai
ST_PERIOD = 10            # Supertrend Adaptive: src=hl2, ATR=RMA, seed trend=1
ST_MULT   = 3.0

FILTER_TAG = "ATR Str A1 A2 C2"   # meniru label chart "BREAK C:x%" + tag filter

INTERVAL_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "6h": 21_600_000,
    "8h": 28_800_000, "12h": 43_200_000, "1d": 86_400_000, "3d": 259_200_000,
    "1w": 604_800_000,
}


def ts_utc(ms):
    if ms is None:
        return ""
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


# ═══════════════════════════════════════════════════════════════
# KANDIDAT — snapshot BEKU 1 wave (tipe Cand di Pine)
# ═══════════════════════════════════════════════════════════════
class Candidate:
    __slots__ = ("a_val", "a_bar", "b_val", "b_bar", "c_val", "c_bar", "active", "persist",
                 "was_visible")

    def __init__(self, a_val, a_bar, b_val, b_bar, c_val, c_bar, was_visible=True):
        self.a_val = a_val
        self.a_bar = a_bar
        self.b_val = b_val
        self.b_bar = b_bar
        self.c_val = c_val
        self.c_bar = c_bar
        self.active = False
        self.persist = 0
        # v11.1: wave kelihatan di chart SAAT C terkunci? (gate trend ST; default
        # setting EMA gate OFF & tbC2Valid selalu True -> praktis = status ST saja)
        self.was_visible = was_visible


# ═══════════════════════════════════════════════════════════════
# ENGINE
# ═══════════════════════════════════════════════════════════════
class FBFEngine:
    """
    Urutan eksekusi per bar (WAJIB, jebakan #4):
      Stasiun 0 (pivot, ATR, Supertrend) -> Otak 1 Tracker -> Otak 2 Juri.
    Kandidat lahir via tbLockBreak (close>B) bisa langsung dievaluasi Juri bar itu juga.
    """

    def __init__(self, open_times, opens, highs, lows, closes, interval_ms, debug_raw=False):
        self.t = open_times
        self.o = opens
        self.h = highs
        self.l = lows
        self.c = closes
        self.interval_ms = interval_ms
        self.debug_raw = debug_raw
        self.n = len(closes)

        # ATR RMA/Wilder
        self.atr = None

        # Supertrend Adaptive state (seed trend awal = 1)
        self.st_up_final = None
        self.st_dn_final = None
        self.st_trend = 1
        self._st_atr_val = None   # ST-ATR (stAdaptPeriod=10, RMA) — siap sebelum ATR(14)
        self._st_tr_acc = 0.0

        # SMI state (double-EMA + EMA smoothing) — alt-strict
        self._smi_e1 = None
        self._smi_e2 = None
        self._smi_e1_rng = None
        self._smi_e2_rng = None
        self._smi_ema_v = None
        self.smi = 0.0
        self.smi_ema = 0.0

        # memori pivot (Stasiun 0)
        self.last_ph = None       # (val, bar) pivot high utama
        self.last_pl = None
        self.last_a_ph = None     # pivot besar A1
        self.last_a_pl = None
        self.snap_low_at_high = None   # titik A wave bull: pivot low BESAR saat pivot high utama muncul
        self.snap_high_at_low = None   # mirror bear

        # pivot terdeteksi BAR INI (di-reset tiap bar)
        self.cur_ph = None
        self.cur_pl = None

        # Otak 1 — tracker (1 slot live per sisi)
        self.trk = {
            "bull": {"phase": 0, "a_val": None, "a_bar": None, "b_val": None, "b_bar": None,
                     "c_val": None, "c_bar": None},
            "bear": {"phase": 0, "a_val": None, "a_bar": None, "b_val": None, "b_bar": None,
                     "c_val": None, "c_bar": None},
        }

        # Otak 2 — juri multi-slot
        self.candidates = {"bull": [], "bear": []}
        self.last_confirmed_b = {"bull": None, "bear": None}  # kunci duplikat per b_bar (jebakan #8)

        self.events = []
        self.breaks = []

    # ── helper event ──
    def _ev(self, i, etype, side, a_val=None, a_bar=None, b_val=None, b_bar=None,
            c_val=None, c_bar=None, retr=None, extra=""):
        self.events.append({
            "bar": i,
            "time_open": self.t[i],
            "time_close": self.t[i] + self.interval_ms,
            "event": etype,
            "side": side,
            "a_val": a_val, "a_bar": a_bar,
            "a_bar_time": self.t[a_bar] if a_bar is not None else None,
            "b_val": b_val, "b_bar": b_bar,
            "b_bar_time": self.t[b_bar] if b_bar is not None else None,
            "c_val": c_val, "c_bar": c_bar,
            "c_bar_time": self.t[c_bar] if c_bar is not None else None,
            "retrace_pct": round(retr * 100, 1) if retr is not None else None,
            "atr14": self.atr,
            "st_trend": self.st_trend,
            "extra": extra,
        })

    # ── Stasiun 0: pivot (semantik ta.pivothigh/low persis — ketat dua sisi, jebakan #2) ──
    def _pivot(self, arr, i, left, right, is_high):
        p = i - right
        if p - left < 0:
            return None
        v = arr[p]
        if is_high:
            for j in range(p - left, p):
                if arr[j] >= v:
                    return None
            for j in range(p + 1, i + 1):
                if arr[j] >= v:
                    return None
        else:
            for j in range(p - left, p):
                if arr[j] <= v:
                    return None
            for j in range(p + 1, i + 1):
                if arr[j] <= v:
                    return None
        return (v, p)   # (nilai, bar_asli = bar_deteksi - rightBars)

    def _station0(self, i):
        # ATR(14) RMA/Wilder: seed = SMA 14 TR pertama, lalu (atr_prev*13 + TR)/14
        if i == 0:
            tr = self.h[i] - self.l[i]
            self._tr_acc = tr
        else:
            pc = self.c[i - 1]
            tr = max(self.h[i] - self.l[i], abs(self.h[i] - pc), abs(self.l[i] - pc))
        if i < ATR_LEN:
            if i > 0:
                self._tr_acc += tr
            if i == ATR_LEN - 1:
                self.atr = self._tr_acc / ATR_LEN
        else:
            self.atr = (self.atr * (ATR_LEN - 1) + tr) / ATR_LEN

        # Supertrend Adaptive — replika PERSIS blok Pine (jebakan #5)
        # GATE: pakai ST-ATR (stAdaptPeriod=10), BUKAN main ATR(14).
        # Kalau pakai main ATR, ST baru jalan di bar 13 → history trend
        # bars 9-12 hilang → bisa salah sembunyikan BREAK (jebakan #5/#6).
        if self.st_atr(i) is not None:
            src = (self.h[i] + self.l[i]) / 2.0   # hl2
            up = src - ST_MULT * self.st_atr(i)
            dn = src + ST_MULT * self.st_atr(i)
            prev_up_f = self.st_up_final if self.st_up_final is not None else up   # nz(upF[1], up)
            prev_dn_f = self.st_dn_final if self.st_dn_final is not None else dn
            c1 = self.c[i - 1] if i > 0 else None
            up_f = max(up, prev_up_f) if (c1 is not None and c1 > prev_up_f) else up
            dn_f = min(dn, prev_dn_f) if (c1 is not None and c1 < prev_dn_f) else dn
            trend = self.st_trend
            if trend == -1 and self.c[i] > prev_dn_f:
                trend = 1
            elif trend == 1 and self.c[i] < prev_up_f:
                trend = -1
            self.st_up_final = up_f
            self.st_dn_final = dn_f
            self.st_trend = trend

        # SMI internal (hanya dihitung kalau ENABLE_SMI_FILTER)
        if ENABLE_SMI_FILTER:
            if i >= SMI_LEN_K:
                lo = max(0, i - SMI_LEN_K)
                hh = self.h[lo]
                ll = self.l[lo]
                for j in range(lo + 1, i + 1):
                    if self.h[j] > hh:
                        hh = self.h[j]
                    if self.l[j] < ll:
                        ll = self.l[j]
                rel = self.c[i] - (hh + ll) / 2.0
                rng = hh - ll
                ema1 = self._ema_ema_state(rel)
                ema2 = self._ema_ema_state_rng(rng)
                self.smi = 200.0 * (ema1 / ema2) if ema2 != 0 else 0.0
                self.smi_ema = self._smi_ema_state(self.smi)
            else:
                self.smi = 0.0
                self.smi_ema = 0.0

        # pivot bar ini
        self.cur_ph = self._pivot(self.h, i, LEFT_BARS, RIGHT_BARS, True)
        self.cur_pl = self._pivot(self.l, i, LEFT_BARS, RIGHT_BARS, False)
        cur_a_ph = self._pivot(self.h, i, A_LEFT_BARS, A_RIGHT_BARS, True) if ENABLE_A_FRACTAL else None
        cur_a_pl = self._pivot(self.l, i, A_LEFT_BARS, A_RIGHT_BARS, False) if ENABLE_A_FRACTAL else None

        # urutan Pine: blok A1 update dulu, baru blok pivot utama + snapshot
        if cur_a_ph is not None:
            self.last_a_ph = cur_a_ph
        if cur_a_pl is not None:
            self.last_a_pl = cur_a_pl
        if self.cur_ph is not None:
            self.snap_low_at_high = self.last_a_pl if ENABLE_A_FRACTAL else self.last_pl
            self.last_ph = self.cur_ph
        if self.cur_pl is not None:
            self.snap_high_at_low = self.last_a_ph if ENABLE_A_FRACTAL else self.last_ph
            self.last_pl = self.cur_pl

        if self.debug_raw:
            if self.last_ph is not None and self.c[i] > self.last_ph[0]:
                self._ev(i, "RAW_CANDIDATE", "bull", b_val=self.last_ph[0], b_bar=self.last_ph[1])
            if self.last_pl is not None and self.c[i] < self.last_pl[0]:
                self._ev(i, "RAW_CANDIDATE", "bear", b_val=self.last_pl[0], b_bar=self.last_pl[1])

    def st_atr(self, i):
        # stAdaptPeriod=10 pakai RMA sendiri (stAdaptAtrSma=False -> ta.atr)
        return self._st_atr_val

    def _iz(self, v):
        # True kalau state belum di-init (Pine: nz(x,0) fallback 0)
        return v is None

    # ── SMI helpers (Pine: emaEma = ema(ema(s,l),l); smi = 200*emaEma(rel)/emaEma(rng)) ──
    def _ema_ema_state(self, val):
        a = SMI_LEN_D
        alpha = 2.0 / (a + 1)
        if self._iz(self._smi_e1):
            self._smi_e1 = val
        else:
            self._smi_e1 = val * alpha + self._smi_e1 * (1 - alpha)
        if self._iz(self._smi_e2):
            self._smi_e2 = self._smi_e1
        else:
            self._smi_e2 = self._smi_e1 * alpha + self._smi_e2 * (1 - alpha)
        return self._smi_e2

    def _ema_ema_state_rng(self, val):
        a = SMI_LEN_D
        alpha = 2.0 / (a + 1)
        if self._iz(self._smi_e1_rng):
            self._smi_e1_rng = val
        else:
            self._smi_e1_rng = val * alpha + self._smi_e1_rng * (1 - alpha)
        if self._iz(self._smi_e2_rng):
            self._smi_e2_rng = self._smi_e1_rng
        else:
            self._smi_e2_rng = self._smi_e1_rng * alpha + self._smi_e2_rng * (1 - alpha)
        return self._smi_e2_rng

    def _smi_ema_state(self, val):
        a = SMI_LEN_E
        alpha = 2.0 / (a + 1)
        if self._iz(self._smi_ema_v):
            self._smi_ema_v = val
        else:
            self._smi_ema_v = val * alpha + self._smi_ema_v * (1 - alpha)
        return self._smi_ema_v

    def _st_atr_update(self, i):
        # RMA/Wilder: seed = SMA pertama ST_PERIOD TR, lalu (prev*(P-1)+TR)/P
        if i == 0:
            tr = self.h[i] - self.l[i]
            self._st_tr_acc = tr
        else:
            pc = self.c[i - 1]
            tr = max(self.h[i] - self.l[i], abs(self.h[i] - pc), abs(self.l[i] - pc))
            if i < ST_PERIOD:
                self._st_tr_acc += tr
            else:
                self._st_atr_val = (self._st_atr_val * (ST_PERIOD - 1) + tr) / ST_PERIOD
        if i == ST_PERIOD - 1:
            self._st_atr_val = self._st_tr_acc / ST_PERIOD

    # ── zona fibo (buat laporan C_LOCKED): hijau=valid, oranye=lewat, abu=belum masuk ──
    def _fibo_zone_state(self, side, a, b, cval):
        if cval is None:
            return "abu"
        if side == "bull":
            z_top = b - BC_FIBO_MIN * (b - a)
            z_bot = b - BC_FIBO_MAX * (b - a)
            if cval > z_top:
                return "abu"
            if cval >= z_bot:
                return "hijau"
            return "oranye"
        else:
            z_bot = b + BC_FIBO_MIN * (a - b)
            z_top = b + BC_FIBO_MAX * (a - b)
            if cval < z_bot:
                return "abu"
            if cval <= z_top:
                return "hijau"
            return "oranye"

    # ── Otak 1 — TRACKER (bull; bear = mirror total via s) ──
    def _tracker(self, i, side):
        s = 1 if side == "bull" else -1
        T = self.trk[side]
        close = self.c[i]
        ext = self.l if side == "bull" else self.h        # running-extreme C: bull=low, bear=high
        piv_b = self.cur_ph if side == "bull" else self.cur_pl   # pivot pemicu B
        piv_lock = self.cur_pl if side == "bull" else self.cur_ph  # pivot pengunci C
        snap = self.snap_low_at_high if side == "bull" else self.snap_high_at_low

        start_ok = (T["phase"] == 0 and piv_b is not None and snap is not None
                    and s * snap[0] < s * piv_b[0] and snap[1] < piv_b[1])

        if start_ok:
            T["a_val"], T["a_bar"] = snap
            T["b_val"], T["b_bar"] = piv_b
            T["c_val"], T["c_bar"] = None, None
            # C awal = scan ekstrem pada rightBars bar "kanan pivot" yang sudah lewat
            for k in range(RIGHT_BARS):
                idx = i - k
                if idx > T["b_bar"]:
                    v = ext[idx]
                    if T["c_val"] is None or s * v < s * T["c_val"]:
                        T["c_val"], T["c_bar"] = v, idx
            T["phase"] = 1
            self._ev(i, "WAVE_STARTED", side, a_val=T["a_val"], a_bar=T["a_bar"],
                     b_val=T["b_val"], b_bar=T["b_bar"], c_val=T["c_val"], c_bar=T["c_bar"],
                     extra="C? tentatif")
            return

        if T["phase"] > 0:
            # 1. wave batal: close lewat titik A
            if s * close < s * T["a_val"]:
                self._ev(i, "WAVE_CANCELLED", side, a_val=T["a_val"], a_bar=T["a_bar"],
                         b_val=T["b_val"], b_bar=T["b_bar"], c_val=T["c_val"], c_bar=T["c_bar"])
                T["phase"] = 0
                return
            # 2. update "C?" running-extreme
            v = ext[i]
            if T["c_val"] is None or s * v < s * T["c_val"]:
                T["c_val"], T["c_bar"] = v, i
            # 3. kunci C — dua pemicu OR; pivot menang
            lock_pivot = piv_lock is not None and piv_lock[1] > T["b_bar"]
            lock_break = s * close > s * T["b_val"]
            if lock_pivot or lock_break:
                c_val, c_bar = piv_lock if lock_pivot else (T["c_val"], T["c_bar"])
                # C3: wave batal struktur
                if ENABLE_STRUCT_FILTER and not (s * c_val > s * T["a_val"]):
                    self._ev(i, "WAVE_STRUCT_REJECTED", side, a_val=T["a_val"], a_bar=T["a_bar"],
                             b_val=T["b_val"], b_bar=T["b_bar"], c_val=c_val, c_bar=c_bar)
                    T["phase"] = 0
                    return
                T["c_val"], T["c_bar"] = c_val, c_bar
                zone = self._fibo_zone_state(side, T["a_val"], T["b_val"], c_val)
                self._ev(i, "C_LOCKED", side, a_val=T["a_val"], a_bar=T["a_bar"],
                         b_val=T["b_val"], b_bar=T["b_bar"], c_val=c_val, c_bar=c_bar,
                         extra=f"zona fibo {zone}; via {'pivot' if lock_pivot else 'breakout'}")
                # PUSH kandidat (snapshot BEKU) -> Otak 2; slot langsung bebas
                # was_visible v11.1: bullWaveVisible/bearWaveVisible saat C_LOCKED
                was_visible = (self.st_trend == s)
                cand = Candidate(T["a_val"], T["a_bar"], T["b_val"], T["b_bar"], c_val, c_bar,
                                  was_visible)
                arr = self.candidates[side]
                arr.append(cand)
                if len(arr) > MAX_CAND:
                    old = arr.pop(0)
                    self._ev(i, "CANDIDATE_EVICTED", side, a_val=old.a_val, a_bar=old.a_bar,
                             b_val=old.b_val, b_bar=old.b_bar, c_val=old.c_val, c_bar=old.c_bar)
                T["phase"] = 0

    # ── Otak 2 — JURI (multi-slot; iterasi terbalik = aman hapus, sama dengan Pine) ──
    def _judge(self, i, side):
        s = 1 if side == "bull" else -1
        arr = self.candidates[side]
        if not arr:
            return
        close = self.c[i]
        atr = self.atr
        for idx in range(len(arr) - 1, -1, -1):
            cand = arr[idx]

            # [A] kandidat mati: close lewat aVal sebelum sempat aktif
            if not cand.active and s * close < s * cand.a_val:
                del arr[idx]
                self._ev(i, "CANDIDATE_INVALIDATED", side, a_val=cand.a_val, a_bar=cand.a_bar,
                         b_val=cand.b_val, b_bar=cand.b_bar, c_val=cand.c_val, c_bar=cand.c_bar)
                continue

            # [A] aktivasi: breakout level B + buffer ATR
            just_activated = False
            if not cand.active and s * close > s * cand.b_val:
                dist_ok = (not ENABLE_ATR_FILTER) or (
                    atr is not None and s * (close - cand.b_val) >= ATR_MULT * atr)
                if dist_ok:
                    cand.active = True
                    cand.persist = 1
                    just_activated = True
                    self._ev(i, "B_LINE_TRACKING", side, a_val=cand.a_val, a_bar=cand.a_bar,
                             b_val=cand.b_val, b_bar=cand.b_bar, c_val=cand.c_val, c_bar=cand.c_bar,
                             extra="level B aktif, dipantau")

            # [B] pemantauan: bertahan di luar B + buffer ATR tiap bar
            if cand.active and not just_activated:
                still_beyond = s * close > s * cand.b_val
                dist_ok2 = (not ENABLE_ATR_FILTER) or (
                    atr is not None and s * (close - cand.b_val) >= ATR_MULT * atr)
                if still_beyond and dist_ok2:
                    cand.persist += 1
                else:
                    cand.active = False
                    cand.persist = 0
                    self._ev(i, "CANDIDATE_FAILED", side, a_val=cand.a_val, a_bar=cand.a_bar,
                             b_val=cand.b_val, b_bar=cand.b_bar, c_val=cand.c_val, c_bar=cand.c_bar,
                             extra="kandidat gugur ✖ (buffer ATR); boleh breakout ulang")

            # [C] vonis (data BEKU kandidat)
            if cand.active:
                time_ok = cand.persist >= REQ_N                       # Persist OFF
                smi_ok = (not ENABLE_SMI_FILTER) or (self.smi >= self.smi_ema)
                c_valid = (cand.c_bar is not None and cand.c_bar > cand.b_bar
                           and cand.c_bar < i)
                a_valid = cand.a_bar is not None
                # A2 pakai ATR pada BAR EVALUASI (jebakan #9)
                dist_a_ok = (not ENABLE_A_DIST) or (
                    a_valid and atr is not None
                    and s * (cand.b_val - cand.a_val) >= A_DIST_MULT * atr)
                struct_ok = (not ENABLE_STRUCT_FILTER) or (
                    a_valid and c_valid and s * cand.c_val > s * cand.a_val)
                smi_ok = (not ENABLE_SMI_FILTER) or (self.smi <= self.smi_ema)
                c_fr_ok = True                                         # C1 OFF
                fibo_ok = True
                if ENABLE_FIBO_BC and a_valid and c_valid:
                    leg_ab = s * (cand.b_val - cand.a_val)
                    retr = (s * (cand.b_val - cand.c_val) / leg_ab) if leg_ab > 0 else 0.0
                    fibo_ok = BC_FIBO_MIN <= retr <= BC_FIBO_MAX
                confirmed = time_ok and smi_ok and struct_ok and dist_a_ok and c_fr_ok and fibo_ok
                if confirmed:
                    last = self.last_confirmed_b[side]
                    if NO_DUPLICATE and last is not None and cand.b_bar == last:
                        del arr[idx]
                        self._ev(i, "BREAK_DUPLICATE_SKIPPED", side, a_val=cand.a_val,
                                 a_bar=cand.a_bar, b_val=cand.b_val, b_bar=cand.b_bar,
                                 c_val=cand.c_val, c_bar=cand.c_bar, retr=retr)
                        continue
                    # state mesin tetap update — gate visual TIDAK di sini (jebakan #6)
                    self.last_confirmed_b[side] = cand.b_bar
                    del arr[idx]
                    # ═══ STASIUN 3 — GATE OUTPUT (apa yang user LIHAT) ═══
                    visible = (not ENABLE_ST_TREND_FILTER) or (self.st_trend == s)
                    if visible:
                        # v11.1: bukan gate — cuma penanda label BREAK vs BREAK↺
                        born_against_trend = not cand.was_visible
                        label = "BREAK↺" if born_against_trend else "BREAK"
                        self._ev(i, "BREAK", side, a_val=cand.a_val, a_bar=cand.a_bar,
                                 b_val=cand.b_val, b_bar=cand.b_bar, c_val=cand.c_val,
                                 c_bar=cand.c_bar, retr=retr,
                                 extra=f"{FILTER_TAG} [{label}]")
                        self.breaks.append({
                            "timestamp_close_bar": ts_utc(self.t[i] + self.interval_ms),
                            "side": side,
                            "label": label,
                            "b_val": cand.b_val,
                            "b_bar_time": ts_utc(self.t[cand.b_bar]),
                            "a_val": cand.a_val,
                            "c_val": cand.c_val,
                            "c_bar_time": ts_utc(self.t[cand.c_bar]),
                            "retrace_pct": round(retr * 100, 1) if retr is not None else None,
                            "atr14": round(atr, 8) if atr is not None else None,
                            "st_trend": self.st_trend,
                            "filter_tag": FILTER_TAG,
                            "born_against_trend": born_against_trend,
                            "break_price": self.h[i] if side == "bull" else self.l[i],  # garis B->D
                        })
                    else:
                        self._ev(i, "BREAK_HIDDEN_BY_TREND", side, a_val=cand.a_val,
                                 a_bar=cand.a_bar, b_val=cand.b_val, b_bar=cand.b_bar,
                                 c_val=cand.c_val, c_bar=cand.c_bar, retr=retr,
                                 extra="mesin lihat break, chart sembunyikan (lawan trend ST)")
                    continue

    def run(self):
        for i in range(self.n):
            self._st_atr_update(i)
            self._station0(i)
            self._tracker(i, "bull")
            self._tracker(i, "bear")
            self._judge(i, "bull")
            self._judge(i, "bear")
        return self.breaks, self.events

    # ── diagnosa: kronologi event di sekitar timestamp ──
    def explain(self, ts_str, window_bars=30):
        try:
            t = dt.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=dt.timezone.utc)
            target_ms = int(t.timestamp() * 1000)
        except ValueError:
            print(f"Timestamp tidak valid: {ts_str} (pakai format ISO, mis. 2026-07-01T12:00)")
            return
        bar = min(range(self.n), key=lambda i: abs(self.t[i] - target_ms))
        lo, hi = bar - window_bars, bar + window_bars
        near = [e for e in self.events if lo <= e["bar"] <= hi]
        print(f"\n== explain({ts_str}) — bar {bar} ({ts_utc(self.t[bar])} UTC open), "
              f"window ±{window_bars} bar ==")
        if not near:
            print("Tidak ada event di window ini.")
            return
        for e in near:
            parts = [f"[{ts_utc(e['time_close'])} close]", f"bar {e['bar']}",
                     e["event"], e["side"] or ""]
            if e["b_val"] is not None:
                parts.append(f"B={e['b_val']:.8g}@{ts_utc(e['b_bar_time'])}")
            if e["a_val"] is not None:
                parts.append(f"A={e['a_val']:.8g}")
            if e["c_val"] is not None:
                parts.append(f"C={e['c_val']:.8g}")
            if e["retrace_pct"] is not None:
                parts.append(f"C:{e['retrace_pct']}%")
            parts.append(f"ST={'up' if e['st_trend'] == 1 else 'down'}")
            if e["extra"]:
                parts.append(f"({e['extra']})")
            print("  " + "  ".join(str(p) for p in parts))


# ═══════════════════════════════════════════════════════════════
# DATA — Binance klines (candle CLOSED saja, jebakan #3) / CSV offline
# ═══════════════════════════════════════════════════════════════
def fetch_binance(symbol, interval, bars):
    ms = INTERVAL_MS[interval]
    out = []
    end_time = int(_time.time() * 1000)
    remaining = bars + 2  # +margin buat buang candle berjalan
    while remaining > 0:
        limit = min(1000, remaining)
        qs = urllib.parse.urlencode({
            "symbol": symbol.upper(), "interval": interval,
            "endTime": end_time, "limit": limit,
        })
        url = f"https://api.binance.com/api/v3/klines?{qs}"
        with urllib.request.urlopen(url, timeout=30) as r:
            chunk = json.loads(r.read())
        if not chunk:
            break
        out = chunk + out
        remaining -= len(chunk)
        end_time = chunk[0][0] - 1
        if len(chunk) < limit:
            break
    # dedupe + sort by openTime
    seen = {}
    for k in out:
        seen[k[0]] = k
    klines = [seen[t] for t in sorted(seen)]
    # buang candle terakhir yang masih berjalan (closeTime belum lewat)
    now_ms = int(_time.time() * 1000)
    while klines and int(klines[-1][6]) >= now_ms:
        klines.pop()
    klines = klines[-bars:]
    t = [int(k[0]) for k in klines]
    o = [float(k[1]) for k in klines]
    h = [float(k[2]) for k in klines]
    l = [float(k[3]) for k in klines]
    c = [float(k[4]) for k in klines]
    return t, o, h, l, c


def load_csv(path):
    t, o, h, l, c = [], [], [], [], []
    with open(path, newline="") as f:
        rd = csv.reader(f)
        for row in rd:
            if not row or not row[0].strip() or not row[0].strip()[0].isdigit():
                continue  # skip header
            ts = row[0].strip()
            if ts.isdigit():
                ms = int(ts)
                if ms < 10**12:
                    ms *= 1000  # detik -> ms
            else:
                d = dt.datetime.fromisoformat(ts)
                if d.tzinfo is None:
                    d = d.replace(tzinfo=dt.timezone.utc)
                ms = int(d.timestamp() * 1000)
            t.append(ms)
            o.append(float(row[1]))
            h.append(float(row[2]))
            l.append(float(row[3]))
            c.append(float(row[4]))
    return t, o, h, l, c


# ═══════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════
def print_breaks(breaks):
    if not breaks:
        print("Tidak ada BREAK di periode ini.")
        return
    cols = ["timestamp_close_bar", "side", "label", "b_val", "b_bar_time", "a_val", "c_val",
            "c_bar_time", "retrace_pct", "atr14", "st_trend", "filter_tag"]
    rows = [[str(b[c]) for c in cols] for b in breaks]
    widths = [max(len(c), *(len(r[j]) for r in rows)) for j, c in enumerate(cols)]
    print("  ".join(c.ljust(widths[j]) for j, c in enumerate(cols)))
    print("  ".join("-" * widths[j] for j in range(len(cols))))
    for r in rows:
        print("  ".join(r[j].ljust(widths[j]) for j in range(len(cols))))


def write_csvs(breaks, events, symbol, interval):
    tag = f"{symbol.upper()}_{interval}_mhermes"
    bpath = f"fbf_breaks_{tag}.csv"
    epath = f"fbf_events_{tag}.csv"
    if breaks:
        with open(bpath, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(breaks[0].keys()))
            w.writeheader()
            w.writerows(breaks)
    ev_rows = []
    for e in events:
        ev_rows.append({
            "time_close_utc": ts_utc(e["time_close"]),
            "bar": e["bar"],
            "event": e["event"],
            "side": e["side"],
            "a_val": e["a_val"],
            "a_bar_time_utc": ts_utc(e["a_bar_time"]) if e["a_bar_time"] else "",
            "b_val": e["b_val"],
            "b_bar_time_utc": ts_utc(e["b_bar_time"]) if e["b_bar_time"] else "",
            "c_val": e["c_val"],
            "c_bar_time_utc": ts_utc(e["c_bar_time"]) if e["c_bar_time"] else "",
            "retrace_pct": e["retrace_pct"],
            "atr14": e["atr14"],
            "st_trend": e["st_trend"],
            "extra": e["extra"],
        })
    with open(epath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ev_rows[0].keys()) if ev_rows else
                           ["time_close_utc", "bar", "event", "side"])
        w.writeheader()
        w.writerows(ev_rows)
    return bpath if breaks else None, epath


def main():
    ap = argparse.ArgumentParser(description="FBF v11 backtest engine (chart-faithful)")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", default="1h", choices=sorted(INTERVAL_MS))
    ap.add_argument("--bars", type=int, default=1000)
    ap.add_argument("--csv", help="OHLCV lokal (kolom: time,open,high,low,close). Skip Binance.")
    ap.add_argument("--explain", help="timestamp ISO — cetak kronologi event di sekitarnya")
    ap.add_argument("--explain-window", type=int, default=30, help="window ±N bar buat --explain")
    ap.add_argument("--debug-raw", action="store_true", help="catat event RAW_CANDIDATE")
    args = ap.parse_args()

    if args.csv:
        t, o, h, l, c = load_csv(args.csv)
        src = args.csv
    else:
        t, o, h, l, c = fetch_binance(args.symbol, args.interval, args.bars)
        src = f"Binance {args.symbol.upper()} {args.interval}"
    if len(c) < 60:
        print(f"Data terlalu sedikit ({len(c)} bar). Minimal ~60 bar buat warmup.")
        sys.exit(1)

    print(f"Data: {src} — {len(c)} candle CLOSED "
          f"({ts_utc(t[0])} s/d {ts_utc(t[-1] + INTERVAL_MS[args.interval])} UTC)")
    print("Catatan warmup: pivot/ATR/Supertrend butuh history — event di ±50 bar pertama "
          "bisa beda dengan chart TradingView (TV punya history lebih panjang di kiri).\n")

    eng = FBFEngine(t, o, h, l, c, INTERVAL_MS[args.interval], debug_raw=args.debug_raw)
    breaks, events = eng.run()

    counts = {}
    for e in events:
        counts[e["event"]] = counts.get(e["event"], 0) + 1
    print("Ringkasan event: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"\n== TABEL BREAK ({len(breaks)}) — data utama, waktu = candle CLOSE (UTC) ==")
    print_breaks(breaks)

    # v11.1: breakdown BREAK kontinuasi vs BREAK↺ (pasca-flip trend) — hanya laporan,
    # jumlah/posisi BREAK tidak berubah dari v11.
    flip = [b for b in breaks if b["born_against_trend"]]
    cont = [b for b in breaks if not b["born_against_trend"]]
    print(f"\nBreakdown: BREAK (kontinuasi)={len(cont)}, BREAK↺ (pasca-flip)={len(flip)}")

    bpath, epath = write_csvs(breaks, events, args.symbol if not args.csv else "CSV",
                              args.interval)
    print(f"\nCSV: {bpath or '(tidak ada BREAK)'} + {epath}")

    if args.explain:
        eng.explain(args.explain, args.explain_window)


if __name__ == "__main__":
    main()
