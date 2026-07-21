# U5Spring Cleanup Plan

Tujuan:
- menetapkan `strategies/u5spring/` sebagai workspace strategy family yang canonical
- memisahkan mana artefak baru, mana legacy root-level
- memberi urutan cleanup aman tanpa risiko merusak source lama

Status sekarang:
- struktur baru U5Spring sudah dibuat
- file penting sudah disalin ke struktur baru
- source lama di root `backtests/METEORA/` masih utuh
- belum ada delete / move destructive

## 1. Canonical workspace

Workspace canonical baru:
- `/home/ubuntu/trading-research/backtests/METEORA/strategies/u5spring/`

Maknanya:
- pengembangan lanjut sebaiknya baca/tulis dari folder ini
- file root lama diperlakukan sebagai legacy source / historical source
- tuning, note baru, dan payload baru sebaiknya masuk family folder ini

## 2. Legacy items yang masih ada di root METEORA

Legacy docs root:
- `METEORA_SETUP_DEPLOYMENT_NOTES.md`
- `MERIDIAN_PRESET_THESIS.md`
- `MERIDIAN_OPERATOR_PLAYBOOK.md`
- `MERIDIAN_OPERATOR_PLAYBOOK_COMPACT.md`
- `MERIDIAN_CONFIG_DRAFT.md`
- `MERIDIAN_PROFILE_MAPPING.md`
- `MERIDIAN_PROMPTNOTES_FINAL.md`
- `MERIDIAN_READY_TO_APPLY_JSONS.md`
- `STRATEGY_NAMING_CONCEPT.md`
- `U5SPRING_STRUCTURE_PREVIEW.md`
- `U5SPRING_MOCK_FOLDER_TREE_FINAL.md`

Legacy payload folder:
- `READY_LOAD_PROFILES/`

Legacy research root:
- `POOL_DISCOVERY/`

## 3. Rule after migration

Mulai sekarang:
- kalau mau recall strategy, buka `strategies/u5spring/README.md`
- kalau mau tuning, buka `strategies/u5spring/00-index/file-map.md`
- kalau mau edit thesis/operator/meridian docs, edit yang di `strategies/u5spring/`
- jangan bikin versi baru lagi di root METEORA kecuali memang sengaja sebagai legacy snapshot

## 4. Cleanup phases

### Phase A — Safe coexistence
Status: sudah tercapai.

Ciri:
- file baru ada di U5Spring
- file lama tetap ada
- tidak ada risiko kehilangan referensi lama

### Phase B — Navigation polish
Status: dijalankan sekarang.

Isi:
- tambah roadmap
- tambah file-map
- tambah master-index
- tambah tuning-guide
- tambah README layer
- tandai canonical workspace

### Phase C — Soft deprecation
Belum dijalankan.

Isi nanti:
- beri note di root METEORA bahwa U5Spring workspace baru adalah canonical
- optional tambahkan prefix `LEGACY_` pada file tertentu hanya jika benar-benar perlu
- atau buat satu `LEGACY_MAP.md` di root

### Phase D — Hard cleanup
Belum dijalankan.

Isi nanti, hanya jika sudah yakin:
- arsipkan / pindahkan sebagian file root lama ke folder legacy terpisah
- jangan delete sebelum yakin tidak ada referensi yang masih dipakai

## 5. Recommendation: what NOT to delete yet

Belum usah hapus sekarang:
- `POOL_DISCOVERY/`
- `READY_LOAD_PROFILES/`
- semua markdown root-level lama

Kenapa:
- masih berguna sebagai fallback
- masih aman untuk cross-check
- belum ada masa adaptasi cukup lama

## 6. Recommendation: what can become source of truth now

Source of truth now:
- overview: `README.md`
- navigation: `00-index/roadmap.md`
- lookup cepat: `00-index/file-map.md`
- tuning guidance: `00-index/tuning-guide.md`
- latest payloads: `05-payloads/ready-load-profiles/`

## 7. Trigger untuk future hard cleanup

Hard cleanup baru layak kalau:
- sudah 1-2 siklus kerja pakai U5Spring folder
- tidak ada lagi file baru ditulis ke root legacy
- semua referensi manusia sudah pindah ke folder baru
- payload baru selalu lahir dari folder baru

## 8. Bottom line

Keputusan kerja yang disarankan:
- U5Spring = canonical strategy workspace
- root METEORA lama = legacy reference sementara
- phase-2 cleanup = polish + navigation
- hard delete / archive besar ditunda dulu
