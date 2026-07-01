"""tools/verdict.py is the mechanical half of the gate; these tests prove the machinery
itself: promotes only what the declared rules certify, rejects nulls and traps, fails
closed when the search size is undeclared, and stays deterministic run-to-run."""
import json
import subprocess
import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent.parent
VERDICT = EXAMPLE_DIR / "tools" / "verdict.py"
RUN_EVAL = EXAMPLE_DIR / "eval" / "run_eval.py"

PROMOTE, REJECT, FAIL_CLOSED = 0, 1, 3


def run_verdict(*args):
    return subprocess.run([sys.executable, str(VERDICT), *args],
                          capture_output=True, text=True)


def write_vector(tmp_path, name, values):
    p = tmp_path / name
    p.write_text("\n".join(str(v) for v in values) + "\n")
    return str(p)


def eval_json(tmp_path, technique, split):
    out = subprocess.run(
        [sys.executable, str(RUN_EVAL), "--technique", technique, "--split", split, "--model", "mock"],
        capture_output=True, text=True, cwd=EXAMPLE_DIR / "eval", check=True)
    p = tmp_path / f"{technique.replace('+', '_')}_{split}.json"
    p.write_text(out.stdout.strip().splitlines()[-1])
    return str(p)


def test_self_test_passes():
    r = run_verdict("self-test")
    assert r.returncode == 0, r.stderr
    assert "all" in r.stdout and "pass" in r.stdout


def test_confirm_fails_closed_without_search_size(tmp_path):
    a = write_vector(tmp_path, "a", [0, 1] * 10)
    b = write_vector(tmp_path, "b", [1, 1] * 10)
    r = run_verdict("confirm", "--champion", a, "--challenger", b)
    assert r.returncode == FAIL_CLOSED
    assert "search-size" in r.stderr


def test_confirm_rejects_null(tmp_path):
    a = write_vector(tmp_path, "a", [0, 1] * 10)
    r = run_verdict("confirm", "--champion", a, "--challenger", a, "--search-size", "1")
    assert r.returncode == REJECT
    assert "no discordant pairs" in r.stdout


def test_confirm_rejects_small_gain_under_deflation(tmp_path):
    a = write_vector(tmp_path, "a", [0, 0, 0] + [1] * 17)
    b = write_vector(tmp_path, "b", [1, 1, 1] + [1] * 17)  # +3, real but uncertifiable at n=20
    r = run_verdict("confirm", "--champion", a, "--challenger", b, "--search-size", "24")
    assert r.returncode == REJECT


def test_confirm_certifies_rout(tmp_path):
    a = write_vector(tmp_path, "a", [0] * 12 + [1] * 8)
    b = write_vector(tmp_path, "b", [1] * 20)
    r = run_verdict("confirm", "--champion", a, "--challenger", b, "--search-size", "24")
    assert r.returncode == PROMOTE
    assert json.loads(r.stdout.splitlines()[-1])["wins"] == 12


def test_confirm_rejects_challenger_that_loses(tmp_path):
    a = write_vector(tmp_path, "a", [1] * 15 + [0] * 5)
    b = write_vector(tmp_path, "b", [0] * 15 + [1] * 5)
    r = run_verdict("confirm", "--champion", a, "--challenger", b, "--search-size", "1")
    assert r.returncode == REJECT


def test_confirm_refuses_continuous_values(tmp_path):
    a = write_vector(tmp_path, "a", [0.5] * 5)
    b = write_vector(tmp_path, "b", [0.9] * 5)
    r = run_verdict("confirm", "--champion", a, "--challenger", b, "--search-size", "1")
    assert r.returncode == FAIL_CLOSED


def test_reproduce_rejects_planted_trap_on_real_data(tmp_path):
    """keyword_rules wins on dev but not holdout; the mechanical gate must catch it."""
    champ = "zero_shot"  # seed champion the trap challenges
    r = run_verdict(
        "reproduce",
        "--champion-dev", eval_json(tmp_path, champ, "dev"),
        "--challenger-dev", eval_json(tmp_path, "keyword_rules", "dev"),
        "--champion-holdout", eval_json(tmp_path, champ, "holdout"),
        "--challenger-holdout", eval_json(tmp_path, "keyword_rules", "holdout"))
    assert r.returncode == REJECT, r.stdout
    detail = json.loads(r.stdout.splitlines()[-1])
    assert detail["dev_gain"] >= 2 and detail["holdout_gain"] < detail["required_holdout_gain"]


def test_reproduce_promotes_genuine_technique_on_real_data(tmp_path):
    r = run_verdict(
        "reproduce",
        "--champion-dev", eval_json(tmp_path, "zero_shot", "dev"),
        "--challenger-dev", eval_json(tmp_path, "few_shot", "dev"),
        "--champion-holdout", eval_json(tmp_path, "zero_shot", "holdout"),
        "--challenger-holdout", eval_json(tmp_path, "few_shot", "holdout"))
    assert r.returncode == PROMOTE, r.stdout


def test_final_claim_certifies_on_real_data(tmp_path):
    """Champion vs baseline on holdout must survive the sign test deflated by the full
    declared candidate budget (24), so the campaign's headline claim is mechanically true."""
    r = run_verdict(
        "confirm",
        "--champion", eval_json(tmp_path, "zero_shot", "holdout"),
        "--challenger", eval_json(tmp_path, "few_shot+chain_of_thought+decomposition", "holdout"),
        "--search-size", "24")
    assert r.returncode == PROMOTE, r.stdout


def test_compare_promotes_clear_continuous_win(tmp_path):
    a = write_vector(tmp_path, "a", [200 + (i * 37 % 100) for i in range(200)])
    b = write_vector(tmp_path, "b", [v - 50 for v in [200 + (i * 37 % 100) for i in range(200)]])
    r = run_verdict("compare", "--champion", a, "--challenger", b, "--search-size", "10",
                    "--stat", "p95", "--direction", "lower", "--resamples", "300")
    assert r.returncode == PROMOTE


def test_compare_rejects_null_and_is_deterministic(tmp_path):
    a = write_vector(tmp_path, "a", [200 + (i * 37 % 100) for i in range(200)])
    r1 = run_verdict("compare", "--champion", a, "--challenger", a, "--search-size", "10",
                     "--resamples", "300")
    r2 = run_verdict("compare", "--champion", a, "--challenger", a, "--search-size", "10",
                     "--resamples", "300")
    assert r1.returncode == REJECT
    assert r1.stdout == r2.stdout  # seeded bootstrap: same inputs, same verdict, byte-identical


def test_floor():
    assert run_verdict("floor", "--value", "0.01", "--max", "0.02").returncode == PROMOTE
    assert run_verdict("floor", "--value", "0.03", "--max", "0.02").returncode == REJECT
    assert run_verdict("floor", "--value", "5", "--min", "10").returncode == REJECT


def test_mismatched_vector_lengths_fail_closed(tmp_path):
    a = write_vector(tmp_path, "a", [1, 0, 1])
    b = write_vector(tmp_path, "b", [1, 0])
    r = run_verdict("screen", "--champion", a, "--challenger", b)
    assert r.returncode == FAIL_CLOSED


def test_identical_to_template_copy():
    """The tool is shared machinery; the instantiated copy must not drift from template."""
    template = EXAMPLE_DIR.parent.parent / "template" / "tools" / "verdict.py"
    if not template.exists():  # example copied out of the repo; nothing to compare against
        return
    assert VERDICT.read_text() == template.read_text()
