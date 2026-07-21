# METEORA Legacy Map

Tujuan:
- tandai mana workspace canonical baru
- tandai mana file/folder root lama yang masih dipertahankan sementara
- bantu transisi tanpa bikin bingung

## Canonical now

Canonical workspace untuk strategy family yang sudah matang:
- `strategies/u5spring/`

Kalau mau kerja aktif di family ini, gunakan folder itu.

## Legacy root items

Masih tersisa di root aktif:
- `POOL_DISCOVERY/`

Sudah dipindahkan ke archive reversible:
- `legacy/root-duplicates-2026-07-19/METEORA_SETUP_DEPLOYMENT_NOTES.md`
- `legacy/root-duplicates-2026-07-19/MERIDIAN_PRESET_THESIS.md`
- `legacy/root-duplicates-2026-07-19/MERIDIAN_OPERATOR_PLAYBOOK.md`
- `legacy/root-duplicates-2026-07-19/MERIDIAN_OPERATOR_PLAYBOOK_COMPACT.md`
- `legacy/root-duplicates-2026-07-19/MERIDIAN_CONFIG_DRAFT.md`
- `legacy/root-duplicates-2026-07-19/MERIDIAN_PROFILE_MAPPING.md`
- `legacy/root-duplicates-2026-07-19/MERIDIAN_PROMPTNOTES_FINAL.md`
- `legacy/root-duplicates-2026-07-19/MERIDIAN_READY_TO_APPLY_JSONS.md`
- `legacy/root-duplicates-2026-07-19/STRATEGY_NAMING_CONCEPT.md`
- `legacy/root-duplicates-2026-07-19/U5SPRING_STRUCTURE_PREVIEW.md`
- `legacy/root-duplicates-2026-07-19/U5SPRING_MOCK_FOLDER_TREE_FINAL.md`
- `legacy/root-duplicates-2026-07-19/READY_LOAD_PROFILES/`

## Canonical replacements

- `METEORA_SETUP_DEPLOYMENT_NOTES.md`
  now use `strategies/u5spring/02-thesis/setup-notes.md`

- `MERIDIAN_PRESET_THESIS.md`
  now use `strategies/u5spring/02-thesis/meridian-thesis.md`

- `MERIDIAN_OPERATOR_PLAYBOOK.md`
  now use `strategies/u5spring/03-operator/playbook.md`

- `MERIDIAN_OPERATOR_PLAYBOOK_COMPACT.md`
  now use `strategies/u5spring/03-operator/playbook-compact.md`

- `MERIDIAN_CONFIG_DRAFT.md`
  now use `strategies/u5spring/04-meridian/config-draft.md`

- `MERIDIAN_PROFILE_MAPPING.md`
  now use `strategies/u5spring/04-meridian/profile-mapping.md`

- `MERIDIAN_PROMPTNOTES_FINAL.md`
  now use `strategies/u5spring/04-meridian/promptnotes.md`

- `MERIDIAN_READY_TO_APPLY_JSONS.md`
  now use `strategies/u5spring/04-meridian/ready-jsons.md`

- `legacy/root-duplicates-2026-07-19/READY_LOAD_PROFILES/`
  now use `strategies/u5spring/05-payloads/ready-load-profiles/`

- `POOL_DISCOVERY/`
  now use:
  - `strategies/u5spring/01-research/pool-discovery/`
  - `strategies/u5spring/01-research/chart-backtests/`

## Rule

- baca/tulis baru: pakai `strategies/u5spring/`
- `POOL_DISCOVERY/` di root: keep for reference only until hard cleanup phase
- retired duplicates: buka dari `legacy/root-duplicates-2026-07-19/` hanya kalau perlu jejak historis
