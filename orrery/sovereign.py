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
        cold_lo: float = 0.30,
        cold_hi: float = 0.70,
        warm_lo: float = 0.93,
        warm_hi: float = 0.99,
    ):
        self.uptime_lo, self.uptime_hi = uptime_lo, uptime_hi
        self.cold_lo, self.cold_hi = cold_lo, cold_hi
        self.warm_lo, self.warm_hi = warm_lo, warm_hi

    def simulate(self, seed: int, kind: str = "warm", **_) -> float:
        """Liveness probability. `cold`: first hit after idle — the Render
        free-tier dyno may be asleep and must spin up. `warm`: dyno already
        hot from earlier probes. Both additionally carry the deployment's
        baseline uptime regime."""
        rng = random.Random(seed)
        uptime = rng.uniform(self.uptime_lo, self.uptime_hi)
        if kind == "cold":
            return uptime * rng.uniform(self.cold_lo, self.cold_hi)
        return uptime * rng.uniform(self.warm_lo, self.warm_hi)
