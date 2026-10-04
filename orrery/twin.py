"""Twin base + ensemble machinery.

A Twin is a stochastic model of a real system. Each `run(seed)` returns the
twin's probability for the claim under one hypothesis-draw. The ensemble is
N seeded runs of the SAME claim — averaging them denoises toward the twin's
actual belief (the property crucible's ensemble test proves).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Forecast:
    """Ensemble forecast for one claim."""

    text: str
    sources: list[str]
    probs: list[float]
    seeds: list[int] = field(default_factory=list)

    @property
    def mean(self) -> float:
        return sum(self.probs) / len(self.probs)

    @property
    def spread(self) -> float:
        """Max-min of the ensemble — how much the twin's hypotheses disagree."""
        return max(self.probs) - min(self.probs)


class Twin:
    """Base class. Subclasses implement `simulate(seed, **claim_kwargs)`.

    `simulate` must be deterministic given (seed, kwargs) — that is what makes
    the ensemble reproducible and the spread interpretable.
    """

    name: str = "twin"

    def simulate(self, seed: int, **claim_kwargs) -> float:
        raise NotImplementedError

    def forecast(
        self,
        text: str,
        sources: list[str],
        n_runs: int = 9,
        seed0: int = 0,
        **claim_kwargs,
    ) -> Forecast:
        """Ensemble n_runs seeded simulations of one claim."""
        if not sources:
            raise ValueError(
                "a prediction without a resolution source is not a prediction"
            )
        probs: list[float] = []
        seeds: list[int] = []
        for i in range(n_runs):
            seed = seed0 + i
            p = float(self.simulate(seed, **claim_kwargs))
            if not 0.0 <= p <= 1.0:
                raise ValueError(f"simulate returned invalid probability {p}")
            probs.append(p)
            seeds.append(seed)
        return Forecast(text=text, sources=list(sources), probs=probs, seeds=seeds)
