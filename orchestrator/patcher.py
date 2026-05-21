import subprocess
import tempfile
import os

from orchestrator.logger import log


def apply_patch(workspace, diff_text):
    if not diff_text.strip():
        raise Exception("Empty patch")

    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False
    ) as f:
        f.write(diff_text)

        # Ensure trailing newline
        if not diff_text.endswith("\n"):
            f.write("\n")

        patch_file = f.name

    try:
        # Validate patch first
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
                "git apply --check failed:\n"
                f"STDOUT:\n{check.stdout}\n"
                f"STDERR:\n{check.stderr}"
            )

        # Apply patch
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
                "git apply failed:\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        # VERIFY filesystem changed
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False
        )

        log(f"GIT STATUS AFTER PATCH:\n{status.stdout}")

        # Extra safety:
        # fail if patch produced no filesystem changes
        if not status.stdout.strip():
            raise Exception(
                "Patch applied cleanly but produced no file changes"
            )

        log(f"Patch applied successfully in {workspace}")

    finally:
        os.unlink(patch_file)
