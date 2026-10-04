# Orrery

**Clockwork twins of real systems, scored against reality.**

An orrery is a clockwork model of the solar system: turn the gears, watch
where the planets *will* be. Orrery builds such models for real software
systems — a lead-qualification funnel, a deployed web app — predicts what the
real system will do, acts on the real system, and publishes the calibration
scorecard of how well the twin knew.

The scoreboard is [crucible](https://github.com/nKOxxx/crucible) (MIT):
Brier/log scoring, exact Murphy decomposition, reliability bins. The twins are
explicit stochastic models with declared priors. The loop is the product:

```
twin.forecast(claim)  ──►  act on the REAL system  ──►  resolve  ──►  calibrate
      (ensemble, N seeds)      (no act, no resolution)     (0/1)     (this README's point)
```

## Laws

1. **Every round appends to a JSONL ledger** — forecasts, seeds, outcomes,
   timestamps. Spend and decisions are auditable (the nybls law).
2. **No resolution source, no claim.** `Twin.forecast` refuses source-less
   predictions; the loop refuses outcomes that are not 0/1 — no coercion.
3. **One run is a vibe.** Every forecast is an ensemble; `spread` is reported
   beside `mean` so disagreement between hypotheses is visible.

## Twins in the box

- `SGTwin` — sovereign-grid-o707 (latent uptime × correctness regime;
  resolved by live HTTP probes of the deployment).
- `GateTwin` — Alleadz lane-qualification gate (lane base rate × dossier
  strength × exclusion/threshold penalties; resolved by the prod rubric's
  actual verdicts on real dossiers).

## Layout

- `orrery/twin.py` — Twin base + ensemble machinery
- `orrery/loop.py` — round loop + JSONL ledger + report
- `orrery/sovereign.py`, `orrery/alleadz.py` — the twins
- `experiments/` — run scripts, ledgers, and `RESULTS.md` (calibration cards)

## Run

```bash
uv venv .venv --python 3.12
uv pip install -e ".[dev]" --python .venv/bin/python
.venv/bin/python -m pytest tests/ -q
.venv/bin/python experiments/run_sovereign.py   # live probes, slow by design
.venv/bin/python experiments/run_alleadz.py     # rubric backtest
```

MIT. Sister repos: [crucible](https://github.com/nKOxxx/crucible) (scoring),
[alleadz](https://github.com/nKOxxx/alleadz) (the funnel being modeled),
[sovereign-grid](https://github.com/nKOxxx/sovereign-grid) (the deployment
being probed).
