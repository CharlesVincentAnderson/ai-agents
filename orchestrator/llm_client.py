import subprocess
import json
import re
import time

from orchestrator.logger import log


def deep_unescape(obj):
    """
    Recursively convert JSON-escaped sequences into real characters.
    This fixes '\\n' -> '\n' inside patch strings.
    """

    if isinstance(obj, str):
        return obj.encode("utf-8").decode("unicode_escape")

    if isinstance(obj, list):
        return [deep_unescape(x) for x in obj]

    if isinstance(obj, dict):
        return {k: deep_unescape(v) for k, v in obj.items()}

    return obj


def repair_multiline_strings(text):
    pattern = r'"content":\s*"([\s\S]*?)"(?=\s*[\},])'

    def repl(match):
        inner = match.group(1)

        inner = inner.replace("\\", "\\\\")
        inner = inner.replace("\n", "\\n")
        inner = inner.replace("\r", "")
        inner = inner.replace("\t", "\\t")
        inner = inner.replace('"', '\\"')

        return f'"content": "{inner}"'

    return re.sub(pattern, repl, text)


def extract_json(text):
    text = text.strip()

    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    text = re.sub(r"^\s*json\s*", "", text, flags=re.IGNORECASE)

    text = text.strip()

    text = repair_multiline_strings(text)

    try:
        parsed = json.loads(text)
        return deep_unescape(parsed)
    except Exception:
        pass

    object_match = re.search(r"\{.*\}", text, re.DOTALL)

    if object_match:
        candidate = repair_multiline_strings(object_match.group(0))
        parsed = json.loads(candidate)
        return deep_unescape(parsed)

    raise ValueError(f"Failed to parse JSON:\n{text}")


def stop_ollama_models():
    subprocess.run(
        ["ollama", "stop", "all"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)


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

    if output:
        print(output)

    if process.returncode != 0:
        raise Exception(f"Model error: {stderr}")

    log(f"[LLM] Completed {model}")

    return extract_json(output)
