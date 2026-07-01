# Minimal sandbox image for an unattended selfsmith loop: Claude Code + Python + git, run as
# an unprivileged user. Extend with your domain's dependencies (see sandbox/README.md);
# the hard restrictions (read-only rootfs, cap-drop, ceilings, read-only floor mounts)
# live in run-sandboxed.sh, not here.
FROM node:22-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-pytest git ca-certificates coreutils procps \
 && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code

# Unprivileged, fixed UID so run-sandboxed.sh can pin --user and volume permissions are
# predictable. Never run the loop as root.
RUN useradd --create-home --uid 10001 loop
USER loop
WORKDIR /loop

ENTRYPOINT ["./run-iteration.sh"]
