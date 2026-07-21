# SETUP1 SHORT — TRIGGER SPEC (v1 & v2)

Tujuan: pisahkan ENTRY TRIGGER dari exit (SL/TP/TRAIL).
Trigger = "kapan kita MASUK". SL/TP/TRAIL = "kapan kita KELUAR"
(lihat TRADE_TEMPLATE.md untuk exit). File ini HANYA soal trigger.

Konvensi nama arsip (tag di journal / report):
  S1S-TRG-v1 = SETUP1 SHORT TRIGGER v1 (base FBF v6.10)
  S1S-TRG-v2 = SETUP1 SHORT TRIGGER v2 (base FBF v11, alur umum)
  S1S-TRG-v2.a = v2 + rule "1 wave = 1 posisi" (filter backtest)
  "S1S" = Setup 1 Short.

================================================================
BAGIAN UMUM (sama di v1 & v2)
================================================================
Arah: SHORT (jual leverage).
Pair/TF: BTCUSDT 1D / 2H / 4H (backtest engine).
Timezone: WIB (UTC+8) — entry_time = jam close bar.

--- SMI Pro v3 (3-step confluence) — TETAP SAMA rule-nya ---
Urutan HARUS berurutan di bar yang naik:
  FMB  = [!] Fail MID Buy  (SMI gagal hold di mid, bearish)
  PD   = [~]/[OK] PD / "PD TRIGGERED"  (distribusi)
  XDN  = [X] Cross DN  (SMI %K cross di bawah %D = confirm)
Entry SMI = close bar XDN.

--- ST gate (Supertrend) ---
  ST downtrend (-1) di bar C confirm DAN di bar entry (XDN).
  v1: supertrend_full(period=10, mult=3.0) manual.
  v2: ST-ATR(10) internal FBF v11 (sama semantik, netral di BTC).

--- Validity window ---
  Wave/AB batal (tidak masuk) kalau sebelum entry terjadi:
  v1: close > A_val (wave bull batal) / C belum > B saat entry.
  v2: WAVE_CANCELLED / WAVE_STRUCT_REJECTED / CANDIDATE_INVALIDATED.

================================================================
S1S-TRG-v1  (base FBF v6.10 — engine lama di backtest.py)
================================================================
Alur FBF (AB manual, scan pivot):
  1. A = pivot high, B = pivot low, syarat A_val > B_val.
  2. bear break: close[i] < B_val.
  3. confirm = B_bar + 3.
  4. C = pivot high sesudah B dgn C_val > B_val (struktur valid).
  AB confirm = saat C_val > B_val terdeteksi (C > B).

Entry rule (AND):
  - AB confirm (C > B) sudah terjadi SEBELUM entry.
  - SMI 3-step lengkap: FMB → PD → XDN (XDN di bar >= FMB).
  - ST gate ok di bar C dan bar XDN.
  - Entry price = close bar XDN.
  - Loop batas: sampai close < B_val (end), kalau C_bar > end -> skip.

Catatan: ini yang JALAN di backtest.py SETUP1/1D (dan 2H/4H legacy).

================================================================
S1S-TRG-v2  (base FBF v11 — LOCK di B, entry no-wait C) [alur umum]
================================================================
Base: fbf_v11_backtest.py (engine default, utuh, chart-faithful).
Event visual v11 (istilah chart): WAVE_STARTED, C_LOCKED,
B_LINE_TRACKING, BREAK, WAVE_CANCELLED, WAVE_STRUCT_REJECTED.

Alur FBF v11 (LOCK cuma di B, SMI dipantau selama tracking C?):
  Tahap 0 — LOCK di B (WAVE_STARTED):
    FBF v11 WAVE_STARTED (side bear) = A pivot high > B pivot low
    terkunci, wave bear mulai. INI cukup sebagai "lock" kita —
    TIDAK perlu nunggu C. Catat A_bar/A_val, B_bar/B_val.
    (B = titik lock tunggal. C tidak wajib di-confirm untuk entry.)

  Tahap 1 — C? tracking window (AREA VALID = tempat SMI dicek):
    Setelah WAVE_STARTED, FBF mulai tracking C? (running extreme
    low bear-side, belum tentatif locked). Selama window ini BELUM
    terjadi WAVE_CANCELLED / WAVE_STRUCT_REJECTED,
    area dianggap VALID -> KITA PANTAU SMI 3-step
    (FMB → PD → XDN) sebagai confluence.
    NOTE: C_LOCKED tetap boleh terjadi nanti, tapi BUKAN syarat.
    Kalau C_LOCKED kejadian duluan sebelum XDN, ya gapapa — yang
    penting entry di-tripper oleh SMI, bukan oleh C.

Entry rule (AND) — entry = SMI selesai, TANPA tunggu C:
  - WAVE_STARTED SUDAH terjadi (AB locked di B).
  - SMI 3-step lengkap SELAMA window tracking C? (belum cancel):
      FMB → PD → XDN, XDN di bar >= FMB.
    Boleh terjadi SEBELUM maupun SESUDAH C_LOCKED — asal masih
    dalam validity wave (belum WAVE_CANCELLED / REJECTED).
  - ST gate ok di bar entry (XDN).
      (v1 butuh ST gate di bar C + bar entry; v2 cukup di bar entry
       karena C bukan lagi gate — boleh tambah ST di WAVE_STARTED
       kalau mau stricter.)
  - Entry price = close bar XDN — TIDAK perlu max(C_LOCKED, XDN),
    karena C confirm tidak wajib. XDN sendiri yang jadi trigger.
  - Fallback (opsional): event BREAK v11 (aktivasi + persist>=2,
    ST-gated) bisa jadi entry alternatif, tapi DEFAULT trigger =
    WAVE_STARTED + SMI 3-step (XDN) selama C? tracking valid.

RULE POSISI v2.a (tambahan di ATAS v2 umum — BERLAKU WAKTU DIPAKAI DI BACKTEST):
  v2.a = v2 alur umum + rule "1 wave = 1 posisi" di bawah.
  v2 tetap pakai alur umum (tanpa rule ini) kalau gak butuh filter
  posisi. v2.a dipakai kalau mau batasi 1 posisi per wave.
  Satu rangkaian wave ABC = cerminan 1 TRIGGER = MAKS 1 POSISI.
  - Tiap wave (WAVE_STARTED ... sampai wave selesai/cancel) hanya
    boleh membuka 1 posisi short, meski SMI 3-step sempat lengkap
    lebih dari sekali di dalam window yang sama.
  - Setelah 1 posisi terbuka, wave-wave BERIKUTNYA (WAVE_STARTED
    baru) DIABAIKAN dulu sampai posisi itu CLEAR:
        clear = kena SL  / kena TP  / kena TRAILING exit
    (belum clear = masih open, baik floating profit/loss).
  - Baru setelah clear, WAVE_STARTED berikutnya boleh di-evaluasi
    lagi sebagai trigger potensial.
  - Tujuannya: cegah over-trade / stacking posisi di cluster wave
    dalam 1 sesi; 1 trigger = 1 posisi = 1 hasil R.

Perbedaan v1 vs v2 (inti):
  - v1: lock di B, C confirm manual (close > B). SMI dicek SETELAH C.
        entry = close XDN SETELAH C>B.
  - v2: lock cuma di B (WAVE_STARTED). SMI dipantau PARALER selama
        FBF masih tracking C? (belum cancel). Begitu SMI 3-step
        lengkap (XDN), LANGSUNG trigger entry — TDK usah tunggu
        C_LOCKED. entry = close XDN (saat SMI confirm).
  - Base indikator beda: v6.10 (AB manual) vs v11 (wave tracker
    + juri + ST-ATR + fibo zone).
  - Implikasi: v2 akan menghasilkan entry LEBIH AWAL + LEBIH BANYAK
    (tidak ke-filter oleh C belum confirm). Risk: bisa entry saat
    struktur C belum jelas (false C? yang batal). Perlu cek PF.

================================================================
STATUS
================================================================
- v1: JALAN di backtest.py (SETUP1/1D, 2H, 4H).
- v2: SPEC ini baru (belum di-code ke backtest). Engine bridge
  sudah ada: indicators/fbf_v11 + backtests/.../1D/fbf_v11_signal.py
  (ambil BREAK bear / WAVE_STARTED). Untuk v2 trigger cukup pakai
  event WAVE_STARTED (lock di B) + smi_pro 3-step overlapping SELAMA
  window C? tracking (belum WAVE_CANCELLED/REJECTED). TIDAK perlu
  menunggu C_LOCKED. entry = close XDN.
- TODO (kalau lanjut): tulis backtest_v2.py yang pakai
  FBFEngine event WAVE_STARTED sebagai lock + smi_pro 3-step
  overlap (XDN trigger), tanpa gate C_LOCKED.
  backtest_v2a.py = versi + rule v2.a (1 wave = 1 posisi).

================================================================
CROSS-CHECK DGN TV
================================================================
- v1: entry = close bar XDN setelah C>B. Cocokkan dgn chart:
  SMI Cross DN + FBF bear break.
- v2: entry = close bar XDN saat SMI 3-step lengkap, SELAMA FBF
  masih tracking C? (WAVE_STARTED aktif, belum WAVE_CANCELLED/
  REJECTED). Tidak perlu nunggu C_LOCKED. Di chart TV, cek:
  FBF v11 wave bear STARTED (label A/B), lalu SMI Cross DN — entry
  di close bar XDN itu. Pastikan wave belum cancelled.

================================================================
UPDATE 14 Jul 2026 — v3 (aktif, menggantikan v2.b)
================================================================
v3 fix vs v2.b: FULL RESET setiap WAVE_STARTED.

```python
# v2.b (BUG) — partial reset
if pd_b is None: fmb_b = None

# v3 (FIXED) — unconditional
fmb_b = None; pd_b = None
```

Detail: CHANGELOG_v3.md dan SETUP_SPEC_v3.md di direktori yang sama.
Module shared: indicators/setup1_trigger.py (source of truth).
