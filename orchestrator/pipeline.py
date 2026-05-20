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

    # git apply expects newline at EOF
    if not diff.endswith("\n"):
        diff += "\n"

    return diff

def git_commit(message):
    result = subprocess.run(
        ["git", "add", "."],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0:
        raise Exception(result.stderr)

    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0:
        raise Exception(result.stderr)


def validate_patches(task, patches):
    if not isinstance(patches, list) or len(patches) == 0:
        raise Exception("No patches returned by developer")

    allowed_files = set(task.get("files", []))

    for i, patch in enumerate(patches):
        if not isinstance(patch, dict):
            raise Exception(f"Patch {i} is not an object")

        file_path = patch.get("file")
        diff = patch.get("diff")

        if isinstance(diff, str):
            diff = normalize_patch(diff)
            patch["diff"] = diff

        if not file_path:
            raise Exception(f"Patch {i} missing 'file'")

        if file_path not in allowed_files:
            raise Exception(f"Unauthorized file change: {file_path}")

        if not diff or not isinstance(diff, str):
            raise Exception(
                f"Patch {file_path} missing or invalid 'diff'"
            )

        if len(diff) > 50_000:
            raise Exception(f"Patch too large: {file_path}")

        if not diff.startswith("diff --git "):
            raise Exception(
                f"Patch missing git diff header: {file_path}"
            )

        if "--- " not in diff:
            raise Exception(f"Patch missing source header: {file_path}")

        if "+++ " not in diff:
            raise Exception(f"Patch missing target header: {file_path}")

        if not diff.endswith("\n"):
            raise Exception(f"Patch missing trailing newline: {file_path}")

        if not any(
            line.startswith("@@")
            for line in diff.splitlines()
        ):
            raise Exception(
                f"Patch missing hunk markers: {file_path}"
            )

        lines = diff.splitlines()

        has_change_lines = any(
            line.startswith("+") or line.startswith("-")
            for line in lines
            if not line.startswith("+++")
            and not line.startswith("---")
        )

        if not has_change_lines:
            raise Exception(
                f"Patch contains no actual changes: {file_path}"
            )

        if "\x00" in diff:
            raise Exception(
                f"Patch contains null bytes: {file_path}"
            )


def ensure_clean_workspace():
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False
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

        approved = False
        attempts = 0

        task.setdefault("history", [])

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
                    apply_patch(
                        temp_workspace,
                        patch["diff"]
                    )

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

                # FINAL COMMIT PHASE (single source of truth)
                ensure_clean_workspace()

                for patch in patches:
                    apply_patch(
                        WORKSPACE,
                        patch["diff"]
                    )

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
