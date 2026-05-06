import os


PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def load_prompt(filename: str) -> str:
    path = os.path.join(PROMPT_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt not found: {path}")

    with open(path, "r") as f:
        return f.read()
