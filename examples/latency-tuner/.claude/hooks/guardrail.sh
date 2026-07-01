#!/usr/bin/env bash
# PreToolUse guardrail for the self-improvement loop. Two floors the loop cannot lift on its
# own; exit 2 blocks the call. A human edits this file by hand to change a floor; the loop
# must not (and the `gate` vetoes any change that weakens a safeguard).
#
# Wired for Bash AND the write tools (Edit|Write|MultiEdit); see .claude/settings.json. A
# deny-list cannot protect itself if the loop can simply edit the deny-list, so write tools
# are gated against the protected paths below. The deny-list is also INHERENTLY INCOMPLETE
# (shell quoting can evade any pattern); it is a tripwire, not a security boundary. The real boundary for
# unattended runs is an OS sandbox that denies the syscalls; run the loop inside one.
#
# This hook FAILS CLOSED: if stdin cannot be parsed into a usable field, it blocks (exit 2).

input="$(cat)"

# Parse tool_name, command (lists joined to a string), and file_path in one pass. On ANY
# parse failure emit "FAIL" so the shell blocks below; never fall through to allow.
parsed="$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    obj = json.load(sys.stdin)
    if not isinstance(obj, dict):
        raise ValueError("top-level not an object")
    ti = obj.get("tool_input")
    if ti is None:
        ti = {}
    if not isinstance(ti, dict):
        raise ValueError("tool_input present but not an object")
    name = obj.get("tool_name") or ""
    cmd = ti.get("command", "")
    if isinstance(cmd, list):
        cmd = " ".join(str(x) for x in cmd)
    fp = ti.get("file_path") or ti.get("filePath") or ti.get("path") or ""
    if isinstance(fp, list):
        fp = " ".join(str(x) for x in fp)
    if not (str(name) or str(cmd) or str(fp)):
        raise ValueError("no usable field")
    print("OK")
    print(str(name))
    print(str(cmd))
    print(str(fp))
except Exception:
    print("FAIL")
' 2>/dev/null || printf "FAIL\n")"

if [ "$(printf '%s' "$parsed" | sed -n '1p')" != "OK" ]; then
  echo "BLOCKED: guardrail could not parse the tool call; failing closed (exit 2)." >&2
  exit 2
fi
tool_name="$(printf '%s' "$parsed" | sed -n '2p')"
cmd="$(printf '%s' "$parsed" | sed -n '3p')"
file_path="$(printf '%s' "$parsed" | sed -n '4p')"

# PROTECTED PATHS: the loop must never edit its own floor or a domain-sacred file. ALWAYS
# .claude/hooks/ and .claude/settings.json (the loop can never edit its own floor); the holdout
# and BOTH traffic traces are domain-protected (the ruler; the loop must never write them).
# NOTE: .claude/agents/ and .claude/commands/ are deliberately NOT protected; the meta-improver
# edits those by design.
PROTECTED_PATHS='\.claude/hooks/|\.claude/settings\.json|traces/'
# A write verb in a Bash command (mirrors the write-tool gate so a redirect can't do what an
# Edit cannot): >/>> redirection (covers the `: >` empty-truncate form), tee, cp, mv, install,
# sed -i, dd … of=, truncate, and a python open() write.
WRITE_VERBS='>|tee[[:space:]]|tee$|\bcp\b|\bmv\b|\binstall\b|sed[[:space:]]+-i|dd[[:space:]]+.*of=|\btruncate\b|python[[:space:]].*-c.*open'

# WRITE-TOOL PROTECTION: the architectural fix. A Bash-only deny-list is moot if the loop can
# just Edit/Write the deny-list (or overwrite the sacred holdout). For Edit|Write|MultiEdit|NotebookEdit,
# block any write into a protected path.
if printf '%s' "$tool_name" | grep -Eq '^(Edit|Write|MultiEdit|NotebookEdit)$'; then
  if printf '%s' "$file_path" | grep -Eq "$PROTECTED_PATHS"; then
    echo "BLOCKED: write-tool floor: refusing to edit a protected path ('$file_path'). Edit .claude/hooks/guardrail.sh by hand to change this floor." >&2
    exit 2
  fi
  exit 0
fi

# BASH-SIDE PROTECTED-PATH WRITE: parity with the write-tool gate. A redirect/cp/tee/sed -i into
# a protected path (the floor files OR the sacred holdout) is a write the Edit gate would refuse;
# refuse it here too. Two-condition match (protected path referenced AND a write verb present) -
# order-independent and fail-safe. Reading a protected path with no write verb (e.g.
# `cat .claude/hooks/guardrail.sh`, `wc -l cases/holdout.jsonl`) stays ALLOWED.
if printf '%s' "$cmd" | grep -Eq "$PROTECTED_PATHS" && printf '%s' "$cmd" | grep -Eq "$WRITE_VERBS"; then
  echo "BLOCKED: protected-path floor: refusing to write a protected path via Bash ('$cmd'). Edit .claude/hooks/guardrail.sh by hand to change this floor." >&2
  exit 2
fi

# Floor 1: DOMAIN SAFETY (Bash). Blocks trace regeneration; the traces are the fixed measurement
# data; rerunning the generator mid-campaign would rewrite the ruler.
# Matches EXECUTIONS (python file/module form, or direct ./ execution); reading the
# generator (`cat sim/make_traces.py`) stays allowed; it is provenance, not a write.
if printf '%s' "$cmd" | grep -Eq 'python[0-9.]*[[:space:]][^|;&]*make_traces|(^|[;&|][[:space:]]*)(\./)?sim/make_traces\.py'; then
  echo "BLOCKED: domain-safety floor: refusing to regenerate the traffic traces ('$cmd'). Edit .claude/hooks/guardrail.sh to change this floor." >&2
  exit 2
fi

# Floor 2: MACHINE SAFETY (do not weaken; a destructive/exfiltration deny-list for unattended loops). /dev/null stays
# allowed; only real block devices are caught.
if printf '%s' "$cmd" | grep -Eq 'rm[[:space:]]+-[A-Za-z]*r[A-Za-z]*f|rm[[:space:]]+-[A-Za-z]*f[A-Za-z]*r|rm[[:space:]]+-r[A-Za-z]*[[:space:]]+-f|rm[[:space:]]+-f[A-Za-z]*[[:space:]]+-r|rm[[:space:]]+.*--recursive|rm[[:space:]]+.*--force|find[[:space:]]+.*-delete|chmod[[:space:]]+.*(-[A-Za-z]*R|--recursive|777)|\bsudo\b|git[[:space:]]+reset[[:space:]]+--hard|git[[:space:]]+.*\bpush\b.*(--force|[[:space:]]-[A-Za-z]*f)|git[[:space:]]+clean[[:space:]]+.*-[A-Za-z]*f|git[[:space:]]+branch[[:space:]]+.*-D([[:space:]]|$)|git[[:space:]]+checkout[[:space:]]+--[[:space:]]|\bmkfs\b|\bdd[[:space:]]+if=|of=/dev/(disk|rdisk|sd|nvme|hd)|>[[:space:]]*/dev/(disk|rdisk|sd|nvme|hd)|(tee|cp|mv)[[:space:]]+.*/dev/(disk|rdisk|sd|nvme|hd)|\{[[:space:]]*:[[:space:]]*\|[[:space:]]*:[[:space:]]*&|\|[[:space:]]*(sh|bash|zsh)([[:space:]]|$)|(curl|wget)[[:space:]].*\|[[:space:]]*(sh|bash|zsh)'; then
  echo "BLOCKED: non-destructive floor: refusing a destructive/exfiltration command ('$cmd')." >&2
  exit 2
fi

exit 0
