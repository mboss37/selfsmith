#!/usr/bin/env python3
"""Generate the fixed traffic traces — run ONCE at project start, then never again.

The traces are the measurement data: two windows of pre-drawn upstream behavior that the
replay harness (run_eval.py) scores policies against. Regenerating them mid-campaign would
rewrite the ruler — the guardrail blocks this script inside the loop, and traces/ is a
protected path. Seeded PRNG throughout: same seed, same traces, byte for byte.

Each trace line is one request: MAX_ATTEMPTS pre-drawn upstream outcomes
  {"attempts": [{"lat": <upstream ms>, "ok": <bool>}, ...]}
so any (timeout, retries, backoff) policy can be replayed deterministically against
identical traffic.

The physics that makes tuning non-trivial: upstream slowness comes in MODES (fast /
medium / slow-congested), and a request's later attempts keep the previous attempt's mode
with probability RHO. Train window ("days 1-5"): rho=0.3 — slowness is transient blips, a
quick retry usually escapes, so tight timeouts look brilliant. Holdout window ("days
6-7"): the upstream has degraded — medians shift up, the slow mode is common, and rho=0.75
— congestion PERSISTS, so a timeout-and-retry storm burns its whole attempt budget inside
the same congested episode and turns into an error. A policy tuned to train's transient
regime breaks here; a robust one holds.
"""
import json
import random
from pathlib import Path

MAX_ATTEMPTS = 4
TRACES = Path(__file__).resolve().parent.parent / "traces"


def make_window(seed, n, fail_p, rho, modes):
    """modes: list of (probability, draw_fn(rng) -> latency_ms)."""
    rng = random.Random(seed)

    def draw_mode():
        u, acc = rng.random(), 0.0
        for i, (p, _) in enumerate(modes):
            acc += p
            if u < acc:
                return i
        return len(modes) - 1

    lines = []
    for _ in range(n):
        mode = draw_mode()
        attempts = []
        for i in range(MAX_ATTEMPTS):
            if i > 0 and rng.random() >= rho:  # escape the episode; else mode persists
                mode = draw_mode()
            lat = max(5.0, modes[mode][1](rng))
            attempts.append({"lat": round(lat, 1), "ok": rng.random() >= fail_p})
        lines.append(json.dumps({"attempts": attempts}))
    return "\n".join(lines) + "\n"


def main():
    TRACES.mkdir(exist_ok=True)
    # days 1-5: healthy upstream — slowness is transient (rho=0.3), retries escape it
    (TRACES / "train.jsonl").write_text(make_window(
        seed=1101, n=1000, fail_p=0.03, rho=0.30,
        modes=[
            (0.65, lambda r: r.gauss(120, 25)),                 # fast
            (0.25, lambda r: r.gauss(210, 25)),                 # medium
            (0.10, lambda r: 800 + r.expovariate(1 / 1200)),    # slow episode
        ]))
    # days 6-7: degraded upstream — medians up, congestion persists (rho=0.75), retries
    # tend to land inside the same slow episode
    (TRACES / "holdout.jsonl").write_text(make_window(
        seed=2207, n=600, fail_p=0.05, rho=0.75,
        modes=[
            (0.66, lambda r: r.gauss(150, 35)),                 # fast, slower than before
            (0.25, lambda r: r.gauss(290, 40)),                 # medium, now above 260ms
            (0.09, lambda r: 800 + r.expovariate(1 / 800)),     # slow episode
        ]))
    print("wrote traces/train.jsonl (n=1000) and traces/holdout.jsonl (n=600)")


if __name__ == "__main__":
    main()
