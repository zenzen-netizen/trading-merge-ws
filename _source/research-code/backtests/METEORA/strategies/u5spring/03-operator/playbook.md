# Meridian Operator Playbook — Meteora Reclaim Setup

Tujuan file ini:
- mengubah thesis + draft config yang sudah ada menjadi playbook operator yang lebih praktis,
- membantu memutuskan kapan deploy, kapan skip, kapan pakai baseline, dan kapan eksperimen boleh jalan,
- menjaga supaya workflow manual, semi-manual, dan bot tetap disiplin terhadap thesis yang sama.

Urutan baca file Meteora sekarang:
1. `METEORA_SETUP_DEPLOYMENT_NOTES.md`
   - thesis konseptual setup
2. `MERIDIAN_PRESET_THESIS.md`
   - mapping thesis ke workflow Meridian
3. `MERIDIAN_CONFIG_DRAFT.md`
   - draft config operasional
4. `MERIDIAN_OPERATOR_PLAYBOOK.md`
   - rule eksekusi operator

PENTING:
- playbook ini dibangun untuk thesis `bullish reclaim timing overlay`,
- bukan untuk thesis `deep dip accumulation engine`,
- jadi tujuan utama operator bukan mencari diskon terdalam,
- tapi mencari pool sehat yang memberi reclaim timing bersih.

## 1. Operator mental model

Kalimat inti yang harus diingat:

`Pool quality dulu, reclaim timing kedua, deploy expression ketiga.`

Urutan prioritas:
1. pool quality
2. market/context sanity
3. reclaim timing
4. strategy expression
5. management discipline

Artinya:
- sinyal chart bagus TIDAK boleh menyelamatkan pool jelek,
- strategy yang kreatif TIDAK boleh dipakai untuk menutupi conviction yang lemah,
- dual-side TIDAK boleh menjadi kompensasi untuk setup yang sebenarnya belum cukup bagus.

## 2. Default operating stance

Kalau tidak ada alasan kuat untuk menyimpang, pakai stance ini:

```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": false,
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "timeframe": "5m"
}
```

Cara baca stance default:
- SOL-paired only
- `spot` jadi baseline deploy expression
- single-side dulu
- reclaim 5m jadi engine utama
- 15m hanya context / confirm overlay
- management dibaca sebagai `BE1 style`

## 3. Kapan deploy

Deploy hanya saat 3 lapis ini align:

### 3.1 Layer 1 — Pool quality lolos
Minimal pembacaan operator:
- liquidity tidak tipis / tidak absurd
- fee/TVL tidak rusak
- holder structure tidak terlalu kacau
- organic flow masih masuk akal
- launchpad / token hygiene tidak red-flag berat
- narasi masih hidup atau setidaknya tidak busuk

Kalau layer ini gagal:
- skip,
- meskipun reclaim timing terlihat cantik.

### 3.2 Layer 2 — Context tidak rusak
Hal yang dicari:
- struktur besar belum tampak breakdown parah
- 15m tidak menunjukkan damage yang jelas
- bukan kondisi euforia rusak yang tinggal menunggu dump besar
- bukan pool yang cuma spike liar tanpa follow-through sehat

Kalau 5m bagus tapi 15m kelihatan rusak:
- default action = skip,
- kecuali sesi manual dengan conviction sangat spesifik dan size kecil.

### 3.3 Layer 3 — Reclaim timing bersih
Hal yang dicari:
- reclaim muncul setelah pullback / cooldown yang masih sehat,
- bukan setelah collapse berat,
- bukan setelah chart chaos panjang,
- ada sense bahwa move berikutnya adalah continuation reclaim, bukan dead-cat bounce.

Kalau timing muncul tapi terasa telat / extension sudah jauh:
- jangan kejar,
- tunggu candidate lain.

## 4. Kapan skip

Skip lebih bagus daripada memaksa deploy jelek.

### 4.1 Skip karena quality
Skip jika:
- pool terlalu tipis,
- hygiene token jelek,
- volume terlihat palsu / tidak organik,
- holder structure terlalu berbahaya,
- narasi kosong dan tidak ada hal lain yang benar-benar menebusnya.

### 4.2 Skip karena context
Skip jika:
- 15m context rusak jelas,
- trend besar terasa sudah patah,
- reclaim 5m muncul melawan damage context yang terlalu besar,
- price action terlalu chaotic untuk dibaca sebagai reclaim sehat.

### 4.3 Skip karena timing
Skip jika:
- setup terlalu telat,
- reward sudah banyak termakan,
- trigger terlihat dipaksakan,
- chart lebih mirip bounce random daripada reclaim continuation.

### 4.4 Skip karena comparability discipline
Skip juga jika operator merasa ingin mengubah terlalu banyak variabel sekaligus:
- mau buka dual-side,
- mau ubah bins,
- mau longgarkan screening,
- mau ubah sizing,
- mau ganti strategy expression,
- semua pada candidate yang sama.

Kalau sampai begini:
- stop,
- balik ke baseline,
- jangan bikin eksperimen jadi kotor.

## 5. Kapan anggap candidate premium

`Candidate premium` bukan berarti auto-deploy.
Artinya: candidate ini boleh dipertimbangkan untuk diberi sedikit ruang ekstra dibanding baseline biasa.

### 5.1 Ciri candidate premium
Semakin banyak poin ini terpenuhi, semakin layak disebut premium:
- pool quality jelas di atas rata-rata candidate harian,
- context 15m bersih dan mendukung,
- reclaim 5m bersih, tidak telat, tidak chaos,
- narasi / organic flow terasa nyata,
- struktur chart terasa continuation-quality, bukan cuma mean-reversion liar,
- operator bisa menjelaskan edge-nya dengan kalimat sederhana.

Tes sederhana:
- kalau operator sulit menjelaskan kenapa ini premium selain "kelihatan bagus",
  maka kemungkinan belum premium.

### 5.2 Apa yang boleh berubah untuk candidate premium
Boleh dipertimbangkan:
- size sedikit lebih percaya diri, tetap dalam risk budget,
- management sedikit lebih sabar daripada candidate biasa,
- pada mode manual, optional test `curve` dalam sandbox terpisah.

Yang TIDAK otomatis boleh:
- langsung dual-side besar,
- langsung ganti thesis jadi dip-capture,
- langsung longgar total pada risk discipline.

### 5.3 Premium tetap bukan alasan melanggar thesis
Kalau candidate premium tapi deploy expression yang terlintas justru `bid_ask` berat bawah,
operator harus tanya:
- apakah saya masih main reclaim thesis,
- atau saya diam-diam sudah pindah ke dip-accumulation thesis?

Kalau jawabannya sudah pindah thesis:
- jangan pakai profile baseline,
- pindah ke sandbox / manual experiment.

## 6. Kapan pakai baseline

Pakai baseline untuk hampir semua use case default.

### Baseline cocok untuk:
- production bot utama,
- guarded live pertama,
- paper baseline pembanding,
- candidate normal yang bagus tapi bukan top-tier premium,
- semua sesi saat operator ingin hasil yang paling comparable.

### Baseline adalah pilihan default jika:
- operator ragu,
- candidate bagus tapi tidak luar biasa,
- belum ada bukti eksperimen lain lebih unggul,
- tujuan utama masih observasi dan learning disiplin.

### Rumus singkat
Kalau bingung:
- pilih baseline.

## 7. Kapan dual-side boleh dicoba

Dual-side adalah eksperimen terkontrol.
Bukan default produksi.

### 7.1 Syarat minimum sebelum dual-side dicoba
Dual-side baru layak dicoba jika:
- baseline sudah jelas dan stabil sebagai pembanding,
- candidate memang cukup kuat,
- operator ingin menguji upside sleeve, bukan mengobati conviction yang lemah,
- profile eksperimen dipisah dari baseline,
- size tetap kecil / guarded.

### 7.2 Use case dual-side yang masuk akal
Dual-side paling masuk akal saat:
- thesis utama tetap reclaim bullish,
- operator ingin memberi sedikit exposure upside tambahan,
- tapi tetap menjaga baseline behavior single-side sebagai jangkar utama.

### 7.3 Preset dual-side awal yang disiplin
```json
{
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": true,
  "dualSideTokenPct": 10,
  "dualSideUpsidePct": 12,
  "dualSideStrategy": "spot"
}
```

### 7.4 Jangan pakai dual-side jika motifnya salah
Jangan aktifkan dual-side bila:
- candidate sebenarnya mediocre,
- operator takut ketinggalan move lalu ingin "tambal" setup,
- operator belum punya baseline comparator,
- operator juga ingin ubah bins / sizing / screening sekaligus.

### 7.5 Rule audit dual-side
Kalau dual-side dipakai, evaluasi harus membandingkan terhadap:
- baseline single-side spot,
- pada kondisi thesis yang mirip,
- bukan dibanding random trade discretionary.

## 8. Checklist sesi manual vs bot

## 8.1 Checklist sesi bot
Checklist bot harus sederhana dan repeatable:
- profile yang dipakai baseline atau eksperimen?
- config masih sesuai preset?
- strategy masih `spot` locked kalau baseline?
- dual-side OFF kalau baseline?
- bins masih `35 / 52 / 52`?
- timeframe masih `5m`?
- promptNotes / lesson masih selaras reclaim thesis?
- tidak ada perubahan ekstra yang bikin eksperimen kotor?

Keputusan bot mode:
- kalau ragu, baseline,
- kalau mau test, test di profile terpisah,
- jangan campur profile produksi dengan eksperimen baru.

## 8.2 Checklist sesi manual / semi-manual
Sebelum deploy manual, tanya cepat:
1. pool quality lolos?
2. 15m context sehat?
3. reclaim 5m clean?
4. ini candidate biasa atau premium?
5. saya sedang pakai thesis reclaim atau diam-diam bergeser ke thesis lain?
6. baseline cukup, atau memang ada alasan auditable untuk eksperimen?
7. kalau eksperimen gagal, saya masih bisa menjelaskan kenapa eksperimen itu layak diuji?

Kalau 2 atau lebih jawaban terasa kabur:
- jangan deploy.

## 9. Management style policy

Policy ini sengaja ditulis sebagai behavior, bukan key literal.

### 9.1 Baseline management
Untuk baseline:
- manage lebih dekat ke `BE1 style`,
- cut ambiguity relatif cepat,
- jangan terlalu mengandalkan deep recovery,
- anggap capital protection lebih penting daripada memeras semua upside.

### 9.2 Premium management
Untuk candidate premium manual:
- boleh sedikit lebih sabar,
- tapi hanya jika alasan premium-nya jelas,
- dan tetap jangan berubah menjadi deep-recovery cult.

### 9.3 Eksperimen management
Untuk dual-side experiment:
- jangan sekaligus longgarkan management terlalu jauh,
- kalau deploy expression berubah, management sebaiknya tetap sedekat mungkin ke baseline dulu,
- supaya attribution hasil tetap bersih.

## 10. Field yang jangan diubah bersamaan

Supaya eksperimen tetap clean, jangan ubah banyak field ini dalam satu langkah:
- `strategyLock`
- `dualSideEnabled`
- `dualSideTokenPct`
- `dualSideUpsidePct`
- `dualSideStrategy`
- `minBinsBelow`
- `maxBinsBelow`
- `defaultBinsBelow`
- sizing utama
- screening looseness besar
- management tolerance besar

Rule:
- satu eksperimen sebaiknya punya satu pertanyaan utama,
- bukan sepuluh perubahan sekaligus.

## 11. Profile / instance layout recommendation

### Profile 1 — production baseline
Pakai untuk:
- bot utama,
- guarded live,
- pembanding utama.

Karakter:
- `spot`
- single-side
- `spot` locked
- dual-side OFF
- `35 / 52 / 52`
- `5m` engine
- `BE1 style`

### Profile 2 — dual-side experiment
Pakai untuk:
- paper,
- guarded live kecil,
- eksperimen upside sleeve.

Karakter:
- `spot` locked
- dual-side ON
- token sleeve kecil
- compare langsung vs baseline

### Profile 3 — manual sandbox
Pakai untuk:
- discretionary test,
- candidate premium,
- optional `curve` exploration,
- management variation yang tidak boleh langsung mencemari profile produksi.

## 12. Decision ladder singkat

Kalau mau super ringkas, operator bisa pakai ladder ini:

### Step 1
Pool sehat?
- tidak: skip
- ya: lanjut

### Step 2
15m context sehat?
- tidak: skip
- ya: lanjut

### Step 3
5m reclaim clean?
- tidak: skip
- ya: lanjut

### Step 4
Candidate biasa atau premium?
- biasa: baseline
- premium: baseline dulu, eksperimen hanya kalau ada alasan auditable

### Step 5
Perlu dual-side?
- kalau masih tanya-tanya: tidak
- kalau alasan jelas dan profile terpisah: boleh test kecil

## 13. Bottom line operator

Kalau hanya mau satu policy paling waras:
- deploy hanya pada pool sehat dengan reclaim timing bersih,
- pakai `spot` single-side baseline dulu,
- treat `dual-side` as controlled experiment only,
- pakai `5m` sebagai engine dan `15m` sebagai context,
- manage lebih dekat ke `BE1 style`,
- jangan ubah terlalu banyak variabel sekaligus.

Kalau ragu antara baseline vs eksperimen:
- baseline menang.

Kalau ragu antara deploy vs skip:
- skip lebih sehat daripada deploy jelek.
