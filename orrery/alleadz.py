"""Alleadz gate twin — clockwork model of the prod lane-qualification rubric.

The real gate (server/src/lib/rubric.js + verticals presets) hard-fails
dossiers that (a) touch excluded geos or (b) carry an expected deposit under
the lane's $1M threshold. This twin models a dossier's pass chance BEFORE
looking at the rubric: lane base rate, dossier strength prior, and how much
the gate punishes excluded-markets exposure. Resolution source is the rubric
itself, executed on the real dossiers.
"""

from __future__ import annotations

import random

from .twin import Twin

LANE_BASE = {"bank-frick": 0.55, "own-products": 0.65}


class GateTwin(Twin):
    name = "alleadz-gate-twin"

    def simulate(
        self,
        seed: int,
        lane: str = "bank-frick",
        strength: float = 0.5,
        excluded_hit: bool = False,
        under_threshold: bool = False,
        **_,
    ) -> float:
        rng = random.Random(seed)
        base = LANE_BASE.get(lane, 0.5)
        strength_sample = min(0.98, max(0.02, strength + rng.gauss(0, 0.08)))
        penalty = rng.uniform(0.55, 0.75)
        p = 0.4 * base + 0.6 * strength_sample
        if excluded_hit:
            p *= penalty  # hard geo fail ~ certain; twin leaves residual doubt
        if under_threshold:
            p *= rng.uniform(0.15, 0.35)
        return min(0.98, max(0.02, p))
