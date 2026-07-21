# FBF v11 — cluster indikator + backtest engine

Acuan: `fbf_v11.pine` (salinan persis dari kode Pine FBF v11 yang
dikirim user). Semua engine di bawah ini chart-faithful: output =
APA YANG USER LIHAT di chart TradingView (default setting), bukan lebih.

## File

- `fbf_v11.pine`        — source Pine v11 (sumber kebenaran).
- `fbf_v11_backtest.py` — **ENGINE DEFAULT** (di /home/ubuntu/, bukan sini).
                           Persis brief §2: seluruh filter default ON kecuali
                           Persist & SMI (OFF). Ini yang dicocokan langsung
                           dengan chart user. JANGAN ubah file ini.
- `fbf_v11_mhermes.py`  — **ENGINE ALTERNATIF (STRICT), buatan mhermes** —
                           file BARU, terpisah, tidak menyentuh engine default.
                           Basis brief + Pine, TAPI mengaktifkan 2 filter
                           opsional yang di default OFF:
                             • Persistence = 2  (kandidat harus bertahan
                                              ≥2 bar di luar level B)
                             • SMI agreement    (arah SMI harus searah break)
                           Hasilnya = SUBSET lebih ketat dari default →
                           alat crosscheck (lihat false-positive default).
                           Plus perbaikan kecil: ST gate pakai ST-ATR(10)
                           sendiri (bukan ATR14 utama) — netral di BTC
                           karena flip trend ST ditentukan HARGA, tapi lebih
                           benar secarra intern.

## Cara pakai

    # default (mirror chart user)
    python3 /home/ubuntu/fbf_v11_backtest.py --symbol BTCUSDT --interval 4h --bars 800

    # alternatif strict (buatan mhermes)
    python3 fbf_v11_mhermes.py --symbol BTCUSDT --interval 1h --bars 1500

    # diagnosa: kronologi event di sekitar 1 waktu
    python3 fbf_v11_mhermes.py --symbol BTCUSDT --interval 1h --bars 1500 \
        --explain "2026-05-19T00:00" --explain-window 12

Output: tabel BREAK di stdout + `fbf_breaks_*.csv` (data utama) +
`fbf_events_*.csv` (semua event, istilah visual: WAVE_STARTED,
C_LOCKED, B_LINE_TRACKING, CANDIDATE_FAILED ✖, BREAK, dst).

CSV mhermes ditandai suffix `_mhermes` supaya tidak menimpa CSV default.

## Bukti konsistensi (BTCUSDT 1h, 1500 bar)

- Tracker IDENTIK di kedua engine:
  C_LOCKED=170, WAVE_STARTED=265, WAVE_CANCELLED=75,
  WAVE_STRUCT_REJECTED=20  (SAMA PERSIS).
- BREAK: default=28, alt-strict=27. Alt lebih sedikit & sebagian
  confirm TERLAMBAT 1 bar (Persist=2) — wajar. 4 BREAK alt yang
  level-B-nya tidak ada di default = di default berstatus
  BREAK_HIDDEN_BY_TREND (strict menunda, pas confirm ST sudah
  searah). BUKAN bug.

## Jebakan yang sudah diamankan (lihat brief §7)

1. ATR = RMA/Wilder (bukan SMA).
2. Pivot = semantik ta.pivothigh/low persis, lag = rightBars.
3. Non-repaint: hanya candle CLOSED; candle Binance terakhir dibuang.
4. Urutan per bar: Stasiun0 → Tracker → Juri; kandidat lahir via
   breakout bisa aktif bar itu juga.
5. Supertrend seed trend=1, band/flip persis Pine.
6. Gate trend (enableStTrendFilter) ditaruh di LAPISAN OUTPUT, bukan
   mesin — state last_confirmed & hapus kandidat tetap update.
7. Data feed beda = beda DATA, bukan bug (cek OHLC dulu).
8. noDuplicate = kunci per b_bar per sisi.
9. A2 (distAOk) pakai ATR saat BAR EVALUASI.
10. Fade lookback = kosmetik, event lama TIDAK dibuang.
