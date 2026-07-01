# Methodology

## Window discipline (time-based split)

The measurement data is two fixed traffic traces under `traces/`, replayed deterministically:

| Window | File | Role |
|---|---|---|
| train | `train.jsonl` | Days 1–5, healthy upstream. Measure every candidate here. The working signal. |
| holdout | `holdout.jsonl` | Days 6–7, degraded upstream. Adjudicate a challenger ONCE, after a train win. **Sacred.** |

This is the optimize-a-running-system flavor of holdout: **out-of-time**, not out-of-sample.
The future is the only thing production serves, so the adjudication window is later data
under drifted conditions — slower medians, fatter tails, and congestion that PERSISTS
across retry attempts (mode persistence 0.75 vs train's 0.30). Contaminating the holdout
here means iterating against days 6–7: scoring candidates on it to pick between them,
or tuning any knob in response to a holdout number other than reject-the-challenger.

The traces themselves are the ruler. `sim/make_traces.py` exists for provenance and is
**blocked inside the loop** (guardrail Floor 1); `traces/` is a protected path for every
write tool. Regenerating traffic until the numbers look better is the same crime as
editing the holdout.

## The physics (why this domain overfits)

Upstream slowness arrives in modes (fast / medium / slow-congested). On train, a request's
later attempts usually ESCAPE a slow mode (transient blips) — so aggressive
timeout-and-retry looks brilliant: cut losses at 260ms, retry into a fast attempt.
On holdout the upstream has degraded and congestion persists across attempts — the same
policy burns its whole attempt budget inside one slow episode: timeout, backoff, timeout,
backoff, error. The planted trap (`timeout_ms=260, retries=3`) tops the train leaderboard
(mean effective ≈ 320ms vs the honest optimum ≈ 332ms) and runs **8.8% errors** on
holdout, more than four times the floor.

## Failure modes to guard against

**The cheap-error reward-hack.** Percentiles over successful requests improve when errors
increase (slow requests convert to fast failures). Countermeasures, both mechanical: the
headline stat is EFFECTIVE latency (errors costed at elapsed + 10,000ms), and
`error_rate <= 2%` is a hard floor checked with `tools/verdict.py floor`.

**Regime overfit.** Tuning the timeout to the train window's latency shape (the trap).
Countermeasure: out-of-time adjudication with a mechanical non-inferiority check.

**Noise mining.** With n=1000 (train) / n=600 (holdout), small mean differences can be
resampling luck — and 24 candidates give 24 chances to be lucky. Countermeasure: the
paired bootstrap in `tools/verdict.py compare` at alpha 0.05 **Bonferroni-deflated by the
declared budget of 24**; the whole CI must clear zero.

**Scorer bugs.** A silent change to `sim/run_eval.py` that inflates scores.
Countermeasure: `python -m pytest sim/ -q` before and after every change (the trace
checksums are pinned in tests), plus the metric contract at triage.

## Go/no-go gate

A challenger replaces the champion **only if ALL of the following hold** (each check is a
command, not an opinion):

1. **Train gain is certified.** Dump paired per-request effective latencies for champion
   and challenger (`--dump`), then
   `tools/verdict.py compare --stat mean --direction lower --search-size 24` → PROMOTE.
2. **Floor holds everywhere.** `tools/verdict.py floor --value <error_rate> --max 0.02`
   on train AND holdout.
3. **Holdout non-inferiority.** Swap the roles: with the CHALLENGER as `--champion` and
   the old champion as `--challenger`, `compare` on the holdout window with
   `--search-size 1` must NOT return PROMOTE (the old config shows no significant win —
   the challenger hasn't regressed out-of-time).
4. **Regression clean.** `python -m pytest sim/ -q` passes.

**Candidate budget, fixed up front: 24** (see GOAL.md — 6 timeouts × 4 retry/backoff
pairs). The `--search-size` in every certification is 24, regardless of how many
candidates have been tried so far — the deflation is against the declared budget, never
the running log.

The gate agent (`.claude/agents/gate.md`) runs these checks independently, starting with
`tools/verdict.py self-test` (the automated known-nothing control). Its verdict is
binding — the orchestrator cannot override a REJECT.
