#!/usr/bin/env bash
# run-iteration.sh — single-flight, time-boxed, fresh-session wrapper for unattended runs.
#
# Schedule THIS (not `claude` directly) from cron / launchd / a systemd timer so that:
#   - iterations never overlap (atomic mkdir lock with stale-PID reclaim),
#   - a wedged iteration is killed instead of spinning forever (timeout), and
#   - every tick is a FRESH session: `claude -p`, never `--continue`. The loop's memory lives
#     on disk (LOG.md, champion state, git), so each run re-grounds from truth.
#
# This wrapper does NOT sandbox. The guardrail deny-list is a tripwire, not a jail (shell
# quoting evades any string match). For genuinely safe unattended runs, launch this inside an
# OS sandbox, a container, or an unprivileged user. See README "How to run".
set -euo pipefail

cd "$(dirname "$0")"

LOCK_DIR=".loop.lock"
TIMEOUT="${ITER_TIMEOUT:-50m}"   # per-iteration wall-clock ceiling; override with ITER_TIMEOUT=...
MAX_TURNS="${ITER_MAX_TURNS:-50}"  # per-iteration agent-turn ceiling — the token/cost budget.
                                   # An unattended loop needs a spend floor it cannot argue past,
                                   # exactly like the safety floor: a wedged or over-eager iteration
                                   # is cut off mechanically, not by its own judgment. Raise it
                                   # deliberately (ITER_MAX_TURNS=80) rather than removing it.

# single-flight: mkdir is atomic on POSIX. If the lock exists but its owner is dead (a previous
# run was hard-killed), reclaim it; otherwise skip this tick cleanly.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  if [ -f "$LOCK_DIR/pid" ] && kill -0 "$(cat "$LOCK_DIR/pid" 2>/dev/null)" 2>/dev/null; then
    echo "run-iteration: previous iteration still running — skipping this tick" >&2
    exit 0
  fi
  echo "run-iteration: reclaiming stale lock" >&2
  rm -rf "$LOCK_DIR"
  mkdir "$LOCK_DIR"
fi
printf '%s\n' "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT

# choose a timeout binary if one exists (GNU coreutils `timeout`, or `gtimeout` on macOS via
# coreutils); otherwise run without a hard ceiling and say so.
if command -v timeout >/dev/null 2>&1; then
  TO=(timeout "$TIMEOUT")
elif command -v gtimeout >/dev/null 2>&1; then
  TO=(gtimeout "$TIMEOUT")
else
  TO=()
  echo "run-iteration: no timeout binary found — running without a hard ceiling" >&2
fi

# fresh session every tick — NO --continue (disk is the loop's memory).
# bash 3.x (macOS default) treats "${TO[@]}" as unbound when TO=(); check length first.
if [ "${#TO[@]}" -gt 0 ]; then
  "${TO[@]}" claude -p --max-turns "$MAX_TURNS" "/iterate"
else
  claude -p --max-turns "$MAX_TURNS" "/iterate"
fi
