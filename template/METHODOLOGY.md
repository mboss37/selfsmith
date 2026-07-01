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
5. It runs the **mechanical certification** in `tools/verdict.py` (self-test first, then the
   mode matching the claim — `screen`/`reproduce`/`confirm`/`compare`/`floor`). The arithmetic
   half of the gate is code, not judgment; a verdict.py REJECT cannot be argued past.
6. If any check fails, the change is rejected — iteration is logged as a no-op.

**Declare the candidate budget here, up front** (verdict.py `confirm`/`compare` refuse to
certify without it): <!-- e.g. "CANDIDATE BUDGET: 30 — the N configs in the fixed grid" -->
Every rule in "Not fooling yourself at the gate" below has its mechanical form in the tool:
two-sided by construction, deflated by the declared budget (not the running log), fails closed
when the search size is undeclared.

<!-- Add domain-specific gate criteria here -->

## What would make this overfit

<!-- Fill in the domain-specific warning signs that the loop is tuning to noise:
     - Metric improves on in-sample but not out-of-sample
     - Changes are increasingly micro (adjusting a single threshold by 0.1%)
     - The improvement claim relies on a sample too small to be reliable
     - Multiple parameters are changed simultaneously to "cooperate"
     Add concrete thresholds or heuristics your gate agent should check. -->

## Hard-won pitfalls (a self-improving loop keeps re-learning these)

### Measurement integrity

- **Suspect your own rig first.** When the thing you're improving is scored by an evaluation harness you also built, that harness is where bugs hide — a measurement error silently certifies bad changes or kills good ones. Make "is the measurement itself correct?" the first question every iteration; a suspected measurement bug outranks any new feature.
- **Promote every measurement fix into a standing invariant — and test it on degenerate inputs.** Don't just fix the instance; add a permanent calibration/conservation check covering the whole class, and exercise it on boundary/empty/missing-value inputs, not just well-formed data. The corner is where the bug lives.

### Not fooling yourself at the gate

- **The candidate set itself can rig the gate.** A one-sided or naive test can be gamed by the *shape* of what you submit — e.g. submitting a variant and its exact opposite, so the test auto-blesses whichever drifted favorably on this single run (selection masquerading as significance). Refuse to certify a "winner" whose exact negation is in the same batch; collapse symmetric pairs into one two-sided test.
- **Deflate for everything that was tried, including implicit search.** Any automated proposer (a model, a search) silently evaluates far more variants than you wrote down; the multiple-comparisons penalty must reflect that hidden count, not your hand-count. When unsure how much to deflate, deflate harder. Fail closed: refuse to certify if an automated proposer hasn't declared its search size.
- **Fix the candidate set once, up front.** If significance is deflated against "everything seen so far," the same result scores differently depending on *when* you look — significance becomes path-dependent on history. Define the batch before seeing outcomes; keep the running log as an audit trail, never as the denominator.
- **Every attempt counts — even the ones you abandon.** A cheap pre-check may kill a hypothesis before a full evaluation (good — it saves a cycle), but a tried-and-dropped idea still inflates your error rate if uncounted. Log every attempt, including pre-filtered kills.
- **A surprise winner is guilty until proven structural.** If the variant that survives isn't the one you hypothesized, suspect selection-on-noise. Accept it only if its parameter neighborhood is smooth (a ramp, not a lone spike among dead/negative neighbors) AND the mechanism predicts it — and run the robustness checks on the variant that actually survived, not the one you pre-registered.

### Validating a check itself

- **A demonstration must stress the real thing.** Proving a check "works" is worthless unless it (a) calls the *literal* production function the gate invokes — not a copy, however identical — and (b) includes a positive control the check must catch, paired with a clean negative it must pass. The evidence is the contrast, not a single number.

### The loop auditing itself

- **Periodically feed the gate a known-nothing control.** The cheapest way to find holes in your gate is to submit something you *know* is meaningless-but-clean and confirm it gets rejected. If it survives, you've found a gate bug — not a discovery.
- **An honest "nothing improved" is a successful iteration — and a loop measured by activity will reward-hack.** Treat a well-understood negative as success. Once the genuine work is exhausted, escalate or wait on the human-gated blocker; do NOT manufacture busywork (re-polishing the rig, re-running on mined-out inputs) to look productive. Watch for the reward-hacking signature: a proxy metric drifting up without out-of-sample confirmation, or the gate's reject-rate quietly decaying.

### Running unattended

- **Never build on unreviewed leftovers.** A cut-short iteration can leave uncommitted work; detect a dirty working state at triage and decide deliberately — finish-and-review it or discard it — never silently build on or commit it.
- **Run load-bearing work inline.** If the expensive step is backgrounded, a timeout can kill the session *after* it runs but *before* the result is reviewed, committed, and logged — losing the work and leaving a mess. Keep the heavy computation in the foreground of the iteration.
- **A false self-report is a correctness bug.** The operator's only windows into an unattended loop are its log and its status surface. Anything that misrepresents state — a stale count, an inflated metric, instrumentation shown as a real result, a page that won't load — destroys the trust the loop runs on. Fix it at measurement priority, and smoke-test the surface (it loads, populates, no errors), not just the computation behind it.
