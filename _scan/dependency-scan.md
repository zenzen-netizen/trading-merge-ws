# Dependency Scan — pre-merge snapshot

Scrubbed. Names/paths only, zero secret content.

## crontab -l

```
# Meridian daily backup -> 00:00 WIB (= 01:00 server-local Asia/Shanghai, UTC+8). CRON_TZ tak didukung di sini.
0 1 * * * /home/ubuntu/meridianzen/backup.sh  >> /home/ubuntu/meridianzen-backups/cron.log 2>&1
0 1 * * * /home/ubuntu/meridianzen2/backup.sh >> /home/ubuntu/meridianzen2-backups/cron.log 2>&1
```

## pm2 (pruned: name | cwd | script — env/args dropped)

```
meridian                  | /home/ubuntu/meridianzen      | /home/ubuntu/meridianzen/index.js
meridian-v3               | /home/ubuntu/meridianzen2     | /home/ubuntu/meridianzen2/index.js
meridian-meridianzenbot3  | /home/ubuntu/meridianzen      | /home/ubuntu/meridianzen/index.js
meridian-main-zenpack84   | /home/ubuntu/meridianzen-pack | /home/ubuntu/meridianzen-pack/index.js
```

Note: all pm2 processes + cron run against `meridianzen*` dirs, which are NOT
copied into this staging repo.

## Cache consumers (file names only)

Single-writer cache is `cache_io.py`; consumers below are read-only per convention.

```
lab/data/cache_io.py                         # writer (canonical)
lab/data/test_cache_io.py
lab/data/fetch_ohlcv.py
lab/indicators/python/new_set_v1_20260714/robust_momcand.py
lab/indicators/python/new_set_v1_20260714/atr_percentage.py
lab/indicators/python/new_set_v1_20260714/rsi_pro_enhanced.py
_source/research-code/indicators/cache_io.py
_source/research-code/indicators/test_cache_io.py
_source/research-code/backtests/BTCUSDT/SETUP1/fetch_data_tf.py
_source/research-code/backtests/BTCUSDT/SETUP1/1H/_whatif_reverse_long.py
_source/research-code/backtests/BTCUSDT/SETUP1/_archive_v2b/*.py   # legacy archive
```
