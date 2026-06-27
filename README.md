# Selfsmith

> A self-improving loop that forges itself, one tested change at a time.

![CI](https://github.com/mboss37/selfsmith/actions/workflows/ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reusable, domain-agnostic self-improvement loop, extracted from a production Claude Code harness and hardened to run unattended without (a) fooling itself or (b) wrecking the machine.

### Why use this

Building this loop yourself takes several painful iterations to discover the failure modes this ships as structure: the adversarial gate that independently vetoes each change, the mechanical floor the loop genuinely cannot lift (not just an instruction it could argue around), honest-negative logging that counts "tested and killed" as a win, and the holdout discipline that prevents the loop from gaming its own metric. Those four things are what make an unattended loop trustworthy rather than theatrical.

Copy `template/`, fill the blanks, and have a disciplined, unattended, self-improving Claude Code loop for your domain. The `examples/prompt-technique-tournament/` directory is the same engine fully instantiated — runs offline with no API key.

---

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code) — the loop runs as a Claude Code slash command.
- Python 3.11+ and `pip install -r requirements.txt` (installs pytest) to run the example offline without an API key.

## Quick start

The loop is a Claude Code **slash command**. Open Claude Code **in the loop's directory** (so it loads that `.claude/`), then:

```
/iterate              # run ONE iteration, manually
/loop 1h /iterate     # run CONTINUOUSLY — one iteration every hour (pick any interval)
```

`/iterate` shows up in the `/` menu automatically — it's defined in `.claude/commands/iterate.md`. For hands-off runs, schedule the bundled `run-iteration.sh` on a timer (cron, launchd, or a systemd timer). New here? Copy `template/`, fill the blanks per `INSTANTIATE.md`, then trigger as above.

---

## What this is

Anthropic's evaluator–optimizer pattern, disciplined enough for unattended operation. One role evaluates and diagnoses. Another proposes and implements. A third tries to kill the change. The machine can only improve by running this cycle — it can never promote itself past the gate.

Two properties make it disciplined enough to leave running:

- **A mechanical floor the loop can't lift.** A shell hook — not an instruction — gates Bash AND the file-edit tools (Edit/Write/MultiEdit/NotebookEdit), so the loop can't rewrite its own guardrail, settings, or a protected path — whether via a file-edit tool OR a Bash redirect/`cp`/`tee`/`sed -i` (the Bash branch mirrors the write-tool gate). The hook fails closed: an unparseable tool call is blocked, not allowed through. That said, a command deny-list is a **tripwire for honest mistakes, not a complete security boundary** against an adversarial agent — shell quoting and obfuscation can evade any string-matching list. For genuinely safe unattended runs, add an OS sandbox (macOS Sandbox, a container, or an unprivileged user) where destructive syscalls are impossible at the OS level, and optionally `chmod 0444` the guardrail and settings files. Distinguish the **mechanical floor** (hook + OS sandbox) from the **disciplinary controls** (gate veto, meta-improver restraint, orchestrator) — the latter are LLM judgment, not hard blocks.
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
3. The loop **can't lift its own floor** — hook (mechanical, gates Bash + write tools, fails closed) + gate (judgment) + meta-improver barred from loosening safeguards. The deny-list is a tripwire; the real boundary for unattended runs is an OS sandbox.
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

**Unattended (any OS):**

Schedule the bundled `run-iteration.sh` — never raw `claude`. Each tick is a **fresh session** (`claude -p`, no `--continue`: the loop's memory is on disk — `LOG.md`, champion state, git — so every run re-grounds from truth). The wrapper takes a **single-flight lock** so iterations never overlap, and **time-boxes** each run so a wedged iteration is killed, not left spinning.

```bash
chmod +x run-iteration.sh                       # once

# POSIX cron (Linux, macOS, WSL) — every hour:
0 * * * * cd /path/to/my-loop && ./run-iteration.sh
```

Prefer your platform's native scheduler if you like — **launchd** (macOS), a **systemd timer** (Linux), or **Task Scheduler** via WSL (Windows). Each just runs `run-iteration.sh` on a timer. Override the per-iteration ceiling with `ITER_TIMEOUT` (default `50m`). The time-box needs GNU `timeout` (or `gtimeout`); stock macOS ships neither until you `brew install coreutils`, and without one the single-flight lock still holds but there is **no per-iteration ceiling** — the wrapper says so on stderr.

**Run until done (bounded loops):**

For a loop with a finish line — a checklist to complete, a winner to converge on — don't tick on a clock; run iterations **back-to-back until it converges**, then stop. `drive-to-goal.sh` does exactly that: it calls `run-iteration.sh` in series (so each tick is still a fresh, single-flight, time-boxed session) and stops on the first of — a `DONE` marker the loop writes at convergence, a **stall** (no new commit for `STALL_LIMIT` iterations, default 3), or `MAX_ITERS` (default 20).

```bash
./drive-to-goal.sh                                # run until DONE / stalled / capped
MAX_ITERS=40 STALL_LIMIT=5 ./drive-to-goal.sh     # override the bounds
```

**Which mode?** Back-to-back (`drive-to-goal.sh`) for **bounded / convergent** work — go fast to the goal, then stop. A **timer** (cron / launchd / systemd running `run-iteration.sh`) for **ongoing / time-dependent** work — tuning a live system where you *want* spacing so new data accumulates between ticks. Same fresh-session-per-tick discipline either way; only the trigger differs.

The wrapper handles overlap and timeouts. It does **not** sandbox — that is still on you, and it is the real boundary: the guardrail deny-list is a **tripwire for honest mistakes, not a jail** (shell quoting, encoding, and command substitution evade any string match). For genuinely safe unattended runs, launch the wrapper inside an **OS sandbox** (macOS Sandbox, Linux namespaces, or a container with a minimal filesystem) or an unprivileged user where destructive syscalls are impossible at the OS level, and optionally `chmod 0444` the guardrail and settings files.

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
