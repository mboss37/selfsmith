# Technique tournament leaderboard

Use-case: support-message triage (`eval/task.md`). Metric: exact-match pass-rate.
Gate rule: a challenger is promoted only if it beats the champion on **dev** AND the gain
**reproduces on the never-tuned holdout** (at least roughly half the dev gain, same sign),
the gain is at least 2 cases (above the noise floor at n=20), and for a combo, each added
technique is non-redundant. Wilson 95% CIs are wide at n=20; they are reported for honesty,
not used as the promote test (two genuine-but-overlapping intervals would wrongly read as
"no edge").

| Rank | Technique | Dev | Holdout | Verdict |
|---|---|---|---|---|
| 1 | few_shot + chain_of_thought + decomposition | 90% | 90% | **champion** |
| 2 | few_shot + chain_of_thought | 75% | 75% | promoted (superseded) |
| 3 | few_shot | 55% | 55% | promoted (superseded) |
| 3 | chain_of_thought | 55% | 55% | promoted (superseded) |
| 5 | decomposition | 50% | 50% | promoted (superseded) |
| n/a | self_critique | 55% | n/a | redundant with chain_of_thought (adds cost, not edge) |
| n/a | keyword_rules | 45% | 35% | **rejected, overfit** (dev gain vanishes on holdout) |
| n/a | zero_shot (baseline) | 35% | 35% | start |

**Read this:** `keyword_rules` topped a naive dev-only ranking but **did not reproduce on the
holdout**. That's the planted trap, caught. The converged champion stacks three techniques
whose gains each generalize; `self_critique` was left out because it solved nothing that
`chain_of_thought` didn't.
