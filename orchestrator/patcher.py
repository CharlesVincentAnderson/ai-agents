import subprocess
import tempfile
import os

from orchestrator.logger import log


def apply_patch(workspace, diff_text):
    if not diff_text.strip():
        raise Exception("Empty patch")

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(diff_text)
        patch_file = f.name

    try:
        # 1. Validate patch
        check = subprocess.run(
            ["git", "apply", "--check", "--allow-empty", patch_file],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if check.returncode != 0:
            raise Exception(
                f"git apply --check failed:\nSTDOUT:\n{check.stdout}\nSTDERR:\n{check.stderr}"
            )

        # 2. Apply patch
        result = subprocess.run(
            ["git", "apply", "--allow-empty", patch_file],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(
                f"git apply failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        log(f"Patch applied successfully in {workspace}")

    finally:
        os.unlink(patch_file)
