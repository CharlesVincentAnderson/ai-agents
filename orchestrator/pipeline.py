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
    if not patches:
        raise Exception("Developer returned no patches")

    allowed_files = set(task["files"])

    for patch in patches:
        file_path = patch.get("file")
        diff = patch.get("diff")

        if not file_path:
            raise Exception("Patch missing file")

        if file_path not in allowed_files:
            raise Exception(f"Unauthorized file change: {file_path}")

        if not diff or not isinstance(diff, str):
            raise Exception("Invalid diff")

        if diff.count("\n") > 300:
            raise Exception("Patch too large")

        if not diff.startswith("diff --git"):
            raise Exception("Patch missing git diff header")

        if "+++ " not in diff:
            raise Exception("Patch missing target file header")

        if "@@" not in diff:
            raise Exception("Patch missing hunk markers")


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
                continue

            patches = result.get("patches", [])

            try:
                validate_patches(task, patches)

            except Exception as e:
                log(f"Patch validation failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "error": str(e)
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

                test_result = run_tests(temp_workspace)

                if not test_result["passed"]:
                    log("Tests failed")

                    task["latest_test_output"] = test_result["output"]

                    task["history"].append({
                        "attempt": attempts,
                        "test_output": test_result["output"]
                    })

                    task["feedback"] = [
                        test_result["output"]
                    ]

                    continue

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

                    continue

                ensure_clean_workspace()

                for patch in patches:
                    apply_patch(
                        WORKSPACE,
                        patch["diff"]
                    )

                git_commit(
                    f"Task {task['id']}: {task['title']}"
                )

                approved = True

                log("Task completed")

            except Exception as e:
                log(f"Pipeline failure: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "pipeline_error": str(e)
                })

                task["feedback"] = [str(e)]

            finally:
                cleanup_temp_workspace(temp_workspace)

        if not approved:
            log(f"Task failed after {MAX_RETRIES}")

    log("Pipeline finished")
