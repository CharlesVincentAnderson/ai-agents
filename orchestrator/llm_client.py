import subprocess
import json
from orchestrator.logger import log


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
        text=True,
        bufsize=1
    )

    output = ""

    # send prompt
    process.stdin.write(prompt)
    process.stdin.close()

    # stream output
    for line in process.stdout:
        print(line, end="", flush=True)
        output += line

    process.wait()

    if process.returncode != 0:
        err = process.stderr.read()
        raise Exception(f"Model error: {err}")

    log(f"[LLM] Completed {model}")

    # extract JSON
    try:
        return json.loads(output)
    except:
        start = output.find("{")
        end = output.rfind("}") + 1
        return json.loads(output[start:end])
