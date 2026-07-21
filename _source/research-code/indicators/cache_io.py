"""Satu pintu masuk untuk cache kline CSV.

Semua konsumen (watcher, arm alert, forward test, backtest) baca lewat sini.
Pengaman: tulis atomik, kunci non-blok, validasi sebelum tukar, backup .prev.
Stdlib saja — fcntl, os, tempfile. Tidak ada dependensi baru.
"""

import os
import sys
import time
import fcntl
import tempfile
import datetime as _dt

import pandas as pd
import requests

CACHE_BASE = "/home/ubuntu/trading-research/backtests/BTCUSDT/SETUP1"
SYM = "BTCUSDT"
OHLCV = ["open", "high", "low", "close", "volume"]
OHLC = ["open", "high", "low", "close"]

# Tiap refresh ambil ulang sekian bar terakhir dan timpa yang tersimpan. Biaya
# tetap satu request, tapi bar mana pun yang terlanjur tersimpan separuh jadi
# sembuh sendiri di refresh berikutnya, tanpa skrip migrasi terpisah.
REHEAL_BARS = 300


def cache_path(tf_dir, base=None):
    base = base or CACHE_BASE
    return os.path.join(base, tf_dir, f"data_BTCUSDT_{tf_dir.lower()}_2019now.csv")


def _warn(msg):
    print(f"[cache_io] WARN {msg}", file=sys.stderr)


# ─── BACA ────────────────────────────────────────────────────────
def read_cache(tf_dir, base=None, iv_ms=None, path=None):
    """Baca cache + validasi. None kalau file tidak ada.

    Raise CacheCorrupt kalau rusak struktural — jangan pernah diam-diam dipakai.
    """
    path = path or cache_path(tf_dir, base)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = _normalize(df)
    problems = validate(df, iv_ms=iv_ms)
    if problems:
        raise CacheCorrupt(f"{path}: " + "; ".join(problems))
    return df


class CacheCorrupt(Exception):
    pass


def _normalize(df):
    """Gabung kolom 'vol' warisan ke 'volume', buang sisanya.

    Cache lama punya dua kolom volume: baris historis di 'volume', baris hasil
    fetch di 'vol' — akibat fetch_klines dulu menamai kolomnya 'vol' lalu
    di-concat ke cache berkolom 'volume'. Keduanya saling isi, tidak tumpang tindih.
    """
    if "vol" in df.columns:
        if "volume" in df.columns:
            df["volume"] = df["volume"].fillna(df["vol"])
        else:
            df = df.rename(columns={"vol": "volume"})
        df = df.drop(columns=[c for c in ["vol"] if c in df.columns])
    return df[[c for c in OHLCV if c in df.columns]]


# ─── VALIDASI ────────────────────────────────────────────────────
def validate(df, iv_ms=None, prev_len=None):
    """Kembalikan daftar masalah fatal. Kosong = lolos.

    Bolong antar bar tidak diperiksa di sini — cache 2019 memang punya 21 bolong
    sisa outage Binance, itu data asli dan permanen. Yang layak diteriakkan cuma
    bolong baru; itu diperiksa di _refresh() pada baris yang baru datang saja.
    """
    p = []
    if df is None or df.empty:
        return ["kosong"]
    missing = [c for c in OHLCV if c not in df.columns]
    if missing:
        p.append(f"kolom hilang: {missing}")
    extra = [c for c in df.columns if c not in OHLCV]
    if extra:
        p.append(f"kolom asing: {extra}")
    if not isinstance(df.index, pd.DatetimeIndex):
        p.append("index bukan datetime")
        return p
    if df.index.tz is None:
        p.append("index tanpa timezone")
    if not df.index.is_monotonic_increasing:
        p.append("index tidak monoton naik")
    ndup = int(df.index.duplicated().sum())
    if ndup:
        p.append(f"{ndup} timestamp duplikat")
    have = [c for c in OHLC if c in df.columns]
    if have:
        nnan = int(df[have].isna().sum().sum())
        if nnan:
            p.append(f"{nnan} NaN di OHLC")
    if len(have) == 4:
        bad = int((
            (df["low"] > df[["open", "close"]].min(axis=1))
            | (df["high"] < df[["open", "close"]].max(axis=1))
        ).sum())
        if bad:
            p.append(f"{bad} bar low/high tidak konsisten")
    now = pd.Timestamp.now(tz="UTC")
    if df.index[-1] > now + pd.Timedelta(minutes=1):
        p.append(f"bar masa depan: {df.index[-1]}")
    if prev_len is not None and len(df) < prev_len:
        p.append(f"baris menyusut {prev_len} -> {len(df)}")
    return p


def warn_new_gaps(df, iv_ms, since, label=""):
    """Teriak hanya untuk bolong di bar yang baru datang. Tidak menggagalkan."""
    if not iv_ms or since is None:
        return 0
    d = df.loc[df.index >= since].index.to_series().diff() \
        .dt.total_seconds().mul(1000).dropna()
    ngap = int((d != iv_ms).sum())
    if ngap:
        _warn(f"{label}{ngap} bolong antar bar BARU sejak {since} — cek Binance")
    return ngap


# ─── AMBIL DARI BINANCE ──────────────────────────────────────────
def fetch_klines(sym, tf_binance, start_ts, end_ts, iv_ms):
    url = "https://api.binance.com/api/v3/klines"
    rows = []
    cur = int(start_ts.timestamp() * 1000)
    end_ms = int(end_ts.timestamp() * 1000)
    step = 895 * iv_ms
    while cur < end_ms:
        nxt = min(cur + step, end_ms)
        r = requests.get(url, params={
            "symbol": sym, "interval": tf_binance,
            "startTime": cur, "endTime": nxt, "limit": 1000
        }, timeout=30).json()
        if not r:
            break
        rows.extend(r)
        cur = r[-1][0] + 1
        time.sleep(0.2)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=[
        "ot", "open", "high", "low", "close", "volume",
        "ct", "qv", "n", "tb", "tq", "ig"
    ])
    for c in OHLCV:
        df[c] = df[c].astype(float)
    df["ot"] = pd.to_datetime(df["ot"], unit="ms", utc=True)
    df = df.set_index("ot").sort_index()
    return df[OHLCV]


# ─── TULIS ATOMIK ────────────────────────────────────────────────
def atomic_write(df, path):
    """Tulis ke tmp lalu os.replace — pembaca lihat file lama utuh atau baru utuh.

    Yang lama disimpan jadi .prev lewat hardlink: satu generasi backup, nol salinan byte.
    """
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    os.close(fd)
    try:
        df.to_csv(tmp)
        if os.path.exists(path):
            prev = path + ".prev"
            if os.path.exists(prev):
                os.unlink(prev)
            os.link(path, prev)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ─── PINTU MASUK ─────────────────────────────────────────────────
def load_df(tf_dir, tf_binance, iv_ms, base=None, refresh=True, fallback_mult=3.0):
    """Cache siap pakai: refresh kalau basi, validasi, buang bar yang masih terbentuk.

    None kalau data tidak cukup (<50 bar) atau tidak ada cache sama sekali.
    Kalau proses lain sedang refresh, langsung pakai cache yang ada — konsumen
    butuh data tidak rusak, bukan data detik-terbaru.

    refresh=False → mode baca-saja: hak tulis dipegang cron fetcher tunggal.
    Tapi kalau cache sudah lewat `fallback_mult` x interval, konsumen refresh
    sendiri dan berteriak. Itu jaring pengaman kalau fetcher-nya mati: lebih baik
    lambat sekali-kali daripada semua konsumen jalan mulus di atas data basi.
    """
    path = cache_path(tf_dir, base)
    now = _dt.datetime.now(_dt.timezone.utc)

    df = read_cache(tf_dir, base=base, iv_ms=iv_ms, path=path)
    if df is None:
        df = pd.DataFrame()
        last_cached, age_s = None, 999999
    else:
        last_cached = df.index[-1]
        age_s = (now - last_cached).total_seconds()

    if refresh and age_s > iv_ms / 1000 * 0.5:
        df = _refresh(df, path, tf_binance, iv_ms, last_cached, now)
    elif not refresh and age_s > iv_ms / 1000 * fallback_mult:
        _warn(f"{tf_dir} basi {age_s / 60:.0f} menit dalam mode baca-saja — "
              f"fetcher tunggal diam? refresh darurat oleh konsumen")
        df = _refresh(df, path, tf_binance, iv_ms, last_cached, now)

    if df.empty:
        return None
    last_ct = df.index[-1] + _dt.timedelta(milliseconds=iv_ms)
    if now < last_ct and len(df) > 1:
        df = df.iloc[:-1]
    if len(df) < 50:
        return None
    return df


def _refresh(df, path, tf_binance, iv_ms, last_cached, now):
    """Fetch bar baru dan tukar file. Kembalikan df terpakai (baru kalau sukses)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lockp = path + ".lock"
    lockf = open(lockp, "a+")
    try:
        try:
            fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return df  # proses lain lagi refresh, pakai yang ada

        # Baca ulang di dalam kunci: proses lain mungkin baru saja menukar file.
        fresh = read_cache(None, iv_ms=iv_ms, path=path)
        if fresh is not None:
            df = fresh
            last_cached = df.index[-1]
            if (now - last_cached).total_seconds() <= iv_ms / 1000 * 0.5:
                return df

        # Mundur REHEAL_BARS, jangan mulai dari last_cached+1ms. Kode lama mulai
        # persis setelah bar terakhir, jadi bar yang tertulis saat masih terbentuk
        # tidak pernah dikoreksi — high/low/close-nya beku separuh jalan selamanya.
        fs = (last_cached - _dt.timedelta(milliseconds=iv_ms * REHEAL_BARS)) \
            if last_cached is not None else pd.Timestamp("2019-01-01", tz="UTC")
        new_df = fetch_klines(SYM, tf_binance, fs, now, iv_ms)
        if new_df.empty:
            return df

        # Data baru menang untuk bar yang beririsan — itu yang menyembuhkan bar beku.
        merged = pd.concat([df[~df.index.isin(new_df.index)], new_df]).sort_index() \
            if not df.empty else new_df

        # Jangan pernah simpan bar yang belum tutup. Ini akar bug di atas.
        closed = merged.index <= now - _dt.timedelta(milliseconds=iv_ms)
        merged = merged[closed]
        if merged.empty:
            return df

        # Bandingkan sesama bar tutup, kalau tidak cek anti-susut salah tuduh
        # sekali saat bar terbentuk yang dulu ikut tersimpan akhirnya dibuang.
        prev_closed = int((df.index <= now - _dt.timedelta(milliseconds=iv_ms)).sum()) \
            if not df.empty else None
        problems = validate(merged, iv_ms=iv_ms, prev_len=prev_closed)
        if problems:
            _warn(f"refresh {path} dibatalkan: {'; '.join(problems)}")
            return df  # pertahankan file lama

        warn_new_gaps(merged, iv_ms, last_cached, label=f"{os.path.basename(path)}: ")
        atomic_write(merged, path)
        return merged
    finally:
        try:
            fcntl.flock(lockf, fcntl.LOCK_UN)
        finally:
            lockf.close()
