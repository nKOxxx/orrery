"""Alleadz leg — twin predicts the lane gate; the prod rubric resolves.

Eight real dossiers go through the REAL lane gate (server/src/lib/rubric.js +
verticals presets, the code that ships on prod). The twin never sees the
rubric's answers: it forecasts from lane base rates + dossier priors, then the
loop resolves each claim against the actual verdict.

Resolution source: alleadz rubric-v1.1 runLaneGate (prod code, executed here).
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orrery.alleadz import GateTwin
from orrery.loop import Loop

EVAL = "/tmp/_eval_gate.mjs"

DOSSIERS = [
    # tag, lane, country, expected_deposit_usd
    ("bf-strong-ch",       "bank-frick",   "Switzerland",     8_000_000),
    ("bf-excluded-brazil", "bank-frick",   "Brazil",         12_000_000),
    ("bf-excluded-iran",   "bank-frick",   "Iran",           20_000_000),
    ("bf-under-1m",        "bank-frick",   "Germany",          250_000),
    ("bf-no-deposit",      "bank-frick",   "Singapore",           None),
    ("op-strong-us",       "own-products", "United States",    5_000_000),
    ("op-under-1m",        "own-products", "Estonia",            400_000),
    ("op-unknown-deposit", "own-products", "India",               None),
]


def rubric_verdict(lane: str, country: str, deposit) -> str:
    dep = "" if deposit is None else str(deposit)
    r = subprocess.run(
        ["node", EVAL, lane, country, dep],
        capture_output=True, text=True, timeout=30,
    )
    lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
    if not lines:
        raise RuntimeError(f"rubric eval failed: {r.stderr[:200]}")
    return lines[-1].strip()


def main() -> None:
    ledger = Path(__file__).parent / "ledgers" / "alleadz.jsonl"
    loop = Loop(GateTwin(), ledger)
    verdicts: list[tuple[str, str]] = []

    for tag, lane, country, deposit in DOSSIERS:
        def act(fc, _lane=lane, _country=country, _dep=deposit, _tag=tag):
            v = rubric_verdict(_lane, _country, _dep)
            verdicts.append((_tag, v))
            return 1 if v == "pass" else 0

        rec = loop.round(
            f"lane gate passes {tag} ({lane}, {country}, "
            f"deposit={'n/a' if deposit is None else deposit})",
            sources=["alleadz:rubric-v1.1:runLaneGate"],
            act=act,
            n_runs=9,
            lane=lane,
            strength={"bf-strong-ch": 0.90, "bf-excluded-brazil": 0.80,
                      "bf-excluded-iran": 0.35, "bf-under-1m": 0.70,
                      "bf-no-deposit": 0.55, "op-strong-us": 0.85,
                      "op-under-1m": 0.60, "op-unknown-deposit": 0.45}[tag],
            excluded_hit=tag.endswith(("brazil", "iran")),
            under_threshold=tag.endswith("1m") and "under" in tag,
        )
        print(f"{tag:22s} twin={rec['mean']:.3f} spread={rec['spread']:.3f} "
              f"→ rubric: {verdicts[-1][1]}")

    rep = loop.report(n_bins=2)
    print("\n=== ALLEADZ GATE CALIBRATION ===")
    print(rep.summary())
    print("\nverdicts:", json.dumps(dict(verdicts)))


if __name__ == "__main__":
    main()
