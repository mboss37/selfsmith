"""tools/metric-contract.sh is Step 0 of instantiation — the loop must not run on a metric
that is non-numeric, non-deterministic, or unable to tell good from bad. These tests prove
the shipped contract passes on this example and that each failure mode is actually caught."""
import subprocess
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent.parent
CONTRACT = EXAMPLE_DIR / "tools" / "metric-contract.sh"


def run_contract(env_file=None):
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
    if env_file is not None:
        env["METRIC_CONTRACT_ENV"] = str(env_file)
    return subprocess.run(["bash", str(CONTRACT)], capture_output=True, text=True,
                          cwd=EXAMPLE_DIR, env=env)


def write_env(tmp_path, good, bad, direction="higher"):
    p = tmp_path / "metric.env"
    p.write_text(f"METRIC_GOOD_CMD='{good}'\nMETRIC_BAD_CMD='{bad}'\nMETRIC_DIRECTION='{direction}'\n")
    return p


def test_shipped_contract_passes():
    r = run_contract()
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stdout


def test_separation_failure_is_caught(tmp_path):
    r = run_contract(write_env(tmp_path, good="echo 0.2", bad="echo 0.9"))
    assert r.returncode == 1
    assert "SEPARATION" in r.stderr


def test_direction_is_respected(tmp_path):
    r = run_contract(write_env(tmp_path, good="echo 120", bad="echo 300", direction="lower"))
    assert r.returncode == 0, r.stderr


def test_nondeterminism_is_caught(tmp_path):
    flaky = tmp_path / "flaky.sh"
    flaky.write_text("#!/usr/bin/env bash\ncat counter 2>/dev/null || echo 0 > counter\n"
                     "n=$(cat counter); echo $((n+1)) > counter; echo \"0.$n\"\n")
    r = run_contract(write_env(tmp_path, good=f"cd {tmp_path} && bash flaky.sh", bad="echo 0.1"))
    assert r.returncode == 1
    assert "DETERMINISM" in r.stderr


def test_non_numeric_output_is_caught(tmp_path):
    r = run_contract(write_env(tmp_path, good="echo great", bad="echo 0.1"))
    assert r.returncode == 1
    assert "not a number" in r.stderr


def test_missing_env_file_fails(tmp_path):
    r = run_contract(tmp_path / "does-not-exist.env")
    assert r.returncode == 1


def test_identical_to_template_copy():
    template = EXAMPLE_DIR.parent.parent / "template" / "tools" / "metric-contract.sh"
    if not template.exists():  # example copied out of the repo — nothing to compare against
        return
    assert CONTRACT.read_text() == template.read_text()
