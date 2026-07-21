# Meteora Ready-Load Profiles

Ini BUKAN apply langsung.
Ini hanya file siap-load / siap-copy sebagai calon `user-config.json`.

Safety:
- tidak ada bot live yang diubah
- tidak ada file di `/home/ubuntu/meridianzen/` yang disentuh
- semua file di folder ini hanya template siap pakai

Folder ini isi:
- `meteora-baseline.user-config.json`
- `meteora-dualside-exp.user-config.json`
- `meteora-manual-sandbox.user-config.json`

Cara pakai aman:
1. review file dulu
2. copy ke profile baru / sandbox
3. baru load manual saat siap
4. restart profile target sendiri nanti, bukan otomatis dari file ini

Intent file:
- baseline = comparator utama
- dual-side = eksperimen upside sleeve kecil
- manual = sandbox discretionary

Catatan penting:
- file ini sengaja tidak menyimpan secret `.env`
- file ini tidak mengubah PM2
- file ini tidak mengubah profile existing
- kalau nanti mau dipakai live, review dulu `dryRun`, model, chat id, dan key profile target
