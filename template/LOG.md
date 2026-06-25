# LOG.md

Append-only improvement log. One entry per iteration. Never edit or delete past entries.

## Format

Each entry must contain:
- **Iteration number** — monotonically increasing, starting at 1
- **Date** — ISO-8601 (YYYY-MM-DD)
- **Agent** — which agent proposed the change (or "no-op" if nothing changed)
- **Change** — one sentence: what was modified and why
- **Metric before / after** — the primary objective metric value before and after
- **Verify** — PASS or FAIL (output of `{{VERIFY_COMMAND}}`)
- **Prove** — the concrete measurement from `{{PROVE_COMMAND}}`
- **Gate decision** — ACCEPTED or REJECTED, with the gate agent's rationale
- **Notes** — anything else relevant: reversibility, concerns, next hypothesis

## Template

```
## Iter N — YYYY-MM-DD

- Agent: <proposer | implementer | evaluator | gate | meta-improver | manual>
- Change: <one sentence>
- Metric before: <value>
- Metric after: <value>
- Verify: PASS | FAIL
- Prove: <measurement>
- Gate: ACCEPTED | REJECTED — <rationale>
- Notes: <optional>
```

## Log entries

<!-- First entry goes here -->
