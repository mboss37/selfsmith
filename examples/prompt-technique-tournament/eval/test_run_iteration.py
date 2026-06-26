"""Behavior proof for run-iteration.sh: fresh session (no --continue) + single-flight lock.

The wrapper is copied into an isolated tmp dir and run there with a stubbed `claude` on PATH,
so the test exercises the real script's bytes without touching the repo's working tree. Parity
with the template copy is enforced separately in CI (diff), so this copy cannot silently drift.
"""
import os
import shutil
import subprocess
import textwrap
import threading
import time
from pathlib import Path

WRAPPER = Path(__file__).resolve().parents[1] / "run-iteration.sh"


def _install_stub_claude(dirpath, marker, sleep):
    """A fake `claude` that records its argv to `marker`, then sleeps to widen the lock window."""
    stub = dirpath / "claude"
    stub.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "$@" >> "{marker}"
        sleep {sleep}
    """))
    stub.chmod(0o755)


def _env(tmp_path):
    return {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}", "ITER_TIMEOUT": "30s"}


def _run(tmp_path):
    return subprocess.run(
        ["bash", str(tmp_path / "run-iteration.sh")],
        env=_env(tmp_path), capture_output=True, text=True,
    )


def test_runs_fresh_session_not_continue(tmp_path):
    shutil.copy(WRAPPER, tmp_path / "run-iteration.sh")
    marker = tmp_path / "calls.txt"
    _install_stub_claude(tmp_path, marker, sleep=0)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    calls = marker.read_text()
    assert "-p /iterate" in calls, f"expected a fresh /iterate call, got: {calls!r}"
    assert "--continue" not in calls, "wrapper must NOT pass --continue (disk is the memory)"


def test_single_flight_second_tick_skips(tmp_path):
    shutil.copy(WRAPPER, tmp_path / "run-iteration.sh")
    marker = tmp_path / "calls.txt"
    _install_stub_claude(tmp_path, marker, sleep=1.0)  # first run holds the lock ~1s
    results = {}

    def go(key):
        results[key] = _run(tmp_path)

    first = threading.Thread(target=go, args=("first",))
    first.start()
    time.sleep(0.25)  # let the first run acquire the lock
    go("second")      # fires while the first still holds it
    first.join()

    assert marker.read_text().count("/iterate") == 1, "exactly one iteration may run at a time"
    assert results["first"].returncode == 0, results["first"].stderr
    assert results["second"].returncode == 0, "the skipped tick must exit cleanly (0)"
    assert "skipping this tick" in results["second"].stderr
