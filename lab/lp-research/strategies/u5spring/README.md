# U5Spring

U5Spring = strategy family untuk bullish reclaim continuation pada pool Meteora.

Core identity:
- pool quality first
- 5m timing, 15m context
- spot-first deployment
- protection mindset dekat `BE1 style`
- dual-side hanya eksperimen kecil, bukan default produksi

Folder ini sengaja memisahkan alur penuh:
- `01-research` = evidence mentah dan hasil backtest
- `02-thesis` = reasoning dan translasi konsep
- `03-operator` = aturan keputusan operator
- `04-meridian` = mapping ke config / prompt / profile Meridian
- `05-payloads` = file siap-load, non-destructive
- `99-archive` = catatan meta, naming, preview struktur

Kalau baru masuk folder ini, baca urutan berikut:
1. `00-index/roadmap.md`
2. `00-index/experiment-guide.md`
3. `00-index/experiment-template.md`
4. `02-thesis/setup-notes.md`
5. `02-thesis/meridian-thesis.md`
6. `03-operator/playbook.md`
7. `04-meridian/config-draft.md`
8. `04-meridian/ready-jsons.md`
9. `05-payloads/ready-load-profiles/README.md`

Kalau tujuanmu spesifik:
- mau lihat bukti backtest: buka `01-research/`
- mau paham kenapa thesis ini lahir: buka `02-thesis/`
- mau tuning cara keputusan: buka `03-operator/`
- mau ubah mapping ke Meridian: buka `04-meridian/`
- mau cari file siap copy/load: buka `05-payloads/`
- mau nambah eksperimen sehat tanpa merusak baseline: buka `00-index/experiment-guide.md`
- mau agent langsung isi brief eksperimen: buka `00-index/experiment-template.md`
- mau workflow eksperimen berulang yang lebih lengkap: buka `00-index/templates/README.md`

Catatan safety:
- payload di sini bukan apply langsung ke bot
- file `.json` di `05-payloads/` adalah artefak siap-load / siap-copy
- tidak ada secret `.env` di folder ini
