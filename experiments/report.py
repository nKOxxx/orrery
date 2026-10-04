"""Generate the calibration cards from both ledgers -> experiments/RESULTS.md body."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crucible.calibration import calibration_report


def load(name: str):
    path = Path(__file__).parent / "ledgers" / name
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().strip().splitlines() if l.strip()]


def card(title: str, rows):
    probs = [r["mean"] for r in rows]
    outs = [r["outcome"] for r in rows]
    rep = calibration_report(probs, outs, n_bins=2)
    print(f"### {title}")
    print("```")
    print(rep.summary())
    print("```")
    print()
    print("| # | twin mean | spread | outcome |")
    print("|---|---|---|---|")
    for r in rows:
        print(f"| {r['round']} | {r['mean']:.3f} | {r['spread']:.3f} | {r['outcome']} |")
    print()
    return rep


if __name__ == "__main__":
    sg = load("sovereign.jsonl")
    al = load("alleadz.jsonl")
    if sg:
        card("Sovereign twin (liveness, cold+warm)", sg)
    if al:
        card("Alleadz gate twin (prod rubric verdicts)", al)
