import subprocess
import sys
import os

def run_tests(workspace: str):
    try:
        env = os.environ.copy()

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
                "passed": False,
                "output": (
                    "Pytest collected 0 tests.\n\n"
                    + output
                )
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
