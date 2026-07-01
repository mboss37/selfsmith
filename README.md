# Selfsmith

> A self-improving loop that forges itself, one tested change at a time.

![CI](https://github.com/mboss37/selfsmith/actions/workflows/ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reusable, domain-agnostic self-improvement loop, extracted from a production Claude Code harness and hardened to run unattended without (a) fooling itself or (b) wrecking the machine.

### Why use this

Building this loop yourself takes several painful iterations to discover the failure modes this ships as structure: the adversarial gate that independently vetoes each change — with its certification arithmetic in code (`tools/verdict.py`) so a plausible-but-wrong gain can't be argued past it; the mechanical floor the loop genuinely cannot lift (not just an instruction it could argue around), with the OS-level jail bundled in `sandbox/`; the metric contract that refuses to start a loop on a measurement that can't tell good from bad; honest-negative logging that counts "tested and killed" as a win; and the holdout discipline that prevents the loop from gaming its own metric. Those things are what make an unattended loop trustworthy rather than theatrical.

Copy `template/`, fill the blanks, and have a disciplined, unattended, self-improving Claude Code loop for your domain. Both flavors ship fully instantiated and offline (no API key): `examples/prompt-technique-tournament/` (discover-and-validate) and `examples/latency-tuner/` (optimize-a-running-system).

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

- **A mechanical floor the loop can't lift.** A shell hook — not an instruction — gates Bash AND the file-edit tools (Edit/Write/MultiEdit/NotebookEdit), so the loop can't rewrite its own guardrail, settings, or a protected path — whether via a file-edit tool OR a Bash redirect/`cp`/`tee`/`sed -i` (the Bash branch mirrors the write-tool gate). The hook fails closed: an unparseable tool call is blocked, not allowed through. That said, a command deny-list is a **tripwire for honest mistakes, not a complete security boundary** against an adversarial agent — shell quoting and obfuscation can evade any string-matching list. For genuinely safe unattended runs, add an OS sandbox where destructive syscalls are impossible at the OS level — ready-to-adapt jails ship in `template/sandbox/` (container, hardened systemd unit, macOS Seatbelt) — and optionally `chmod 0444` the guardrail and settings files. Distinguish the **mechanical floor** (hook + OS sandbox) from the **disciplinary controls** (gate veto, meta-improver restraint, orchestrator) — the latter are LLM judgment, not hard blocks.
- **Gates default to REJECT.** Killing a good idea is cheaper than shipping a bad one.

---

## The anatomy — 9 structural parts

| Part | Role |
|---|---|
| `commands/iterate.md` | **Orchestrator** — thin router; runs ONE disciplined iteration |
| `PERSONA.md` | **Decision philosophy** — a named expert archetype and operating principles |
| `GOAL.md` | **Mission, priority order, acceptance test, candidate budget, definition of done** |
| `agents/*.md` | **Worker roles** — 4–5 archetypes (see below) |
| `hooks/guardrail.sh` + `settings.json` | **The floor** — a mechanical guardrail the loop can't lift itself |
| `METHODOLOGY.md` | **"How we don't fool ourselves"** — rulebook and go/no-go gate |
| `LOG.md` | **Memory** — append-only honest diary, one entry per iteration |
| `tools/verdict.py` + `tools/metric-contract.sh` | **The arithmetic** — mechanical certification (sign test / paired bootstrap, deflated by the declared search budget, fails closed) and the prove-your-metric-first contract |
| `sandbox/` | **The jail** — container, systemd, and Seatbelt configs; the boundary the tripwire is not |

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
- **Worked example:** `examples/latency-tuner/` — retry-policy tuning against replayed traffic, with an out-of-time holdout, a hard error-rate floor, and a planted config that tops the train leaderboard and breaches the floor out-of-time

### Discover and validate

The loop searches a space of candidates (techniques, strategies, configurations) for the one that genuinely generalizes. A holdout split is sacred and only touched to adjudicate a winner — never iterated against.

- **Agents used:** evaluator → proposer → implementer → gate (with holdout check)
- **Proposer:** required (each candidate needs a stated mechanism — "no mechanism → don't propose")
- **Holdout:** written once, read only when a challenger wins on the dev/train split
- **Worked example:** `examples/prompt-technique-tournament/` — the loop searches a catalog of prompting techniques for the one that generalizes to unseen cases, and the gate rejects any candidate whose dev win doesn't reproduce on the holdout

---

## How to instantiate

```bash
cp -r template/ my-loop/
```

Then follow `INSTANTIATE.md` in your new directory (it lives at `template/INSTANTIATE.md` in this repo). It is an ordered checklist — **metric contract first (Step 0)** → GOAL → PERSONA → METHODOLOGY → guardrail → agents → iterate command → run mechanism — with a glossary of every `{{TOKEN}}` and what it means.

Step 0 is the one people skip and regret: before any other blank, `metric-contract.env` + `bash tools/metric-contract.sh` must prove your metric is numeric, deterministic, and able to score a planted-bad control worse than a known-good one. The loop is only as good as the metric it optimizes; a loop pointed at a metric that fails its own contract optimizes a lie, and no downstream gate can save it.

The tokens you fill in across the files (see `INSTANTIATE.md` for the full glossary): `{{METRIC_GOOD_CMD}}`/`{{METRIC_BAD_CMD}}` (Step 0), `{{PERSONA_NAME}}`, `{{MISSION}}`, `{{VERIFY_COMMAND}}`, `{{PROVE_COMMAND}}`, `{{STATE_SOURCE}}`, `{{LOG_FILE}}`, `{{NOTIFY_COMMAND}}`, `{{DOMAIN_SAFETY_FLOOR}}`, and the `guardrail.sh` Floor-1 token `{{DOMAIN_FORBIDDEN_PATTERN}}`. Fill them top-to-bottom; later files reference tokens set in earlier ones. Declare the **candidate budget** in `GOAL.md`/`METHODOLOGY.md` while you're there — `tools/verdict.py` refuses to certify significance without it.

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

Prefer your platform's native scheduler if you like — **launchd** (macOS), a **systemd timer** (Linux; a hardened unit+timer pair ships in `sandbox/`), or **Task Scheduler** via WSL (Windows). Each just runs `run-iteration.sh` on a timer. Override the per-iteration wall-clock ceiling with `ITER_TIMEOUT` (default `50m`) and the per-iteration **spend ceiling** with `ITER_MAX_TURNS` (default `50` agent turns, passed to `claude -p --max-turns`) — an unattended loop needs a budget floor it cannot argue past, exactly like the safety floor; raise it deliberately rather than removing it. The time-box needs GNU `timeout` (or `gtimeout`); stock macOS ships neither until you `brew install coreutils`, and without one the single-flight lock still holds but there is **no per-iteration ceiling** — the wrapper says so on stderr.

**Run until done (bounded loops):**

For a loop with a finish line — a checklist to complete, a winner to converge on — don't tick on a clock; run iterations **back-to-back until it converges**, then stop. `drive-to-goal.sh` does exactly that: it calls `run-iteration.sh` in series (so each tick is still a fresh, single-flight, time-boxed session) and stops on the first of — a `DONE` marker the loop writes at convergence, a **stall** (no new commit for `STALL_LIMIT` iterations, default 3), or `MAX_ITERS` (default 20).

```bash
./drive-to-goal.sh                                # run until DONE / stalled / capped
MAX_ITERS=40 STALL_LIMIT=5 ./drive-to-goal.sh     # override the bounds
```

**Which mode?** Back-to-back (`drive-to-goal.sh`) for **bounded / convergent** work — go fast to the goal, then stop. A **timer** (cron / launchd / systemd running `run-iteration.sh`) for **ongoing / time-dependent** work — tuning a live system where you *want* spacing so new data accumulates between ticks. Same fresh-session-per-tick discipline either way; only the trigger differs.

The wrapper handles overlap and timeouts. It does **not** sandbox — and the sandbox is the real boundary: the guardrail deny-list is a **tripwire for honest mistakes, not a jail** (shell quoting, encoding, and command substitution evade any string match). The jail ships in **`sandbox/`**: a container image + locked-down runner (`sandbox/run-sandboxed.sh` — read-only rootfs, dropped capabilities, resource ceilings, the floor files mounted read-only even inside the writable area), a hardened **systemd** unit+timer, and a macOS **Seatbelt** profile. Pick one before running unattended — see `sandbox/README.md` — and optionally `chmod 0444` the guardrail and settings files on top.

Before running unattended, confirm the guardrail actually blocks what it should — not just that the script parses:
```bash
bash -n .claude/hooks/guardrail.sh && echo "syntax OK"   # syntax check only
```
A syntax check does not prove the floors fire. The worked example ships `eval/test_guardrail.py`, which feeds the hook real tool-call JSON via subprocess and asserts both floors return exit 2 (block) on forbidden commands and exit 0 on benign ones. Copy that test pattern to verify your own Floor-1 pattern genuinely blocks.

---

## Worked examples — both flavors, both with a planted trap the gate must catch

Every example is offline and deterministic (no API key), fully instantiated from the template, and ships a trap that looks like the best candidate on the in-sample data and fails out-of-sample — so "the gate bites" is a tested property, not a claim.

### `examples/prompt-technique-tournament/` — discover and validate

Searches a catalog of named prompting techniques (few-shot, chain-of-thought, decomposition, …) for the best-generalizing one on a support-message triage task.

```bash
cd examples/prompt-technique-tournament
python eval/run_eval.py --technique few_shot --split dev --model mock   # score any technique
python -m pytest eval/ -q                                               # full suite passes
claude   # then: /iterate
```

The trap: `keyword_rules` wins +2 cases on dev and +0 on holdout — `tools/verdict.py reproduce` rejects it mechanically. The converged champion is `few_shot+chain_of_thought+decomposition`, and its final claim over the baseline survives an exact sign test deflated by the full declared 24-candidate budget (11W/0L on holdout, p ≈ 0.001). See its README for the split discipline and the production seam (`--model claude`).

### `examples/latency-tuner/` — optimize a running system

Tunes a service's retry policy (`timeout_ms`, `retries`, `backoff_ms`) against replayed traffic, promoting only what survives an **out-of-time** holdout window with a degraded upstream.

```bash
cd examples/latency-tuner
python sim/run_eval.py --config config.json --window train              # score the champion
python -m pytest sim/ -q                                                # full suite passes
claude   # then: /iterate
```

The trap: `timeout_ms=260, retries=3` **tops the train leaderboard** (mean effective 320ms vs the honest 332ms) and runs **8.8% errors** on the holdout window, where congestion persists across retries — `tools/verdict.py floor` kills it. The domain also teaches the classic reward-hack: success-only latency improves when you fail fast, so the headline metric costs every error at +10s and the error floor is checked separately, both mechanically.
