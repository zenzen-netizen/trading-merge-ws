# Meridian Ready-to-Apply JSONs — Meteora Reclaim Setup

Tujuan:
- kasih block JSON yang lebih dekat ke `langsung pakai`,
- memudahkan copy-paste ke profile Meridian,
- menjaga baseline, dual-side, dan sandbox tetap terpisah rapi.

PENTING:
- ini template operasional,
- bukan jaminan semua key di instance sekarang 100% sama nama/final shape-nya,
- jadi pakai ini sebagai `ready draft payload`, lalu sesuaikan minor jika schema profile kamu sedikit beda.

Prinsip utama:
- baseline dulu,
- eksperimen dipisah,
- jangan ubah terlalu banyak field sekaligus.

## 1. Baseline profile — ready JSON

Nama intent:
- profile produksi utama
- guarded live baseline
- paper comparator utama

```json
{
  "activeSetup": "meteora-reclaim-baseline",
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": false,
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "timeframe": "5m",
  "screeningIntervalMin": 30,
  "managementIntervalMin": 10,
  "adaptiveScreening": true,
  "maxPositions": 2,
  "deployAmountSol": 0.05,
  "positionSizePct": 0.20,
  "maxDeployAmount": 0.10,
  "gasReserve": 0.03,
  "minSolToOpen": 0.12,
  "rentPerPositionSol": 0.057,
  "promptNotes": {
    "screener": [
      "Treat this setup as a bullish reclaim timing overlay, not a deep dip-buying system.",
      "Pool quality remains the first gate. Do not force a deploy just because chart timing looks attractive.",
      "Prefer healthy SOL pools with clean reclaim timing on 5m and non-damaged 15m context.",
      "Default deploy expression is spot and single-side SOL unless there is a very strong, auditable reason otherwise.",
      "Do not use creative strategy expression to compensate for weak conviction or poor pool quality.",
      "If the setup looks late, chaotic, or more like a random bounce than a clean reclaim continuation, prefer no-deploy."
    ],
    "manager": [
      "Manage this setup with ambiguity-cutting behavior closer to BE1 than deep recovery tolerance.",
      "Protect capital first. Do not assume deep drawdowns will recover.",
      "If reclaim thesis weakens quickly, prefer faster defensive action over hopeful tolerance.",
      "Large recovery expectations should be treated as exceptions, not as the default management mindset."
    ],
    "general": [
      "This profile is the baseline comparator for the Meteora reclaim thesis. Keep behavior stable and auditable."
    ]
  }
}
```

## 2. Dual-side experiment profile — ready JSON

Nama intent:
- eksperimen upside sleeve
- guarded live kecil
- paper experiment compare lawan baseline

```json
{
  "activeSetup": "meteora-reclaim-dualside-exp",
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": true,
  "dualSideTokenPct": 10,
  "dualSideUpsidePct": 12,
  "dualSideStrategy": "spot",
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "timeframe": "5m",
  "screeningIntervalMin": 30,
  "managementIntervalMin": 10,
  "adaptiveScreening": true,
  "maxPositions": 2,
  "deployAmountSol": 0.05,
  "positionSizePct": 0.20,
  "maxDeployAmount": 0.10,
  "gasReserve": 0.03,
  "minSolToOpen": 0.12,
  "rentPerPositionSol": 0.057,
  "promptNotes": {
    "screener": [
      "This profile is still a bullish reclaim timing overlay, not a new thesis.",
      "Pool quality remains the first gate. No deploy on weak or chaotic pools.",
      "Treat dual-side as a small upside sleeve experiment layered on top of the baseline spot reclaim thesis.",
      "Keep the token sleeve small and only use this profile when the candidate is already strong enough on baseline terms.",
      "Do not use dual-side to rescue weak conviction, late timing, or damaged context.",
      "Compare decisions and outcomes against the baseline single-side spot profile, not against random discretionary trades."
    ],
    "manager": [
      "Keep management close to baseline BE1-style behavior so attribution stays clean.",
      "Do not simultaneously loosen management just because deploy expression is more experimental.",
      "If thesis weakens, protect capital first and avoid turning the experiment into a deep-recovery hold."
    ],
    "general": [
      "This profile exists to test a controlled dual-side upside sleeve, not to replace the baseline production profile."
    ]
  }
}
```

## 3. Manual sandbox profile — ready JSON

Nama intent:
- discretionary operator
- candidate premium
- optional `curve` exploration
- sandbox pembelajaran

```json
{
  "activeSetup": "meteora-reclaim-manual",
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": false,
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "timeframe": "5m",
  "screeningIntervalMin": 30,
  "managementIntervalMin": 10,
  "adaptiveScreening": true,
  "maxPositions": 2,
  "deployAmountSol": 0.05,
  "positionSizePct": 0.20,
  "maxDeployAmount": 0.10,
  "gasReserve": 0.03,
  "minSolToOpen": 0.12,
  "rentPerPositionSol": 0.057,
  "promptNotes": {
    "screener": [
      "Use the same reclaim thesis: pool quality first, then context, then timing.",
      "Only treat a candidate as premium when the edge can be explained clearly and simply.",
      "Manual flexibility does not mean lower discipline. Skip chaotic or low-quality pools even when chart timing looks tempting.",
      "Default expression remains spot. Curve is optional and only for deliberate sandbox exploration.",
      "Bid-ask should only be considered when the thesis explicitly shifts toward dip-accumulation or fee-capture, not standard reclaim continuation."
    ],
    "manager": [
      "Default to BE1-style protection even in manual mode.",
      "Slightly more patience is acceptable only for truly premium candidates with clear justification.",
      "Do not turn manual discretion into unchecked deep recovery tolerance."
    ],
    "general": [
      "This profile is a sandbox for discretionary learning, not the source of truth for production without proper comparison."
    ]
  }
}
```

## 4. Optional lesson text — ready snippets

Kalau mau tambah operator lesson terpisah, bisa pakai snippet ini.

### 4.1 Baseline lesson
```text
[GATE] Treat Meteora reclaim as a pool-quality-first timing overlay. Clean reclaim timing cannot rescue weak pool quality.
```

### 4.2 Dual-side lesson
```text
[EXPERIMENT] Dual-side is only a small upside sleeve experiment on top of the baseline spot reclaim thesis. Never use it to compensate for weak conviction.
```

### 4.3 Manual premium lesson
```text
[PREMIUM] A premium candidate must be explainable in simple terms: stronger-than-usual pool quality, clean 15m context, and clean 5m reclaim continuation.
```

## 5. Ready mini-blocks only

Kalau kamu cuma mau block inti tanpa size + notes, pakai ini.

### 5.1 Baseline mini-block
```json
{
  "activeSetup": "meteora-reclaim-baseline",
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

### 5.2 Dual-side mini-block
```json
{
  "activeSetup": "meteora-reclaim-dualside-exp",
  "solMode": true,
  "strategy": "spot",
  "strategyLock": "spot",
  "dualSideEnabled": true,
  "dualSideTokenPct": 10,
  "dualSideUpsidePct": 12,
  "dualSideStrategy": "spot",
  "minBinsBelow": 35,
  "maxBinsBelow": 52,
  "defaultBinsBelow": 52,
  "timeframe": "5m"
}
```

### 5.3 Manual mini-block
```json
{
  "activeSetup": "meteora-reclaim-manual",
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

## 6. Apply discipline

Rule pakai:
- baseline profile = block baseline
- dual-side profile = block dual-side
- manual sandbox = block manual
- jangan campur block eksperimen ke baseline
- jangan ubah bins + dual-side + sizing + management sekaligus

## 7. Bottom line

Kalau mau paling praktis sekarang:
- produksi utama pakai JSON baseline
- eksperimen pakai JSON dual-side
- discretionary test pakai JSON manual sandbox

Kalau bingung pilih mana:
- baseline.