#!/usr/bin/env bash
# PreToolUse guardrail for the self-improvement loop (Bash tool). Two floors the loop cannot
# lift on its own — exit 2 blocks the call. A human edits this file by hand to change a floor;
# the loop must not (and the `gate` vetoes any change that weakens a safeguard).
input="$(cat)"
cmd="$(printf '%s' "$input" | python3 -c 'import sys,json; print((json.load(sys.stdin).get("tool_input") or {}).get("command",""))' 2>/dev/null || true)"

# Floor 1 — DOMAIN SAFETY. Blocks holdout mutation and paid model calls.
if printf '%s' "$cmd" | grep -Eq '>[[:space:]]*.*cases/holdout\.jsonl|--model[[:space:]]+claude'; then
  echo "BLOCKED: domain-safety floor — refusing to mutate the sacred holdout or enable paid model calls ('$cmd')." >&2
  exit 2
fi

# Floor 2 — MACHINE SAFETY (do not weaken; see task-6-brief.md for provenance). /dev/null stays
# allowed; only real block devices are caught.
if printf '%s' "$cmd" | grep -Eq 'rm[[:space:]]+-[A-Za-z]*r[A-Za-z]*f|rm[[:space:]]+-[A-Za-z]*f[A-Za-z]*r|rm[[:space:]]+-r[A-Za-z]*[[:space:]]+-f|rm[[:space:]]+-f[A-Za-z]*[[:space:]]+-r|\bsudo\b|git[[:space:]]+reset[[:space:]]+--hard|\bmkfs\b|\bdd[[:space:]]+if=|>[[:space:]]*/dev/(disk|rdisk|sd|nvme|hd)|\|[[:space:]]*(sh|bash|zsh)([[:space:]]|$)|(curl|wget)[[:space:]].*\|[[:space:]]*(sh|bash|zsh)'; then
  echo "BLOCKED: non-destructive floor — refusing a destructive/exfiltration command ('$cmd')." >&2
  exit 2
fi

exit 0
