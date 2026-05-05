from orchestrator.llm_client import call_model
from orchestrator.config import MODELS, WORKSPACE
import os

def load_prompt():
    with open("prompts/developer_system.txt") as f:
        return f.read()

def get_workspace_snapshot():
    snapshot = []
    for root, _, files in os.walk(WORKSPACE):
        for f in files:
            path = os.path.join(root, f)
            with open(path, "r", errors="ignore") as fh:
                snapshot.append(f"FILE: {path}\n{fh.read()}\n")
    return "\n".join(snapshot)

def implement(task):
    system = load_prompt()
    context = get_workspace_snapshot()

    prompt = f"""
TASK:
{task}

CURRENT CODEBASE:
{context}
"""
    return call_model(MODELS["developer"], system, prompt)
