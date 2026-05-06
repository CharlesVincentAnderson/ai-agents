import subprocess
import json
import re
from orchestrator.logger import log


def extract_json(text):
    text = text.strip()

    # remove code fences if present
    text = re.sub(r"```json|```", "", text)

    # try direct parse first
    try:
        return json.loads(text)
    except:
        pass

    # fallback: extract first JSON block (object or array)
    matches = re.findall(r"(\{.*\}|\[.*\])", text, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match)
        except:
            continue

    raise ValueError(f"Failed to parse JSON:\n{text}")


def call_model(model, system_prompt, user_prompt):
    prompt = f"""<system>
{system_prompt}
</system>

<user>
{user_prompt}
</user>
"""

    log(f"[LLM] Running {model} via CLI")

    process = subprocess.Popen(
        ["ollama", "run", model],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(prompt)

    if process.returncode != 0:
        raise Exception(f"Model error: {stderr}")

    log(f"[LLM] Completed {model}")

    return extract_json(stdout)
