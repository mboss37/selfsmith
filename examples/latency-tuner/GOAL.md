# Goal: tune the retry policy of a running service — without wrecking it out-of-time

## Mission

The edge API's call policy against its flaky upstream (`config.json`: `timeout_ms`,
`retries`, `backoff_ms`) is in production breaching its SLO: the seed policy
(timeout 2000ms, no retries) runs ~7% errors against a 2% error budget, and its tail
latency is bloated. Bring the error rate under the floor, then minimize **mean effective
latency** — per-request elapsed ms with every error costed at +10,000ms — on the train
window, subject to the change HOLDING on the out-of-time holdout window. The measure of
success is what survives days 6–7, not what tops the days 1–5 leaderboard.

## Priority order when in conflict

1. **Harness and scorer correctness.** If `python -m pytest sim/ -q` is red or
   `sim/run_eval.py` produces suspect numbers, fix measurement before touching the policy.
   A broken ruler makes every subsequent reading worthless.

2. **The error-rate floor.** `error_rate <= 2%` on EVERY adjudicated window. A latency win
   bought with errors is the reward-hack this domain teaches: time out fast, fail cheap,
   and "latency" improves while users see failures. The floor is checked mechanically
   (`tools/verdict.py floor`) and is never traded against the headline metric.

3. **Trace integrity.** `traces/train.jsonl` and `traces/holdout.jsonl` are the fixed
   measurement data. Never regenerate (`sim/make_traces.py` is blocked inside the loop),
   never edit. The holdout window is adjudication-only: score it once per challenger,
   after a train win — never iterate against it.

4. **Mean effective latency on train.** The working signal. Minimize it — but a train gain
   is evidence, not proof.

5. **Out-of-time reproduction.** The promote test: the train gain must not degrade the
   holdout window (non-inferiority, checked mechanically) and must keep the floor there.
   Days 6–7 have a degraded upstream — persistence, slower medians, fatter tails. A policy
   tuned to train's transient blips dies there; that death must happen at the gate, not in
   production.

## Candidate budget (fixed up front — verdict.py refuses to certify without it)

**24 configurations**: timeouts {260, 600, 1000, 1500, 2000, 2600} × (retries, backoff)
pairs {(1,0), (2,0), (2,60), (3,60)}. This is the whole campaign's search space; widening
it is a NEW campaign with a new budget, not an amendment.

## Acceptance criteria (per promotion)

- `python -m pytest sim/ -q` passes.
- `tools/verdict.py compare` (train, `--stat mean --direction lower`, `--search-size 24`)
  PROMOTEs the challenger over the champion.
- `tools/verdict.py floor` holds `error_rate <= 0.02` on train AND holdout.
- Holdout non-inferiority holds: with champion and challenger swapped,
  `tools/verdict.py compare` on holdout must NOT show the old champion significantly
  beating the challenger.
- The gate approves; a verdict.py REJECT is binding.

## Done

The champion's error rate is under the floor on both windows, mean effective latency is at
the grid optimum reachable without a holdout regression, at least one tempting
train-winner has been killed by the out-of-time check (confirming the gate bites), and a
full sweep of the remaining budget produces no promotable challenger. Write the `DONE`
marker only then.
