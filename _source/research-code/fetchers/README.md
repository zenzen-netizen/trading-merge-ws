# FETCHERS — data OHLCV

Pengambil kline dari exchange publik (no API key).
Semua filter unclosed candle (drop candle belum close).

## File
- `data_fetcher.py`   — Binance (spot + futures/perp).
                         Dipakai oleh: label_window_1d.py,
                         archive/fold_helpers/fbf_smi_daily_tester.py.
- `bybit_fetcher.py`  — Bybit (perp + spot), buat pair
                         TradeFi e.g. XAUUSDT.
                         Standalone, interval map Binance→Bybit.
- `mt5_tradfi.py`    — Bybit TradFi via MetaTrader 5.
                         Auto-detect gold symbol (XAUUSD+, XAUUSD, dll).
                         Return quote + OHLC (JSON + DataFrame).

## Dependency
- `MetaTrader5` Python package + MT5 terminal login aktif.
- `pandas` untuk frame output.

## Usage
```python
import sys; sys.path.insert(0, "fetchers")
import data_fetcher as df
df.get_klines(...)   # lihat fungsi di file
```
