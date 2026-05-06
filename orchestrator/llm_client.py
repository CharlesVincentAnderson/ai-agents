import subprocess
import json
from orchestrator.logger import log


def stop_ollama():
    try:
        subprocess.run(
            ["ollama", "stop", "all"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log("[LLM] Stopped all Ollama models")
    except Exception as e:
        log(f"[LLM] Failed to stop models: {e}")


def call_model(model, system_prompt, user_prompt):
    prompt = f"""<system>
{system_prompt}
</system>

<user>
{user_prompt}
</user>
"""

    # Ensure clean memory before starting
    stop_ollama()

    log(f"[LLM] Running {model} via CLI")

    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True
    )

    output = result.stdout

    if result.returncode != 0:
        err = result.stderr
        stop_ollama()
        raise Exception(f"Model error: {err}")

    print(output)  # show full output after completion

    log(f"[LLM] Completed {model}")

    # Free memory immediately after run
    stop_ollama()

    # Extract JSON safely
    try:
        return json.loads(output)
    except:
        start = output.find("{")
        end = output.rfind("}") + 1
        if start == -1 or end == -1:
            raise Exception("No JSON found in model output")
        return json.loads(output[start:end])
