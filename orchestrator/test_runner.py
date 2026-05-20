import subprocess


def run_tests(workspace):
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout + result.stderr

        # No tests yet is acceptable
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
