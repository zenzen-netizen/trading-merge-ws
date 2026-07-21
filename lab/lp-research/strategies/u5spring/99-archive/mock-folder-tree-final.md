# U5Spring — Mock Final Folder Tree

Ini mock final.
Belum execute move.
Belum rename real file.
Belum sentuh bot.

Tujuan:
- kasih bentuk akhir yang lebih polished
- pakai nama file pendek final
- jadi blueprint rapi sebelum migration beneran

## 1. Final root concept

```text
backtests/METEORA/
  strategies/
    u5spring/
      README.md
      00-index/
        roadmap.md
        file-map.md
      01-research/
        README.md
        pool-discovery/
          README.md
          snapshots/
            top20-sol-30m-fee-tvl-age15h.json
            top20-sol-30m-fee-tvl-age15h.md
            top10-sol-30m-fee-tvl-age15h.md
            top5-sol-30m-fee-tvl-age15h.md
            top5-sol-30m-fee-tvl.md
            top5-summary.md
        chart-backtests/
          rsi-fractal-mhermes-be/
            README.md
            metric-definitions.md
            summary.csv
            summary.md
            report.md
            full-report.md
            trade-journal.csv
            ohlcv/
              ohlcv_burger-SOL_1m.csv
              ohlcv_burger-SOL_5m.csv
              ohlcv_burger-SOL_15m.csv
              ...
      02-thesis/
        README.md
        setup-notes.md
        meridian-thesis.md
      03-operator/
        README.md
        playbook.md
        playbook-compact.md
      04-meridian/
        README.md
        config-draft.md
        profile-mapping.md
        promptnotes.md
        ready-jsons.md
      05-payloads/
        README.md
        ready-load-profiles/
          README.md
          baseline.user-config.json
          dualside-exp.user-config.json
          manual-sandbox.user-config.json
      99-archive/
        naming-concept.md
        structure-preview.md
```

## 2. Why this version more polished

Perbaikan dari preview awal:
- ada root `README.md`
- ada `00-index/` buat peta navigasi
- file names dipendekin lebih konsisten
- `pool-discovery` dipisah lagi ke `snapshots/`
- backtest csv besar masuk subfolder lebih jelas
- payload json names lebih pendek
- archive jelas terpisah

## 3. Final short file names

## 3.1 Thesis

```text
02-thesis/
  setup-notes.md
  meridian-thesis.md
```

Kenapa:
- singkat
- jelas
- tidak redundant karena context sudah kebawa folder

## 3.2 Operator

```text
03-operator/
  playbook.md
  playbook-compact.md
```

Kenapa:
- paling natural
- gampang dipanggil
- tidak perlu prefix panjang lagi

## 3.3 Meridian

```text
04-meridian/
  config-draft.md
  profile-mapping.md
  promptnotes.md
  ready-jsons.md
```

Kenapa:
- langsung kebaca fungsi file
- cukup pendek
- tetap jelas

## 3.4 Payloads

```text
05-payloads/
  ready-load-profiles/
    baseline.user-config.json
    dualside-exp.user-config.json
    manual-sandbox.user-config.json
```

Kenapa:
- pendek
- langsung kebaca role file
- tetap satu family

## 4. Exact old-to-new naming mock

### Root docs sekarang

- `METEORA_SETUP_DEPLOYMENT_NOTES.md`
  becomes
  `strategies/u5spring/02-thesis/setup-notes.md`

- `MERIDIAN_PRESET_THESIS.md`
  becomes
  `strategies/u5spring/02-thesis/meridian-thesis.md`

- `MERIDIAN_OPERATOR_PLAYBOOK.md`
  becomes
  `strategies/u5spring/03-operator/playbook.md`

- `MERIDIAN_OPERATOR_PLAYBOOK_COMPACT.md`
  becomes
  `strategies/u5spring/03-operator/playbook-compact.md`

- `MERIDIAN_CONFIG_DRAFT.md`
  becomes
  `strategies/u5spring/04-meridian/config-draft.md`

- `MERIDIAN_PROFILE_MAPPING.md`
  becomes
  `strategies/u5spring/04-meridian/profile-mapping.md`

- `MERIDIAN_PROMPTNOTES_FINAL.md`
  becomes
  `strategies/u5spring/04-meridian/promptnotes.md`

- `MERIDIAN_READY_TO_APPLY_JSONS.md`
  becomes
  `strategies/u5spring/04-meridian/ready-jsons.md`

- `STRATEGY_NAMING_CONCEPT.md`
  becomes
  `strategies/u5spring/99-archive/naming-concept.md`

- `U5SPRING_STRUCTURE_PREVIEW.md`
  becomes
  `strategies/u5spring/99-archive/structure-preview.md`

### Payload folder sekarang

- `READY_LOAD_PROFILES/README.md`
  becomes
  `strategies/u5spring/05-payloads/ready-load-profiles/README.md`

- `READY_LOAD_PROFILES/meteora-baseline.user-config.json`
  becomes
  `strategies/u5spring/05-payloads/ready-load-profiles/baseline.user-config.json`

- `READY_LOAD_PROFILES/meteora-dualside-exp.user-config.json`
  becomes
  `strategies/u5spring/05-payloads/ready-load-profiles/dualside-exp.user-config.json`

- `READY_LOAD_PROFILES/meteora-manual-sandbox.user-config.json`
  becomes
  `strategies/u5spring/05-payloads/ready-load-profiles/manual-sandbox.user-config.json`

### Research folder sekarang

- `POOL_DISCOVERY/top20_sol_30m_fee_tvl_age15h.json`
  becomes
  `strategies/u5spring/01-research/pool-discovery/snapshots/top20-sol-30m-fee-tvl-age15h.json`

- `POOL_DISCOVERY/top20_sol_30m_fee_tvl_age15h.md`
  becomes
  `strategies/u5spring/01-research/pool-discovery/snapshots/top20-sol-30m-fee-tvl-age15h.md`

- `POOL_DISCOVERY/top10_sol_30m_fee_tvl_age15h.md`
  becomes
  `strategies/u5spring/01-research/pool-discovery/snapshots/top10-sol-30m-fee-tvl-age15h.md`

- `POOL_DISCOVERY/top5_sol_30m_fee_tvl_age15h.md`
  becomes
  `strategies/u5spring/01-research/pool-discovery/snapshots/top5-sol-30m-fee-tvl-age15h.md`

- `POOL_DISCOVERY/top5_sol_30m_fee_tvl.md`
  becomes
  `strategies/u5spring/01-research/pool-discovery/snapshots/top5-sol-30m-fee-tvl.md`

- `POOL_DISCOVERY/top5_summary.md`
  becomes
  `strategies/u5spring/01-research/pool-discovery/snapshots/top5-summary.md`

- `POOL_DISCOVERY/README.md`
  becomes
  `strategies/u5spring/01-research/pool-discovery/README.md`

- `POOL_DISCOVERY/rsi_fractal_backtest_mhermes_be/`
  becomes
  `strategies/u5spring/01-research/chart-backtests/rsi-fractal-mhermes-be/`

## 5. Recommended small helper docs

Biar folder enak dipakai, aku sarankan nanti ada 3 README kecil tambahan.

### 5.1 Root README

Isi singkat:
- what is U5Spring
- thesis one-liner
- folder guide
- where to start reading

### 5.2 `00-index/roadmap.md`

Isi singkat:
- urutan baca
- research -> thesis -> operator -> meridian -> payloads

### 5.3 `00-index/file-map.md`

Isi singkat:
- old path -> new path
- sangat membantu saat migration

## 6. Suggested read order after cleanup

Kalau folder final jadi, urutan baca ideal:

1. `README.md`
2. `00-index/roadmap.md`
3. `02-thesis/setup-notes.md`
4. `02-thesis/meridian-thesis.md`
5. `03-operator/playbook.md`
6. `04-meridian/config-draft.md`
7. `04-meridian/ready-jsons.md`
8. `05-payloads/ready-load-profiles/README.md`

## 7. Naming style rule for future siblings

Kalau nanti ada strategy lain:
- pakai folder pendek lowercase kebab or flat-token
- pakai layer sama
- pakai file names pendek sama

Contoh sibling:
```text
strategies/
  u5spring/
  dipforge/
  trendvault/
```

Consistency rules:
- thesis always in `02-thesis/`
- operator always in `03-operator/`
- Meridian translation always in `04-meridian/`
- ready-load payload always in `05-payloads/`

## 8. Final opinion

Versi ini sudah paling clean.

Yang paling bagus dari mock ini:
- tidak terlalu verbose
- hierarchy kebaca langsung
- file names final pendek
- tetap scalable
- future strategy lain gampang ikut pola

Kalau nanti migrate beneran, aku sarankan pakai mock ini sebagai source of truth.