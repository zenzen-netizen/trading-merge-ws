# U5Spring File Map

Tujuan:
- jawab cepat: kalau mau ubah X, buka file mana?
- bantu maintenance, tuning, dan audit

## 1. Mau paham strategi ini secara singkat
- `../README.md`
- `roadmap.md`
- `experiment-guide.md`
- `experiment-template.md`
- `templates/README.md`

## 1b. Mau nambah eksperimen baru tanpa merusak baseline
- `experiment-guide.md`
- `experiment-template.md`
- `templates/experiment-brief.md`
- `../01-research/chart-backtests/rsi-fractal-mhermes-be/README.md`
- `../02-thesis/setup-notes.md`

## 2. Mau lihat bukti riset mentah
- pool discovery snapshots: `../01-research/pool-discovery/snapshots/`
- backtest summary: `../01-research/chart-backtests/rsi-fractal-mhermes-be/summary.md`
- backtest full detail: `../01-research/chart-backtests/rsi-fractal-mhermes-be/full-report.md`
- trade level data: `../01-research/chart-backtests/rsi-fractal-mhermes-be/trade-journal.csv`
- OHLCV raw: `../01-research/chart-backtests/rsi-fractal-mhermes-be/ohlcv/`

## 3. Mau cek thesis inti
- high-level thesis: `../02-thesis/setup-notes.md`
- Meridian-specific thesis: `../02-thesis/meridian-thesis.md`

## 4. Mau ubah deploy/skip doctrine
- full operator rules: `../03-operator/playbook.md`
- compact operator rules: `../03-operator/playbook-compact.md`

## 5. Mau ubah draft config Meridian
- config draft: `../04-meridian/config-draft.md`

## 6. Mau ubah mapping profile baseline / experiment / sandbox
- profile mapping: `../04-meridian/profile-mapping.md`

## 7. Mau ubah promptNotes / wording operator nudge
- promptnotes: `../04-meridian/promptnotes.md`

## 8. Mau cari JSON siap copy
- ready json docs: `../04-meridian/ready-jsons.md`
- ready-load files: `../05-payloads/ready-load-profiles/`

## 9. Mau pilih payload yang tepat
- baseline comparator: `../05-payloads/ready-load-profiles/baseline.user-config.json`
- dual-side experiment: `../05-payloads/ready-load-profiles/dualside-exp.user-config.json`
- manual sandbox: `../05-payloads/ready-load-profiles/manual-sandbox.user-config.json`

## 10. Mau telusuri asal file lama
- naming + architecture concept: `../99-archive/naming-concept.md`
- first preview: `../99-archive/structure-preview.md`
- final mock tree: `../99-archive/mock-folder-tree-final.md`

## 10b. Mau cek aturan propagasi hasil eksperimen
- eksperimen sehat & flow propagasi: `experiment-guide.md`
- template brief eksperimen: `experiment-template.md`
- comparison note template: `templates/comparison-note.md`
- thesis addendum template: `templates/thesis-addendum.md`
- reasoning inti: `../02-thesis/setup-notes.md`
- doctrine operator: `../03-operator/playbook.md`
- translasi Meridian: `../04-meridian/profile-mapping.md`

## 11. Old path to new path
- `METEORA_SETUP_DEPLOYMENT_NOTES.md` -> `../02-thesis/setup-notes.md`
- `MERIDIAN_PRESET_THESIS.md` -> `../02-thesis/meridian-thesis.md`
- `MERIDIAN_OPERATOR_PLAYBOOK.md` -> `../03-operator/playbook.md`
- `MERIDIAN_OPERATOR_PLAYBOOK_COMPACT.md` -> `../03-operator/playbook-compact.md`
- `MERIDIAN_CONFIG_DRAFT.md` -> `../04-meridian/config-draft.md`
- `MERIDIAN_PROFILE_MAPPING.md` -> `../04-meridian/profile-mapping.md`
- `MERIDIAN_PROMPTNOTES_FINAL.md` -> `../04-meridian/promptnotes.md`
- `MERIDIAN_READY_TO_APPLY_JSONS.md` -> `../04-meridian/ready-jsons.md`
- `READY_LOAD_PROFILES/*.json` -> `../05-payloads/ready-load-profiles/*.json`
- `POOL_DISCOVERY/` -> `../01-research/pool-discovery/` and `../01-research/chart-backtests/`
