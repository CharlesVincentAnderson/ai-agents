import subprocess
import os

from agents.manager import generate_plan
from agents.developer import implement
from agents.reviewer import review

from orchestrator.test_runner import run_tests
from orchestrator.logger import log

from orchestrator.workspace_utils import (
    create_temp_workspace,
    cleanup_temp_workspace
)

from orchestrator.patcher import apply_patch
from orchestrator.diff_gen import (
    generate_diff,
    get_existing_content
)

from orchestrator.config import MAX_RETRIES


WORKSPACE = "workspace/project"


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


def validate_changes(changes):
    if not isinstance(changes, list):
        raise Exception("Changes must be a list")

    if not changes:
        raise Exception("No changes returned")

    if len(changes) > 20:
        raise Exception("Too many modified files")

    for change in changes:
        if not isinstance(change, dict):
            raise Exception("Invalid change object")

        file_path = change.get("file")
        content = change.get("content")

        if not file_path:
            raise Exception("Missing file path")

        if not isinstance(content, str):
            raise Exception(
                f"Invalid content for {file_path}"
            )

        if "\x00" in content:
            raise Exception(
                f"Null byte detected in {file_path}"
            )

def build_patches(workspace, changes):
    patches = []

    for change in changes:
        file_path = change["file"]
        new_content = change["content"]

        full_path = os.path.join(workspace, file_path)

        old_content = get_existing_content(full_path)

        diff = generate_diff(
            old_content=old_content,
            new_content=new_content,
            file_path=file_path
        )

        patches.append({
            "file": file_path,
            "diff": diff
        })

    return patches


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
        task.setdefault("feedback", [])

        approved = False
        attempts = 0

        while attempts < MAX_RETRIES and not approved:
            temp_workspace = None

            try:
                attempts += 1
                log(f"Attempt {attempts}")

                from orchestrator.repo_indexer import (
                    build_repo_index
                )
                from orchestrator.context_selector import (
                    select_relevant_files
                )

                repo_index = build_repo_index(WORKSPACE)

                relevant_files = select_relevant_files(
                    WORKSPACE,
                    repo_index,
                    task["description"]
                )

                result = implement(
                    task=task,
                    repo_index=repo_index,
                    relevant_files=relevant_files
                )

                changes = result.get("changes", [])

                validate_changes(changes)

                patches = build_patches(
                    WORKSPACE,
                    changes
                )

                temp_workspace = create_temp_workspace(WORKSPACE)

                for patch in patches:
                    log("GENERATED PATCH:")
                    log(patch["diff"])

                    apply_patch(temp_workspace, patch["diff"])

                test_result = run_tests(temp_workspace)

                if not test_result["passed"]:
                    raise Exception(test_result["output"])

                updated_context = select_relevant_files(
                    temp_workspace,
                    repo_index,
                    task["description"]
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

                ensure_clean_workspace()

                for patch in patches:
                    log("GENERATED PATCH:")
                    log(patch["diff"])

                    apply_patch(WORKSPACE, patch["diff"])

                git_commit(
                    f"Task {task['id']}: {task['title']}"
                )

                approved = True
                log("Task completed")

            except Exception as e:
                log(f"Attempt failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "error": str(e)
                })

                task["feedback"].append(str(e))

            finally:
                if temp_workspace:
                    cleanup_temp_workspace(temp_workspace)

        if not approved:
            log(f"Task failed after {MAX_RETRIES} attempts")

    log("Pipeline finished")
