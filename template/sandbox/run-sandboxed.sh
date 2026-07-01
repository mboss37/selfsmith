#!/usr/bin/env bash
# run-sandboxed.sh — one iteration inside the container jail. Schedule THIS from cron for
# unattended runs if you want the jail on every tick (recommended):
#   0 * * * * cd /path/to/my-loop && ./sandbox/run-sandboxed.sh
#
# What the jail enforces at the OS level (the guardrail hook only tripwires these):
#   - rootfs read-only; the ONLY writable paths are the loop dir, /tmp, and the home dir
#   - the floor (.claude/hooks/, settings.json) re-mounted READ-ONLY inside the loop dir —
#     even a hook bug cannot lift the floor
#   - all capabilities dropped, no privilege escalation, unprivileged fixed UID
#   - memory / CPU / pid ceilings so a runaway degrades, not the machine
#
# Build once from the loop root:  docker build -t selfsmith-loop sandbox/
# Podman works too:               CONTAINER_ENGINE=podman ./sandbox/run-sandboxed.sh
set -euo pipefail
cd "$(dirname "$0")/.."   # loop root

ENGINE="${CONTAINER_ENGINE:-docker}"
IMAGE="${LOOP_IMAGE:-selfsmith-loop}"

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "run-sandboxed: ANTHROPIC_API_KEY is not set — the containerized CLI authenticates via env" >&2
  exit 1
fi

exec "$ENGINE" run --rm --init \
  --user 10001:10001 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --read-only \
  --tmpfs /tmp:rw,size=256m \
  --tmpfs /home/loop:rw,size=512m,uid=10001,gid=10001 \
  --memory "${LOOP_MEM:-2g}" \
  --cpus "${LOOP_CPUS:-2}" \
  --pids-limit "${LOOP_PIDS:-256}" \
  -v "$PWD":/loop \
  -v "$PWD/.claude/hooks":/loop/.claude/hooks:ro \
  -v "$PWD/.claude/settings.json":/loop/.claude/settings.json:ro \
  -e ANTHROPIC_API_KEY \
  -e ITER_TIMEOUT \
  -e ITER_MAX_TURNS \
  -e GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-selfsmith-loop}" \
  -e GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-loop@localhost}" \
  -e GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-selfsmith-loop}" \
  -e GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-loop@localhost}" \
  -e GIT_CONFIG_COUNT=1 \
  -e GIT_CONFIG_KEY_0=safe.directory \
  -e GIT_CONFIG_VALUE_0=/loop \
  "$IMAGE"
