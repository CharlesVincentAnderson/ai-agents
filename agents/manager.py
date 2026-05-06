from orchestrator.llm_client import call_model
from orchestrator.prompt_loader import load_prompt
from orchestrator.model_registry import get_model


SYSTEM_PROMPT = load_prompt("manager_system.txt")


def generate_plan(idea):
    return call_model(
        model=get_model("manager"),
        system_prompt=SYSTEM_PROMPT,
        user_prompt=idea
    )
