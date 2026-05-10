from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model

SYSTEM_PROMPT = load_prompt("reviewer_system.txt")


def review(task, result):
    return call_model(
        model=get_model("reviewer"),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"""
Task:
{task}

Proposed Changes:
{result}
"""
    )
