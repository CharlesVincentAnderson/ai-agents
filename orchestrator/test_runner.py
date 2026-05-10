import subprocess
from orchestrator.logger import log

WORKSPACE = "workspace/project"


def run_tests():
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True
        )

        return {
            "passed": result.returncode == 0,
            "output": result.stdout + result.stderr
        }

    except Exception as e:
        return {
            "passed": False,
            "output": str(e)
        }
