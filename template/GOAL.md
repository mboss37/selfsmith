# GOAL.md
# Replace every {{TOKEN}} with your domain specifics before running the loop.

## Mission

{{MISSION}}

## Scope layers

{{SCOPE_LAYERS}}

## Priority order

{{PRIORITY_ORDER}}

Skeleton (keep or replace):
1. Correctness and safety — output must be valid; no constraint violation
2. Persistence and integrity — improvements must survive restart; state must not corrupt
3. Core logic quality — the main decision/control loop does the right thing
4. Tuning — numeric parameters are well-calibrated
5. Scope expansion — new capabilities, only after the above are solid

## Primary objective

{{PRIMARY_OBJECTIVE}}

## Backlog

<!-- Append candidate improvements here. The proposer agent draws from this list. -->
<!-- Format: - [ ] <idea> — <rationale> — <risk> -->
<!-- - [ ] Example: reduce cold-start latency — p99 too high — risk: don't regress steady-state throughput -->

## Definition of an improvement

A change is an improvement when ALL of these hold:
- The objective metric improves, or a known blocker is removed
- No safety constraint or invariant is weakened
- The change is verified by `{{VERIFY_COMMAND}}` passing
- The claim is proven by `{{PROVE_COMMAND}}` producing a measurable result

If any condition is false, the iteration is a no-op — revert and log the lesson.

## Hard constraints (domain safety floor)

{{DOMAIN_SAFETY_FLOOR}}

These constraints are enforced by `.claude/hooks/guardrail.sh` Floor 1. The loop cannot
override them. A human must edit the hook to change this floor.

## Definition of done

{{DONE_DEFINITION}}
