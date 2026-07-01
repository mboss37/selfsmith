# Methodology

## Split discipline

The dataset is divided into three non-overlapping splits under `eval/cases/`:

| Split | File | Role |
|---|---|---|
| train | `train.jsonl` | Inspect cases, build few-shot example pools. Never used for measuring pass-rate. |
| dev | `dev.jsonl` | Measure pass-rate on every iteration. The working signal for technique development. |
| holdout | `holdout.jsonl` | Adjudicate challengers only. Never inspect for technique ideas, never iterate against. **Sacred.** |

**Train is for building, not measuring.** When constructing few-shot pools, draw examples from `train.jsonl`. Drawing examples from `dev.jsonl` teaches the model dev-specific patterns (teaching to the test).

**Dev is for iteration, not promotion.** Every new technique gets scored on dev. A dev gain is evidence, not proof. Promotion requires reproduction on holdout.

**Holdout is for adjudication, not iteration.** Run the holdout **once** per challenger, only to adjudicate after a dev win. Never run it proactively. If you find yourself thinking "let me check holdout to see if X might work," stop: that is tuning against the test set.

---

## Technique catalog

Each technique is a prompt renderer defined in `eval/techniques.py`. A combo is applied left-to-right: each renderer wraps the previous prompt.

| Technique | Mechanism |
|---|---|
| `zero_shot` | Baseline. Instruction only, no scaffolding. Establishes the floor. |
| `few_shot` | Labeled examples drawn from the training pool teach the exact label set (category × urgency × wants_refund). Reduces label-set ambiguity; helps on cases where the model guesses a wrong but plausible category. |
| `chain_of_thought` | Prompt asks the model to reason about category, urgency, and refund before answering. Intermediate reasoning steps unlock correct handling of multi-issue or ambiguous urgency cases. |
| `role` | Prepends a domain role ("meticulous customer-support triage analyst"). Primes domain-appropriate attention patterns. Marginal on its own; may interact with other techniques. |
| `format_spec` | Adds an explicit JSON schema instruction. Reduces malformed or incomplete output; useful when the base model returns free text instead of structured JSON. |
| `decomposition` | Asks the model to answer each sub-question (category, urgency, wants_refund) in sequence before assembling. Separating the sub-questions isolates the refund decision, which is the hardest field. |
| `self_critique` | Adds a draft-then-critique pass before the final answer. In principle catches reasoning slips. In practice, for this task, it adds latency and token cost without holdout cases beyond what `chain_of_thought` already solves; cataloged as **redundant**. |
| `keyword_rules` | Appends a surface-token heuristic (e.g., "if the message mentions a reopened ticket, set wants_refund=true"). Brittle: exploits correlations in dev that do not hold on holdout. The planted overfit trap. |

Combos compose these renderers. The champion is `few_shot+chain_of_thought+decomposition` (dev 90%, holdout 90%).

---

## Failure modes to guard against

**Overfitting a technique to dev.** Iterating on a technique until it maximizes dev scores, then expecting holdout to match. Solution: one change per iteration; adjudicate on holdout only after a genuine dev win.

**Few-shot pool leakage.** Drawing examples from `dev.jsonl` instead of `train.jsonl` for the few-shot pool. The examples then teach dev-specific surface patterns, not general label patterns. The model is effectively memorizing dev answers. Solution: always use `train.jsonl` as the pool source.

**Tiny-N over-reading.** At n=20, a one- or two-case swing is noise. Reporting a Wilson 95% CI is honest, but at n=20 two genuinely different techniques will often show overlapping intervals. **Do not treat overlapping CIs as evidence that techniques are equal.** The Wilson CI is reported for honesty, not used as the promote test. Reproduction on the never-tuned holdout is the test.

**Redundant-combo bloat.** Stacking two techniques that solve the same underlying failure mode adds token cost without adding holdout cases. Solution: for each technique added to a combo, verify it resolves cases the combo without it does not.

**Scorer or renderer bugs.** A silent change to `run_eval.py` or a technique renderer that inflates scores without improving the model. Solution: run `python -m pytest eval/ -q` before and after every change; the gate re-runs independently.

---

## Go/no-go gate

A challenger replaces the current champion **only if ALL of the following hold**:

1. **Dev gain is real.** The challenger's dev pass-rate beats the champion's dev pass-rate by at least 2 cases (above the n=20 noise floor).

2. **Holdout reproduction.** `python eval/run_eval.py --technique <challenger> --split holdout --model mock` shows the same sign of gain, with at least roughly half the dev improvement in absolute cases. A technique that adds +2 on dev but +0 on holdout is an overfit; reject it.

3. **Non-redundancy (for combos).** Each technique added beyond the current champion resolves at least one holdout case the champion does not. If a technique adds zero holdout cases the champion doesn't already solve, it is redundant; reject the combo.

4. **Regression clean.** `python -m pytest eval/ -q` passes after the change.

**On Wilson CIs:** The harness reports Wilson 95% CIs for every scored technique. At n=20, genuine improvements often produce overlapping intervals: a gain from 7/20 to 11/20 (35% → 55%) is real and meaningful, but the intervals overlap. Treating overlapping CIs as "no edge" would cause Type-II errors on every genuine improvement at this sample size. The promote test is reproduction-on-holdout, not non-overlapping CIs. CIs are there so you can see the uncertainty honestly, not to gate promotion.

The gate agent (`.claude/agents/gate.md`) runs these checks independently. Its verdict is binding; the orchestrator cannot override a REJECT.

---

## Mechanical certification (`tools/verdict.py`)

The rules above are mechanized so the certification arithmetic is code the gate runs, not prose it interprets:

- **Candidate budget, fixed up front: 24.** That is the 8 catalog techniques plus 16 combos (every 2- and 3-technique combination of the four mechanism-backed techniques `few_shot`, `chain_of_thought`, `decomposition`, `format_spec`, plus shortlisted `role`/`self_critique` stacks). The budget is declared here, at campaign start, and does not grow with the log. If the proposer wants candidates beyond it, that is a NEW campaign with a new budget, not an amendment to this one.
- **Per-step promotion** = `verdict.py reproduce` (dev gain ≥ 2 cases, holdout gain same sign and ≥ half the dev gain). At n=20 an exact test cannot certify small steps; reproduction on the never-tuned holdout is the honest instrument, and the tool enforces it mechanically.
- **Final claim** ("the converged champion genuinely beats the baseline") = `verdict.py confirm --search-size 24`, an exact two-sided sign test on the holdout, Bonferroni-deflated by the full declared budget. The converged champion passes it: 11W/0L, p ≈ 0.001 ≤ 0.05/24.
- **Known-nothing control** = `verdict.py self-test`, run at the start of every gate review. A gate that would bless a null is a gate bug, and this catches it mechanically.

The tool fails closed: `confirm` without a declared `--search-size` exits 3 and certifies nothing.
