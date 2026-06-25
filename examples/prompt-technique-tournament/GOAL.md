# Goal: find the prompting technique that generalizes

## Mission

Find the prompting technique (or minimal combo) that best solves support-message triage on **unseen cases**, not the one that merely tops the dev leaderboard. The measure of success is held-out pass-rate after honest adjudication — not dev rank, not CI width, not subjective complexity.

## Priority order when in conflict

1. **Harness and scorer correctness.** If `python -m pytest eval/ -q` is red, or if `run_eval.py` produces suspect numbers, fix measurement before touching techniques. A broken ruler makes every subsequent reading worthless.

2. **Holdout integrity.** The held-out split (`eval/cases/holdout.jsonl`) is never touched, inspected for technique ideas, or scored during development. It exists only to adjudicate a challenger that already beat the champion on dev.

3. **Dev pass-rate.** Maximize it as a working signal — but treat it as necessary, not sufficient. A dev gain below 2 cases (at n=20) is within noise and is not a real improvement.

4. **Held-out generalization.** The dev gain must reproduce on holdout: same sign, at least roughly half the dev improvement in absolute cases. This is the promote test.

5. **Prompt cost (tokens and latency).** Among techniques that tie on held-out pass-rate, prefer the simpler and cheaper one. A combo that adds a technique without adding holdout cases is bloat.

## Objective

- Do not fool yourself. The holdout is the cure; keep it sacred.
- Maximize held-out pass-rate on the support-message triage task (`eval/task.md`).
- On a tie, promote the cheaper technique.

## Acceptance criteria

- `python -m pytest eval/ -q` passes (33 tests green).
- The go/no-go gate approves the challenger.
- The new champion beats the prior champion on dev by at least 2 cases AND the gain reproduces on holdout (same sign, magnitude above the noise floor).
- The champion has survived at least one honest challenger that lost — confirming the holdout gate is biting.

## Done

A champion clears the go/no-go gate on holdout and survives N iterations unbeaten by an honest challenger. The planted trap (`keyword_rules`: dev gain does not reproduce on holdout) has been caught and rejected. The loop can continue, but further gains require real generalization, not dev tuning.
