# Iteration log — append-only

Each entry: timestamp · change made · gate verdict · verify · prove result · metric moved.
Honest entries ("reverted, broke verify", "rejected-regime-overfit") are as valuable as wins.

---

## 2026-06-08T07:02Z — PROMOTE: add retries (timeout 2000 / retries 0→2 / backoff 100)

**Evaluator verdict:** Seed policy is breaching the SLO: train error rate 7.3% against a 2% floor (single attempt — every transient upstream failure and every >2s stall is a user-facing error). Priority 2 outranks latency: fix the floor first.

**Proposer hypothesis:** Train-window slowness is transient (mode persistence 0.30) — a retry usually escapes the episode. Two retries should collapse the fail-chain error rate to (per-attempt failure)³ ≈ well under the floor, at a small latency cost on retried requests.

**Implementer:** `config.json` retries 0→2, backoff_ms 0→100. Prove: train error 7.3% → 0.0%, mean effective 1022ms → 340ms (errors no longer costed at +10s).

**Gate:** `verdict.py self-test` green. Train compare vs seed: mean improvement +682ms, CI[+466, +910] at deflated alpha 0.05/24 — PROMOTE. Floor: train 0.0% ✓. Holdout adjudication: error 0.0% ✓, non-inferiority ✓ (holdout mean 1005ms → 305ms). Verify: `python -m pytest sim/ -q` green.

**Verdict: APPROVE — promoted. SLO restored.**

Metric: train mean effective 1022ms → 340ms; error rate 7.3% → 0.0%.

---

## 2026-06-09T07:04Z — REJECT regime-overfit: tight timeout (260 / 3 / 20)

**Evaluator verdict:** Champion healthy (train mean eff 340ms, err 0%). Biggest remaining cost: slow-episode requests waiting up to 2s before retrying. Recommended focus: cut losses earlier.

**Proposer hypothesis:** Slow episodes exceed 260ms almost surely; timing out at 260ms and retrying into a (transiently) healthy upstream converts ~2s waits into ~450ms recoveries. Expected train mean effective −20ms or better. Known failure mode: assumes the NEXT attempt escapes the episode — false under persistent congestion.

**Implementer:** Candidate via overrides (no config change until gate): train mean effective 320ms (−20ms, the best number any candidate has posted), error 1.2%, under the floor. Tempting.

**Gate:** Train compare: PROMOTE (CI clears zero). Floor train ✓. **Holdout adjudication: error rate 8.83% — floor REJECT** (`verdict.py floor --value 0.0883 --max 0.02`), mean effective 1211ms vs champion's 305ms. Under day-6–7 persistence the retry storm burns all four attempts inside the same congested episode. The stated failure mode is exactly what happened.

**Verdict: REJECT — regime overfit. The train leaderboard's best config is a production incident.**

Metric: unchanged (champion stands). The out-of-time gate is confirmed to bite.

---

## 2026-06-10T07:03Z — PROMOTE: drop retry backoff (2000 / 2 / 100→0)

**Evaluator verdict:** Champion stands. Residual waste: 100ms of backoff per retry buys nothing when the upstream mostly recovers instantly on train (and under holdout persistence a 100ms wait doesn't outlast an episode either — it's dead time in both regimes).

**Proposer hypothesis:** Backoff exists to shed load from a struggling upstream; the replay pays its latency cost with none of that benefit modeled as needed at this traffic level. Removing it should shave the full 100–200ms from every retried request, both windows, error-neutral.

**Implementer:** `config.json` backoff_ms 100→0. Prove: train mean effective 340.4ms → 332.3ms.

**Gate:** Train compare vs champion: +8.1ms, CI[+5.6, +11.2] at deflated alpha 0.05/24 — PROMOTE. Floor: train 0.0% ✓, holdout 0.0% ✓. Holdout non-inferiority: swapped compare shows the challenger ahead (−6.5ms for the old champion) — no regression ✓. Verify green.

**Verdict: APPROVE — promoted. Champion is now timeout 2000 / retries 2 / backoff 0.**

Metric: train mean effective 340.4ms → 332.3ms; holdout 305.5ms → 299.0ms.
