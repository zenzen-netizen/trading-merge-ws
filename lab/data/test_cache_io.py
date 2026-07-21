"""Self-check cache_io. Jalankan: python3 test_cache_io.py

Tidak menyentuh cache asli — semua di folder sementara. Tidak ada jaringan:
fetch_klines diganti stub.
"""

import os
import sys
import time
import signal
import hashlib
import tempfile
import multiprocessing as mp

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache_io

IV = 1800000  # 30m


def mkdf(n, start="2019-01-01", freq="30min"):
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC", name="ot")
    base = np.arange(n, dtype=float) + 100.0
    return pd.DataFrame({
        "open": base, "high": base + 1, "low": base - 1,
        "close": base, "volume": base,
    }, index=idx)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def test_validate():
    assert validate_ok(mkdf(100))

    d = mkdf(100).copy()
    d.iloc[5, d.columns.get_loc("close")] = np.nan
    assert "NaN" in " ".join(cache_io.validate(d))

    d = mkdf(100).copy()
    d.iloc[5, d.columns.get_loc("low")] = 1e9
    assert "low/high" in " ".join(cache_io.validate(d))

    d = pd.concat([mkdf(100), mkdf(100).iloc[:1]])
    assert "duplikat" in " ".join(cache_io.validate(d))

    d = mkdf(100).iloc[::-1]
    assert "monoton" in " ".join(cache_io.validate(d))

    d = mkdf(100, start=pd.Timestamp.now(tz="UTC"))
    assert "masa depan" in " ".join(cache_io.validate(d))

    # anti-susut
    assert "menyusut" in " ".join(cache_io.validate(mkdf(50), prev_len=100))
    assert not cache_io.validate(mkdf(150), prev_len=100)

    d = mkdf(100).copy()
    d["asing"] = 1
    assert "asing" in " ".join(cache_io.validate(d))
    print("ok validate")


def validate_ok(d):
    p = cache_io.validate(d)
    assert not p, p
    return True


def test_normalize_vol():
    """Cache asli punya kolom 'volume' dan 'vol' saling isi — harus digabung."""
    d = mkdf(10)
    d["vol"] = np.nan
    d.loc[d.index[5:], "vol"] = d.loc[d.index[5:], "volume"]
    d.loc[d.index[5:], "volume"] = np.nan
    out = cache_io._normalize(d)
    assert list(out.columns) == cache_io.OHLCV, out.columns
    assert out["volume"].isna().sum() == 0
    assert not cache_io.validate(out)
    print("ok normalize vol->volume")


def test_atomic_and_prev():
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "c.csv")
        cache_io.atomic_write(mkdf(100), p)
        h1 = md5(p)
        cache_io.atomic_write(mkdf(150), p)
        assert os.path.exists(p + ".prev")
        assert md5(p + ".prev") == h1, "backup satu generasi harus versi lama"
        assert len(pd.read_csv(p)) == 150
        assert not [f for f in os.listdir(t) if f.endswith(".tmp")], "tmp yatim"
    print("ok atomic write + .prev")


def test_read_corrupt():
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "c.csv")
        cache_io.atomic_write(mkdf(100), p)
        raw = open(p).read()
        open(p, "w").write(raw[: len(raw) // 2])  # potong di tengah
        try:
            cache_io.read_cache(None, path=p)
            raise AssertionError("CSV terpotong lolos tanpa terdeteksi")
        except cache_io.CacheCorrupt:
            pass
        except pd.errors.ParserError:
            pass
    print("ok deteksi file terpotong")


# ─── uji tabrakan: 3 proses refresh TF sama ──────────────────────
def _worker(path, out):
    def stub(sym, tfb, start, end, iv):
        time.sleep(0.3)  # perlebar jendela tabrakan
        return mkdf(300)
    cache_io.fetch_klines = stub
    try:
        df = cache_io.load_df("30m", "30m", IV, base=os.path.dirname(os.path.dirname(path)))
        out.put(("ok", len(df) if df is not None else 0))
    except Exception as e:
        out.put(("err", repr(e)))


def test_concurrent(rounds=10):
    for r in range(rounds):
        with tempfile.TemporaryDirectory() as t:
            d = os.path.join(t, "30m")
            os.makedirs(d)
            p = cache_io.cache_path("30m", base=t)
            cache_io.atomic_write(mkdf(200), p)
            q = mp.Queue()
            ps = [mp.Process(target=_worker, args=(p, q)) for _ in range(3)]
            for x in ps:
                x.start()
            for x in ps:
                x.join(30)
            res = [q.get() for _ in range(3)]
            assert all(s == "ok" for s, _ in res), res
            final = cache_io.read_cache("30m", base=t, iv_ms=IV)
            assert not cache_io.validate(final, iv_ms=IV), cache_io.validate(final)
            assert len(final) >= 200, f"cache menyusut: {len(final)}"
            assert not [f for f in os.listdir(d) if f.endswith(".tmp")], "tmp yatim"
    print(f"ok tabrakan 3 proses x{rounds} — file akhir selalu utuh")


# ─── uji mati di tengah tulis ────────────────────────────────────
def _slow_writer(path):
    cache_io.atomic_write(mkdf(400000), path)  # cukup besar untuk dibunuh di tengah


def test_kill_mid_write():
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "c.csv")
        cache_io.atomic_write(mkdf(100), p)
        before = md5(p)
        proc = mp.Process(target=_slow_writer, args=(p,))
        proc.start()
        time.sleep(0.35)
        os.kill(proc.pid, signal.SIGKILL)
        proc.join(10)
        assert md5(p) == before, "file asli berubah setelah proses dibunuh"
        assert len(cache_io.read_cache(None, path=p)) == 100
    print("ok mati di tengah tulis — file asli utuh")


if __name__ == "__main__":
    test_validate()
    test_normalize_vol()
    test_atomic_and_prev()
    test_read_corrupt()
    test_kill_mid_write()
    test_concurrent()
    print("\nSEMUA LOLOS")
