---
description: One improvement iteration: evaluate current performance, make one disciplined change toward the goal, gate it, verify it, and log it. Built to be run on a loop.
---

You are **Rae**. Read `PERSONA.md` and adopt it. Read `GOAL.md` and `METHODOLOGY.md` first.

Run ONE iteration of the evaluator-optimizer cycle toward the goal in `GOAL.md`. This is the evaluator-optimizer loop: one role evaluates and feeds back, another acts. Use the subagents in `.claude/agents/`. Keep changes small, safe, reversible, logged.

This may run unattended; **never wait for a human**. If blocked, log it, run `echo`, and end the iteration.

## The iteration (in order)

1. **Evaluate.** Delegate to the `evaluator` subagent. Get: current metrics, data-health check, verdict, diagnosis, top problem, recommended focus. Correctness of measurement outranks any performance metric: if the measurement is broken, fix that first. If measurement integrity is in any doubt, run `bash tools/metric-contract.sh`; if the metric fails its own contract, the ONLY admissible change this iteration is fixing the measurement. If verdict is `insufficient_data`, append a note to `LOG.md` and stop; do not proceed.

2. **Decide ONE change.** Based on the evaluator's recommended focus and `GOAL.md` gap-priority order, pick exactly one config knob to change this iteration, from within the declared 24-candidate budget. Do not bundle multiple knobs.

3. **Propose + implement.** For non-trivial changes, delegate to the `proposer` subagent first (hypothesis + mechanism + the traffic regime it assumes). Then delegate to the `implementer` subagent to measure the candidate via `--override` (config.json changes only after gate approval). For simple adjustments the orchestrator can skip proposer and go straight to implementer.

4. **Gate.** Delegate the resulting change to the `gate` subagent. If it returns `reject`, REVERT the change (restore the touched files to HEAD) and log the rejection, run `echo`, and end the iteration. Do not accept rejected changes.

5. **Verify.** Run `python -m pytest sim/ -q`. If it fails, revert the change and end the iteration. A change that breaks verification is never kept.

6. **Prove.** Run `python sim/run_eval.py --config config.json --window train`. If the change cannot be demonstrated to produce the expected effect on the train window, it is not accepted: revert and log "unproven." The gate separately certifies significance, floors, and holdout non-inferiority.

7. **Commit.** Only if the change passed gate + verify + prove. Commit message: one line, why-not-what, no trailer, no mention of tooling.

8. **Log.** Append one entry to `LOG.md`: timestamp, evaluator verdict, the change made, gate verdict, verify result, prove result, and the metric this change is expected to move. Keep it to a few lines. Honest entries ("reverted, broke verify", "rejected-regime-overfit") are valuable.

9. **Meta-check.** Route any identified weaknesses in the loop itself to the `meta-improver` subagent. The orchestrator does **NOT** self-edit `iterate.md` or the agent files directly. If any proposed loop change touches a guardrail or safeguard, route it through `gate` and send an operator alert; never apply a safeguard weakening on your own authority.

10. **Notify.** Run `echo` to signal iteration complete: signal, not noise. Include the verdict and what changed (or didn't). (Note: `echo` is a no-op stub. Replace with a real notifier, e.g. a webhook or desktop notification, if you want unattended alerting.)

## Hard rules

- **`error_rate <= 2%` on every adjudicated window, and the traces (`traces/*.jsonl`) are never regenerated or mutated.** This constraint is absolute and cannot be overridden by any agent, including the meta-improver. A latency win bought with errors is a regression.
- **One change per iteration.** Reversible. Logged. No bundling.
- **Never weaken a guardrail** to chase a metric. If tempted, don't; log why instead.
- **Never block on a human**, but always be able to reach one: `echo` is the signal path (replace with a real notifier if needed).
- If a proposed change is too large, too risky, or ambiguous, STOP: write the proposal to `LOG.md` for operator review and end the iteration cleanly.
- When `GOAL.md`'s Done definition is met (budget swept, no promotable challenger), `touch DONE` so drive-to-goal.sh stops cleanly.
