# U5Spring Tuning Guide

Tujuan:
- jawab cepat file mana disentuh saat mau tuning sesuatu
- cegah salah layer

## 1. Mau tuning thesis
Sentuh:
- `../02-thesis/setup-notes.md`
- `../02-thesis/meridian-thesis.md`

Jangan mulai dari payload kalau problem sebenarnya thesis.

## 2. Mau tuning deploy/skip decision rule
Sentuh:
- `../03-operator/playbook.md`
- `../03-operator/playbook-compact.md`
- kadang `../04-meridian/promptnotes.md`

## 3. Mau tuning config numbers / profile defaults
Sentuh:
- `../04-meridian/config-draft.md`
- `../04-meridian/profile-mapping.md`
- `../04-meridian/ready-jsons.md`
- payload `.json` di `../05-payloads/ready-load-profiles/`

## 4. Mau tuning wording prompt / soft guidance
Sentuh:
- `../04-meridian/promptnotes.md`

## 5. Mau tuning ready-load profile
Sentuh:
- `../05-payloads/ready-load-profiles/baseline.user-config.json`
- `../05-payloads/ready-load-profiles/dualside-exp.user-config.json`
- `../05-payloads/ready-load-profiles/manual-sandbox.user-config.json`

## 6. Mau audit apakah tuning masih sesuai evidence
Cek ulang:
- `../01-research/chart-backtests/rsi-fractal-mhermes-be/full-report.md`
- `../01-research/chart-backtests/rsi-fractal-mhermes-be/summary.md`
- `../01-research/chart-backtests/rsi-fractal-mhermes-be/trade-journal.csv`

## 7. Golden rule
Urutan sehat:
- evidence
- thesis
- doctrine
- meridian translation
- payload

Kalau payload diubah duluan tanpa cek layer atas, strategi gampang drift.

## 8. Kalau mau eksperimen baru
Mulai dari:
- `experiment-guide.md`
- `experiment-template.md`
- `templates/README.md`

Rule cepat:
- baseline jangan ditimpa
- satu eksperimen satu pertanyaan
- mulai dari `01-research`
- naik ke thesis/operator/Meridian/payload hanya kalau evidence cukup kuat
