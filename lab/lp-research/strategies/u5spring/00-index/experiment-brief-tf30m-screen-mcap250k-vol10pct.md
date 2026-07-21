# U5Spring Experiment Brief — TF30m Backtest + Screen MCAP250k + Vol10pct

Tujuan file ini:
- memulai eksperimen nyata pertama dengan guardrail U5Spring yang sudah disepakati
- menjaga supaya eksperimen tetap berbasis thesis U5Spring, bukan drift ke thesis lain
- memberi brief yang cukup jelas agar Hermes/agent lain bisa lanjut kerja tanpa merusak baseline canonical

## 1. Identity
- Experiment name: `rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct`
- Date: 2026-07-19
- Owner / agent: Hermes-Server
- Status: `re-executed after pool-name collision fix`

## 2. User intent
- What the user wants:
  - tetap memakai base U5Spring
  - rule utama, SL/TP, dan metric family tetap ikut dibawa
  - screening pool Meteora tetap sourced dari `timeframe=30m`
  - tambah filter screening pool
  - uji `30m` sebagai salah satu timeframe backtest
- Non-negotiables from user:
  - jangan rusak tatanan U5Spring yang sudah ada
  - baseline canonical tetap jadi pembanding resmi
  - eksperimen tetap masih dianggap varian U5Spring
- Output expected from this experiment:
  - satu cabang research baru yang bisa dibandingkan lawan baseline
  - evaluasi apakah filter pool lebih ketat membantu kualitas candidate
  - evaluasi apakah `30m` layak sebagai salah satu TF backtest

## 3. Main question
- Main question:
  - Apakah varian U5Spring yang memakai universe screening Meteora `30m`, lalu menambah filter minimum market cap 250k dan minimum volume/tvl ratio 10%, sambil menguji `30m` sebagai salah satu timeframe backtest, bisa meningkatkan kualitas candidate tanpa merusak identity baseline?
- Why this matters:
  - baseline discovery lama masih fee/TVL-first
  - user ingin kualitas pool lebih dijaga lewat mcap dan volume floor
  - user juga ingin melihat apakah `30m` bisa diuji sebagai timeframe backtest tambahan

## 4. Base rule to preserve
- Strategy family: `u5spring`
- Canonical baseline: `../01-research/chart-backtests/rsi-fractal-mhermes-be/`
- Identity that must stay fixed:
  - [x] pool quality first
  - [x] reclaim timing second
  - [x] deploy expression third
  - [x] 5m baseline comparator remains visible
  - [x] 15m baseline comparator remains visible
  - [x] spot-first baseline remains comparator
  - [x] protection mindset near `BE1 style`
  - [x] this is still a U5Spring variant, not a new thesis

## 5. Scope
- What changes:
  - universe screening Meteora tetap `timeframe=30m`
  - tambah filter screening pool:
    - minimum market cap = 250000
    - minimum volume/tvl ratio = 0.10
  - tambah `30m` sebagai timeframe backtest candidate
- What stays fixed:
  - entry logic
  - fractal confirmation logic
  - TP logic
  - SL families
  - BE families
  - metrics structure
- Variables under test:
  - kualitas universe hasil screen baru
  - kelayakan `30m` sebagai timeframe backtest
- What is explicitly NOT being changed:
  - tidak langsung ganti thesis ke thesis lain
  - tidak langsung ganti doctrine/operator/Meridian/payload
- Research-only or potentially operational later:
  - research-only dulu
  - hanya naik level kalau evidence kuat

## 6. Two-layer meaning of 30m
Catatan penting agar agent lain tidak salah paham:
1. `30m` pada layer screening discovery:
   - universe pool tetap sourced dari Meteora `timeframe=30m`
2. `30m` pada layer backtest:
   - `30m` juga diuji sebagai salah satu TF backtest

Jadi `30m` hidup di dua layer berbeda, bukan salah satu saja.

## 7. Paths
- Baseline comparator path:
  - `../01-research/chart-backtests/rsi-fractal-mhermes-be/`
- New experiment folder path:
  - `../01-research/chart-backtests/rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct/`
- Comparison note path:
  - `../01-research/chart-backtests/comparisons/baseline-vs-tf30m-screen-mcap250k-vol10pct.md`
- Auxiliary follow-up path:
  - `../01-research/chart-backtests/rsi-fractal-mhermes-be-screen-mcap250k-vol10pct-usabletf/`
- Any downstream thesis note path if needed:
  - `../02-thesis/timeframe-screening-extension-notes.md`

## 8. Execution status observed
- Integrity correction before rerun:
  - earlier 2026-07-19 artifacts were found to have a data-keying bug
  - same-name pools could collide because cache filenames and summary grouping used pool name instead of `pool_address`
  - baseline + experiment were patched and rerun cleanly before keeping the current artifacts
- Discovery universe berhasil dibangun dari Meteora screening `30m` dengan filter baru
- Backtest variant berhasil mencoba TF: `1m`, `5m`, `15m`, `30m`
- Hasil penting:
  - `1m`, `5m`, `15m` menghasilkan row summary
  - `30m` fetch path berhasil dicoba, tetapi seri candle terlalu pendek untuk EMA50 + fractal warmup
  - akibatnya `30m` tidak menghasilkan row final di `summary.csv`

## 9. Required artifacts
- [x] folder eksperimen sibling baru dibuat di `../01-research/chart-backtests/`
- [x] `report.md`
- [x] `summary.csv`
- [x] `trade-journal.csv`
- [x] discovery snapshot variant
- [x] comparison note
- [x] note yang memisahkan pembacaan `screening effect` vs `30m backtest effect`

## 10. Metrics / evaluation
- Primary metrics:
  - positive family-best rows per TF
  - median family-best `sum_R` per TF
  - quality/breadth tradeoff
- Secondary metrics:
  - total trade count
  - pool breadth
  - resolved win rate
  - BE dependence
  - apakah `30m` menghasilkan data warmup-ready
- What would count as improvement:
  - filtered universe membaik tanpa merusak comparability
  - `30m` menghasilkan dataset yang cukup untuk diuji sebagai TF backtest
- What would count as drift or failure:
  - candidate terlalu sedikit / terlalu bias
  - hasil memburuk atau jadi tidak comparable
  - `30m` gagal menghasilkan data yang layak uji

## 11. Current verdict after execution
- Screening effect:
  - promising pada `1m`, `5m`, `15m`
- `30m` backtest effect:
  - belum bisa divalidasi, karena data depth belum cukup
- Jadi eksperimen ini valid sebagai:
  - screening experiment yang juga mencoba `30m` backtest
- Tetapi belum valid sebagai:
  - proof bahwa `30m` backtest bekerja

## 12. Guardrails
- [x] do not overwrite canonical baseline
- [x] do not work directly inside the baseline folder
- [x] do not touch operator/Meridian/payload before evidence is strong
- [x] keep baseline comparator visible
- [x] explicitly document assumption that `min vol 10%` means `volume_tvl_ratio >= 0.10`
- [x] explicitly document that screening `30m` and backtest `30m` are different layers

## 13. Execution notes for future agent
Saat melanjutkan eksperimen ini, agent harus:
1. pertahankan screening Meteora `timeframe=30m`
2. pertahankan filter baru:
   - SOL pairs only
   - exclude USDC
   - age >= 15h
   - sort by fee_active_tvl_ratio desc
   - add min market cap 250k
   - add min volume/tvl ratio 0.10
3. pertahankan target backtest TF:
   - `1m`, `5m`, `15m`, `30m`
4. dokumentasikan dengan tegas apakah `30m` backtest benar-benar testable atau belum
5. jangan ubah doctrine/operator/Meridian sebelum evidence compare selesai

## 14. Quick instruction block for another agent
```text
Use U5Spring base rules.
Do not overwrite canonical baseline.
Create/use sibling research run named:
- rsi-fractal-mhermes-be-tf30m-screen-mcap250k-vol10pct

Interpret 30m in TWO layers:
1. screening discovery stays Meteora timeframe=30m
2. backtest should also try 30m as one TF candidate

Add screens:
- min market cap 250000
- min volume/tvl ratio 0.10

Keep visible:
- baseline 5m comparator
- baseline 15m comparator
- existing exit/SL/metric family for comparability

Required outputs:
- discovery delta vs baseline
- full experiment artifacts
- comparison note vs baseline
- explicit read on screening effect vs 30m backtest effect

Only propagate upward if evidence is strong.
```
