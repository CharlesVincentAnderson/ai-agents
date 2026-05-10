from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model

SYSTEM_PROMPT = load_prompt("developer_system.txt")


def build_user_prompt(task):
    return f"""
Task ID: {task['id']}

Title:
{task['title']}

Description:
{task['description']}

Files to modify:
{task['files']}

Acceptance Criteria:
{task['acceptance_criteria']}

Feedback (if any):
{task.get('feedback', [])}
"""


def implement(task):
    return call_model(
        model=get_model("developer"),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(task)
    )
