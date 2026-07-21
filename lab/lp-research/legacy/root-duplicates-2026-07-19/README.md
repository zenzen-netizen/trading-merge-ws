# Root duplicate retirement — 2026-07-19

Purpose:
- remove obvious duplicate clutter from `METEORA/` root
- keep all retired items reversible
- preserve canonical workspace under `strategies/u5spring/`

What was moved here:
- root markdown files whose contents were checksum-identical to canonical copies under `strategies/u5spring/`
- legacy `READY_LOAD_PROFILES/` folder whose JSON payloads were checksum-identical to canonical payloads under `strategies/u5spring/05-payloads/ready-load-profiles/`

What was intentionally NOT moved in this phase:
- `POOL_DISCOVERY/`
- `README.md`
- `LEGACY_MAP.md`
- `strategies/`

Reason:
- `POOL_DISCOVERY/` still contains some root-only source artifacts (not yet fully mirrored in canonical tree), so it was left in place for a later, higher-caution phase.
