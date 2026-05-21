from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model
from orchestrator.logger import log

SYSTEM_PROMPT = load_prompt("developer_system.txt")


def build_user_prompt(
    task,
    repo_index,
    relevant_files
):
    return f"""
Task ID:
{task['id']}

Title:
{task['title']}

Description:
{task['description']}

Acceptance Criteria:
{task['acceptance_criteria']}

Repository Index:
{repo_index}

Relevant File Contents:
{relevant_files}

Previous Feedback:
{task.get('feedback', [])}

Attempt History:
{task.get('history', [])}

Latest Test Output:
{task.get('latest_test_output', '')}
"""

def validate_result(result):
    if not isinstance(result, dict):
        raise Exception("Developer output must be a JSON object")

    if "changes" not in result:
        raise Exception("Developer output missing 'changes'")

    if not isinstance(result["changes"], list):
        raise Exception("'changes' must be a list")

    if not result["changes"]:
        raise Exception("Developer returned no changes")

    for change in result["changes"]:
        if not isinstance(change, dict):
            raise Exception("Change must be an object")

        if "file" not in change:
            raise Exception("Change missing file")

        if "content" not in change:
            raise Exception("Change missing content")


def implement(task, file_context):
    result = call_model(
        model=get_model("developer"),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(task, file_context)
    )

    log("RAW DEVELOPER RESPONSE:")
    log(repr(result))

    validate_result(result)

    return result
