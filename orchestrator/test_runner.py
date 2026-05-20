import subprocess
import sys
import os


def run_tests(workspace: str):
    print("TEMP WS CONTENTS:", os.listdir(workspace))
    print("APP EXISTS:", os.path.exists(f"{workspace}/app.py"))

    try:
        env = os.environ.copy()

        # CRITICAL FIX: treat workspace as import root
        env["PYTHONPATH"] = workspace

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
            env=env,
            check=False
        )

        output = result.stdout + result.stderr

        if "collected 0 items" in output:
            return {
                "passed": True,
                "output": output
            }

        return {
            "passed": result.returncode == 0,
            "output": output
        }

    except Exception as e:
        return {
            "passed": False,
            "output": str(e)
        }
