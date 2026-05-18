import subprocess


def run_tests(workspace):
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
            timeout=120
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
