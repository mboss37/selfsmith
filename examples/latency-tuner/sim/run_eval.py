#!/usr/bin/env python3
"""Replay a retry/timeout policy against a fixed traffic trace and score it.

Fully deterministic: the traces pre-draw every upstream outcome, so the same config on the
same window produces the same numbers, byte for byte. That determinism is what makes the
gate's arithmetic trustworthy (see tools/metric-contract.sh).

Policy (config.json): {"timeout_ms": T, "retries": R, "backoff_ms": B}
Replay per request: attempt i uses the i-th pre-drawn upstream outcome. An attempt whose
upstream latency exceeds T costs T and fails (client timeout); a `!ok` attempt costs its
latency and fails; otherwise it succeeds at its latency. B ms elapse between attempts.
A request with no successful attempt within R+1 tries is an ERROR.

Scoring — the reward-hacking trap this domain teaches, encoded in the metric:
  - Latency percentiles over SUCCESSES ONLY are gameable: time out fast, fail cheap, and
    "latency" improves while users see errors.
  - So the headline stat is EFFECTIVE latency: per-request elapsed ms, with every error
    costed at elapsed + ERROR_PENALTY_MS. Pairs by trace line, so per-request vectors feed
    tools/verdict.py compare mode directly (--dump FILE, one number per line).
  - error_rate is additionally a HARD FLOOR (GOAL.md: <= 2%), checked with
    tools/verdict.py floor — the composite stat never replaces the floor.
"""
import argparse
import json
import math
import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parent
MAX_ATTEMPTS = 4
ERROR_PENALTY_MS = 10_000.0  # an error costs the user a failure, not just its elapsed ms

DEFAULTS = {"timeout_ms": 2000.0, "retries": 1, "backoff_ms": 100.0}


def load_trace(window):
    path = ROOT / "traces" / f"{window}.jsonl"
    if not path.exists():
        sys.exit(f"run_eval: no trace at {path} — traces are fixed measurement data (see sim/make_traces.py)")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_config(path, overrides):
    cfg = dict(DEFAULTS)
    if path:
        cfg.update(json.loads(Path(path).read_text()))
    for ov in overrides:
        key, _, value = ov.partition("=")
        if key not in DEFAULTS:
            sys.exit(f"run_eval: unknown config key '{key}' (known: {', '.join(DEFAULTS)})")
        cfg[key] = float(value)
    cfg["retries"] = int(cfg["retries"])
    if not (0 <= cfg["retries"] <= MAX_ATTEMPTS - 1):
        sys.exit(f"run_eval: retries must be in [0, {MAX_ATTEMPTS - 1}]")
    if cfg["timeout_ms"] <= 0 or cfg["backoff_ms"] < 0:
        sys.exit("run_eval: timeout_ms must be > 0 and backoff_ms >= 0")
    return cfg


def replay_request(request, cfg):
    """Return (success, elapsed_ms) for one request under the policy."""
    elapsed = 0.0
    for i in range(cfg["retries"] + 1):
        attempt = request["attempts"][i]
        if attempt["lat"] > cfg["timeout_ms"]:
            elapsed += cfg["timeout_ms"]          # client gave up on this attempt
        elif not attempt["ok"]:
            elapsed += attempt["lat"]             # upstream answered with a failure
        else:
            return True, elapsed + attempt["lat"]  # success
        if i < cfg["retries"]:
            elapsed += cfg["backoff_ms"]
    return False, elapsed


def percentile(values, q):
    if not values:
        return math.inf  # degenerate window (e.g. zero successes) — worst possible, never a divide-by-zero
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def score(cfg, window):
    trace = load_trace(window)
    effective, success_lat, errors = [], [], 0
    for request in trace:
        ok, elapsed = replay_request(request, cfg)
        if ok:
            success_lat.append(elapsed)
            effective.append(elapsed)
        else:
            errors += 1
            effective.append(elapsed + ERROR_PENALTY_MS)
    n = len(trace)
    return {
        "window": window, "n": n, "config": cfg,
        "errors": errors, "error_rate": round(errors / n, 4) if n else 1.0,
        "p50_ms": round(percentile(success_lat, 0.50), 1),
        "p95_ms": round(percentile(success_lat, 0.95), 1),
        "p95_effective_ms": round(percentile(effective, 0.95), 1),
        "mean_effective_ms": round(sum(effective) / n, 1) if n else math.inf,
    }, effective


def main():
    ap = argparse.ArgumentParser(description="Replay a retry/timeout policy against a fixed traffic window.")
    ap.add_argument("--config", default=str(ROOT / "config.json"), help="policy JSON (default: config.json)")
    ap.add_argument("--window", choices=["train", "holdout"], default="train")
    ap.add_argument("--override", action="append", default=[], metavar="KEY=VALUE",
                    help="override a config key for this run, e.g. --override timeout_ms=450")
    ap.add_argument("--dump", default=None, metavar="FILE",
                    help="write per-request effective latencies (one per line) for tools/verdict.py")
    args = ap.parse_args()
    cfg = load_config(args.config, args.override)
    result, effective = score(cfg, args.window)
    if args.dump:
        Path(args.dump).write_text("\n".join(f"{v:.1f}" for v in effective) + "\n")
    print(f"timeout={cfg['timeout_ms']:.0f}ms retries={cfg['retries']} backoff={cfg['backoff_ms']:.0f}ms "
          f"on {result['window']:7s}: p95_eff={result['p95_effective_ms']:.0f}ms "
          f"p95={result['p95_ms']:.0f}ms err={result['error_rate']:.2%} (n={result['n']})")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
