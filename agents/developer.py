import json

from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model
from orchestrator.logger import log

SYSTEM_PROMPT = load_prompt("developer_system.txt")


def extract_json(raw_output):
    start = raw_output.find("{")
    end = raw_output.rfind("}")

    if start == -1 or end == -1:
        raise Exception("No JSON object found")

    return raw_output[start:end + 1]


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


def validate_raw_json_output(raw_output):
    """
    Detect obvious malformed JSON patterns before parsing.
    """

    if not raw_output.strip():
        raise Exception("Empty developer response")

    if '"changes"' not in raw_output:
        raise Exception('Developer response missing "changes" field')

    if raw_output.count("{") != raw_output.count("}"):
        raise Exception("Mismatched curly braces in developer response")

    if raw_output.count("[") != raw_output.count("]"):
        raise Exception("Mismatched square brackets in developer response")

def implement(task):
    raw_output = call_model(
        model=get_model("developer"),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(task)
    )

    log("RAW DEVELOPER RESPONSE:")
    log(repr(raw_output))

    # already parsed
    if isinstance(raw_output, dict):
        result = raw_output

    # raw JSON string
    else:
        raw_output = extract_json(raw_output)

        try:
            result = json.loads(raw_output)

        except json.JSONDecodeError as e:
            log(f"JSON parse error: {e}")
            log(repr(raw_output))

            raise Exception(f"Developer returned invalid JSON: {e}")

    # schema validation

    if not isinstance(result, dict):
        raise Exception("Developer output must be a JSON object")

    if "changes" not in result:
        raise Exception("Developer output missing 'changes'")

    if not isinstance(result["changes"], list):
        raise Exception("'changes' must be a list")

    return result
