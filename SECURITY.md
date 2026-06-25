# Security Policy

## Scope

The following are in scope for vulnerability reports:

- **Guardrail bypass** — any command, file edit, encoding trick, or argument construction that defeats a floor, or that mutates `guardrail.sh` / `settings.json` from inside a running loop without human action.
- **Holdout / eval contamination** — a code path reachable without tripping a floor that lets the loop read or write holdout data during iteration.
- **Secret exposure** — a harness code path that could leak API keys or credentials.
- **Unsafe harness code (`eval/`)** — a bug in the eval harness that allows arbitrary code execution or data corruption from a malformed input.
- **Host damage** — any sequence of loop iterations that, without human intervention, could cause destructive or irreversible host-level side effects.

### Out of scope

- A **human** deliberately editing `guardrail.sh` or `settings.json` by hand — that is an intentional documented escape hatch, not a vulnerability.
- Intended `--model claude` billed API calls made knowingly by a human operator.
- CVEs in third-party dependencies (report those upstream to the dependency maintainer).

### Important boundary note

The deny-list in `guardrail.sh` is a **tripwire for honest mistakes, not a complete security boundary**. Shell quoting, character encoding, and command substitution can evade any string-matching list. The real boundary for genuinely unattended safe operation is an **OS sandbox** (e.g. macOS Sandbox, Linux namespaces, a container with a minimal filesystem) where destructive syscalls are impossible at the OS level. If you find a bypass that defeats the deny-list through obfuscation, that is still a valid in-scope report — we want to know.

## Reporting

**Preferred:** GitHub private vulnerability reporting — go to the Security tab of this repository and click **"Report a vulnerability"**.

**Alternate:** Email **mihael@bosnjak.io** with:
- A minimal proof-of-concept command, file, or sequence of steps.
- Which floor it defeats (write-tool protection, Floor 1, Floor 2, eval integrity).
- Whether it requires prior access to the host or only the loop's working directory.

**Response commitment:** We will acknowledge the report within **3 business days** and aim to assess severity and scope within 7 days.

## Disclosure

Please do not publicly disclose a bypass until we have had a chance to respond and patch.
