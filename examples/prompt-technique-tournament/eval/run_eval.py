#!/usr/bin/env python3
"""Render a prompting technique onto the base prompt, run it over an eval split, score it.

Offline by default (--model mock): a deterministic stub whose correctness is driven by each
case's `_solved_by` metadata, so the leaderboard tells a true generalization story with no API
key. Swap --model claude for a real Anthropic call (the production seam).
"""
import argparse
import json
import math
import sys
from pathlib import Path

from techniques import TECHNIQUES, active_set, render

EVAL_DIR = Path(__file__).resolve().parent
CASES_DIR = EVAL_DIR / "cases"


def load_split(split):
    path = CASES_DIR / f"{split}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def wilson(passes, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = passes / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, center - half), min(1.0, center + half))


def mock_model(active, case):
    """Deterministic stand-in: a case is solved iff the baseline solves it OR an active
    technique is in its `_solved_by` set. The whole generalization story lives in the data."""
    solvers = set(case["_solved_by"])
    if "baseline" in solvers or (solvers & set(active)):
        return case["expected"]
    wrong = dict(case["expected"])
    wrong["category"] = "__unsolved__"
    return wrong


def claude_model(prompt, input_text):
    """PRODUCTION SEAM — swap mock for this for real use. Requires `pip install anthropic`
    and ANTHROPIC_API_KEY. See the claude-api skill for current model ids and SDK usage."""
    try:
        import os

        import anthropic
    except ImportError:
        sys.exit("--model claude needs `pip install anthropic` (the offline demo uses --model mock)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("--model claude needs ANTHROPIC_API_KEY (the offline demo uses --model mock)")
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": f"{prompt}\n\nMessage:\n{input_text}"}],
    )
    text = msg.content[0].text
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return {}


def score(technique, split, model):
    cases = load_split(split)
    base = (EVAL_DIR / "base_prompt.txt").read_text()
    active = active_set(technique)
    pool = load_split("train") if "few_shot" in active else []  # only few_shot needs the pool
    prompt = render(technique, base, pool)
    passes, results = 0, []
    for case in cases:
        pred = mock_model(active, case) if model == "mock" else claude_model(prompt, case["input"])
        ok = pred == case["expected"]
        passes += int(ok)
        results.append({"input": case["input"][:48], "pass": bool(ok)})
    n = len(cases)
    lo, hi = wilson(passes, n)
    return {
        "technique": technique, "split": split, "passes": passes, "n": n,
        "pass_rate": round(passes / n, 3) if n else 0.0,
        "wilson95": [round(lo, 3), round(hi, 3)], "results": results,
    }


def main():
    ap = argparse.ArgumentParser(description="Score a prompting technique on an eval split.")
    ap.add_argument("--technique", default="zero_shot",
                    help="technique name or '+'-joined combo, e.g. few_shot+chain_of_thought")
    ap.add_argument("--split", choices=["train", "dev", "holdout"], default="dev")
    ap.add_argument("--model", choices=["mock", "claude"], default="mock")
    args = ap.parse_args()
    for name in active_set(args.technique):
        if name not in TECHNIQUES:
            sys.exit(f"unknown technique '{name}' — known: {', '.join(sorted(TECHNIQUES))}")
    r = score(args.technique, args.split, args.model)
    print(f"{r['technique']:40s} {r['split']:8s} {r['passes']}/{r['n']} = "
          f"{r['pass_rate']:.0%}  (95% CI {r['wilson95'][0]:.0%}-{r['wilson95'][1]:.0%})")
    print(json.dumps(r))


if __name__ == "__main__":
    main()
