#!/usr/bin/env bash
# SETUP1 batch runner — jalanin 1D/2H/4H, simpan per run ke results/<ts>/
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
LOG="$BASE/batch_${TS}.log"
echo "=== SETUP1 batch @ $TS ===" | tee "$LOG"
for tf in 1D 2H 4H; do
  echo "" | tee -a "$LOG"
  echo ">>> RUN $tf" | tee -a "$LOG"
  pushd "$BASE/$tf" >/dev/null || { echo "MISSING $tf"; continue; }
  # tee stdout ke results/<ts>/summary.txt sekaligus log batch
  RUN_TS="$TS" python3 backtest.py 2>&1 | tee -a "$LOG" > "$BASE/$tf/results/${TS}/summary.txt"
  popd >/dev/null
done
echo "" | tee -a "$LOG"
echo "=== DONE @ $TS ===" | tee -a "$LOG"
echo "Results: $BASE/{1D,2H,4H}/results/$TS/"
