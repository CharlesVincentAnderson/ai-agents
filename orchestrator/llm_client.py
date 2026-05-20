import subprocess
import json
import re
import time

from orchestrator.logger import log


# ----------------------------
# SAFE DEEP UNESCAPE (post-parse only)
# ----------------------------

def deep_unescape(obj):
    """
    Only used AFTER json.loads().
    Converts double-escaped sequences into real characters safely.
    """

    if isinstance(obj, str):
        return obj.encode("utf-8").decode("unicode_escape")

    if isinstance(obj, list):
        return [deep_unescape(x) for x in obj]

    if isinstance(obj, dict):
        return {k: deep_unescape(v) for k, v in obj.items()}

    return obj


# ----------------------------
# STRICT JSON EXTRACTION
# ----------------------------

def extract_json(text: str):
    text = text.strip()

    # Remove code fences
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # Remove accidental "json" prefixes
    text = re.sub(r"^\s*json\s*", "", text, flags=re.IGNORECASE)

    text = text.strip()

    # First attempt: strict parse
    try:
        return deep_unescape(json.loads(text))
    except Exception:
        pass

    # Fallback: extract first JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Failed to locate JSON object:\n{text}")

    candidate = match.group(0)

    try:
        return deep_unescape(json.loads(candidate))
    except Exception as e:
        raise ValueError(f"Failed to parse extracted JSON:\n{candidate}\n\nError: {e}")


# ----------------------------
# OLLAMA CONTROL
# ----------------------------

def stop_ollama_models():
    subprocess.run(
        ["ollama", "stop", "all"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)


def call_model(model, system_prompt, user_prompt):
    stop_ollama_models()

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

    output = stdout.strip()

    if process.returncode != 0:
        raise Exception(f"Model error: {stderr}")

    log(f"[LLM] Completed {model}")

    return extract_json(output)
