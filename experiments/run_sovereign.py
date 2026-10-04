"""Sovereign leg — twin predicts the real deployment, live probes resolve.

16 rounds (8 health, 8 deal-pipeline) against https://sovereign-grid-o707.onrender.com.
Each round: twin ensemble forecasts P(probe succeeds), then we actually probe.
Unreachable or 5xx = outcome 0. One probe every ~20s — Render free tier sleeps;
waking it IS the phenomenon under study (and the twin's uptime prior models it).

Resolution sources: live HTTP behavior of the deployment + the repo's push
history (github.com/nKOxxx/sovereign-grid/actions).
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orrery.loop import Loop
from orrery.sovereign import SGTwin

BASE = "https://sovereign-grid-o707.onrender.com"
PROBES = [
    ("health", f"{BASE}/api/health"),
    ("deal", f"{BASE}/api/deals"),
]


def probe(url: str, attempts: int = 2) -> tuple[int, str]:
    """Return (outcome, note). Unreachable/5xx = 0. Retries once after 3s."""
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "orrery/0.1"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.status
                if 200 <= code < 500:
                    return 1, f"HTTP {code}"
                return 0, f"HTTP {code}"
        except urllib.error.HTTPError as e:
            return 0, f"HTTPError {e.code}"
        except Exception as e:  # noqa: BLE001 — the observation IS the failure
            if i == 0:
                time.sleep(3)
                continue
            return 0, f"{type(e).__name__}: {str(e)[:80]}"
    return 0, "unreachable"


def main() -> None:
    ledger = Path(__file__).parent / "ledgers" / "sovereign.jsonl"
    loop = Loop(SGTwin(), ledger)
    notes: list[str] = []

    for rnd in range(16):
        kind, url = PROBES[rnd % 2]
        claim = f"{'GET /api/health' if kind == 'health' else 'GET /api/deals'} succeeds (round {rnd + 1}/16)"
        fc_holder = {}

        def act(fc, _url=url, _kind=kind, _h=fc_holder, _n=notes):
            _h["fc"] = fc
            outcome, note = probe(_url)
            _n.append(note)
            return outcome

        rec = loop.round(
            claim,
            sources=[
                f"live:GET {url}",
                "push-history:github.com/nKOxxx/sovereign-grid/actions",
            ],
            act=act,
            n_runs=16,
            kind=kind,
        )
        print(f"r{rec['round']:02d} {kind:6s} twin={rec['mean']:.3f} "
              f"spread={rec['spread']:.3f} → {notes[-1]}")
        time.sleep(20)

    rep = loop.report(n_bins=2)
    print("\n=== SOVEREIGN TWIN CALIBRATION ===")
    print(rep.summary())
    print("\nledger:", ledger)


if __name__ == "__main__":
    main()
