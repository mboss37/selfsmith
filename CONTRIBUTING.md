# Contributing

Welcome. The most valuable contributions are:

- **Bug fixes** — especially in the eval harness, guardrail logic, or token-substitution mechanics.
- **New worked examples** — a new domain instantiation (a different problem shape, industry, or optimization target) that ships with a complete `eval/` test suite and a filled `INSTANTIATE.md`.
- **Guardrail and agent improvements** — strengthening a floor, tightening a gate, improving the orchestrator's routing logic.
- **Documentation** — clearer instructions, better glossary, sharper worked examples.

### Out of scope

- Anything that **weakens the two-floor guardrail** (write-tool protection + machine-safety deny-list). The CI `guardrail-integrity` job enforces this and will reject any PR that removes or softens a floor.
- Changes that **couple the template to one domain** — `template/` must remain domain-neutral.
- Converting the project into a pip-installable library.

## How to contribute

1. Fork the repo.
2. Branch off `main` — one focused change per branch.
3. Make your change.
4. If you **add a new example**: ship a working `eval/` test suite (pytest, offline by default) and a filled `INSTANTIATE.md`. Every `{{TOKEN}}` in the template files must be replaced.
5. If you **touch the template**: ensure no `{{TOKEN}}` is left broken and the example still passes `pytest eval/ -q`.
6. If you **touch the guardrail**: the change must STRENGTHEN, not weaken, a floor. The CI `guardrail-integrity` job enforces this.
7. Open a PR against `main`. Fill in the pull request template.

## Running the tests

```bash
cd examples/prompt-technique-tournament
pip install -r requirements.txt
python -m pytest eval/ -q
# expect 91 passed
```

The full suite must pass before any PR is merged.

## Style

- Plain Python. No unnecessary abstractions.
- Comments only where logic is non-obvious.
- No new dependencies unless genuinely required — add them to `requirements.txt` with a version pin.
