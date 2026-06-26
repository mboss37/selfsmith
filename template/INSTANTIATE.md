# INSTANTIATE.md
# Step-by-step guide to turning this template into a working self-improvement loop.
# Complete the steps in order — later steps depend on earlier ones.

---

## Ordered fill-in checklist

### Step 1 — Fill in GOAL.md

Open `GOAL.md` and replace every `{{TOKEN}}`:

- [ ] `{{MISSION}}` — one paragraph: what the loop is optimizing and why it matters
- [ ] `{{SCOPE_LAYERS}}` — bullet list of what is in and out of scope for the loop
- [ ] `{{PRIORITY_ORDER}}` — ordered list of improvement priorities (replace or keep skeleton)
- [ ] `{{PRIMARY_OBJECTIVE}}` — the single metric or outcome the loop maximizes
- [ ] `{{DONE_DEFINITION}}` — what state means "we are done iterating for now"
- [ ] `{{DOMAIN_SAFETY_FLOOR}}` — the hard constraints the loop must never violate

Add at least one seed item to the Backlog section.

### Step 2 — Fill in PERSONA.md

Open `PERSONA.md` and replace every `{{TOKEN}}`:

- [ ] `{{PERSONA_NAME}}` — the name agents will use when addressing the orchestrator persona
- [ ] `{{EXPERT_ARCHETYPE}}` — the domain role this persona embodies (e.g. "quantitative analyst",
  "compiler engineer", "ML researcher")
- [ ] `{{ONE_LINE_BIO}}` — one sentence: who this persona is and what they care about
- [ ] Add domain-specific principles to the "Domain-specific principles" section if needed

### Step 3 — Fill in METHODOLOGY.md

Open `METHODOLOGY.md` and complete each section:

- [ ] Philosophy — the intellectual framework for decisions in your domain
- [ ] Domain failure modes — how improvement attempts typically go wrong here
- [ ] Holdout discipline — what "contaminating the holdout" means in your domain
- [ ] In-loop evaluation — what numbers the evaluator agent tracks each iteration
- [ ] Go/no-go gate — domain-specific gate criteria beyond the generic ones
- [ ] Overfitting warning signs — concrete heuristics the gate agent should check

### Step 4 — Wire guardrail Floor 1

Open `.claude/hooks/guardrail.sh`:

- [ ] Replace `{{DOMAIN_FORBIDDEN_PATTERN}}` with the ERE pattern that matches your domain's
  "never do this" commands (e.g. `enable_live|--real-money|mutate.*holdout`)
- [ ] Replace `{{PROTECTED_PATHS}}` with an ERE alternation of the domain paths the loop must
  never edit via a file tool (Edit/Write/MultiEdit) — e.g. a sacred holdout: `cases/holdout\.jsonl`.
  `.claude/hooks/` and `.claude/settings.json` are ALWAYS protected (the loop can never edit its
  own floor); `{{PROTECTED_PATHS}}` adds your domain's untouchable files on top. If your domain
  has none, replace it with a never-match token (e.g. `__NO_PROTECTED_PATHS__`) — do not leave
  the literal `{{PROTECTED_PATHS}}` in place.
- [ ] Test: `bash -n .claude/hooks/guardrail.sh` must exit 0
- [ ] If your domain has no Floor-1 concern, delete only the Floor 1 block — **leave Floor 2 and
  the write-tool protection untouched** (Floor 2 is a machine-safety deny-list; do not weaken it)

### Step 5 — Customize the five agents

In `.claude/agents/`, open each file and fill in any remaining `{{TOKEN}}`s:

- [ ] `evaluator.md` — confirm `{{STATE_SOURCE}}`, `{{PROVE_COMMAND}}`, `{{LOG_FILE}}`
- [ ] `proposer.md` — confirm `{{DOMAIN_SAFETY_FLOOR}}`, `{{LOG_FILE}}`
- [ ] `implementer.md` — confirm `{{VERIFY_COMMAND}}`, `{{LOG_FILE}}`
- [ ] `gate.md` — confirm `{{DOMAIN_SAFETY_FLOOR}}`, `{{LOG_FILE}}`
- [ ] `meta-improver.md` — confirm `{{LOG_FILE}}`

Add any domain-specific instructions or constraints inside each agent file.

### Step 6 — Customize iterate.md

Open `.claude/commands/iterate.md`:

- [ ] Confirm `{{PERSONA_NAME}}` matches what you set in PERSONA.md
- [ ] Confirm `{{VERIFY_COMMAND}}` is the right lint/test/check command for this project
- [ ] Confirm `{{PROVE_COMMAND}}` produces the metric that proves improvement
- [ ] Confirm `{{LOG_FILE}}` is the correct relative path to LOG.md (or your log file)
- [ ] Confirm `{{NOTIFY_COMMAND}}` is a valid shell command or leave it as a no-op (`true`)
- [ ] Confirm `{{STATE_SOURCE}}` points to the file or command that gives current state

### Step 7 — Set up the run mechanism

Choose how the loop runs:

- [ ] **Manual one-shot** — run `/iterate` from within a Claude Code session
- [ ] **Session loop** — run `/loop 1h /iterate` to repeat on a timer within the session
- [ ] **Unattended (any OS)** — schedule the bundled `run-iteration.sh` (NOT raw `claude`) on a
  timer: POSIX cron, launchd (macOS), a systemd timer (Linux), or Task Scheduler via WSL
  (Windows). Each tick is a fresh session (`claude -p`, no `--continue` — disk is the loop's
  memory); the wrapper takes a single-flight lock and time-boxes the run. Sandbox it for safe
  unattended use. Make it executable once: `chmod +x run-iteration.sh`.

Verify the hook is active before running unattended:
```bash
bash -n .claude/hooks/guardrail.sh && echo OK
```

---

## Token glossary

Every `{{TOKEN}}` used anywhere in this template, with a one-line meaning.

| Token | Meaning |
|-------|---------|
| `{{PERSONA_NAME}}` | The name of the orchestrating persona — used in agent instructions and the iterate command |
| `{{EXPERT_ARCHETYPE}}` | The domain role the persona embodies (e.g. "quantitative analyst", "compiler engineer") |
| `{{ONE_LINE_BIO}}` | One sentence describing who the persona is and what they care about |
| `{{MISSION}}` | A short paragraph describing what the loop is optimizing and why |
| `{{SCOPE_LAYERS}}` | A bullet list of what is in scope and out of scope for the loop |
| `{{PRIORITY_ORDER}}` | An ordered list of improvement priorities the loop follows |
| `{{PRIMARY_OBJECTIVE}}` | The single metric or outcome the loop maximizes each iteration |
| `{{DONE_DEFINITION}}` | The condition under which the loop should stop iterating |
| `{{DOMAIN_SAFETY_FLOOR}}` | Hard constraints the loop must never violate — enforced by guardrail Floor 1 |
| `{{DOMAIN_FORBIDDEN_PATTERN}}` | ERE regex in guardrail.sh Floor 1 matching commands the loop must never run |
| `{{PROTECTED_PATHS}}` | ERE alternation of domain paths the loop must never edit via a file tool (Edit/Write/MultiEdit) — e.g. a sacred holdout. Sits on top of the always-protected `.claude/hooks/` and `.claude/settings.json` |
| `{{VERIFY_COMMAND}}` | Shell command that must exit 0 before any change is accepted (lint, tests, etc.) |
| `{{PROVE_COMMAND}}` | Shell command that produces the measurable metric proving an improvement occurred |
| `{{LOG_FILE}}` | Relative path to the append-only iteration log (e.g. `LOG.md`) |
| `{{NOTIFY_COMMAND}}` | Shell command to notify a human after each iteration (or `true` for silent) |
| `{{STATE_SOURCE}}` | File path or command that gives the evaluator agent the current system state |
