# Iteration log — append-only

Each entry: timestamp · change made · gate verdict · verify · prove result · metric moved.
Honest entries ("reverted, broke verify", "rejected-overfit") are as valuable as wins.

---

## 2026-06-01T09:14Z — PROMOTE: few_shot

**Evaluator verdict:** Champion is `zero_shot` at dev 35% / holdout 35%. Leaderboard is sparse; the untried technique with the strongest prior is `few_shot` — labeled examples teach the exact category set and should resolve ambiguous-label cases the baseline guesses wrong.

**Proposer hypothesis:** `few_shot` renders four labeled train examples into the prompt, teaching category × urgency × wants_refund combinations the model has not seen in the instruction alone. Expected dev gain: +4 cases from label-ambiguity failures.

**Implementer:** No code change needed — `few_shot` already exists in `techniques.py`. Ran `python eval/run_eval.py --technique few_shot --split dev --model mock`. Result: 11/20 = 55%.

**Gate:** Dev 35% → 55% (+4 cases). Ran holdout: `python eval/run_eval.py --technique few_shot --split holdout --model mock`. Result: 11/20 = 55% (+4 cases). Gain reproduces on holdout (same sign, same magnitude). Above noise floor. Regression: `python -m pytest eval/ -q` — 33 passed.

**Verdict: APPROVE — promoted to champion.**

Metric: held-out pass-rate 35% → 55%.

---

## 2026-06-02T11:03Z — REJECT overfit: keyword_rules

**Evaluator verdict:** Champion is `few_shot` at dev 55% / holdout 55%. Next untried technique: `keyword_rules` — surface-token heuristic that sets `wants_refund=true` on "reopened" / "repeated ticket" patterns.

**Proposer hypothesis:** Some refund-request cases use consistent surface vocabulary ("reopened ticket", "still unresolved"). A keyword heuristic should resolve those directly, bypassing reasoning. Expected dev gain: a couple of cases.

**Implementer:** Ran `python eval/run_eval.py --technique keyword_rules --split dev --model mock`. Result: 9/20 = 45% — a +2 case gain on dev over the `zero_shot` floor (35%).

**Gate:** The dev signal is small, so the only thing that matters is whether it reproduces. Ran holdout: `python eval/run_eval.py --technique keyword_rules --split holdout --model mock`. Result: 7/20 = 35% — flat, **+0 cases**. The dev gain **does not reproduce on the never-tuned holdout**: this is the planted surface-token trap, exploiting a correlation present in dev but absent from holdout, and the gate caught it. (It also never threatened the standing champion `few_shot` at 55% — even its dev score is lower.) Regression: `python -m pytest eval/ -q` — 33 passed.

**Verdict: REJECT — overfit. The dev gain didn't generalize (holdout flat at 35%). Champion unchanged (few_shot, holdout 55%).**

Metric: held-out pass-rate unchanged at 55%.

---
