# U5Spring Experiment Guide

Tujuan file ini:
- jadi rujukan sehat saat mau menambah eksperimen baru di U5Spring
- menjaga supaya agent tidak merusak baseline, thesis, operator doctrine, atau payload yang sudah ada
- memberi alur keputusan yang jelas dari ide eksperimen sampai kemungkinan naik ke Meridian profile / payload

Template siap pakai:
- `experiment-template.md`

Template pack tambahan:
- `templates/README.md`
- `templates/experiment-brief.md`
- `templates/comparison-note.md`
- `templates/thesis-addendum.md`

File ini berlaku untuk:
- Hermes
- subagent lain
- agent coding / riset lain
- operator manusia yang mau menambah varian riset di family U5Spring

## 1. Prinsip inti

U5Spring sudah punya identity yang jelas:
- pool quality first
- reclaim timing second
- deploy expression third
- 5m sebagai engine utama
- 15m sebagai context utama
- spot-first baseline
- protection mindset dekat `BE1 style`
- dual-side hanya eksperimen kecil, bukan default produksi

Karena itu, semua eksperimen baru harus dimulai dari pertanyaan ini:

`Apakah saya masih sedang menguji variasi dari thesis U5Spring, atau diam-diam sudah pindah ke thesis lain?`

Kalau masih variasi dari thesis yang sama:
- tetap di family `u5spring/`
- eksperimen masuk sebagai cabang riset baru

Kalau sudah pindah thesis:
- jangan dipaksa tetap jadi bagian inti U5Spring
- pertimbangkan family strategi baru

## 2. Golden rules

1. Jangan overwrite baseline canonical.
2. Satu eksperimen = satu pertanyaan utama.
3. Jangan ubah banyak variabel sekaligus.
4. Semua eksperimen mulai dari `01-research`.
5. Jangan naik ke operator / Meridian / payload sebelum evidence cukup.
6. Comparator baseline harus tetap stabil.
7. Kalau ragu apakah eksperimen layak naik level, tahan di layer research dulu.

## 3. Apa yang dianggap baseline canonical sekarang

Canonical baseline saat ini dibaca dari family riset utama:
- `../01-research/chart-backtests/rsi-fractal-mhermes-be/`

Baseline ini diperlakukan sebagai:
- pembanding resmi
- anchor thesis
- sumber evidence utama untuk dokumen operator dan Meridian

Artinya:
- jangan timpa `summary.*`, `report.*`, `full-report.md`, `trade-journal.csv`, atau isi `ohlcv/` baseline
- jangan jadikan file baseline sebagai scratchpad eksperimen
- kalau ada run baru, simpan sebagai folder sibling baru

## 4. Kapan TIDAK perlu folder family baru

Tetap di `u5spring/` kalau eksperimen masih menjaga identity inti strategy, misalnya:
- tambah sample pool
- tambah timeframe uji
- tambah context timeframe baru
- tweak confirm / filter kecil
- tweak exit variant
- tweak SL variant
- perketat / longgarkan screening secara terbatas
- test deployment expression kecil yang masih tunduk pada thesis yang sama

Contoh:
- `5m engine + 30m context`
- `sample pool diperbesar dari set lama`
- `BE variant baru`
- `O2 tetap, tapi confirm filter beda sedikit`

## 5. Kapan perlu family strategi baru

Pertimbangkan family baru kalau eksperimen menggeser identity inti, misalnya:
- dari bullish reclaim continuation menjadi dip-accumulation thesis
- dari spot-first menjadi bid_ask-heavy default
- dari 5m reclaim ke 1m scalp/high-noise engine utama
- dari pool-quality-first menjadi fee-chop / inventory-first thesis
- dari operator discipline baseline menjadi discretionary thesis yang sangat berbeda

Rule praktis:
- `varian` = tetap di `u5spring/`
- `thesis baru` = family baru

## 6. Lokasi eksperimen yang sehat

Semua eksperimen baru mulai dari:
- `../01-research/chart-backtests/`

Pola yang disarankan:
- `rsi-fractal-mhermes-be/` <- baseline freeze
- `rsi-fractal-mhermes-be-ext-sample/`
- `rsi-fractal-mhermes-be-tf30m-context/`
- `rsi-fractal-mhermes-be-tf30m-engine/`
- `rsi-fractal-mhermes-be-alt-exit/`
- `rsi-fractal-mhermes-be-alt-confirm/`

Kalau eksperimen makin banyak, boleh tambah folder ringkas seperti:
- `../01-research/chart-backtests/comparisons/`

Isi contoh:
- `baseline-vs-ext-sample.md`
- `baseline-vs-tf30m-context.md`
- `baseline-vs-alt-exit.md`

## 7. Naming convention eksperimen

Nama folder eksperimen harus menjawab:
- baseline apa yang dipakai
- apa variabel yang diubah
- eksperimen itu menguji apa

Gunakan pola sederhana:
- `<baseline>-<focus>`
- `<baseline>-<focus>-<intent>`

Contoh baik:
- `rsi-fractal-mhermes-be-ext-sample`
- `rsi-fractal-mhermes-be-tf30m-context`
- `rsi-fractal-mhermes-be-tf30m-engine`
- `rsi-fractal-mhermes-be-alt-exit`
- `rsi-fractal-mhermes-be-screen-looser-v1`

Hindari nama kabur seperti:
- `newtest`
- `trial2`
- `revisi_final_fix`
- `better_version`

## 8. Satu eksperimen = satu pertanyaan

Setiap eksperimen harus bisa diringkas dalam satu pertanyaan utama.

Contoh sehat:
- `Apakah sample lebih besar masih mendukung thesis 5m reclaim?`
- `Apakah 30m lebih berguna sebagai context daripada engine?`
- `Apakah alt exit ini memperbaiki payoff tanpa merusak breadth?`
- `Apakah filter tambahan ini meningkatkan kualitas candidate tanpa memangkas terlalu banyak peluang?`

Kalau pertanyaannya berubah jadi banyak sekaligus, pecah eksperimennya.

Contoh tidak sehat:
- ganti timeframe
- ganti exit
- ganti screening
- ganti sizing
- ganti management
- lalu ambil kesimpulan dari satu run campur

Itu bukan eksperimen bersih. Itu drift.

Kalau mau langsung menulis brief eksperimennya, pakai:
- `experiment-template.md`

## 9. Alur sehat eksperimen

Urutan sehat selalu:
- evidence
- thesis
- doctrine
- Meridian translation
- payload

Detailnya:

### Step 1 — Rumuskan pertanyaan eksperimen
Tulis jelas:
- apa yang diubah
- apa yang tetap
- pembandingnya siapa
- metrik apa yang dipakai menilai hasil

Minimal jawab:
- `base rule apa yang tetap saya jaga?`
- `satu hal apa yang saya uji?`
- `baseline pembanding saya yang mana?`

### Step 2 — Buat run research baru
Buat folder sibling baru di `01-research/chart-backtests/`.

Jangan kerja di folder baseline canonical.

### Step 3 — Simpan artefak lengkap
Sebisa mungkin simpan bentuk yang sebanding dengan baseline:
- `summary.md`
- `report.md`
- `full-report.md`
- `trade-journal.csv`
- `summary.csv`
- `ohlcv/` jika relevan
- `split-by-mode/` jika relevan

Tujuan:
- agent lain bisa audit
- comparison lebih bersih
- reasoning tidak menggantung pada chat lama

### Step 4 — Buat comparison vs baseline
Setiap eksperimen sebaiknya punya note compare singkat.

Template siap pakai:
- `templates/comparison-note.md`

Minimal isi:
- pertanyaan eksperimen
- apa yang berubah
- apa yang tetap
- hasil utama vs baseline
- verdict: lebih baik / lebih buruk / tidak konklusif
- apakah layak naik ke thesis

### Step 5 — Evaluasi apakah hasil hanya research atau sudah mengubah belief
Tanya:
- apakah hasil ini cukup kuat untuk mengubah key belief?
- apakah hasil ini konsisten atau cuma kebetulan subset?
- apakah perubahan ini tetap nyambung dengan identity U5Spring?

Kalau belum kuat:
- simpan di research saja
- jangan ubah operator/Meridian

Kalau cukup kuat:
- baru naik ke `02-thesis`

### Step 6 — Naik ke thesis bila perlu
Sentuh `../02-thesis/` hanya jika eksperimen benar-benar mengubah reasoning inti.

Template siap pakai:
- `templates/thesis-addendum.md`

Contoh:
- 30m ternyata lebih kuat sebagai context tambahan
- sample besar menguatkan atau melemahkan key belief lama
- exit baru mengubah pembacaan karakter recovery

Boleh update file lama atau tambah addendum baru, misalnya:
- `validation-addendum.md`
- `variant-comparison.md`
- `timeframe-extension-notes.md`

### Step 7 — Naik ke operator doctrine bila keputusan lapangan berubah
Sentuh `../03-operator/` hanya jika eksperimen mengubah keputusan operator nyata.

Contoh:
- kapan deploy
- kapan skip
- premium candidate butuh filter tambahan
- kapan 30m wajib dibaca
- kapan varian tertentu boleh dipakai

Kalau hanya hasil statistik menarik tapi belum mengubah keputusan lapangan:
- jangan sentuh playbook dulu

### Step 8 — Naik ke Meridian translation bila mapping bot ikut berubah
Sentuh `../04-meridian/` hanya jika ada implikasi konfigurasi / profile / promptnotes.

Contoh:
- timeframe field berubah
- context logic berubah
- promptnotes perlu guardrail baru
- profile mapping perlu profile eksperimen baru

### Step 9 — Naik ke payload hanya jika siap operasional
Sentuh `../05-payloads/` hanya jika eksperimen sudah cukup matang untuk diuji sebagai profile nyata.

Payload baru hanya dibuat kalau memang perlu comparator operasional yang bersih.

## 10. Kapan perlu profile / payload Meridian baru

Tidak semua eksperimen butuh profile baru.

Belum perlu payload baru kalau:
- masih riset offline
- masih audit backtest
- belum ada keputusan operasional

Perlu payload baru kalau:
- eksperimen mau diuji paralel lawan baseline
- ada field config yang beda material
- butuh audit hasil live / paper yang terpisah bersih

Contoh payload yang layak ditambah nanti:
- `context30m-exp.user-config.json`
- `alt-exit-exp.user-config.json`

Tapi jangan buat payload hanya karena ide eksperimen muncul.

## 11. Decision tree cepat

### A. Mau tambah sample
- tetap di `u5spring/`
- buat run research baru
- compare vs baseline
- update thesis hanya kalau belief berubah

### B. Mau tambah timeframe
Tanya dulu:
- timeframe baru ini engine, context, atau filter?

Lalu:
- buat run research baru
- jangan langsung ubah playbook / payload
- kalau kuat, baru propagasi ke thesis lalu operator

### C. Mau tambah alternatif rule
Kalau rule baru masih menjaga thesis reclaim yang sama:
- tetap di `u5spring/`
- buat varian research baru
- compare vs baseline

Kalau rule baru ternyata menggeser strategy identity:
- pertimbangkan family baru

## 12. Hal yang dilarang

Jangan lakukan ini:
- overwrite baseline canonical
- menaruh eksperimen mentah di folder operator atau payload
- ubah bins + timeframe + exit + screening + sizing sekaligus
- memaksa thesis baru masuk ke folder lama tanpa penanda jelas
- menjadikan profile produksi sebagai sandbox liar
- membuat payload baru sebelum evidence cukup
- mengambil hasil sandbox lalu menganggapnya source of truth produksi tanpa comparator yang bersih

## 13. Checklist agent sebelum mulai eksperimen

Sebelum agent menambah eksperimen baru di U5Spring, agent harus bisa menjawab:
- strategi dasar yang dijaga apa?
- baseline canonical yang dipakai apa?
- satu pertanyaan eksperimen utamanya apa?
- variabel mana yang berubah?
- variabel mana yang tetap?
- hasil nanti akan disimpan di folder mana?
- apakah eksperimen ini hanya research, atau berpotensi naik ke thesis/operator/Meridian?

Kalau jawaban pertanyaan-pertanyaan ini belum jelas:
- berhenti dulu
- rapikan desain eksperimen

## 14. Checklist agent setelah eksperimen selesai

Setelah run selesai, agent harus menjawab:
- apakah artefak riset lengkap sudah tersimpan?
- apakah comparison vs baseline sudah dibuat?
- verdict-nya apa: menang / kalah / tidak konklusif?
- apakah hasil ini cukup kuat untuk mengubah thesis?
- apakah hasil ini mengubah operator decision?
- apakah hasil ini butuh profile / payload baru?

Kalau tidak ada perubahan key belief:
- cukup simpan sebagai research branch
- jangan propagasi ke layer atas

## 15. Bottom line

Cara paling sehat bereksperimen di U5Spring adalah:
- baseline dibekukan
- varian baru dibuat sebagai branch research sibling
- comparison selalu melawan baseline
- propagasi ke thesis/operator/Meridian/payload hanya jika evidence memaksa
- family baru dibuat hanya saat thesis inti benar-benar bergeser

Kalau bingung harus bagaimana:
- tetap di `01-research`
- ubah satu variabel saja
- bandingkan lawan baseline
- tahan dulu perubahan layer atas
