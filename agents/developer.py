from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model
from orchestrator.logger import log

import json


SYSTEM_PROMPT = load_prompt("developer_system.txt")


def build_user_prompt(
    task,
    relevant_files,
    required_files
):
    relevant_context = []

    if isinstance(relevant_files, dict):
        for path, content in relevant_files.items():
            relevant_context.append(
                f"FILE: {path}\n\n{content}"
            )

    prompt = f"""
Task ID:
{task['id']}

Title:
{task['title']}

Description:
{task['description']}

REQUIRED FILES:
{json.dumps(required_files, indent=2)}

RELEVANT FILE CONTEXT:

{chr(10).join(relevant_context)}

Acceptance Criteria:
{json.dumps(task.get('acceptance_criteria', []), indent=2)}

Previous Feedback:
{json.dumps(task.get('feedback', []), indent=2)}

Attempt History:
{json.dumps(task.get('history', []), indent=2)}

Latest Test Output:
{task.get('latest_test_output', '')}

IMPORTANT:
- Implement ALL required_files
- Preserve module boundaries
- Use imports instead of duplicating logic
- Return ONLY valid JSON
"""

    return prompt


def validate_result(result):
    if not isinstance(result, dict):
        raise Exception(
            "Developer output must be a JSON object"
        )

    if "changes" not in result:
        raise Exception(
            "Developer output missing 'changes'"
        )

    if not isinstance(result["changes"], list):
        raise Exception(
            "'changes' must be a list"
        )

    if not result["changes"]:
        raise Exception(
            "Developer returned no changes"
        )

    for change in result["changes"]:
        if not isinstance(change, dict):
            raise Exception(
                "Change must be an object"
            )

        if "file" not in change:
            raise Exception(
                "Change missing file"
            )

        if "content" not in change:
            raise Exception(
                "Change missing content"
            )

def implement(
    task,
    repo_index,
    relevant_files,
    required_files=None,
    task_context=None
):
    import json

    required_files = required_files or []
    task_context = task_context or {}

    relevant_context = []

    if isinstance(relevant_files, dict):
        for path, content in relevant_files.items():
            relevant_context.append(
                f"FILE: {path}\n\n{content}"
            )

    elif isinstance(relevant_files, list):
        relevant_context = relevant_files

    required_files_text = "\n".join(
        f"- {file_path}"
        for file_path in required_files
    )

    acceptance_text = "\n".join(
        f"- {item}"
        for item in task.get(
            "acceptance_criteria",
            []
        )
    )

    relevant_text = "\n\n".join(relevant_context)

    prompt = f"""
YOU MUST CREATE OR MODIFY ALL REQUIRED FILES.

FAILURE TO RETURN EVERY REQUIRED FILE IS INCORRECT.

TASK ID:
{task.get("id")}

TITLE:
{task.get("title")}

DESCRIPTION:
{task.get("description")}

REQUIRED FILES:
{required_files_text}

ACCEPTANCE CRITERIA:
{acceptance_text}

PREVIOUS FEEDBACK:
{json.dumps(task.get("feedback", []), indent=2)}

ATTEMPT HISTORY:
{json.dumps(task.get("history", []), indent=2)}

RELEVANT FILE CONTEXT:

{relevant_text}

CRITICAL RULES:
- Return ALL required files
- Every required file must appear in "changes"
- "content" must contain FULL file contents
- Do NOT return partial files
- Do NOT return diffs
- Output ONLY valid JSON
"""

    log(
        f"[LLM] Running {get_model('developer')} "
        f"for developer"
    )

    response = call_model(
        model=get_model("developer"),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt
    )

    if isinstance(response, dict):
        result = response
    else:
        result = json.loads(response)

    validate_result(result)

    returned_files = {
        change["file"]
        for change in result["changes"]
    }

    missing_files = [
        file_path
        for file_path in required_files
        if file_path not in returned_files
    ]

    if missing_files:
        raise Exception(
            "Developer failed to return required files: "
            + ", ".join(missing_files)
        )

    return result
