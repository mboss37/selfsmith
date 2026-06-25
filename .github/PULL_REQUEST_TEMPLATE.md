## What changes

<!-- Describe what this PR does. One focused change per PR. -->

## Why

<!-- Why is this change needed? What problem does it solve or improvement does it make? -->

## Checklist

- [ ] All `{{TOKEN}}` placeholders in any touched template files are intact (or intentionally replaced in a new example).
- [ ] If an example was added or changed: `python -m pytest eval/ -q` passes (expect 91 passed).
- [ ] If the guardrail was changed: the change **strengthens** a floor, not weakens it. (CI `guardrail-integrity` will verify this.)
- [ ] If a new dependency was added: it has a version pin and is in `requirements.txt`.
