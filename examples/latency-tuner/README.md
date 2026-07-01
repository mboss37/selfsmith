# Latency tuner — example loop (optimize-a-running-system flavor)

A self-improving loop that tunes a running service's retry policy (`config.json`:
`timeout_ms`, `retries`, `backoff_ms`) against replayed production traffic, and only
promotes changes that survive an **out-of-time** holdout window. Fully offline and
deterministic — no API key, no network.

This is the second flavor described in the root README: where the
[prompt-technique tournament](../prompt-technique-tournament/) *discovers and validates* a
winner from a candidate catalog, this loop *optimizes a running system* — incremental
config changes, a time-based holdout, and a hard operational floor.

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code)
- Python 3.11+ and `pip install -r requirements.txt` (installs pytest)

## What this loop does

The seed policy is breaching its SLO (7.3% errors against a 2% budget). Each iteration,
the loop (`/iterate`):

1. Evaluates the champion config on the train window (days 1–5).
2. Proposes ONE knob change with a stated mechanism — and the traffic regime it assumes.
3. Measures it on train (mean **effective** latency: errors costed at +10,000ms).
4. Gates it mechanically: `tools/verdict.py compare` (paired bootstrap, deflated by the
   declared 24-candidate budget), the 2% error floor on BOTH windows, and holdout
   non-inferiority — days 6–7, where the upstream has degraded and congestion persists.
5. Logs the result and updates `config.json` only on approval.

**The planted trap:** `timeout_ms=260, retries=3` tops the train leaderboard (mean
effective ≈ 320ms vs the honest optimum ≈ 332ms) because train slowness is transient and
retries escape it. On the holdout window congestion persists across attempts — the same
config runs **8.8% errors** (4× the floor) and mean effective 1211ms. The gate must kill
the best-looking config on the board. The converged champion is
`timeout 2000 / retries 2 / backoff 0` (train 332ms, holdout 299ms, 0% errors both).

## Run the harness directly

```bash
cd examples/latency-tuner

# Score the current champion on the train window
python sim/run_eval.py --config config.json --window train

# Score a candidate without touching config.json
python sim/run_eval.py --window train --override timeout_ms=260 --override retries=3 --override backoff_ms=20

# Adjudicate on holdout (once per challenger, after a train win — never to explore)
python sim/run_eval.py --window holdout --override timeout_ms=260 --override retries=3 --override backoff_ms=20

# Dump paired per-request vectors and certify mechanically
python sim/run_eval.py --window train --dump /tmp/champ.txt
python sim/run_eval.py --window train --override timeout_ms=260 --override retries=3 --dump /tmp/trap.txt
python tools/verdict.py compare --champion /tmp/champ.txt --challenger /tmp/trap.txt \
  --search-size 24 --stat mean --direction lower

# Run all harness tests
python -m pytest sim/ -q
```

## Run one iteration

```bash
claude          # open Claude Code in this directory
# inside the session:
/iterate              # ONE iteration, manually
/loop 1h /iterate     # CONTINUOUS — hourly (a timer suits ongoing tuning)
```

## The discipline at a glance

| Mechanism | Where |
|---|---|
| Fixed measurement data | `traces/*.jsonl` — protected paths; `make_traces.py` blocked in-loop (guardrail Floor 1) |
| Reward-hack countermeasure | effective latency (+10s per error) as headline stat AND a mechanical 2% error floor |
| Multiple-comparisons discipline | `verdict.py compare --search-size 24` — budget declared in GOAL.md, fixed up front |
| Out-of-time validation | holdout = later window, degraded upstream, persistence 0.75 vs train 0.30 |
| Metric contract | `bash tools/metric-contract.sh` — numeric, deterministic, separating |

## Files at a glance

```
.claude/
  commands/iterate.md   — orchestrator (Rae)
  agents/               — evaluator, proposer, implementer, gate, meta-improver
  hooks/                — guardrail: blocks trace regeneration/mutation
sim/
  run_eval.py           — deterministic replay scorer (--window, --override, --dump)
  make_traces.py        — trace provenance; run ONCE at project start, blocked in-loop
  test_*.py             — harness, guardrail, verdict, and metric-contract corpora
traces/                 — train.jsonl (days 1–5), holdout.jsonl (days 6–7) — the ruler
tools/                  — verdict.py (mechanical gate), metric-contract.sh
config.json             — the SEED policy (2000/0/0, SLO-breaching); the loop walks it forward
GOAL.md                 — mission, floors, candidate budget, done definition
METHODOLOGY.md          — window discipline, the physics, go/no-go gate
LOG.md                  — worked history: promote, trap rejection, promote
```
