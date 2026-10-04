"""Orrery core tests — determinism, ledger honesty, identity, twins."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crucible.calibration import CalibrationReport, calibration_report

from orrery.alleadz import GateTwin
from orrery.loop import Loop
from orrery.sovereign import SGTwin
from orrery.twin import Twin


class WeightedCoin(Twin):
    """Known-belief twin: every hypothesis says p ~ U(0.65, 0.75)."""

    name = "coin"

    def simulate(self, seed: int, **_):
        import random

        return random.Random(seed).uniform(0.65, 0.75)


def test_forecast_is_deterministic_and_needs_sources():
    t = WeightedCoin()
    a = t.forecast("x", ["probe:now"], n_runs=5, seed0=0)
    b = t.forecast("x", ["probe:now"], n_runs=5, seed0=0)
    assert a.probs == b.probs
    assert a.seeds == [0, 1, 2, 3, 4]
    with pytest.raises(ValueError):
        t.forecast("x", [], n_runs=2)


def test_loop_ledger_round_trip_and_identity(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    lp = Loop(WeightedCoin(), ledger)
    outcomes = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    for i, o in enumerate(outcomes):
        rec = lp.round(
            f"claim {i}", ["probe:now"], lambda fc, o=o: o, n_runs=9, seed0=100 * i
        )
        assert rec["outcome"] == o
        assert 0.0 <= rec["mean"] <= 1.0
    lines = [json.loads(l) for l in ledger.read_text().strip().splitlines()]
    assert len(lines) == 10
    assert lines[0]["twin"] == "coin"
    rep = lp.report(n_bins=2)
    assert isinstance(rep, CalibrationReport)
    identity = rep.reliability - rep.resolution + rep.uncertainty + rep.residual
    assert abs(identity - rep.brier) < 1e-9


def test_loop_refuses_non_binary_outcomes(tmp_path):
    lp = Loop(WeightedCoin(), tmp_path / "l.jsonl")
    with pytest.raises(ValueError):
        lp.round("x", ["probe:now"], lambda fc: 0.5, n_runs=3)


def test_sovereign_twin_cold_beats_warm_never_and_is_graded():
    t = SGTwin()
    warm = [t.simulate(s, kind="warm") for s in range(300)]
    cold = [t.simulate(s, kind="cold") for s in range(300)]
    assert all(0.0 < p < 1.0 for p in warm + cold)
    assert sum(warm) / len(warm) > sum(cold) / len(cold)
    fc = t.forecast("app is live", ["probe:now"], n_runs=16, seed0=0, kind="cold")
    assert fc.spread >= 0.0
    assert abs(fc.mean - sum(fc.probs) / len(fc.probs)) < 1e-12


def test_gate_twin_punishes_exclusions_and_threshold():
    t = GateTwin()
    clean = [t.simulate(s, lane="bank-frick", strength=0.7) for s in range(300)]
    geo = [
        t.simulate(s, lane="bank-frick", strength=0.7, excluded_hit=True)
        for s in range(300)
    ]
    thin = [
        t.simulate(s, lane="bank-frick", strength=0.7, under_threshold=True)
        for s in range(300)
    ]
    mean = lambda xs: sum(xs) / len(xs)
    assert mean(clean) > mean(geo)
    assert mean(clean) > mean(thin)
    assert mean(geo) < 0.5  # exclusions should usually doom a bank-frick dossier
