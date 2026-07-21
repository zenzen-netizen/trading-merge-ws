# Meridian PromptNotes Final — Meteora Reclaim Setup

Tujuan:
- memberi draft `promptNotes` final yang siap dipakai,
- menjaga screener, manager, dan general tetap satu thesis,
- memisahkan baseline dan dual-side experiment.

PENTING:
- ini draft policy text,
- bukan berarti semua kalimat wajib dipakai verbatim,
- tapi wording sengaja dibuat dekat dengan thesis dan playbook.

## 1. Baseline profile — promptNotes final

```json
{
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

## 2. Dual-side experiment profile — promptNotes final

```json
{
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

## 3. Manual / sandbox profile — promptNotes final

```json
{
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

## 4. Optional lessons text

Kalau mau tambah `lessons.json` style note, ini draft ringkas.

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

## 5. Bottom line

Kalau mau paling aman:
- baseline profile pakai block baseline,
- dual-side profile pakai block dual-side,
- sandbox profile pakai block manual,
- jangan campur wording eksperimen ke baseline profile.
