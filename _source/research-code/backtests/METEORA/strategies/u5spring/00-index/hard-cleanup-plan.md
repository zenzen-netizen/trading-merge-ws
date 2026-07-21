# U5Spring Hard Cleanup Planning

Tujuan:
- merencanakan kapan dan bagaimana legacy root items bisa dipensiunkan
- menjaga cleanup tetap aman, bertahap, dan reversible

PENTING:
- ini baru planning
- belum ada delete
- belum ada move destructive

## 1. Preconditions

Hard cleanup baru layak jika semua ini benar:
- sudah minimal 1-2 siklus kerja nyata memakai `strategies/u5spring/`
- tidak ada file baru ditulis ke root legacy untuk family U5Spring
- user/operator sudah terbiasa buka `u5spring/README.md` dan `00-index/master-index.md`
- payload baru sudah selalu diambil dari `05-payloads/ready-load-profiles/`
- tidak ada referensi eksternal yang masih mengandalkan path root lama

## 2. Cleanup tiers

### Tier 1 — Keep but freeze
Item:
- semua root markdown lama
- `READY_LOAD_PROFILES/`
- `POOL_DISCOVERY/`

Action:
- jangan edit lagi
- hanya reference
- canonical workspace sudah pindah

### Tier 2 — Archive move
Item kandidat:
- `STRATEGY_NAMING_CONCEPT.md`
- `U5SPRING_STRUCTURE_PREVIEW.md`
- `U5SPRING_MOCK_FOLDER_TREE_FINAL.md`

Action nanti:
- bisa dipindahkan ke root `legacy/` atau dihapus jika sudah cukup aman karena copy canonical ada di `99-archive/`

### Tier 3 — Retire duplicate docs
Item kandidat:
- `METEORA_SETUP_DEPLOYMENT_NOTES.md`
- `MERIDIAN_PRESET_THESIS.md`
- `MERIDIAN_OPERATOR_PLAYBOOK.md`
- `MERIDIAN_OPERATOR_PLAYBOOK_COMPACT.md`
- `MERIDIAN_CONFIG_DRAFT.md`
- `MERIDIAN_PROFILE_MAPPING.md`
- `MERIDIAN_PROMPTNOTES_FINAL.md`
- `MERIDIAN_READY_TO_APPLY_JSONS.md`

Action nanti:
- archive out of root or delete only after checksum/content cross-check against canonical copies

### Tier 4 — Retire duplicate payload folder
Item kandidat:
- `READY_LOAD_PROFILES/`

Action nanti:
- remove only after confirming canonical payload folder fully covers all files and names

### Tier 5 — Retire legacy research root
Item kandidat:
- `POOL_DISCOVERY/`

Action nanti:
- highest caution
- only after confirming every important report, snapshot, csv, and ohlcv file exists in canonical research tree

## 3. Safety procedure

Saat nanti execute hard cleanup:
1. snapshot file list lama
2. compare old vs canonical
3. verify file counts
4. verify key docs open cleanly
5. only then archive or remove duplicates

## 4. Recommended order

Urutan nanti:
1. retire meta duplicates first
2. retire duplicated markdown docs
3. retire duplicated payload folder
4. retire legacy research root last

## 5. What should remain after hard cleanup

Root `METEORA/` ideal future state:
- `README.md`
- `LEGACY_MAP.md`
- `strategies/`
- maybe `legacy/` if archived copies kept

## 6. Bottom line

Hard cleanup boleh dilakukan nanti, tapi bukan sekarang.
Strategi aman:
- canonical first
- freeze legacy
- archive gradually
- delete last
