# Handoff — Deep-Dive Review Indikator (Pine ↔ Python)

> Dokumen ini dibawa ke chat baru tiap mau bedah 1 indikator. Lampirkan
> file ini + source `.pine`/`.txt` + `.py` indikator yang mau dibahas.
> Chat baru otomatis punya konteks metodologi, mindset, dan tahu harus
> ngapain tanpa perlu dijelasin ulang dari nol.

---

## 0. Konteks Project (Anchor — Baca Dulu Kalau Belum)

Project ini bagian dari sistem backtest multi-strategi (`00_roadmap.md`
di project knowledge). Sesi review indikator per-indikator ini masuk ke
**build-stage 3** (`stage_03_replikasi_indikator.md`) — validasi replikasi
Pine→Python, khususnya layer fase/state, sebelum indikator dipakai bahan
strategi resmi. Playbook eksekusi teknis ada di
`00_playbook_eksekusi_ai_agent.md` langkah 2.

**Status stage 2 (fetcher Binance): belum dibangun.** Artinya semua
review di sesi-sesi ini masih level **cross-check logic Pine vs Python**
(baca kode, bukan baca angka), BUKAN validasi numerik ke data real. Itu
nunggu stage 2 kelar.

---

## 1. Mindset Wajib (Berlaku ke Semua Indikator)

**Chart TradingView = kebenaran setup.** Yang jadi acuan kalibrasi setup
nanti adalah apa yang KETAMPIL di chart, bukan apa yang "kejadian di
mesin" doang. Konsekuensinya, tiap indikator perlu dicek dua lapisan:

- **Lapisan Mesin** — logic yang nentuin APAKAH suatu kondisi/event
  terjadi secara matematis (angka, counter, threshold).
- **Lapisan Visibility** — ada gak elemen yang nentuin APAKAH sesuatu
  KETAMPIL di chart, terpisah dari apakah dia "terjadi". Ini yang paling
  gampang kelewat kalau cuma baca sekilas, karena kelihatannya "cuma
  soal warna/toggle tampilan" padahal bisa nge-gate signifikan (contoh
  nyata: filter trend Supertrend di FBF, default ON, ngefilter mayoritas
  event).

**Default value Pine = default value Python.** Semua parameter Python
harus punya default persis sama dengan input Pine aslinya — ini bukan
opsional, karena "setup yang user pakai" itu ya defaultnya, kecuali user
eksplisit bilang dia ubah sesuatu.

---

## 2. Metodologi Review (Urutan Kerja, Reusable)

1. **Baca source Pine + Python side by side.** Jangan asumsi dari nama
   variabel — telusuri tiap baris logic yang related.
2. **Bikin glossary istilah** — tiap fase/state/filter yang dipakai
   indikator, plus: default value, dampak ON/OFF, status di Python
   (replikasi aktif / replikasi tapi dormant / sengaja dibuang).
3. **Bikin node tree teks** (bukan cuma diagram visual, biar ringan &
   gampang di-copy) buat tiap mesin/state-machine yang ada di indikator.
   Pisah tree per "otak"/"lapisan" kalau indikatornya kompleks (contoh
   FBF: Tracker vs Judge vs Visibility — 3 tree terpisah, baru digabung
   di 1 flow besar).
4. **Cross-check baris-per-baris** — cari SEMUA elemen yang exist di
   Pine tapi mungkin kelewat di Python: state persisten antar-bar,
   operator ambang (`==` vs `>=`), urutan cascade if-elif, filter yang
   defaultnya ON (paling gampang kelewat karena orang cenderung fokus ke
   yang OFF-dijelasin-di-tooltip), dan terutama elemen VISUAL yang
   ternyata NGE-GATE (bukan cuma kosmetik).
5. **Klasifikasi tiap elemen visual** yang ketemu: murni kosmetik (aman
   dibuang) vs nge-gate visibility (WAJIB direplikasi kalau mau
   mindset "chart=kebenaran" konsisten).
6. **Kalau ketemu gap nyata** (elemen nge-gate yang belum direplikasi):
   patch Python-nya. Bump versi filename (`_v1_2`, dst) biar jelas beda
   dari yang lama. Jangan overwrite file lama diam-diam.
7. **Jabarkan semua skenario jalur** yang mungkin terjadi dari kombinasi
   state — termasuk kasus counter-intuitive (kayak FBF skenario F: wave
   sempat kelihatan pas forming, tapi break-nya malah hilang dari chart
   karena trend keburu flip balik pas mau confirm).
8. **Compile jadi 1 dokumen "buku panduan"** — glossary + node tree +
   skenario + tabel dampak ON/OFF + status replikasi akhir. Ini yang
   jadi pegangan kalau lupa cara kerja indikatornya nanti.
9. **Validasi numerik ke data real TETAP PENDING** sampai stage 2 kelar
   — dicatat eksplisit di dokumen sebagai to-do, bukan dianggap selesai.

---

## 3. Status Sesi Sebelumnya — FBF (Fractal Break Filter v11.1)

**Selesai dikerjakan:**
- Node tree Tracker (wave A-B-C) + Judge (candidate→BREAK/FAIL)
- Cross-check baris-per-baris Pine vs Python — ketemu 1 gap nyata
  (visibility gating Supertrend, default ON, belum direplikasi) + 1
  selisih kecil (A3 lookback edge-case NaN vs clip di awal data)
- Patch `fbf_break_filter_v1_2.py` — nambah layer visibility
  (`st_trend`, `bull_wave_visible`, `bear_wave_visible` di bars;
  `visible_at_birth`, `visible_at_confirm` di events), tanpa ubah
  logic Tracker/Judge yang udah tervalidasi
- Dokumen panduan lengkap: `fbf_panduan_pine_vs_python.md` (glossary,
  4 node tree, 7 skenario jalur, tabel ON/OFF, status akhir)

**Belum/To-Do:**
- [ ] Validasi numerik ke data real TradingView — blocked, nunggu
      stage 2 (fetcher Binance)
- [ ] Kalau A3 lookback (`enable_a_lookback`) nanti dipakai aktif: cek
      manual titik-titik dekat awal dataset (selisih NaN vs clip)
- [ ] Kalau `enable_smi_filter`/`enable_c_fractal` nanti diaktifkan:
      belum ada review mendalam ke filter itu (masih dormant, cuma
      dicek eksis di kode, belum dibedah skenarionya)

---

## 4. Template Pembuka Chat Baru — Indikator Selanjutnya

Copy blok di bawah, ganti `[NAMA_INDIKATOR]`, tempel jadi pesan pertama
di chat baru bareng lampiran file ini + source Pine (.txt) + Python (.py)
indikator yang dimaksud:

```
Lanjut review indikator [NAMA_INDIKATOR] — Pine vs Python.
File terlampir: handoff ini, source Pine (.txt), source Python (.py).

Ikuti metodologi & mindset di bagian 1-2 handoff ini. Mulai dari:
1. Node tree alur (text, bukan cuma diagram)
2. Glossary istilah/fase/filter + default + dampak ON/OFF + status Python
3. Cross-check Pine vs Python cari gap (terutama elemen visual yang
   ternyata nge-gate, bukan cuma kosmetik)
4. Kalau ada gap: patch + versionkan filename
5. Compile jadi 1 buku panduan .md kayak fbf_panduan_pine_vs_python.md
```

---

## 5. File yang Udah Dihasilkan (Referensi Lintas-Chat)

| File | Isi |
|---|---|
| `fbf_break_filter_v1_2.py` | Python replikasi FBF, sudah termasuk layer visibility |
| `fbf_panduan_pine_vs_python.md` | Buku panduan lengkap FBF |
| `smi_pro_v3.py` | Python replikasi SMI (versi terkoreksi, gantiin `smi_pro.py` lama) — **belum** melalui deep-dive selengkap FBF, baru sekadar overview awal |

**Catatan:** SMI Pro sempat dibahas overview-nya di chat ini (flow cross
up→cross down, PA/PD, fail mid) tapi belum sedalam FBF (belum ada
cross-check baris-per-baris lengkap, belum ada dokumen panduan
terpisah). Kandidat kuat buat jadi indikator berikutnya yang dibedah
tuntas pakai metodologi di atas.
