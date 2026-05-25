from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model
import re

SYSTEM_PROMPT = load_prompt("manager_system.txt")


def validate_plan(plan, user_request):
    if not isinstance(plan, dict):
        raise Exception("Plan must be a dictionary")

    tasks = plan.get("tasks")

    if not isinstance(tasks, list) or not tasks:
        raise Exception("Plan must contain tasks")

    lowered_request = user_request.lower()

    for task in tasks:
        if not isinstance(task, dict):
            raise Exception("Each task must be a dictionary")

        required_files = task.get("required_files", [])

        if not isinstance(required_files, list):
            raise Exception("required_files must be a list")

        if not required_files:
            raise Exception("Task missing required_files")

        # If tests were requested, ensure at least one test file exists
        if "test" in lowered_request:
            has_test_file = any(
                "test" in f.lower()
                for f in required_files
            )

            if not has_test_file:
                raise Exception(
                    "Plan missing test file"
                )


def generate_plan(idea):
    plan = call_model(
        model=get_model("manager"),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=idea
    )

    validate_plan(plan, idea)

    return plan
