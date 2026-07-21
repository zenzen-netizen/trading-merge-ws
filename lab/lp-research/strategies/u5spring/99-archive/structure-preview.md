# U5Spring — Structure Preview

Ini preview saja.
Belum move file.
Belum rename file.
Belum sentuh bot.

Tujuan:
- kasih gambaran kalau semua artefak sekarang dirapikan ke family strategy `u5spring`
- nunjukin file lama masuk ke slot mana
- bikin next refactor nanti tinggal eksekusi, bukan mikir dari nol

## 1. Nama family

Nama strategy family:
- `u5spring`

Makna kerja:
- `u5` = identitas ringkas, khas, gampang diingat
- `spring` = reclaim / bounce / continuation feel
- cukup branded, tapi masih pendek

## 2. Struktur target

```text
backtests/METEORA/
  strategies/
    u5spring/
      01-research/
        pool-discovery/
        chart-backtests/
        raw-reports/
      02-thesis/
        setup-deployment-notes.md
        meridian-preset-thesis.md
      03-operator/
        meridian-operator-playbook.md
        meridian-operator-playbook-compact.md
      04-meridian/
        meridian-config-draft.md
        meridian-profile-mapping.md
        meridian-promptnotes-final.md
        meridian-ready-to-apply-jsons.md
      05-payloads/
        ready-load-profiles/
          README.md
          meteora-baseline.user-config.json
          meteora-dualside-exp.user-config.json
          meteora-manual-sandbox.user-config.json
      99-archive/
        strategy-naming-concept.md
```

## 3. Mapping file lama ke struktur baru

## 3.1 Thesis layer

File sekarang:
- `METEORA_SETUP_DEPLOYMENT_NOTES.md`
- `MERIDIAN_PRESET_THESIS.md`

Masuk jadi:
```text
02-thesis/
  setup-deployment-notes.md
  meridian-preset-thesis.md
```

Peran:
- source thesis konseptual
- jembatan dari backtest ke logika Meridian

## 3.2 Operator layer

File sekarang:
- `MERIDIAN_OPERATOR_PLAYBOOK.md`
- `MERIDIAN_OPERATOR_PLAYBOOK_COMPACT.md`

Masuk jadi:
```text
03-operator/
  meridian-operator-playbook.md
  meridian-operator-playbook-compact.md
```

Peran:
- doctrine operator
- deploy / skip / premium / experiment discipline

## 3.3 Meridian translation layer

File sekarang:
- `MERIDIAN_CONFIG_DRAFT.md`
- `MERIDIAN_PROFILE_MAPPING.md`
- `MERIDIAN_PROMPTNOTES_FINAL.md`
- `MERIDIAN_READY_TO_APPLY_JSONS.md`

Masuk jadi:
```text
04-meridian/
  meridian-config-draft.md
  meridian-profile-mapping.md
  meridian-promptnotes-final.md
  meridian-ready-to-apply-jsons.md
```

Peran:
- translasi thesis ke config
- translasi doctrine ke profile
- translasi ide ke JSON siap pakai

## 3.4 Payload layer

Folder sekarang:
- `READY_LOAD_PROFILES/`

Masuk jadi:
```text
05-payloads/
  ready-load-profiles/
    README.md
    meteora-baseline.user-config.json
    meteora-dualside-exp.user-config.json
    meteora-manual-sandbox.user-config.json
```

Peran:
- file paling dekat ke `siap load`
- tetap non-destructive
- tetap bukan apply langsung

## 3.5 Research layer

Sumber sekarang:
- `POOL_DISCOVERY/`
- report backtest chart
- csv summary
- trade journal
- ohlcv per pair / timeframe

Masuk jadi kira-kira:
```text
01-research/
  pool-discovery/
    top20_sol_30m_fee_tvl_age15h.json
    top20_sol_30m_fee_tvl_age15h.md
    top10_sol_30m_fee_tvl_age15h.md
    top5_sol_30m_fee_tvl_age15h.md
    top5_sol_30m_fee_tvl.md
    top5_summary.md
    README.md

  chart-backtests/
    rsi_fractal_backtest_mhermes_be/
      summary.csv
      summary.md
      report.md
      full_report.md
      METRIC_DEFINITIONS.md
      trade_journal.csv
      ohlcv_*.csv

  raw-reports/
    (opsional, kalau nanti ada export / notebook / scratch lain)
```

Peran:
- semua bahan mentah
- semua evidence backtest
- semua artefak audit

## 3.6 Archive / meta layer

File sekarang:
- `STRATEGY_NAMING_CONCEPT.md`

Masuk jadi:
```text
99-archive/
  strategy-naming-concept.md
```

Peran:
- meta-doc
- keputusan naming / struktur
- tidak ikut alur operasional harian

## 4. Gambaran tree lengkap dengan isi sekarang

```text
backtests/METEORA/
  strategies/
    u5spring/
      01-research/
        pool-discovery/
          README.md
          top20_sol_30m_fee_tvl_age15h.json
          top20_sol_30m_fee_tvl_age15h.md
          top10_sol_30m_fee_tvl_age15h.md
          top5_sol_30m_fee_tvl_age15h.md
          top5_sol_30m_fee_tvl.md
          top5_summary.md

        chart-backtests/
          rsi_fractal_backtest_mhermes_be/
            METRIC_DEFINITIONS.md
            summary.csv
            summary.md
            report.md
            full_report.md
            trade_journal.csv
            ohlcv_*.csv

      02-thesis/
        setup-deployment-notes.md
        meridian-preset-thesis.md

      03-operator/
        meridian-operator-playbook.md
        meridian-operator-playbook-compact.md

      04-meridian/
        meridian-config-draft.md
        meridian-profile-mapping.md
        meridian-promptnotes-final.md
        meridian-ready-to-apply-jsons.md

      05-payloads/
        ready-load-profiles/
          README.md
          meteora-baseline.user-config.json
          meteora-dualside-exp.user-config.json
          meteora-manual-sandbox.user-config.json

      99-archive/
        strategy-naming-concept.md
```

## 5. Kenapa susunan ini enak

Karena alurnya kebaca lurus:
- research
- thesis
- operator doctrine
- Meridian translation
- payload

Jadi orang buka folder langsung paham:
- data mentah di mana
- reasoning di mana
- aturan operator di mana
- config translation di mana
- file siap load di mana

## 6. Naming style file setelah pindah

Aku sarankan setelah masuk folder `u5spring`, nama file dipendekin.
Tidak perlu semua prefix `MERIDIAN_` / `METEORA_` lagi.

Contoh:
- `METEORA_SETUP_DEPLOYMENT_NOTES.md`
  jadi `setup-deployment-notes.md`
- `MERIDIAN_PRESET_THESIS.md`
  jadi `meridian-preset-thesis.md`
- `MERIDIAN_CONFIG_DRAFT.md`
  jadi `meridian-config-draft.md`

Kenapa:
- context sudah kebawa oleh folder
- nama file jadi lebih bersih
- tidak redundant

## 7. Rule buat strategy lain nanti

Kalau nanti ada metode lain, bikin sibling folder setara:

```text
backtests/METEORA/strategies/
  u5spring/
  dipforge/
  trendvault/
```

Lalu tiap family wajib punya pola mirip:
- `01-research`
- `02-thesis`
- `03-operator`
- `04-meridian`
- `05-payloads`

Jadi repo tetap konsisten.

## 8. Bottom line

Kalau pakai `u5spring`, file-file yang sudah ada sekarang sudah cukup lengkap buat langsung jadi satu family utuh.

Makna layer:
- `01-research` = evidence
- `02-thesis` = reasoning
- `03-operator` = doctrine
- `04-meridian` = translation
- `05-payloads` = ready-load artifacts

Jadi langkah berikut nanti tinggal:
- bikin folder final
- pindahkan file sesuai mapping
- pendekkan nama file
- update README/index kecil kalau perlu
