# LIB — helper scripts (standalone CLI)

Semua dijalankan via CLI: `python3 lib/<file>.py <args>`.
Tidak diimport oleh engine backtest (standalone).

## File
- `format_trade.py`        — format journal → teks trade
                             (cari TP/SL terbaru per mode).
- `format_trade_exact.py`  — cari entry terbaru, fetch kline
                             Binance buat cek exact time/price.
- `extract_last_entry.py`  — print detail entry_date terbaru
                             dari journal + candle sekitarnya.
- `extract_exact.py`       — ekstrak field exact dari journal.

## Related (di root, bukan lib/)
- `label_window_1d.py` + `label_window_1d.csv`
  — label per-bar window 2026 (cross-check TV).
  Pakai fetchers/data_fetcher + smi_pro + fbf_v11.
