from orchestrator.llm_client import call_model
from orchestrator.config import MODELS

def load_prompt():
    with open("prompts/reviewer_system.txt") as f:
        return f.read()

def review(task, changes):
    system = load_prompt()
    prompt = f"""
TASK:
{task}

PROPOSED CHANGES:
{changes}
"""
    return call_model(MODELS["reviewer"], system, prompt)
