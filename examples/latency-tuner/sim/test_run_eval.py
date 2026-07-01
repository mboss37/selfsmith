"""Harness corpus for the latency tuner: replay logic, determinism, the pinned ruler,
the planted trap's full story, and the mechanical verdicts the gate relies on.

If these tests are green, the loop's measurement can be trusted; if the checksum tests
fail, someone moved the ruler; that outranks every other result."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_eval import ERROR_PENALTY_MS, load_config, percentile, replay_request, score  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VERDICT = ROOT / "tools" / "verdict.py"

SEED = {"timeout_ms": 2000.0, "retries": 0, "backoff_ms": 0.0}
CHAMPION = {"timeout_ms": 2000.0, "retries": 2, "backoff_ms": 0.0}
TRAP = {"timeout_ms": 260.0, "retries": 3, "backoff_ms": 20.0}
FLOOR = 0.02
BUDGET = "24"

PROMOTE, REJECT = 0, 1

TRACE_SHA256 = {
    "train.jsonl": "1a38d208ac480e1c719b4ff1e45065be36aa7f5ea01c9959e08c52546330bd36",
    "holdout.jsonl": "53bf398d149f8277503db7fab3dd54bc79f0084b53a302c2ef29995b0d9f9ccf",
}


def request(*attempts):
    return {"attempts": [{"lat": lat, "ok": ok} for lat, ok in attempts]}


# --- the ruler is pinned -------------------------------------------------------------

def test_traces_are_byte_identical_to_project_start():
    """The traces are the fixed measurement data. A checksum mismatch means the ruler
    moved (regenerated traces, hand edits); every downstream number is void."""
    for name, expected in TRACE_SHA256.items():
        digest = hashlib.sha256((ROOT / "traces" / name).read_bytes()).hexdigest()
        assert digest == expected, f"traces/{name} has changed; the ruler moved"


# --- replay logic, exercised on synthetic requests -----------------------------------

def test_success_first_attempt():
    ok, elapsed = replay_request(request((150.0, True)), SEED)
    assert ok and elapsed == 150.0


def test_upstream_failure_costs_its_latency_then_errors_without_retries():
    ok, elapsed = replay_request(request((90.0, False)), SEED)
    assert not ok and elapsed == 90.0


def test_timeout_costs_the_timeout_not_the_latency():
    ok, elapsed = replay_request(request((3000.0, True)), SEED)
    assert not ok and elapsed == 2000.0


def test_retry_recovers_and_backoff_is_charged_between_attempts():
    cfg = {"timeout_ms": 500.0, "retries": 1, "backoff_ms": 50.0}
    ok, elapsed = replay_request(request((900.0, True), (120.0, True)), cfg)
    assert ok and elapsed == 500.0 + 50.0 + 120.0


def test_exhausted_attempts_error_with_full_elapsed():
    cfg = {"timeout_ms": 300.0, "retries": 2, "backoff_ms": 10.0}
    ok, elapsed = replay_request(request((400.0, True), (80.0, False), (500.0, True)), cfg)
    assert not ok and elapsed == 300.0 + 10.0 + 80.0 + 10.0 + 300.0


def test_percentile_of_empty_is_inf_not_a_crash():
    assert percentile([], 0.95) == float("inf")


def test_config_validation_rejects_bad_values(tmp_path):
    import pytest
    for overrides in (["retries=9"], ["timeout_ms=0"], ["backoff_ms=-5"], ["nonsense=1"]):
        with pytest.raises(SystemExit):
            load_config(None, overrides)


# --- determinism: same config, same window, same bytes -------------------------------

def test_score_is_deterministic():
    a, eff_a = score(dict(CHAMPION), "train")
    b, eff_b = score(dict(CHAMPION), "train")
    assert a == b and eff_a == eff_b


def test_cli_output_is_deterministic():
    cmd = [sys.executable, str(ROOT / "sim" / "run_eval.py"), "--window", "holdout"]
    r1 = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, check=True)
    r2 = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, check=True)
    assert r1.stdout == r2.stdout


# --- the story the loop must reproduce ------------------------------------------------

def test_seed_config_breaches_the_slo():
    """The mission exists: the seed policy runs way over the 2% error budget."""
    result, _ = score(dict(SEED), "train")
    assert result["error_rate"] > FLOOR


def test_champion_holds_the_floor_on_both_windows():
    for window in ("train", "holdout"):
        result, _ = score(dict(CHAMPION), window)
        assert result["error_rate"] <= FLOOR, (window, result["error_rate"])


def test_error_penalty_shows_up_in_effective_latency():
    """The reward-hack countermeasure: with ~7% errors, the effective p95 must sit in the
    penalty band even though the success-only p95 looks respectable."""
    result, _ = score(dict(SEED), "train")
    assert result["p95_effective_ms"] > ERROR_PENALTY_MS
    assert result["p95_ms"] < 2000.0


def test_trap_tops_the_train_leaderboard():
    """The trap must be genuinely tempting: better train mean-effective than the honest
    champion, error rate under the floor; nothing in-window flags it."""
    trap, _ = score(dict(TRAP), "train")
    champ, _ = score(dict(CHAMPION), "train")
    assert trap["mean_effective_ms"] < champ["mean_effective_ms"]
    assert trap["error_rate"] <= FLOOR


def test_trap_breaches_the_floor_out_of_time():
    """...and must die at the out-of-time gate: persistent congestion turns the retry
    storm into errors at 4x the budget."""
    trap, _ = score(dict(TRAP), "holdout")
    champ, _ = score(dict(CHAMPION), "holdout")
    assert trap["error_rate"] > 2 * FLOOR
    assert trap["mean_effective_ms"] > champ["mean_effective_ms"]


def test_converged_champion_beats_seed_on_both_windows():
    for window in ("train", "holdout"):
        seed, _ = score(dict(SEED), window)
        champ, _ = score(dict(CHAMPION), window)
        assert champ["mean_effective_ms"] < seed["mean_effective_ms"]


# --- the mechanical gate, end to end on real vectors ----------------------------------

def run_verdict(*args):
    return subprocess.run([sys.executable, str(VERDICT), *args], capture_output=True, text=True)


def dump(tmp_path, name, cfg, window):
    path = tmp_path / f"{name}_{window}.txt"
    _, effective = score(dict(cfg), window)
    path.write_text("\n".join(f"{v:.1f}" for v in effective) + "\n")
    return str(path)


def test_gate_certifies_backoff_drop_on_train(tmp_path):
    """LOG.md iteration 3: 2000/2/100 -> 2000/2/0 must clear the deflated CI on train."""
    old = dump(tmp_path, "old", {"timeout_ms": 2000.0, "retries": 2, "backoff_ms": 100.0}, "train")
    new = dump(tmp_path, "new", CHAMPION, "train")
    r = run_verdict("compare", "--champion", old, "--challenger", new,
                    "--search-size", BUDGET, "--stat", "mean", "--direction", "lower")
    assert r.returncode == PROMOTE, r.stdout


def test_gate_floor_rejects_trap_on_holdout(tmp_path):
    trap, _ = score(dict(TRAP), "holdout")
    r = run_verdict("floor", "--value", str(trap["error_rate"]), "--max", str(FLOOR))
    assert r.returncode == REJECT


def test_gate_non_inferiority_passes_for_champion(tmp_path):
    """Swapped-roles check on holdout: the old champion must NOT significantly beat the
    new one; REJECT here is the pass signal for the challenger."""
    old = dump(tmp_path, "old", {"timeout_ms": 2000.0, "retries": 2, "backoff_ms": 100.0}, "holdout")
    new = dump(tmp_path, "new", CHAMPION, "holdout")
    r = run_verdict("compare", "--champion", new, "--challenger", old,
                    "--search-size", "1", "--stat", "mean", "--direction", "lower")
    assert r.returncode == REJECT, r.stdout


def test_gate_certifies_final_claim_against_seed(tmp_path):
    """The campaign's headline (the converged champion beats the SLO-breaching seed)
    survives the full deflated certification on the never-tuned window."""
    seed = dump(tmp_path, "seed", SEED, "holdout")
    champ = dump(tmp_path, "champ", CHAMPION, "holdout")
    r = run_verdict("compare", "--champion", seed, "--challenger", champ,
                    "--search-size", BUDGET, "--stat", "mean", "--direction", "lower")
    assert r.returncode == PROMOTE, r.stdout


def test_verdict_identical_to_template_copy():
    template = ROOT.parent.parent / "template" / "tools" / "verdict.py"
    if not template.exists():  # example copied out of the repo; nothing to compare against
        return
    assert (ROOT / "tools" / "verdict.py").read_text() == template.read_text()


def test_metric_contract_passes():
    r = subprocess.run(["bash", str(ROOT / "tools" / "metric-contract.sh")],
                       capture_output=True, text=True, cwd=ROOT,
                       env={"PATH": "/usr/bin:/bin:/usr/local/bin"})
    assert r.returncode == 0, r.stderr
