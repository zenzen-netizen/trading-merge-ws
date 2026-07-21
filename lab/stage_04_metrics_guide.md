# Stage 4 — Panduan Metrics Calculator (`metrics.py`)

Dokumen ini menjelaskan arti tiap komponen di `metrics.py` — bukan sekadar apa fungsinya dalam kode, tapi kenapa metric itu penting dan bagaimana cara membacanya saat menganalisis hasil backtest.

---

## A. Profitabilitas Dasar

### Net Profit (`net_profit_abs`, `net_profit_pct`)
Total untung/rugi bersih dari seluruh trade, dalam nominal dan persentase modal awal.

Cara baca: angka ini paling gampang disalahartikan sebagai "ukuran keberhasilan utama". Padahal net profit tinggi bisa dihasilkan dari satu-dua trade beruntung di sampel kecil — tidak berarti strategi robust. Selalu baca berdampingan dengan jumlah total trade dan max drawdown.

### Win Rate (`win_rate_pct`)
Persentase trade yang closing dengan profit.

Cara baca: win rate tinggi terasa enak secara psikologis, tapi **tidak berarti apa-apa tanpa konteks risk-reward**. Strategi dengan win rate 30% bisa lebih menguntungkan daripada win rate 60%, tergantung berapa besar tiap kemenangan dibanding tiap kekalahan. Lihat bagian EV Framework di bawah untuk konteks lengkapnya.

### Profit Factor (`profit_factor`)
Total profit dari trade menang dibagi total kerugian dari trade kalah (dalam nilai absolut).

Cara baca: angka di atas 1 berarti strategi profitable secara kasar. Sebagai patokan umum, di atas 1.5 mulai dianggap sehat, di atas 2 tergolong kuat. Tapi seperti metric lain, tidak berarti apa-apa kalau jumlah trade masih sedikit.

### Avg Win / Avg Loss / Realized RR (`avg_win`, `avg_loss`, `realized_rr`)
Rata-rata besar kemenangan, rata-rata besar kekalahan, dan rasio keduanya (realized risk-reward — bukan target RR yang direncanakan, tapi RR aktual yang benar-benar terjadi di backtest).

Cara baca: bandingkan realized RR dengan RR yang direncanakan saat desain strategi. Kalau jauh berbeda (misalnya rencana 1:3 tapi realized cuma 1:1.2), berarti ada masalah di eksekusi — mungkin take profit kepotong, atau exit rule tidak konsisten dieksekusi backtest engine.

### Expectancy (`expectancy_abs`, `expectancy_r`)
Rata-rata untung/rugi per trade. Versi `_abs` dalam nominal uang, versi `_r` dalam satuan risk (R) — expectancy dalam R lebih portable karena bisa dibandingkan antar strategi atau pair yang pakai ukuran posisi berbeda.

Cara baca: ini metric ringkasan paling jujur untuk "apakah strategi ini menguntungkan secara matematis". Angka positif dalam R berarti setiap kali risk 1 unit, rata-rata dapat lebih dari itu kembali.

---

## B. Konsistensi & Risiko Psikologis

### Max Consecutive Losses / Wins (`max_consecutive_losses`, `max_consecutive_wins`)
Rentetan kalah atau menang terpanjang yang tercatat di backtest.

Cara baca: angka ini penting untuk kesiapan mental dan sizing, bukan cuma statistik. Kalau strategi punya rentetan 8 kali kalah beruntun dalam backtest, itu **akan** terjadi lagi saat live — pertanyaannya bukan "apakah", tapi "apakah risk per trade cukup kecil untuk bertahan saat itu terjadi". Bandingkan dengan tabel Ruin Probability di bagian G.

---

## C. Drawdown & Recovery

### Max Drawdown (`max_drawdown_pct`)
Penurunan terbesar dari titik puncak equity ke titik terendah berikutnya, dalam persentase.

Cara baca: ini salah satu metric paling penting untuk menilai apakah strategi "layak dijalani" secara psikologis, bukan cuma menguntungkan di atas kertas. Drawdown 20% terdengar kecil di spreadsheet, tapi menjalani penurunan modal 20% secara real time jauh lebih berat dari yang dibayangkan.

### Recovery Bars & In Drawdown (`recovery_bars`, `in_drawdown`)
Berapa lama (dalam satuan candle/bar) equity butuh untuk kembali ke puncak sebelumnya setelah drawdown terdalam. `in_drawdown` bernilai true kalau sampai akhir data backtest, equity belum pernah kembali ke puncak lama.

Cara baca: kalau `in_drawdown` true, itu sinyal waspada — artinya periode backtest berakhir saat strategi masih dalam kondisi rugi dari puncaknya, belum terbukti bisa pulih.

### Drawdown Recovery Requirement (`drawdown_recovery_required_pct`)
Persentase gain yang dibutuhkan untuk kembali ke modal awal, dihitung dari max drawdown.

Cara baca: recovery itu tidak simetris — rugi 30% butuh untung 42.9% untuk balik modal, rugi 50% butuh untung 100% (dobel modal). Metric ini secara eksplisit menunjukkan seberapa berat beban recovery, yang sering diremehkan kalau cuma lihat angka drawdown mentah.

### Recovery Factor (`recovery_factor`)
Net profit dibagi max drawdown (dalam nominal). Mengukur efisiensi: berapa banyak profit yang dihasilkan relatif terhadap risiko drawdown yang harus ditanggung untuk mencapainya.

Cara baca: semakin tinggi semakin baik. Recovery factor 3 berarti profit tiga kali lipat dari drawdown terdalam yang pernah dialami.

---

## D. Risk-Adjusted Return

### Sharpe Ratio (`sharpe_ratio`)
Mengukur return per unit risiko, di mana risiko didefinisikan sebagai volatilitas total (naik maupun turun).

Cara baca: berguna untuk membandingkan strategi secara apple-to-apple, tapi Sharpe punya kelemahan — dia menghukum volatilitas ke atas (lonjakan profit besar) sama seperti volatilitas ke bawah, padahal trader biasanya cuma peduli sisi turunnya.

### Sortino Ratio (`sortino_ratio`)
Mirip Sharpe, tapi hanya memperhitungkan volatilitas ke sisi rugi (downside deviation), mengabaikan lonjakan profit sebagai "risiko".

Cara baca: lebih representatif dibanding Sharpe untuk strategi yang punya profit tidak simetris — misalnya trend following yang sesekali profit besar. Kalau Sortino jauh lebih tinggi dari Sharpe, itu tanda strategi punya beberapa winning trade besar yang mendorong return.

---

## E. Exposure

### Exposure Percentage (`exposure_pct`)
Perkiraan persentase waktu modal benar-benar berada di posisi (in-market), dibanding total waktu backtest.

Cara baca: exposure rendah dengan return bagus berarti efisiensi modal tinggi — profit dicapai tanpa modal terus-menerus terkunci di posisi. Ini relevan kalau modal yang sama juga ingin dipakai untuk strategi lain secara bersamaan.

---

## F. Efisiensi Entry/Exit (MAE/MFE)

### MAE — Maximum Adverse Excursion (`avg_mae`)
Rata-rata jarak terjauh yang ditempuh harga melawan posisi, sebelum trade akhirnya closing (profit atau rugi).

Cara baca: kalau MAE rata-rata jauh lebih kecil dari jarak stop loss yang dipakai, itu sinyal stop loss mungkin terlalu longgar — bisa dipersempit tanpa banyak menambah risiko kena stop prematur.

### MFE — Maximum Favorable Excursion (`avg_mfe`)
Rata-rata jarak terjauh yang ditempuh harga searah profit, sebelum akhirnya retrace atau exit.

Cara baca: kalau MFE rata-rata jauh lebih besar dari profit yang benar-benar direalisasi, itu sinyal take profit mungkin terlalu cepat — banyak potensi profit "kebuang" karena exit sebelum waktunya.

### Edge Ratio (`edge_ratio`)
Rasio MFE dibagi MAE. Mengukur secara umum apakah potensi profit di setiap trade cenderung lebih besar dari potensi rugi, terlepas dari hasil akhirnya.

Cara baca: edge ratio di atas 1 artinya secara struktural setup entry punya kecenderungan bergerak lebih jauh searah profit dibanding melawan posisi — sinyal bagus soal kualitas titik entry.

### Trade Efficiency (`trade_efficiency_pct`)
Persentase profit yang benar-benar direalisasi dibanding potensi maksimal (MFE) yang sempat tercapai selama trade berjalan.

Cara baca: angka 100% berarti exit persis di titik terbaik (jarang terjadi). Angka rendah (misalnya 30-40%) menunjukkan banyak profit potensial dilepas begitu saja. **Catatan implementasi**: metric ini cuma valid kalau MFE dihitung dari titik tertinggi/terendah candle selama trade berjalan, bukan cuma dari titik exit — kalau backtest engine salah tracking ini, angka efficiency bisa muncul di atas 100% yang secara logika mustahil.

---

## G. Expected Value Framework

### EV per Trade dalam R (`ev_per_trade_r`)
Formula: `win_rate × realized_RR − (1 − win_rate)`. Mengukur rata-rata hasil per trade dalam satuan risk, menggabungkan win rate dan risk-reward jadi satu angka.

Cara baca: ini metric paling penting untuk menjawab pertanyaan "apakah strategi ini layak dijalankan secara matematis". Positif berarti secara statistik menguntungkan jangka panjang; negatif berarti tidak ada jumlah disiplin yang bisa menyelamatkannya.

### Breakeven Win Rate (`breakeven_win_rate`)
Formula: `1 / (RR + 1)`. Win rate minimum yang dibutuhkan supaya EV tidak negatif, given risk-reward yang dipakai.

Cara baca: dipakai berdampingan dengan win rate aktual. Semakin besar RR, semakin rendah breakeven win rate yang dibutuhkan — artinya strategi dengan RR tinggi "dimaafkan" untuk sering salah arah.

### WR vs Breakeven Gap (`wr_vs_breakeven_gap`)
Selisih antara win rate aktual dan breakeven win rate.

Cara baca: ini "margin aman" strategi. Gap positif besar berarti strategi punya buffer — meskipun performa sedikit menurun di masa depan (win rate turun), strategi masih tetap profitable. Gap tipis atau negatif berarti strategi rapuh terhadap sedikit saja penurunan performa.

---

## Tabel Probabilitas Loss Beruntun (`p_loss_streak_5`, `_7`, `_10`)
Probabilitas mengalami 5, 7, atau 10 kali kalah beruntun, dihitung dari win rate strategi: `(1 − win_rate)^n`.

Cara baca: ini bukan metric "bagus/jelek", tapi alat kesiapan mental dan penentu ukuran risk per trade. Kalau probabilitas kena 7 loss beruntun cukup tinggi (misalnya di atas 5%), risk per trade harus disetel cukup kecil supaya rentetan itu tidak menghancurkan modal saat — bukan kalau — itu terjadi.

---

## H. Validitas Statistik

### Sample Size Warning (`sample_size_warning`)
Flag otomatis bernilai true kalau total trade di bawah 30.

Cara baca: semua metric di atas — terutama win rate dan EV — tidak reliable secara statistik dengan sampel kecil. Kalau flag ini true, kesimpulan apa pun dari run tersebut harus dianggap sementara, bukan final.

---

## I. Biaya Operasional

### Annual Fee Drag (`annual_fee_abs`)
Total biaya trading (fee masuk + keluar) dalam setahun, dihitung dari frekuensi trade dan ukuran posisi rata-rata.

### Annual Funding Drag (`annual_funding_abs`)
Khusus posisi leverage/perpetual futures yang diinapkan — biaya sewa posisi yang dibayar tiap 8 jam.

### Total Drag vs Modal (`annual_total_drag_pct_capital`)
Gabungan fee dan funding drag, dibandingkan terhadap modal awal.

Cara baca: aturan umum, total drag tahunan idealnya di bawah 20% dari modal. Kalau lebih dari itu, gaya trading yang dipilih (misalnya scalping frekuensi tinggi atau leverage tinggi) kemungkinan besar tidak cocok untuk skala modal yang dipakai — terlepas dari seberapa bagus sinyal entry-nya.

---

## Ringkasan Cara Pakai

Urutan baca yang disarankan saat evaluasi hasil satu run backtest:

1. Cek `sample_size_warning` dulu — kalau true, semua kesimpulan di bawah ini sementara.
2. Cek `ev_per_trade_r` dan `wr_vs_breakeven_gap` — ini jawaban inti "apakah strategi ini matematis menguntungkan".
3. Cek `max_drawdown_pct` dan `drawdown_recovery_required_pct` — apakah secara psikologis dan finansial strategi ini bisa dijalani.
4. Cek `p_loss_streak_7` dan `p_loss_streak_10` — apakah risk per trade sudah cukup kecil untuk bertahan dari rentetan kalah yang pasti akan terjadi.
5. Baru setelah empat hal di atas aman, lihat metric lain (Sharpe, edge ratio, exposure, dll) untuk membandingkan dan mengoptimalkan antar strategi.
