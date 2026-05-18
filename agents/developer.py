from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model
from orchestrator.logger import log

SYSTEM_PROMPT = load_prompt("developer_system.txt")


def build_user_prompt(task, file_context):
    return f"""
Task ID:
{task['id']}

Title:
{task['title']}

Description:
{task['description']}

Files:
{task['files']}

Acceptance Criteria:
{task['acceptance_criteria']}

Existing File Context:
{file_context}

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

    if "patches" not in result:
        raise Exception("Developer output missing 'patches'")

    if not isinstance(result["patches"], list):
        raise Exception("'patches' must be a list")

    if not result["patches"]:
        raise Exception("Developer returned no patches")

    for patch in result["patches"]:
        if not isinstance(patch, dict):
            raise Exception("Patch must be an object")

        if "file" not in patch:
            raise Exception("Patch missing file")

        if "diff" not in patch:
            raise Exception("Patch missing diff")


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
