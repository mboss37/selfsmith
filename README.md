# Selfsmith

> A self-improving loop that forges itself, one tested change at a time.

A reusable, domain-agnostic self-improvement loop, extracted from a production Claude Code harness and hardened to run unattended without (a) fooling itself or (b) wrecking the machine.

Copy `template/`, fill the blanks, and have a disciplined, unattended, self-improving Claude Code loop for your domain. The `examples/prompt-technique-tournament/` directory is the same engine fully instantiated — runs offline with no API key.

---

## Quick start

The loop is a Claude Code **slash command**. Open Claude Code **in the loop's directory** (so it loads that `.claude/`), then:

```
/iterate              # run ONE iteration, manually
/loop 1h /iterate     # run CONTINUOUSLY — one iteration every hour (pick any interval)
```

`/iterate` shows up in the `/` menu automatically — it's defined in `.claude/commands/iterate.md`. For hands-off runs, schedule `claude --continue -p "/iterate"` on a cron. New here? Copy `template/`, fill the blanks per `INSTANTIATE.md`, then trigger as above.

---

## What this is

Anthropic's evaluator–optimizer pattern, disciplined enough for unattended operation. One role evaluates and diagnoses. Another proposes and implements. A third tries to kill the change. The machine can only improve by running this cycle — it can never promote itself past the gate.

Two properties make it safe to leave running:

- **The loop can't lift its own floor.** A shell hook (not an instruction, a hard block) enforces the domain safety constraint. An agent can't talk its way around it.
- **Gates default to REJECT.** Killing a good idea is cheaper than shipping a bad one.

---

## The anatomy — 7 structural parts

| Part | Role |
|---|---|
| `commands/iterate.md` | **Orchestrator** — thin router; runs ONE disciplined iteration |
| `PERSONA.md` | **Decision philosophy** — a named expert archetype and operating principles |
| `GOAL.md` | **Mission, priority order, acceptance test, backlog, definition of done** |
| `agents/*.md` | **Worker roles** — 4–5 archetypes (see below) |
| `hooks/guardrail.sh` + `settings.json` | **The floor** — a mechanical guardrail the loop can't lift itself |
| `METHODOLOGY.md` | **"How we don't fool ourselves"** — rulebook and go/no-go gate |
| `LOG.md` | **Memory** — append-only honest diary, one entry per iteration |

---

## The worker archetypes

Five roles cover every safe self-improvement loop. Simple loops can drop the proposer.

| Archetype | Tools | Role |
|---|---|---|
| **Evaluator** | read-only | Judge current state vs GOAL; produce verdict + diagnosis + recommended focus |
| **Proposer** | read-only | Propose ONE mechanism-backed change with a falsifiable expected effect _(optional for simple loops)_ |
| **Implementer** | write | Make the ONE change, test-first, measure, prove it |
| **Gate** | read-only, **VETO** | Adversarially try to kill the change; default-REJECT |
| **Meta-improver** | write | Improve the loop itself; **may not weaken a safeguard** |

The gate is the most important archetype. It runs independently, cannot be overridden by the implementer, and must reach a verdict before any change is accepted.

---

## The 10 principles

These are the IP — carry them verbatim when instantiating.

1. Doing and checking are **never the same role** — independent adversarial review with veto.
2. **One change per iteration** — reversible, logged, attributable.
3. The loop **can't lift its own floor** — hook (mechanical) + gate (judgment) + meta-improver barred from loosening safeguards.
4. Orchestrator is a **thin router** — triage → route → decide, never implements.
5. Gates **default to REJECT** — killing a good idea is cheaper than shipping a bad one.
6. **Honest negatives count** — "tested, killed, why" is a win; no activity theatre.
7. **Never block on a human, always able to reach one** (notify escape hatch).
8. **Priority order puts correctness/safety above the headline metric** — never optimize on a broken measurement.
9. **Meta-improvement is first-class but separate** — the loop gets better at getting better.
10. **Reward-hacking is an explicit threat** — guardrails against the loop gaming its own metrics.

---

## The two flavors

Both are expressed by the same engine. Choose based on the problem shape.

### Optimize a running system

The loop tunes something that is already running. Changes are incremental — parameter adjustments, threshold shifts, configuration fixes.

- **Agents used:** evaluator → implementer → gate
- **Proposer:** optional (the evaluator's diagnosis often points directly at the change)
- **Holdout:** usually a time-based out-of-sample split or a held-out test set

### Discover and validate

The loop searches a space of candidates (techniques, strategies, configurations) for the one that genuinely generalizes. A holdout split is sacred and only touched to adjudicate a winner — never iterated against.

- **Agents used:** evaluator → proposer → implementer → gate (with holdout check)
- **Proposer:** required (each candidate needs a stated mechanism — "no mechanism → don't propose")
- **Holdout:** written once, read only when a challenger wins on the dev/train split

The `examples/prompt-technique-tournament/` is the richer discover-and-validate flavor: the loop searches a catalog of prompting techniques for the one that generalizes to unseen cases, and the gate rejects any candidate whose dev win doesn't reproduce on the holdout.

---

## How to instantiate

```bash
cp -r template/ my-loop/
```

Then follow `INSTANTIATE.md` in your new directory (it lives at `template/INSTANTIATE.md` in this repo). It is an ordered checklist — GOAL → PERSONA → METHODOLOGY → guardrail → agents → iterate command → run mechanism — with a glossary of every `{{TOKEN}}` and what it means.

The tokens you fill in across the files (see `INSTANTIATE.md` for the full glossary): `{{PERSONA_NAME}}`, `{{MISSION}}`, `{{VERIFY_COMMAND}}`, `{{PROVE_COMMAND}}`, `{{STATE_SOURCE}}`, `{{LOG_FILE}}`, `{{NOTIFY_COMMAND}}`, `{{DOMAIN_SAFETY_FLOOR}}`, and the `guardrail.sh` Floor-1 token `{{DOMAIN_FORBIDDEN_PATTERN}}`. Fill them top-to-bottom; later files reference tokens set in earlier ones.

---

## How to run

**One-shot (manual):**
```bash
cd my-loop
claude          # open Claude Code in the loop directory
# inside the session:
/iterate
```

**Session-scoped loop:**
```
/loop 1h /iterate     # fixed interval — runs hourly
/loop /iterate        # no interval — the model self-paces
```
With an interval, `/loop` repeats at that fixed cadence (`1h` = hourly). Omit the interval and the model decides when to run the next iteration.

**Unattended (cron or launchd):**
```bash
# Add to crontab (runs every hour, resumes the same session):
0 * * * * cd /path/to/my-loop && claude --continue -p "/iterate"
```

Before running unattended, confirm the guardrail actually blocks what it should — not just that the script parses:
```bash
bash -n .claude/hooks/guardrail.sh && echo "syntax OK"   # syntax check only
```
A syntax check does not prove the floors fire. The worked example ships `eval/test_guardrail.py`, which feeds the hook real tool-call JSON via subprocess and asserts both floors return exit 2 (block) on forbidden commands and exit 0 on benign ones. Copy that test pattern to verify your own Floor-1 pattern genuinely blocks.

---

## Worked example

`examples/prompt-technique-tournament/` — the discover-and-validate flavor instantiated for a prompt-engineering domain.

The loop searches a catalog of named prompting techniques (few-shot, chain-of-thought, decomposition, etc.) for the best-generalizing one on a support-message triage task. It runs offline with no API key required.

```bash
cd examples/prompt-technique-tournament

# Score any technique
python eval/run_eval.py --technique few_shot --split dev --model mock

# Run all harness tests (the full suite passes)
python -m pytest eval/ -q

# Open Claude Code and run one iteration
claude
# /iterate
```

The example has a planted trap (`keyword_rules`) that wins on dev but not holdout — the gate must catch it. The converged champion is `few_shot+chain_of_thought+decomposition`.

See `examples/prompt-technique-tournament/README.md` for the full runbook, the split discipline, and the production seam (`--model claude` for real Anthropic calls).
