# Use-case: support-message triage

Given a free-text customer support message, output strict JSON:
`{"category": one of delivery|billing|technical|account|other,
  "urgency": one of low|medium|high,
  "wants_refund": true|false}`

Scoring is exact-match on all three fields. The tournament searches prompting techniques for
the one that generalizes best from the dev set to the never-tuned holdout.

Each case also carries `_solved_by` — metadata the **offline mock model** uses to decide
correctness deterministically (a real model ignores it). It lists which technique(s) unlock the
case; `"baseline"` means even the zero-shot prompt gets it. The two trap rows are solvable by
`keyword_rules` on dev but by nothing (`__none__`) on holdout — the planted overfit the gate
must catch.
