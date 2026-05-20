import subprocess

from agents.manager import generate_plan
from agents.developer import implement
from agents.reviewer import review

from orchestrator.test_runner import run_tests
from orchestrator.logger import log

from orchestrator.workspace_utils import (
    create_temp_workspace,
    cleanup_temp_workspace
)

from orchestrator.context_loader import load_file_context
from orchestrator.patcher import apply_patch

from orchestrator.config import MAX_RETRIES


WORKSPACE = "workspace/project"


def normalize_patch(diff: str) -> str:
    diff = diff.encode("utf-8").decode("unicode_escape")

    if not diff.endswith("\n"):
        diff += "\n"

    return diff


def git_commit(message: str):
    subprocess.run(
        ["git", "add", "."],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=True
    )

    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=True
    )


def validate_patches(task, patches):
    if not isinstance(patches, list) or not patches:
        raise Exception("No patches returned by developer")

    allowed_files = set(task.get("files", []))

    for i, patch in enumerate(patches):
        if not isinstance(patch, dict):
            raise Exception(f"Patch {i} is not an object")

        file_path = patch.get("file")
        diff = patch.get("diff")

        if not file_path:
            raise Exception(f"Patch {i} missing 'file'")

        if file_path not in allowed_files:
            raise Exception(f"Unauthorized file change: {file_path}")

        if not isinstance(diff, str):
            raise Exception(f"Patch {file_path} missing or invalid diff")

        diff = normalize_patch(diff)
        patch["diff"] = diff

        if len(diff) > 50_000:
            raise Exception(f"Patch too large: {file_path}")

        if not diff.startswith("diff --git "):
            raise Exception(f"Missing git header: {file_path}")

        if "--- " not in diff or "+++ " not in diff:
            raise Exception(f"Missing file headers: {file_path}")

        if "@@" not in diff:
            raise Exception(f"Missing hunk markers: {file_path}")

        if not any(l.startswith("+") or l.startswith("-")
                   for l in diff.splitlines()
                   if not l.startswith(("+++", "---"))):
            raise Exception(f"Patch has no changes: {file_path}")

        if "\x00" in diff:
            raise Exception(f"Null byte in patch: {file_path}")


def ensure_clean_workspace():
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=True
    )

    if status.stdout.strip():
        raise Exception("Workspace is dirty")


def run_pipeline(idea):
    log("Starting pipeline")

    ensure_clean_workspace()

    plan = generate_plan(idea)
    tasks = plan.get("tasks", [])

    for task in tasks:
        log(f"Running task {task['id']}")

        task.setdefault("history", [])

        approved = False
        attempts = 0

        while attempts < MAX_RETRIES and not approved:
            temp_workspace = None

            try:
                attempts += 1
                log(f"Attempt {attempts}")

                file_context = load_file_context(
                    WORKSPACE,
                    task["files"]
                )

                result = implement(
                    task=task,
                    file_context=file_context
                )

                patches = result.get("patches", [])
                validate_patches(task, patches)

                temp_workspace = create_temp_workspace(WORKSPACE)

                for patch in patches:
                    apply_patch(temp_workspace, patch["diff"])
                    log(f"TEMP WS FILES: {os.listdir(temp_workspace)}")
                    log(f"LOOK FOR APP: {os.path.exists(os.path.join(temp_workspace, 'app.py'))}")

                test_result = run_tests(temp_workspace)

                if not test_result["passed"]:
                    raise Exception(test_result["output"])

                updated_context = load_file_context(
                    temp_workspace,
                    task["files"]
                )

                review_result = review(
                    task=task,
                    patches=patches,
                    test_output=test_result["output"],
                    file_context=updated_context
                )

                if not review_result.get("approved"):
                    raise Exception(
                        str(review_result.get("blocking_issues", []))
                    )

                # FINAL APPLY (source of truth)
                ensure_clean_workspace()

                for patch in patches:
                    apply_patch(WORKSPACE, patch["diff"])

                git_commit(f"Task {task['id']}: {task['title']}")

                approved = True
                log("Task completed")

            except Exception as e:
                log(f"Attempt failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "error": str(e)
                })

                task["feedback"] = [str(e)]

            finally:
                if temp_workspace:
                    cleanup_temp_workspace(temp_workspace)

        if not approved:
            log(f"Task failed after {MAX_RETRIES} attempts")

    log("Pipeline finished")
