#!/usr/bin/env bash
# drive-to-goal.sh — run /iterate back-to-back until the loop CONVERGES, then stop.
#
# This is the "run until done" mode (vs a timer). Use it for a BOUNDED / CONVERGENT campaign — a
# checklist to finish, a winner to converge on — where you want to go as fast as possible to the
# goal and then stop, not tick forever on a clock. For an ONGOING / time-dependent loop (tuning a
# live system as new data arrives), use a timer instead (cron / launchd / systemd) — see the README.
#
# Each iteration is a fresh session via ./run-iteration.sh (single-flight lock + time-box), so the
# loop's memory stays on disk, not in a long-lived context. The driver runs them in series.
#
# Stops on the FIRST of:
#   - a DONE marker file exists        — the loop signalled convergence (have iterate.md `touch DONE`
#                                         at its done-step; see INSTANTIATE.md)
#   - STALL_LIMIT iterations with no new commit — the loop stopped making progress (every accepted
#                                         change commits; a no-op does not), so it's stuck → review
#   - MAX_ITERS total                  — a backstop so a runaway can't loop forever
#
# Watch:  tail -f drive.log     Stop:  kill this script's process.
set -uo pipefail
cd "$(dirname "$0")"

MAX="${MAX_ITERS:-20}"
STALL_LIMIT="${STALL_LIMIT:-3}"
DONE_MARKER="${DONE_MARKER:-DONE}"

head_now() { git rev-parse HEAD 2>/dev/null || echo none; }

prev="$(head_now)"
stall=0

for i in $(seq 1 "$MAX"); do
  if [ -e "$DONE_MARKER" ]; then
    echo "drive: DONE marker present — converged after $((i - 1)) iterations."
    break
  fi
  echo "drive: ===== iteration $i · $(date +%H:%M:%S) ====="
  ./run-iteration.sh >> drive.log 2>&1 || echo "drive: iteration $i exited nonzero (continuing)"

  now="$(head_now)"
  if [ "$now" = "$prev" ]; then stall=$((stall + 1)); else stall=0; fi
  prev="$now"

  if [ -e "$DONE_MARKER" ]; then
    echo "drive: converged (DONE written) after $i iterations."
    break
  fi
  if [ "$stall" -ge "$STALL_LIMIT" ]; then
    echo "drive: STALLED — no new commit in $STALL_LIMIT iterations. Stopping for operator review."
    break
  fi
done

echo "drive: finished at $(date +%H:%M:%S). HEAD=$(head_now). See your log file and git log."
