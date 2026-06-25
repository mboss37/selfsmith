# METHODOLOGY.md
# Replace the {{TOKEN}} placeholders and flesh out each section before running the loop.
# Task 5's agents and iterate.md reference this file by name — do not rename it.

## Philosophy

Generic starting principles — keep these and add domain-specific ones below:

- Every claim is backed by a measurement, not a narrative.
- One change per iteration, so its effect is attributable.
- A gain that doesn't hold beyond the data you tuned on isn't real.

<!-- Describe the intellectual framework that guides improvement decisions in this domain.
     What kind of evidence counts? What counts as proof? What is the unit of progress? -->

## Domain failure modes

Generic failure modes that apply to most domains — extend with your own:

- Overfitting — a gain that only holds on the data you tuned against.
- Broken measurement — optimizing against a metric that is silently wrong.
- Multiple comparisons — trying many variants and keeping the lucky one.

<!-- List the ways improvement attempts typically go wrong in this domain.
     Examples: overfitting a small sample, measuring the wrong metric, confusing correlation
     with causation, optimizing locally while degrading globally. Be specific. -->

## Validation methodology

### Holdout discipline

The holdout set is fixed at the start of the project and never touched during development.
It exists to detect generalization failure — if it is used to make decisions, it is no
longer a holdout.

<!-- Describe how your domain partitions data or evaluation sets, and what "contaminating
     the holdout" means concretely here. -->

### In-loop evaluation

<!-- Describe what the evaluator agent measures in each iteration. What numbers are
     tracked? What constitutes a meaningful signal vs noise? -->

### Go/no-go gate

Before any proposed change is applied:
1. The gate agent reads the diff.
2. It checks that no safety constraint from `GOAL.md` is weakened.
3. It checks that no guardrail floor in `.claude/hooks/guardrail.sh` is softened.
4. It checks that the proposed metric improvement is plausible given the change.
5. If any check fails, the change is rejected — iteration is logged as a no-op.

<!-- Add domain-specific gate criteria here -->

## What would make this overfit

<!-- Fill in the domain-specific warning signs that the loop is tuning to noise:
     - Metric improves on in-sample but not out-of-sample
     - Changes are increasingly micro (adjusting a single threshold by 0.1%)
     - The improvement claim relies on a sample too small to be reliable
     - Multiple parameters are changed simultaneously to "cooperate"
     Add concrete thresholds or heuristics your gate agent should check. -->
