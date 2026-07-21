# U5Spring Experiment Template

Pakai template ini saat mau menambah eksperimen baru di family U5Spring.

Tujuan template ini:
- memaksa eksperimen tetap bersih
- menjaga baseline canonical tidak tertimpa
- memudahkan agent lain membaca maksud eksperimen tanpa harus menebak
- memudahkan keputusan apakah hasil cukup berhenti di research atau layak naik ke thesis/operator/Meridian/payload

Sebelum isi template ini, baca dulu:
- `experiment-guide.md`
- `file-map.md`
- `../01-research/chart-backtests/rsi-fractal-mhermes-be/README.md`
- `../02-thesis/setup-notes.md`

Kalau butuh template pendamping lain:
- `templates/experiment-brief.md`
- `templates/comparison-note.md`
- `templates/thesis-addendum.md`

---

## 0. Header singkat

- Experiment name:
- Date:
- Owner / agent:
- Status: `planned | running | completed | archived`
- Baseline canonical:
- Experiment folder path:
- Comparison note path:

## 1. Pertanyaan eksperimen

Tuliskan SATU pertanyaan utama.

Contoh:
- `Apakah 30m lebih berguna sebagai context tambahan daripada engine utama?`
- `Apakah sample yang diperbesar masih mempertahankan edge 5m reclaim?`
- `Apakah alt exit ini memperbaiki payoff tanpa merusak breadth?`

Isi:
- Main question:
- Why this matters:

## 2. Base rule yang tetap dijaga

Tulis identity inti U5Spring yang tidak boleh diam-diam berubah.

Checklist inti:
- [ ] pool quality first
- [ ] reclaim timing second
- [ ] deploy expression third
- [ ] 5m tetap baseline engine acuan, kecuali eksperimen memang menguji engine baru secara eksplisit
- [ ] 15m tetap baseline context acuan, kecuali eksperimen memang menguji context baru secara eksplisit
- [ ] spot-first baseline tetap jadi comparator
- [ ] protection mindset dekat `BE1 style`
- [ ] eksperimen ini masih varian U5Spring, bukan thesis baru

Catatan tambahan:

## 3. Hipotesis

Isi:
- Hypothesis:
- Expected upside:
- Main risk of being wrong:

Contoh:
- `30m mungkin menambah context cleanliness, tapi berisiko terlalu lambat jika dipaksa jadi engine.`

## 4. Scope eksperimen

Isi:
- What changes:
- What stays fixed:
- Timeframes involved:
- Exit / SL involved:
- Pool universe / sample source:
- Whether this is research-only or potentially operational later:

Rule:
- ubah satu fokus utama saja
- kalau ada beberapa perubahan, pecah jadi eksperimen terpisah

## 5. Comparator baseline

Isi:
- Baseline folder:
- Baseline docs used for comparison:
- Why this baseline is the right comparator:

Minimal biasanya:
- `../01-research/chart-backtests/rsi-fractal-mhermes-be/`

## 6. Artefak yang wajib dibuat

Checklist minimum:
- [ ] folder eksperimen sibling baru dibuat di `../01-research/chart-backtests/`
- [ ] `summary.md`
- [ ] `report.md`
- [ ] `full-report.md`
- [ ] `summary.csv`
- [ ] `trade-journal.csv`
- [ ] `ohlcv/` bila relevan
- [ ] `split-by-mode/` bila relevan
- [ ] comparison note vs baseline

Path rencana:
- Experiment folder path:
- Summary path:
- Full report path:
- Trade journal path:
- Comparison note path:

## 7. Metrik penilaian

Tulis metrik apa yang dipakai untuk menilai eksperimen.

Contoh:
- breadth winner count
- median best result
- positive family ratio
- payoff quality
- drawdown character
- recovery character
- comparability vs baseline

Isi:
- Primary metrics:
- Secondary metrics:
- What would count as a meaningful improvement:
- What would count as failure / drift:

## 8. Guardrails

Isi checklist ini sebelum run:
- [ ] tidak overwrite baseline canonical
- [ ] tidak kerja langsung di folder baseline
- [ ] tidak campur beberapa thesis dalam satu run
- [ ] tidak mengubah bins/sizing/management/exit/timeframe sekaligus tanpa alasan eksplisit
- [ ] belum menyentuh operator doctrine
- [ ] belum menyentuh Meridian config/payload sebelum evidence cukup

Catatan guardrail tambahan:

## 9. Keputusan propagasi layer

Isi ini sebagai niat awal, lalu revisi setelah hasil keluar.

### 9A. Jika hasil lemah / tidak konklusif
- [ ] tetap berhenti di `01-research`
- [ ] tidak update thesis
- [ ] tidak update operator
- [ ] tidak update Meridian
- [ ] tidak buat payload baru

### 9B. Jika hasil cukup kuat mengubah belief
Potensi sentuh:
- [ ] `../02-thesis/`
- [ ] `../03-operator/`
- [ ] `../04-meridian/`
- [ ] `../05-payloads/`

Catatan kondisi naik level:

## 10. Hasil ringkas

Isi setelah run selesai.

- Outcome: `better | worse | mixed | inconclusive`
- Short verdict:
- Main evidence:
- Surprises:
- Did it preserve U5Spring identity?: `yes | no | partially`

## 11. Verdict propagasi

Isi setelah evaluasi selesai.

### 11A. Research only
Pilih ini kalau:
- hasil menarik tapi belum cukup kuat
- hasil tidak konsisten
- hasil tidak mengubah keputusan lapangan

Isi:
- [ ] stop at research layer only
- Why:

### 11B. Thesis update
Pilih ini kalau:
- hasil mengubah reasoning inti

Isi:
- [ ] update `../02-thesis/`
- Which file(s):
- Why:

### 11C. Operator update
Pilih ini kalau:
- hasil mengubah deploy/skip/premium/manual decision nyata

Isi:
- [ ] update `../03-operator/`
- Which file(s):
- Why:

### 11D. Meridian update
Pilih ini kalau:
- hasil mengubah mapping config/profile/promptnotes

Isi:
- [ ] update `../04-meridian/`
- Which file(s):
- Why:

### 11E. Payload/profile update
Pilih ini kalau:
- eksperimen siap diuji sebagai comparator operasional terpisah

Isi:
- [ ] update `../05-payloads/`
- New payload/profile name if any:
- Why:

## 12. Post-run checklist

- [ ] artefak lengkap tersimpan
- [ ] comparison note selesai
- [ ] verdict jelas
- [ ] keputusan propagasi jelas
- [ ] tidak ada overwrite ke baseline canonical
- [ ] kalau hasil belum kuat, perubahan berhenti di research

## 13. Quick copy block

Kalau mau versi super singkat untuk dilempar ke agent lain, copy blok ini:

```text
U5Spring experiment brief
- Main question:
- Keep these base rules fixed:
- Baseline comparator:
- One variable being changed:
- Experiment folder to create:
- Artifacts required:
- Comparison note required:
- Do not overwrite canonical baseline:
- Only propagate to thesis/operator/Meridian/payload if evidence is strong:
```

---

## 14. Minimal example

```text
Experiment name: rsi-fractal-mhermes-be-tf30m-context
Status: planned
Baseline canonical: ../01-research/chart-backtests/rsi-fractal-mhermes-be/

Main question:
Apakah 30m lebih berguna sebagai context tambahan daripada engine utama?

What changes:
- add 30m as context layer candidate

What stays fixed:
- pool-quality-first identity
- reclaim thesis
- 5m baseline engine comparator
- spot-first baseline
- BE1-style protection mindset

Experiment folder path:
../01-research/chart-backtests/rsi-fractal-mhermes-be-tf30m-context/

Comparison note path:
../01-research/chart-backtests/comparisons/baseline-vs-tf30m-context.md

If result is weak:
- stop at research

If result is strong:
- consider thesis update first
- only then evaluate operator/Meridian implications
```
