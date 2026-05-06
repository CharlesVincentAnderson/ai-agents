from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt

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
    user_prompt = build_user_prompt(task)

    return call_model(
        model="mistral-small:24b",
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt
    )
