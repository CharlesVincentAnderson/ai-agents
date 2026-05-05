import subprocess

def run_tests():
    result = subprocess.run(
        ["pytest"],
        cwd="workspace/project",
        capture_output=True,
        text=True
    )

    return {
        "passed": result.returncode == 0,
        "output": result.stdout + result.stderr
    }
