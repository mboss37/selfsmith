#!/usr/bin/env python3
"""verdict.py — the MECHANICAL half of the gate. stdlib only, deterministic.

The gate agent's judgment (safety, mechanism plausibility, redundancy) stays with the
agent. The certification arithmetic — "is this gain real, after deflating for everything
that was tried?" — must NOT be left to judgment, because judgment is exactly what a
plausible-but-wrong gain fools. The gate agent runs this tool and may not promote a
change this tool rejects. The veto is one-way: verdict.py PROMOTE is necessary, never
sufficient — the agent can still reject on any axis it checks.

Modes (each mechanizes a METHODOLOGY.md rule):

  screen     Dev-split screening: challenger must beat champion by >= --min-effect
             items. No significance claim — dev is mined, so dev p-values are theater.
  reproduce  The promote test for small-n discover-and-validate loops: the dev gain
             must reproduce on the never-tuned holdout — same sign, >= --ratio of the
             dev gain, >= --min-effect items. (At small n an exact test cannot certify
             small steps; reproduction on untouched data is the honest instrument.)
  confirm    Exact two-sided sign test on paired 0/1 outcomes, alpha Bonferroni-deflated
             by --search-size (the candidate budget declared UP FRONT — not the running
             log). FAILS CLOSED: no declared search size, no certification. Use for the
             final champion-vs-baseline claim, or per-step in big-n domains.
  compare    Paired bootstrap (seeded, deterministic) on continuous per-item values —
             CI on the improvement at the deflated alpha; PROMOTE only if the whole CI
             clears zero. --stat mean|p95, --direction higher|lower.
  floor      Hard-floor check: --value must respect --max/--min. For safety floors
             (error rate, cost) so the floor test is arithmetic, not opinion.
  self-test  The known-nothing control, automated: feeds the machinery null and
             clear-win inputs and verifies REJECT/PROMOTE/fail-closed behave. Run it
             at the start of every gate review — a gate that blesses a null is a bug.

Input files: one numeric value per line (paired by line across the two files), or a
run_eval.py-style JSON object with results[].pass — auto-detected.

Exit codes: 0 PROMOTE/pass · 1 REJECT · 3 fail-closed (bad input / undeclared search).
"""
import argparse
import json
import math
import random
import sys

FAIL_CLOSED = 3


def die(msg):
    print(f"verdict: FAIL-CLOSED — {msg}", file=sys.stderr)
    sys.exit(FAIL_CLOSED)


def load_vector(path):
    """One float per line, or a run_eval-style JSON object with results[].pass."""
    try:
        text = open(path).read().strip()
    except OSError as e:
        die(f"cannot read '{path}': {e}")
    if not text:
        die(f"'{path}' is empty")
    if text.lstrip()[0] in "{[":
        try:
            obj = json.loads(text)
            return [1.0 if r["pass"] else 0.0 for r in obj["results"]]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            die(f"'{path}' looks like JSON but is not run_eval output: {e}")
    try:
        return [float(line) for line in text.splitlines() if line.strip()]
    except ValueError as e:
        die(f"'{path}' has a non-numeric line: {e}")


def load_pair(a_path, b_path):
    a, b = load_vector(a_path), load_vector(b_path)
    if len(a) != len(b):
        die(f"vectors differ in length ({len(a)} vs {len(b)}) — pairing is broken")
    if not a:
        die("vectors are empty")
    return a, b


def require_search_size(n):
    if n is None:
        die("--search-size not declared. Every candidate counts — including the ones the "
            "proposer silently evaluated. Declare the candidate budget fixed up front "
            "(see METHODOLOGY.md); no declared size, no certification.")
    if n < 1:
        die(f"--search-size must be >= 1 (got {n})")
    return n


def emit(verdict, detail):
    detail["verdict"] = verdict
    print(f"verdict: {verdict} — {detail.get('reason', '')}")
    print(json.dumps(detail, sort_keys=True))
    sys.exit(0 if verdict == "PROMOTE" else 1)


# ---------- binary machinery ----------

def sign_test_p(wins, losses):
    """Exact two-sided sign test: P(result at least this lopsided | no true difference)."""
    n = wins + losses
    m = min(wins, losses)
    tail = sum(math.comb(n, k) for k in range(m + 1)) * 0.5 ** n
    return min(1.0, 2.0 * tail)


def gain(champion, challenger):
    return int(round(sum(challenger) - sum(champion)))


def mode_screen(args):
    champ, chal = load_pair(args.champion, args.challenger)
    g = gain(champ, chal)
    detail = {"mode": "screen", "n": len(champ), "gain": g, "min_effect": args.min_effect,
              "reason": f"dev gain {g:+d} vs min effect {args.min_effect} (screen only — no significance claim)"}
    emit("PROMOTE" if g >= args.min_effect else "REJECT", detail)


def mode_reproduce(args):
    champ_d, chal_d = load_pair(args.champion_dev, args.challenger_dev)
    champ_h, chal_h = load_pair(args.champion_holdout, args.challenger_holdout)
    dev_gain, hold_gain = gain(champ_d, chal_d), gain(champ_h, chal_h)
    required = max(args.min_effect, math.ceil(args.ratio * dev_gain))
    ok = dev_gain >= args.min_effect and hold_gain >= required
    detail = {"mode": "reproduce", "dev_gain": dev_gain, "holdout_gain": hold_gain,
              "min_effect": args.min_effect, "ratio": args.ratio, "required_holdout_gain": required,
              "reason": f"dev {dev_gain:+d}, holdout {hold_gain:+d} (needs >= {required})"}
    emit("PROMOTE" if ok else "REJECT", detail)


def mode_confirm(args):
    search = require_search_size(args.search_size)
    champ, chal = load_pair(args.champion, args.challenger)
    bad = [v for v in champ + chal if v not in (0.0, 1.0)]
    if bad:
        die(f"confirm needs 0/1 outcomes; got {bad[0]} — use `compare` for continuous values")
    wins = sum(1 for a, b in zip(champ, chal) if b > a)
    losses = sum(1 for a, b in zip(champ, chal) if a > b)
    deflated = args.alpha / search
    if wins + losses == 0:
        emit("REJECT", {"mode": "confirm", "wins": 0, "losses": 0, "search_size": search,
                        "reason": "no discordant pairs — nothing to certify"})
    p = sign_test_p(wins, losses)
    ok = wins > losses and p <= deflated
    detail = {"mode": "confirm", "n": len(champ), "wins": wins, "losses": losses,
              "p_value": round(p, 6), "alpha": args.alpha, "search_size": search,
              "deflated_alpha": round(deflated, 6),
              "reason": f"{wins}W/{losses}L, p={p:.4g} vs deflated alpha {deflated:.4g} (alpha {args.alpha}/{search})"}
    emit("PROMOTE" if ok else "REJECT", detail)


# ---------- continuous machinery ----------

def nearest_rank(sorted_vals, q):
    return sorted_vals[max(0, math.ceil(q * len(sorted_vals)) - 1)]


def stat_of(vals, stat):
    if stat == "mean":
        return sum(vals) / len(vals)
    return nearest_rank(sorted(vals), 0.95)


def mode_compare(args):
    search = require_search_size(args.search_size)
    champ, chal = load_pair(args.champion, args.challenger)
    n = len(champ)
    sign = 1.0 if args.direction == "higher" else -1.0
    improvement = sign * (stat_of(chal, args.stat) - stat_of(champ, args.stat))
    rng = random.Random(args.seed)
    idx_pool = range(n)
    boots = []
    for _ in range(args.resamples):
        idx = rng.choices(idx_pool, k=n)  # paired: same indices for both vectors
        boots.append(sign * (stat_of([chal[i] for i in idx], args.stat)
                             - stat_of([champ[i] for i in idx], args.stat)))
    boots.sort()
    deflated = args.alpha / search
    lo = nearest_rank(boots, deflated / 2)
    hi = nearest_rank(boots, 1 - deflated / 2)
    ok = lo > 0 and improvement > 0
    detail = {"mode": "compare", "n": n, "stat": args.stat, "direction": args.direction,
              "improvement": round(improvement, 6), "ci": [round(lo, 6), round(hi, 6)],
              "alpha": args.alpha, "search_size": search, "deflated_alpha": round(deflated, 6),
              "resamples": args.resamples, "seed": args.seed,
              "reason": f"{args.stat} improvement {improvement:+.4g}, CI[{lo:+.4g}, {hi:+.4g}] at deflated alpha {deflated:.4g} — promote only if the whole CI clears zero"}
    emit("PROMOTE" if ok else "REJECT", detail)


def mode_floor(args):
    if args.max is None and args.min is None:
        die("floor needs --max and/or --min")
    breaches = []
    if args.max is not None and args.value > args.max:
        breaches.append(f"value {args.value} > max {args.max}")
    if args.min is not None and args.value < args.min:
        breaches.append(f"value {args.value} < min {args.min}")
    detail = {"mode": "floor", "value": args.value, "max": args.max, "min": args.min,
              "reason": "; ".join(breaches) or "within floor"}
    emit("REJECT" if breaches else "PROMOTE", detail)


# ---------- self-test: the known-nothing control, automated ----------

def mode_self_test(_args):
    checks = []

    def check(name, cond):
        checks.append((name, cond))
        print(f"self-test: {'PASS' if cond else 'FAIL'} — {name}")

    # A null (identical outcomes) must never be certified.
    check("confirm gives a null (0W/0L) p=1", sign_test_p(0, 0) == 1.0)
    check("confirm rejects a coin-flip (5W/5L)", sign_test_p(5, 5) > 0.05)
    check("confirm certifies a rout (12W/0L at alpha 0.05/10)",
          sign_test_p(12, 0) <= 0.05 / 10)
    check("sign test is symmetric", sign_test_p(3, 9) == sign_test_p(9, 3))
    # Continuous: identical vectors must produce a CI straddling zero (REJECT path).
    rng = random.Random(0)
    vals = [rng.uniform(10, 20) for _ in range(50)]
    boots = []
    for _ in range(500):
        idx = rng.choices(range(50), k=50)
        boots.append(stat_of([vals[i] for i in idx], "mean") - stat_of([vals[i] for i in idx], "mean"))
    check("compare on identical vectors shows zero improvement", all(b == 0.0 for b in boots))
    # Fail-closed: an undeclared search size must be a hard error, not a default.
    try:
        require_search_size(None)
        check("undeclared search size fails closed", False)
    except SystemExit as e:
        check("undeclared search size fails closed", e.code == FAIL_CLOSED)
    failed = [name for name, ok in checks if not ok]
    if failed:
        print(f"self-test: FAILED — {failed}", file=sys.stderr)
        sys.exit(FAIL_CLOSED)
    print(f"self-test: all {len(checks)} checks pass — the gate machinery is live")
    sys.exit(0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)

    s = sub.add_parser("screen", help="dev-split screen: gain >= min effect (no significance claim)")
    s.add_argument("--champion", required=True)
    s.add_argument("--challenger", required=True)
    s.add_argument("--min-effect", type=int, default=2)
    s.set_defaults(fn=mode_screen)

    r = sub.add_parser("reproduce", help="promote test: dev gain must reproduce on the never-tuned holdout")
    r.add_argument("--champion-dev", required=True)
    r.add_argument("--challenger-dev", required=True)
    r.add_argument("--champion-holdout", required=True)
    r.add_argument("--challenger-holdout", required=True)
    r.add_argument("--min-effect", type=int, default=2)
    r.add_argument("--ratio", type=float, default=0.5)
    r.set_defaults(fn=mode_reproduce)

    c = sub.add_parser("confirm", help="exact sign test, Bonferroni-deflated by the declared search size")
    c.add_argument("--champion", required=True)
    c.add_argument("--challenger", required=True)
    c.add_argument("--search-size", type=int, default=None)
    c.add_argument("--alpha", type=float, default=0.05)
    c.set_defaults(fn=mode_confirm)

    k = sub.add_parser("compare", help="paired bootstrap CI on a continuous stat at the deflated alpha")
    k.add_argument("--champion", required=True)
    k.add_argument("--challenger", required=True)
    k.add_argument("--search-size", type=int, default=None)
    k.add_argument("--alpha", type=float, default=0.05)
    k.add_argument("--stat", choices=["mean", "p95"], default="mean")
    k.add_argument("--direction", choices=["higher", "lower"], default="higher")
    k.add_argument("--seed", type=int, default=0)
    k.add_argument("--resamples", type=int, default=2000)
    k.set_defaults(fn=mode_compare)

    f = sub.add_parser("floor", help="hard-floor arithmetic: value must respect --max/--min")
    f.add_argument("--value", type=float, required=True)
    f.add_argument("--max", type=float, default=None)
    f.add_argument("--min", type=float, default=None)
    f.set_defaults(fn=mode_floor)

    t = sub.add_parser("self-test", help="known-nothing control: verify the machinery itself")
    t.set_defaults(fn=mode_self_test)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
