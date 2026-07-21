# U5Spring Experiment Brief Template

Gunakan file ini kalau ingin membuat brief eksperimen baru dengan format yang ringkas tapi tetap disiplin.

## 1. Identity
- Experiment name:
- Date:
- Owner / agent:
- Status: `planned | running | completed | archived`

## 2. User intent
- What the user wants:
- Non-negotiables from user:
- Output expected from this experiment:

## 3. Main question
- Main question:
- Why this matters:

## 4. Base rule to preserve
- Strategy family: `u5spring`
- Canonical baseline:
- Identity that must stay fixed:
  - [ ] pool quality first
  - [ ] reclaim timing second
  - [ ] deploy expression third
  - [ ] 5m baseline comparator remains visible
  - [ ] 15m baseline context remains visible unless explicitly tested
  - [ ] spot-first baseline remains comparator
  - [ ] protection mindset near `BE1 style`
  - [ ] this is still a U5Spring variant, not a new thesis

## 5. Scope
- What changes:
- What stays fixed:
- Variable under test:
- What is explicitly NOT being changed:
- Research-only or potentially operational later:

## 6. Paths
- Baseline comparator path:
- New experiment folder path:
- Comparison note path:
- Any downstream thesis note path if needed:

## 7. Required artifacts
- [ ] `summary.md`
- [ ] `report.md`
- [ ] `full-report.md`
- [ ] `summary.csv`
- [ ] `trade-journal.csv`
- [ ] `ohlcv/` if relevant
- [ ] `split-by-mode/` if relevant
- [ ] comparison note

## 8. Metrics / evaluation
- Primary metrics:
- Secondary metrics:
- What would count as improvement:
- What would count as drift or failure:

## 9. Guardrails
- [ ] do not overwrite canonical baseline
- [ ] do not work directly inside the baseline folder
- [ ] do not change many variables at once
- [ ] do not touch operator/Meridian/payload before evidence is strong

## 10. Propagation intent
- If weak result:
  - [ ] stop at research
- If strong result:
  - [ ] consider thesis update
  - [ ] consider operator implication
  - [ ] consider Meridian implication
  - [ ] consider payload/profile implication only if truly operational

## 11. Quick instruction block for another agent
```text
Use U5Spring base rules.
Do not overwrite canonical baseline.
Create a sibling research run.
Compare against baseline.
Only propagate upward if evidence is strong.
User-specific intent:
- 
Non-negotiables:
- 
Main question:
- 
```
