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
            raise Exception(
                f"Patch missing source header: {file_path}"
            )

        if "+++ " not in diff:
            raise Exception(
                f"Patch missing target header: {file_path}"
            )

        if "@@" not in diff:
            raise Exception(
                f"Patch missing hunk markers: {file_path}"
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

        while not approved and attempts < MAX_RETRIES:
            attempts += 1

            log(f"Attempt {attempts}")

            file_context = load_file_context(
                WORKSPACE,
                task["files"]
            )

            try:
                result = implement(
                    task=task,
                    file_context=file_context
                )

            except Exception as e:
                log(f"Developer failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "developer_error": str(e)
                })

                task["feedback"] = [str(e)]

                continue

            patches = result.get("patches", [])

            try:
                validate_patches(task, patches)

            except Exception as e:
                log(f"Patch validation failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "validation_error": str(e)
                })

                task["feedback"] = [str(e)]

                continue

            temp_workspace = create_temp_workspace(WORKSPACE)

            try:
                for patch in patches:
                    apply_patch(
                        temp_workspace,
                        patch["diff"]
                    )

            except Exception as e:
                log(f"Patch apply failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "patch_apply_error": str(e)
                })

                task["feedback"] = [
                    f"Patch failed to apply:\n{e}"
                ]

                cleanup_temp_workspace(temp_workspace)

                continue

            try:
                test_result = run_tests(temp_workspace)

            except Exception as e:
                log(f"Test runner failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "test_runner_error": str(e)
                })

                task["feedback"] = [str(e)]

                cleanup_temp_workspace(temp_workspace)

                continue

            if not test_result["passed"]:
                log("Tests failed")

                task["history"].append({
                    "attempt": attempts,
                    "test_output": test_result["output"]
                })

                task["feedback"] = [
                    test_result["output"]
                ]

                cleanup_temp_workspace(temp_workspace)

                continue

            updated_context = load_file_context(
                temp_workspace,
                task["files"]
            )

            try:
                review_result = review(
                    task=task,
                    patches=patches,
                    test_output=test_result["output"],
                    file_context=updated_context
                )

            except Exception as e:
                log(f"Reviewer failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "reviewer_error": str(e)
                })

                task["feedback"] = [str(e)]

                cleanup_temp_workspace(temp_workspace)

                continue

            if not review_result.get("approved"):
                issues = review_result.get(
                    "blocking_issues",
                    []
                )

                log(f"Reviewer rejected: {issues}")

                task["history"].append({
                    "attempt": attempts,
                    "reviewer_feedback": issues
                })

                task["feedback"] = issues

                cleanup_temp_workspace(temp_workspace)

                continue

            try:
                ensure_clean_workspace()

                for patch in patches:
                    apply_patch(
                        WORKSPACE,
                        patch["diff"]
                    )

                git_commit(
                    f"Task {task['id']}: {task['title']}"
                )

            except Exception as e:
                log(f"Final apply failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "final_apply_error": str(e)
                })

                task["feedback"] = [str(e)]

                cleanup_temp_workspace(temp_workspace)

                continue

            cleanup_temp_workspace(temp_workspace)

            approved = True

            log("Task completed")

        if not approved:
            log(
                f"Task failed after {MAX_RETRIES} attempts"
            )

    log("Pipeline finished")
