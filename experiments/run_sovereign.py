"""Sovereign leg — twin predicts the real deployment, live probes resolve.

16 liveness rounds against https://sovereign-grid-o707.onrender.com.
Claims are strictly LIVENESS ("any well-formed HTTP status") because that is
what an unauthenticated probe can actually resolve — payload correctness needs
credentials, and an unresolvable claim is not a claim.

The physics under study is Render free-tier dyno state: round 1 is plausibly
COLD (dyno asleep after idle, must spin up); later rounds are WARM. Long gap
before round 1, short gaps between rounds.

Resolution sources: live HTTP behavior of the deployment + the repo's push
history (github.com/nKOxxx/sovereign-grid/actions).
"""

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
    (f"{BASE}/api/health", "health"),
    (f"{BASE}/api/deals", "deals"),
]


def probe(url: str, attempts: int = 2) -> tuple[int, str]:
    """Return (outcome, note). Liveness, not authorization.

    Any well-formed HTTP response (1xx-4xx, incl. 401/403) proves the process
    is up and routing — that is the phenomenon under study. Outcome 0 is
    reserved for the deployment being unreachable or failing at the 5xx layer
    (or timing out). Retries once after 3s before declaring 0.
    """
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "orrery/0.1"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                code = resp.status
                return (1, f"HTTP {code}") if code < 500 else (0, f"HTTP {code}")
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return 1, f"HTTP {e.code} (auth/routing ok)"
            return 0, f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001 — the observation IS the failure
            if i == 0:
                time.sleep(3)
                continue
            return 0, f"{type(e).__name__}: {str(e)[:80]}"
    return 0, "unreachable"


def main() -> None:
    ledger = Path(__file__).parent / "ledgers" / "sovereign.jsonl"
    loop = Loop(SGTwin(), ledger)

    for rnd in range(16):
        url, label = PROBES[rnd % 2]
        kind = "cold" if rnd == 0 else "warm"
        gap = 75 if rnd == 0 else 30  # cold: let the dyno idle; warm: inter-probe gap
        time.sleep(gap)

        note_holder = []

        def act(fc, _url=url, _h=note_holder):
            outcome, note = probe(_url)
            _h.append(note)
            return outcome

        rec = loop.round(
            f"GET {url.split('.com')[1]} is live — "
            f"{'cold dyno (after idle)' if kind == 'cold' else 'warm dyno'} "
            f"(round {rnd + 1}/16)",
            sources=[
                f"live:GET {url}",
                "push-history:github.com/nKOxxx/sovereign-grid/actions",
            ],
            act=act,
            n_runs=16,
            kind=kind,
        )
        note = note_holder[-1]
        print(f"r{rec['round']:02d} {kind:4s} {label:6s} twin={rec['mean']:.3f} "
              f"spread={rec['spread']:.3f} → {note}")

    rep = loop.report(n_bins=2)
    print("\n=== SOVEREIGN TWIN CALIBRATION ===")
    print(rep.summary())
    print("\nledger:", ledger)


if __name__ == "__main__":
    main()
