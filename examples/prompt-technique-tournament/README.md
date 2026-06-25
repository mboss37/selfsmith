# Prompt-technique tournament — example loop

A self-improving loop that runs a tournament over prompting techniques for a fixed use-case (support-message triage) and converges on the technique that generalizes best to **unseen cases**. The harness is offline and deterministic by default — no API key needed.

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code)
- Python 3.11+
- `pip install -r requirements.txt` (installs pytest; no API key needed for offline runs)

## What this loop does

Each iteration, the loop (`/iterate`):

1. Evaluates the current champion's dev and holdout scores.
2. Proposes one technique change (or combo).
3. Measures it on dev.
4. Gates it: promotes only if the dev gain reproduces on the **never-tuned holdout** and clears the noise floor.
5. Logs the result (win or rejection) and updates the champion if approved.

The planted trap — `keyword_rules` — gains +2 cases on dev but +0 on holdout. The gate must catch it. The converged champion is `few_shot+chain_of_thought+decomposition` at 90% dev / 90% holdout.

## Run one iteration

```bash
cd examples/prompt-technique-tournament
claude          # opens Claude Code in this directory
```

Inside Claude Code:

```
/iterate              # ONE iteration, manually
/loop 30m /iterate    # CONTINUOUS — one iteration every 30 min (pick any interval)
```

The loop is offline by default — no API key, no paid calls, safe to run unattended.

## Run the harness directly

Score any technique on any split:

```bash
# Score the champion combo on dev
python eval/run_eval.py --technique few_shot+chain_of_thought+decomposition --split dev

# Score it on holdout (do this only to adjudicate, not to iterate)
python eval/run_eval.py --technique few_shot+chain_of_thought+decomposition --split holdout

# Test the planted trap
python eval/run_eval.py --technique keyword_rules --split dev
python eval/run_eval.py --technique keyword_rules --split holdout
```

Run all harness tests:

```bash
python -m pytest eval/ -q   # expects 33 passed
```

## The split discipline

| Split | Use |
|---|---|
| `train` | Inspect cases, build few-shot example pools. |
| `dev` | Measure every candidate technique. Working signal. |
| `holdout` | Adjudicate a challenger only, after it wins on dev. **Never inspect for technique ideas.** |

The holdout is the one honest judge. Iterating against it — even by looking at its cases for inspiration — invalidates the result. The guardrail in `.claude/settings.json` hard-blocks any command that would mutate `holdout.jsonl` inside the loop.

## Production seam

By default the harness uses an offline mock model (deterministic, keyed off each case's `_solved_by` metadata — see `eval/task.md`). To run against a real Anthropic model:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python eval/run_eval.py --technique few_shot+chain_of_thought --split dev --model claude
```

`--model claude` calls `claude-haiku-4-5-20251001` via the Anthropic SDK. See the `claude-api` skill for current model IDs, pricing, and SDK usage before changing the model. The loop itself stays on `--model mock` by the guardrail in `.claude/hooks/`; `--model claude` is for one-off human validation only.

## Files at a glance

```
.claude/
  commands/iterate.md   — orchestrator (Vera)
  agents/               — evaluator, proposer, implementer, gate, meta-improver
  hooks/                — guardrail: blocks holdout mutation and paid model calls
eval/
  run_eval.py           — scorer (--technique, --split, --model)
  techniques.py         — full technique catalog + renderers
  cases/                — train.jsonl, dev.jsonl, holdout.jsonl
  champion.json         — loop's SEED/start state (zero_shot, 35%); the loop walks it forward. The converged champion (few_shot+chain_of_thought+decomposition, 90%) is shown in eval/leaderboard.md
  leaderboard.md        — full ranked history including rejections
GOAL.md                 — what "done" looks like
PERSONA.md              — Vera's principles
METHODOLOGY.md          — split discipline + go/no-go gate
LOG.md                  — append-only iteration history
```
