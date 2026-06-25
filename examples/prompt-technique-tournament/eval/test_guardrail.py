import json
import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".claude/hooks/guardrail.sh"


def _exit_code(command):
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run(["bash", str(HOOK)], input=payload, text=True,
                          capture_output=True).returncode


def test_floor1_blocks_holdout_mutation():
    assert _exit_code("echo x > eval/cases/holdout.jsonl") == 2

def test_floor1_blocks_real_model_spend():
    assert _exit_code("python eval/run_eval.py --split dev --model claude") == 2

def test_floor2_blocks_destructive():
    assert _exit_code("sudo rm -rf /") == 2

def test_allows_benign_run():
    assert _exit_code("python eval/run_eval.py --split dev") == 0
