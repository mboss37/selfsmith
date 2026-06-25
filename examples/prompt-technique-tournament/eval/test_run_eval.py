import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL))
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
