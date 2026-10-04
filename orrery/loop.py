"""Experiment loop: forecast -> act on the real system -> resolve -> score.

Every round appends to a JSONL ledger (the nybls law: spend and decisions are
auditable). Resolution uses crucible's scoring; the aggregated report is the
calibration card for the twin.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from crucible.calibration import calibration_report

from .twin import Forecast, Twin


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Loop:
    """Run a twin against a real system, round by round, with a ledger."""

    def __init__(self, twin: Twin, ledger_path: str | Path):
        self.twin = twin
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.resolved: list[tuple[float, int]] = []  # (mean_prob, outcome)
        self.rounds = 0

    def _append(self, record: dict) -> None:
        with self.ledger_path.open("a") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

    def round(
        self,
        text: str,
        sources: list[str],
        act: Callable[[Forecast], int],
        n_runs: int = 9,
        seed0: int | None = None,
        **claim_kwargs,
    ) -> dict:
        """One full loop turn.

        act(forecast) must (1) do the real-world thing the claim is about and
        (2) return the observed outcome (0/1). Returning the outcome keeps the
        law honest: no act, no resolution, no score.
        """
        if seed0 is None:
            seed0 = 1000 * (self.rounds + 1)
        fc = self.twin.forecast(
            text, sources, n_runs=n_runs, seed0=seed0, **claim_kwargs
        )
        outcome = act(fc)
        if outcome not in (0, 1, True, False):
            raise ValueError(
                f"act must return 0 or 1, got {outcome!r} — no coercing"
            )
        outcome = int(outcome)
        self.rounds += 1
        record = {
            "ts": _now(),
            "round": self.rounds,
            "twin": self.twin.name,
            "claim": text,
            "sources": sources,
            "probs": fc.probs,
            "mean": round(fc.mean, 4),
            "spread": round(fc.spread, 4),
            "outcome": outcome,
        }
        self._append(record)
        self.resolved.append((fc.mean, outcome))
        return record

    def report(self, n_bins: int = 3):
        if not self.resolved:
            raise ValueError("no resolved rounds yet — run the loop first")
        probs = [p for p, _ in self.resolved]
        outs = [o for _, o in self.resolved]
        return calibration_report(probs, outs, n_bins=n_bins)
