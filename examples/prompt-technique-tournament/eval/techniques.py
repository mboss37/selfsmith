"""Catalog of prompting techniques. Each entry = a renderer (transforms the base prompt)
plus a stated mechanism (why it should help). A combo is a '+'-joined, ordered composition.

The MOCK model (run_eval.py) keys off technique *names* via each case's `_solved_by`; the
rendered prompt text is what a REAL model (--model claude) consumes. Both paths are meaningful.
"""
import json


def _zero_shot(base, pool):
    return base

def _few_shot(base, pool):
    ex = "\n".join(f'- {c["input"]}  ->  {json.dumps(c["expected"])}' for c in pool[:4])
    return f"{base}\n\nExamples:\n{ex}"

def _chain_of_thought(base, pool):
    return f"{base}\n\nThink step by step about category, urgency, and refund before answering."

def _role(base, pool):
    return f"You are a meticulous customer-support triage analyst.\n\n{base}"

def _format_spec(base, pool):
    return (f'{base}\n\nRespond with ONLY a JSON object: '
            '{"category": "...", "urgency": "low|medium|high", "wants_refund": true|false}')

def _decomposition(base, pool):
    return (f"{base}\n\nAnswer in three steps: (1) the category, (2) the urgency, "
            "(3) whether the customer is asking for a refund.")

def _self_critique(base, pool):
    return f"{base}\n\nDraft an answer, critique it for mistakes, then give your final answer."

def _keyword_rules(base, pool):
    return (f"{base}\n\nHeuristic: if the message mentions a reopened or repeated ticket, "
            "set wants_refund=true.")


TECHNIQUES = {
    "zero_shot":        (_zero_shot,        "baseline: instruction only, no scaffolding"),
    "few_shot":         (_few_shot,         "labeled examples teach the exact category set"),
    "chain_of_thought": (_chain_of_thought, "intermediate reasoning unlocks multi-issue urgency"),
    "role":             (_role,             "a role primes domain-appropriate attention"),
    "format_spec":      (_format_spec,      "an explicit schema reduces malformed output"),
    "decomposition":    (_decomposition,    "separating sub-questions isolates the refund decision"),
    "self_critique":    (_self_critique,    "a draft-critique pass catches reasoning slips"),
    "keyword_rules":    (_keyword_rules,    "hand rules off surface tokens; brittle, may not generalize"),
}


def active_set(technique: str) -> list[str]:
    return [t.strip() for t in technique.split("+") if t.strip()]

def render(technique: str, base: str, pool: list[dict]) -> str:
    prompt = base
    for name in active_set(technique):
        entry = TECHNIQUES.get(name)
        if entry is None:
            raise KeyError(f"unknown technique '{name}'")
        prompt = entry[0](prompt, pool)
    return prompt
