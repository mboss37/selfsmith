# sandbox/: the OS-level boundary

The guardrail hook is a **tripwire for honest mistakes, not a security boundary**: shell
quoting, encoding, and command substitution can evade any string-matching deny-list. The
boundary that actually holds is an OS-level sandbox where destructive syscalls are
impossible regardless of what the loop tries. This directory ships three ready-to-adapt
sandboxes, ranked by strength. Pick one **before** running unattended; "I'll add the sandbox
later" is how tripwires end up load-bearing.

| Option | Strength | Files |
|---|---|---|
| Container (Linux/macOS/Windows) | Strongest, portable | `Dockerfile`, `run-sandboxed.sh` |
| systemd hardened unit (Linux) | Strong, no container runtime needed | `selfsmith-loop.service`, `selfsmith-loop.timer` |
| Seatbelt profile (macOS) | Good, built-in | `claude-loop.sb` |

All three enforce the same invariants, at the OS level, that the hook enforces as a tripwire:

- The loop can write **only** its own directory (plus scratch space).
- `.claude/hooks/` and `.claude/settings.json` (the floor) are **read-only even inside
  the writable area**, so not even a hook bug lets the loop lift its own floor.
- Resource ceilings (memory, tasks/pids) so a runaway iteration degrades, not the machine.
- No privilege escalation (`no-new-privileges` / `NoNewPrivileges=` / unprivileged user).

## 1. Container

```bash
# once, from the loop root:
docker build -t selfsmith-loop sandbox/

# each tick (or schedule THIS from cron instead of run-iteration.sh):
./sandbox/run-sandboxed.sh
```

`run-sandboxed.sh` runs `run-iteration.sh` inside the container with the root filesystem
read-only, all capabilities dropped, memory/CPU/pid ceilings, the loop directory as the
only writable mount, and the floor files re-mounted read-only on top. Works with
`CONTAINER_ENGINE=podman` too. Add your domain's dependencies (e.g. `pip install pytest`)
by extending the Dockerfile; the base image ships only Claude Code, Python, and git.

## 2. systemd (Linux, no container needed)

```bash
mkdir -p ~/.config/systemd/user
cp sandbox/selfsmith-loop.{service,timer} ~/.config/systemd/user/
# edit both files: replace %h/my-loop with your loop directory, set the API key path
systemctl --user daemon-reload
systemctl --user enable --now selfsmith-loop.timer
```

The unit uses `ProtectSystem=strict` (whole OS read-only), `BindReadOnlyPaths=` on the
floor files, `PrivateTmp=`, `NoNewPrivileges=`, an empty capability set, a syscall filter,
and memory/task ceilings. The timer replaces the cron line: same single-flight,
time-boxed `run-iteration.sh` underneath.

## 3. macOS Seatbelt

```bash
sandbox-exec -f sandbox/claude-loop.sb \
  -D LOOP_DIR="$PWD" -D HOME_DIR="$HOME" \
  ./run-iteration.sh
```

Denies all file writes except the loop directory, temp, and `~` (Claude Code keeps session
state there), then re-denies the floor files inside the loop directory. `sandbox-exec` is
deprecated-but-functional; Apple still uses the mechanism itself. For anything
security-critical prefer the container.

## Extra hardening

Whatever sandbox you pick, also:

```bash
chmod 0444 .claude/hooks/guardrail.sh .claude/settings.json   # loop runs as you? make the floor literally read-only
python3 -m pytest eval/test_guardrail.py -q                    # prove the tripwire fires (worked examples ship this)
```

And verify the sandbox itself once: from inside it, try `touch .claude/hooks/x` and
`touch /etc/x`; both must fail with permission errors, not guardrail messages. A sandbox you
haven't seen refuse a write is a hypothesis, not a boundary.
