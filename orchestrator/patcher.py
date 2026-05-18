import subprocess
import tempfile
import os


def apply_patch(workspace, diff_text):
    if not diff_text.strip():
        raise Exception("Empty patch")

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(diff_text)
        patch_file = f.name

    try:
        result = subprocess.run(
            ["git", "apply", "--check", "--allow-empty", patch_file],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

        result = subprocess.run(
            ["git", "apply", patch_file],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

    finally:
        os.unlink(patch_file)
