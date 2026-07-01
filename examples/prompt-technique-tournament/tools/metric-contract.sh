#!/usr/bin/env bash
# metric-contract.sh; prove the METRIC before you trust the loop with it.
#
# The loop is only as good as its prove command: a broken or noisy metric silently
# certifies bad changes and kills good ones, and no amount of gate discipline can save a
# loop that is optimizing a lie. This contract is the cheapest possible insurance, run
# before the first iteration and again at triage whenever measurement is in doubt:
#
#   1. NUMERIC: both commands exit 0 and print a bare number as their last line.
#   2. DETERMINISM: each command, run twice, prints the identical number. (A stochastic
#                    metric needs averaging/seeding INSIDE the command until it is stable;
#                    if two runs of your metric disagree, every gate verdict is a coin flip.)
#   3. SEPARATION: the known-good scores STRICTLY better than the planted-bad, in the
#                    declared direction. If you cannot produce a planted-bad control that
#                    your metric scores worse, you do not
#                    have a usable metric yet, and the loop would optimize noise.
#
# Config lives in metric-contract.env at the loop root (see INSTANTIATE.md Step 0):
#   METRIC_GOOD_CMD: prints the metric for a known-good variant (e.g. the champion)
#   METRIC_BAD_CMD: prints the metric for a planted-bad control that MUST score worse
#   METRIC_DIRECTION: 'higher' or 'lower', whichever direction is better
#
# Exit 0: contract holds. Exit 1: the metric is not fit to drive a loop; fix it first.
set -euo pipefail
cd "$(dirname "$0")/.."   # tools/ lives one level under the loop root

ENV_FILE="${METRIC_CONTRACT_ENV:-metric-contract.env}"
if [ ! -f "$ENV_FILE" ]; then
  echo "metric-contract: FAIL; no $ENV_FILE (see INSTANTIATE.md Step 0)" >&2
  exit 1
fi
# shellcheck disable=SC1090
. "$ENV_FILE"
: "${METRIC_GOOD_CMD:?metric-contract: METRIC_GOOD_CMD not set in $ENV_FILE}"
: "${METRIC_BAD_CMD:?metric-contract: METRIC_BAD_CMD not set in $ENV_FILE}"
METRIC_DIRECTION="${METRIC_DIRECTION:-higher}"
case "$METRIC_DIRECTION" in higher|lower) ;; *)
  echo "metric-contract: FAIL; METRIC_DIRECTION must be 'higher' or 'lower' (got '$METRIC_DIRECTION')" >&2
  exit 1 ;;
esac

# Run a metric command; emit its last line iff it is a bare number.
measure() {
  local label="$1" cmd="$2" out num
  if ! out="$(bash -c "$cmd" 2>/dev/null)"; then
    echo "metric-contract: FAIL; $label command exited nonzero: $cmd" >&2
    return 1
  fi
  num="$(printf '%s\n' "$out" | tail -n 1 | tr -d '[:space:]')"
  if ! printf '%s' "$num" | python3 -c 'import sys; float(sys.stdin.read())' >/dev/null 2>&1; then
    echo "metric-contract: FAIL; $label command's last line is not a number: '$num'" >&2
    return 1
  fi
  printf '%s' "$num"
}

good1="$(measure GOOD "$METRIC_GOOD_CMD")"
good2="$(measure GOOD "$METRIC_GOOD_CMD")"
bad1="$(measure BAD "$METRIC_BAD_CMD")"
bad2="$(measure BAD "$METRIC_BAD_CMD")"

if [ "$good1" != "$good2" ] || [ "$bad1" != "$bad2" ]; then
  echo "metric-contract: FAIL; DETERMINISM: two runs disagree (good: $good1 vs $good2; bad: $bad1 vs $bad2)." >&2
  echo "metric-contract: stabilize the metric (seed it, average inside the command) before looping." >&2
  exit 1
fi

if ! python3 -c "
import sys
good, bad, direction = float('$good1'), float('$bad1'), '$METRIC_DIRECTION'
sys.exit(0 if (good > bad if direction == 'higher' else good < bad) else 1)
"; then
  echo "metric-contract: FAIL; SEPARATION: known-good ($good1) does not beat planted-bad ($bad1) with direction '$METRIC_DIRECTION'." >&2
  echo "metric-contract: the metric cannot tell good from bad; it is not fit to drive a loop." >&2
  exit 1
fi

echo "metric-contract: PASS; numeric, deterministic, and separating (good=$good1 vs bad=$bad1, $METRIC_DIRECTION is better)."
