# Prompt-technique tournament: example loop

A self-improving loop that tests different prompting techniques against a fixed task (sorting support messages into categories) and finds whichever one actually works on messages it hasn't seen before, not just the one that scored best on the messages it practiced on. Runs offline with realistic fake data; no API key needed.

New to Selfsmith? The [root README](../../README.md) explains the whole idea in plain terms and has a glossary for any term below that isn't obvious.

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code)
- Python 3.11+
- `pip install -r requirements.txt` (installs pytest; no API key needed for offline runs)

## What this loop does

Each run (`/iterate`):

1. Checks how the current best technique is doing.
2. Proposes one technique to try, or one combination of techniques.
3. Scores it against the tuning data.
4. Decides: the new technique only wins if it also holds up on data that was never used for tuning, and the improvement is big enough to trust.
5. Writes down what happened, win or loss, and updates the current best technique if it won.

There's a deliberately planted bad result in the catalog: a technique called `keyword_rules` scores +2 cases better on the tuning data and +0 better on the data set aside for checking. The gate has to catch that and reject it, and the test suite proves it does. The technique that actually wins is a combination called `few_shot+chain_of_thought+decomposition`, scoring 90% on both the tuning data and the checking data.

## Run one iteration

```bash
cd examples/prompt-technique-tournament
claude          # opens Claude Code in this directory
```

Inside Claude Code:

```
/iterate              # ONE run, manually
/loop 30m /iterate    # CONTINUOUS: one run every 30 minutes (pick any interval)
```

The loop is offline by default: no API key, no paid calls, safe to run unattended.

## Run the harness directly

Score any technique against any part of the data:

```bash
# Score the winning combination against the tuning data
python eval/run_eval.py --technique few_shot+chain_of_thought+decomposition --split dev

# Score it against the held-back checking data (only do this to confirm a winner, not to explore)
python eval/run_eval.py --technique few_shot+chain_of_thought+decomposition --split holdout

# Try the planted bad result
python eval/run_eval.py --technique keyword_rules --split dev
python eval/run_eval.py --technique keyword_rules --split holdout
```

Run everything:

```bash
python -m pytest eval/ -q   # expects all green
```

## The three-way data split

| Split | Used for |
|---|---|
| `train` | Building examples, looking at cases, getting a feel for the task. |
| `dev` | Scoring every candidate technique. This is the working signal. |
| `holdout` | Confirming a winner, once, after it already won on `dev`. Never used to come up with ideas. |

`holdout` is the one honest check. Looking at it for inspiration, even without formally scoring against it, defeats the whole point, the same way peeking at exam answers while studying does. The safety script in `.claude/settings.json` blocks any command that would edit `holdout.jsonl` while the loop is running, so this isn't just a rule someone has to remember.

## Running against a real model instead of the offline fake one

By default the harness uses a fake, deterministic stand-in for a model (its answers are decided by metadata attached to each test case; see `eval/task.md`). To run it against an actual Claude model instead:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python eval/run_eval.py --technique few_shot+chain_of_thought --split dev --model claude
```

`--model claude` calls `claude-haiku-4-5-20251001` through the Anthropic SDK. Check the `claude-api` skill for current model names and pricing before changing which model it uses. The loop itself is locked to the offline fake model by the safety script in `.claude/hooks/`; `--model claude` is meant for a human to check by hand, not for the loop to use on its own.

## Files at a glance

```
.claude/
  commands/iterate.md   - the orchestrator (goes by "Vera" in this example)
  agents/                - evaluator, proposer, implementer, gate, meta-improver
  hooks/                 - the safety script: blocks editing holdout data or calling a paid model
eval/
  run_eval.py            - scores a technique (--technique, --split, --model)
  techniques.py          - the full catalog of techniques and how each one changes the prompt
  cases/                 - train.jsonl, dev.jsonl, holdout.jsonl
  champion.json          - the starting point (zero_shot, 35%); the loop walks this forward over time. The eventual winner (few_shot+chain_of_thought+decomposition, 90%) is recorded in eval/leaderboard.md
  leaderboard.md         - the full history, including the techniques that lost
GOAL.md                  - what "done" means for this loop
PERSONA.md               - Vera's guiding principles
METHODOLOGY.md           - the data-split rules and what it takes to promote a winner
LOG.md                   - an append-only diary, one entry per run
```
