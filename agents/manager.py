from orchestrator.llm_client import call_model
from orchestrator.config import MODELS

def load_prompt():
    with open("prompts/manager_system.txt") as f:
        return f.read()

def generate_plan(idea):
    system = load_prompt()
    return call_model(MODELS["manager"], system, idea)
