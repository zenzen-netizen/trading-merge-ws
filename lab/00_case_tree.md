# Case Tree — Kalibrasi Setup [nama_strategi]

Tracker ini rangkum perkembangan pemahaman setup dari seluruh case study, versi demi versi. Diupdate setiap kali case baru dibuat — jangan cuma andalkan file case individual, karena tujuan tracker ini justru supaya tidak perlu buka semua file satu-satu untuk tahu pemahaman terkini.

Copy folder `case_studies/` dari `strategies/_template/` tiap mulai kalibrasi strategi baru, lalu isi tracker ini dari awal (mulai dari kosong, "Belum ada versi").

---

## Versi Aturan Setup Saat Ini

> Bagian ini SELALU mencerminkan pemahaman paling baru — ditimpa/diupdate tiap ada versi baru, bukan riwayat. Untuk riwayat lengkap, lihat tree di bawah.

**Versi aktif**: belum ada (isi setelah `case_v1` selesai dibuat)

**Aturan final saat ini**: —

---

## Tree Perkembangan Versi

```
Kalibrasi Setup [nama_strategi]
│
└─ (belum ada versi — mulai dengan case_v1.md)
```

Contoh format setelah beberapa versi berjalan (ganti sesuai kasus nyata):

```
Kalibrasi Setup [nama_strategi]
│
├─ v1 — Window: 2024-01-01 s/d 2024-01-15
│   └─ Aturan awal: RSI(14) < 30 + MA(50) cross up
│
├─ v2 — Window: 2024-02-10 s/d 2024-02-20
│   └─ Koreksi: tambah syarat volume ≥ 1.5x rata-rata,
│      karena ditemukan near-miss di v1 tanpa volume ini
│
└─ v3 — Window: 2024-03-05 s/d 2024-03-12
    └─ Konfirmasi: aturan v2 valid, tidak ada perubahan,
       dipakai sebagai kasus penguat/reinforcement
```

## Cara Update Tracker Ini

1. Habis bikin `case_v{N}.md` baru, tambah satu baris di tree di atas: nomor versi, window waktu, dan ringkasan satu baris apa yang berubah atau dikonfirmasi.
2. Update bagian "Versi Aturan Setup Saat Ini" di atas dengan aturan final terbaru — bagian ini representasi tunggal yang paling akurat, harus selalu sinkron dengan case versi tertinggi.
3. Kalau sebuah versi cuma mengonfirmasi (tidak ada perubahan aturan), tetap dicatat di tree — ini juga informasi berharga (menunjukkan aturan sudah stabil, bukan cuma kebetulan cocok di satu kasus).
4. Begitu kalibrasi dirasa cukup matang (beberapa versi terakhir berturut-turut cuma konfirmasi, tidak ada koreksi lagi), pemahaman ini siap dibawa ke step "Rule strategi" untuk diterjemahkan jadi kode.

## Riwayat Update Tracker

- Tracker dibuat, belum ada case study.
