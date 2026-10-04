# RESULTS — first calibration runs (2026-10-04)

Two twins, two real systems, one loop: forecast (ensemble) → act on the real
system → resolve → score with crucible. Every round is in `ledgers/*.jsonl`.

- **Sovereign twin** vs https://sovereign-grid-o707.onrender.com — 16 liveness
  probes (1 cold-dyno, 15 warm), 75s idle before the cold probe, 30s gaps.
- **Alleadz gate twin** vs the prod lane-qualification rubric (`rubric-v1.1`,
  `runLaneGate`) — 8 real dossiers through the code that ships.

---

## Sovereign twin (liveness, cold+warm)

```
n=16  brier=0.030  log=0.162
reliability=0.030 (lower=better)  resolution=0.000  uncertainty=0.000  residual=0.0001
identity check: rel - res + unc + residual = 0.030  ✓ exact
```

| # | regime | twin mean | spread | outcome |
|---|---|---|---|---|
| 1 | cold | 0.469 | 0.350 | 1 (HTTP 200) |
| 2–16 | warm | 0.869–0.899 | 0.10–0.17 | 1 ×15 (200s + 401s) |

**Findings**

1. **The twin is slightly UNDER-confident, not over** — the opposite of the
   MiroFish disease. It said ~0.88 warm; reality went 15/15. Perfect
   calibration on this sample would require claiming ~1.0. Warm-regime prior
   (0.93–0.99 mean ~0.96) is if anything too modest: while warm, this
   deployment did not miss once.
2. **Cold vs warm is the real physics.** Round 1 (dyno asleep) carried spread
   0.350 — the twin honestly did not know — and hit anyway (n=1, unproven
   either way). This is the regime a "will it work when I need it" monitor
   must model.
3. **Resolution/uncertainty are 0 because all outcomes were 1.** This run
   measures calibration-in-the-hits, not discrimination. Discrimination needs
   a run where the deployment actually fails (or a deliberately faulted twin).
4. **Design law discovered:** 401 is liveness evidence (process up, routing),
   not failure. Unauthenticated probes cannot resolve payload correctness —
   so the claims are liveness-only. An unresolvable claim is not a claim.

## Alleadz gate twin (prod rubric verdicts)

```
n=8  brier=0.213  log=0.634
reliability=0.006 (lower=better)  resolution=0.062  uncertainty=0.250  residual=0.0200
identity check: rel - res + unc + residual = 0.213  ✓ exact
```

| # | dossier | twin mean | spread | rubric verdict |
|---|---|---|---|---|
| 1 | bf-strong-ch | 0.717 | 0.168 | pass |
| 2 | bf-excluded-brazil | 0.449 | 0.183 | fail |
| 3 | bf-excluded-iran | 0.265 | 0.079 | fail |
| 4 | bf-under-1m | 0.154 | 0.129 | fail |
| 5 | bf-no-deposit | 0.557 | 0.106 | **unknown** (scored 0) |
| 6 | op-strong-us | 0.787 | 0.176 | pass |
| 7 | op-under-1m | 0.145 | 0.072 | pass |
| 8 | op-unknown-deposit | 0.506 | 0.163 | pass |

**Findings**

1. **Reliability 0.006 — the twin's confidence levels mean what they say.**
   Resolution 0.062: it separates passes from fails. Brier 0.213 with n=8.
2. **Biggest single error: the abstention case.** `bf-no-deposit`: twin 0.557,
   verdict `unknown`, scored 0 → contributes 0.31 of the 0.213 mean. The gate
   has a THIRD verdict and the loop currently flattens it to "not pass".
   Abstention semantics (exclude from scoring / score as its own outcome /
   force the twin to forecast "verdict == pass" exactly) is a v1 design
   decision, logged as such.
3. **Geo-exclusion penalty too soft.** Twin gave Brazil 0.449; the rubric's
   answer is deterministic fail. A twin that has read the lane's frozen
   `excluded_markets` list should sit at ~0.05, not 0.45. (Iran at 0.265 was
   rightly more doomed — strength prior did work.)
4. **Prod surprise: own-products lane has NO deposit floor** (`gate:
   min_expected_deposit_usd: null`). The twin wrongly assumed symmetry with
   bank-frick's $1M and got punished (r7 scored 0.145 on a pass). The twin
   found a real fact about prod by being wrong in public. That is the loop
   working.

## What the loop proved about itself

- Deterministic ensembles, JSONL ledger on every round, act-or-no-resolution.
- Crucible's Murphy identity held **exactly** on both real ledgers — which
  required shipping the residual term (within-bin variance − 2·within-bin
  covariance) mid-experiment after orrery's ledger test caught the classical
  three-term form lying by 2.2e-4. The scoreboard got sharper because the
  loop audited it.

## Next

- Sovereign twin: repeat across days for a real uptime distribution (and a
  chance at resolution ≠ 0); feed both ledgers back as v1 priors.
- Gate twin: read the lane presets directly instead of guessing penalties;
  decide abstention semantics.
- Wire a live resolution feed (Metaculus/Manifold) as a third leg.
