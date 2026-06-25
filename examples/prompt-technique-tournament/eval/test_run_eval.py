import json
import subprocess
import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL))
import run_eval as R  # noqa: E402
import techniques as T  # noqa: E402


def test_zero_shot_is_noop():
    assert T.render("zero_shot", "BASE", []) == "BASE"

def test_active_set_splits_combo():
    assert T.active_set("few_shot+chain_of_thought") == ["few_shot", "chain_of_thought"]

def test_render_composes_in_order():
    pool = [{"input": "x", "expected": {"category": "billing"}}]
    out = T.render("role+format_spec", "BASE", pool)
    assert "support triage analyst" in out  # role applied
    assert "JSON object" in out              # format_spec applied
    assert out.index("analyst") < out.index("BASE")  # role wraps before base

def test_unknown_technique_raises():
    with pytest.raises(KeyError):
        T.render("does_not_exist", "BASE", [])

def test_every_technique_has_a_mechanism():
    for name, (fn, mechanism) in T.TECHNIQUES.items():
        assert callable(fn) and isinstance(mechanism, str) and mechanism


# --- Task 2: run_eval ---

def test_wilson_known_value():
    lo, hi = R.wilson(10, 20)
    assert round(lo, 3) == 0.299 and round(hi, 3) == 0.701

def test_wilson_empty():
    assert R.wilson(0, 0) == (0.0, 0.0)

def test_mock_solves_when_active_intersects_solved_by():
    case = {"input": "x", "expected": {"category": "billing"}, "_solved_by": ["few_shot"]}
    assert R.mock_model(["few_shot"], case) == {"category": "billing"}

def test_mock_solves_baseline_regardless():
    case = {"input": "x", "expected": {"category": "other"}, "_solved_by": ["baseline"]}
    assert R.mock_model([], case) == {"category": "other"}

def test_mock_fails_when_no_solver_active():
    case = {"input": "x", "expected": {"category": "billing"}, "_solved_by": ["few_shot"]}
    assert R.mock_model(["chain_of_thought"], case) != {"category": "billing"}

def test_cli_runs_offline_and_prints_json(tmp_path):
    out = subprocess.run(
        [sys.executable, "run_eval.py", "--technique", "zero_shot", "--split", "dev", "--model", "mock"],
        cwd=EVAL, capture_output=True, text=True)
    assert out.returncode == 0
    last = out.stdout.strip().splitlines()[-1]
    report = json.loads(last)
    assert report["split"] == "dev" and report["n"] > 0


# --- Task 3: eval cases + pinned generalization story ---

@pytest.mark.parametrize("technique,split,passes", [
    ("zero_shot", "dev", 7), ("zero_shot", "holdout", 7),
    ("few_shot", "dev", 11), ("few_shot", "holdout", 11),
    ("chain_of_thought", "dev", 11), ("chain_of_thought", "holdout", 11),
    ("self_critique", "dev", 11),                       # solves the same cases as CoT
    ("decomposition", "dev", 10), ("decomposition", "holdout", 10),
    ("keyword_rules", "dev", 9), ("keyword_rules", "holdout", 7),   # TRAP: +2 dev, +0 holdout
    ("few_shot+chain_of_thought", "dev", 15), ("few_shot+chain_of_thought", "holdout", 15),
    ("few_shot+chain_of_thought+self_critique", "dev", 15),         # REDUNDANT: == without it
    ("few_shot+chain_of_thought+decomposition", "dev", 18),
    ("few_shot+chain_of_thought+decomposition", "holdout", 18),
])
def test_generalization_story(technique, split, passes):
    assert R.score(technique, split, "mock")["passes"] == passes

def test_trap_does_not_reproduce_on_holdout():
    dev = R.score("keyword_rules", "dev", "mock")["passes"]
    hold = R.score("keyword_rules", "holdout", "mock")["passes"]
    base_dev = R.score("zero_shot", "dev", "mock")["passes"]
    base_hold = R.score("zero_shot", "holdout", "mock")["passes"]
    assert (dev - base_dev) >= 2 and (hold - base_hold) == 0  # looks good on dev, dies on holdout

def test_splits_are_disjoint_and_sized():
    dev = {json.dumps(c["expected"]) + c["input"] for c in R.load_split("dev")}
    hold = {json.dumps(c["expected"]) + c["input"] for c in R.load_split("holdout")}
    assert len(R.load_split("dev")) == 20 and len(R.load_split("holdout")) == 20
    assert dev.isdisjoint(hold)
