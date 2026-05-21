import os
import shutil
import tempfile
import subprocess

from orchestrator.logger import log


TEMP_ROOT = os.path.join("workspace", "temp")


def create_temp_workspace(source_workspace: str) -> str:
    """
    Creates a clean git clone of the source workspace.
    This ensures:
    - correct Python import structure
    - correct file layout
    - reproducible test environment
    """

    os.makedirs(TEMP_ROOT, exist_ok=True)

    temp_dir = tempfile.mkdtemp(dir=TEMP_ROOT)

    # Clone the repo instead of copying files
    result = subprocess.run(
        ["git", "clone", source_workspace, temp_dir],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0:
        raise Exception(f"Failed to clone workspace: {result.stderr}")

    log(f"[workspace] created temp clone at {temp_dir}")

    return temp_dir


def cleanup_temp_workspace(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
