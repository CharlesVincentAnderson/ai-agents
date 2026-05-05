import subprocess
import tempfile
import os
from orchestrator.logger import log


def apply_patch(diff_text, repo_dir):
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
        f.write(diff_text)
        patch_file = f.name

    try:
        result = subprocess.run(
            ["patch", "-p1", "-i", patch_file],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            log(result.stderr)
            raise Exception("Patch failed")

        log("Patch applied successfully")

    finally:
        os.remove(patch_file)
