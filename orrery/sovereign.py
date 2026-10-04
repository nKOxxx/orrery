"""Sovereign twin — clockwork model of sovereign-grid-o707.onrender.com.

Latent-state Monte Carlo: each seeded hypothesis draw samples the twin's
uncertainty about the deployment's hidden state (uptime regime, code
correctness regime) and returns the implied success probability for a probe.

Resolution sources:
  - live HTTP behavior of the real deployment (probe-oracle)
  - https://api.github.com/repos/nKOxxx/sovereign-grid/actions (push history)
"""

from __future__ import annotations

import random

from .twin import Twin


class SGTwin(Twin):
    name = "sovereign-twin"

    def __init__(
        self,
        uptime_lo: float = 0.85,
        uptime_hi: float = 0.995,
        correctness_lo: float = 0.80,
        correctness_hi: float = 0.97,
    ):
        self.uptime_lo, self.uptime_hi = uptime_lo, uptime_hi
        self.correctness_lo, self.correctness_hi = correctness_lo, correctness_hi

    def simulate(self, seed: int, kind: str = "deal", **_) -> float:
        rng = random.Random(seed)
        uptime = rng.uniform(self.uptime_lo, self.uptime_hi)
        if kind == "health":
            return uptime
        correctness = rng.uniform(self.correctness_lo, self.correctness_hi)
        return uptime * correctness
