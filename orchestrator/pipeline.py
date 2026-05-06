import os
import subprocess

from agents.manager import generate_plan
from agents.developer import implement
from agents.reviewer import review

from orchestrator.diff_gen import generate_diff, get_existing_content
from orchestrator.patch_utils import apply_patch
from orchestrator.test_runner import run_tests
from orchestrator.logger import log
from orchestrator.config import MAX_RETRIES

WORKSPACE = "workspace/project"


def git_commit(message):
    subprocess.run(["git", "add", "."], cwd=WORKSPACE)
    subprocess.run(["git", "commit", "-m", message], cwd=WORKSPACE)


def validate_change(task, change):
    file_path = change.get("file")
    content = change.get("content")

    if not file_path or not isinstance(file_path, str):
        raise Exception("Invalid file path in change")

    if file_path not in task["files"]:
        raise Exception(f"Unauthorized file change: {file_path}")

    if not isinstance(content, str) or not content.strip():
        raise Exception(f"Empty or invalid content for {file_path}")


def build_patches(task, changes):
    patches = []

    for change in changes:
        validate_change(task, change)

        file_path = change["file"]
        new_content = change["content"]

        full_path = os.path.join(WORKSPACE, file_path)
        old_content = get_existing_content(full_path)

        diff = generate_diff(old_content, new_content, file_path)

        if not diff.strip():
            log(f"No changes detected for {file_path}")
            continue

        patches.append(diff)

    return patches


def run_pipeline(idea):
    log("Starting pipeline")

    plan = generate_plan(idea)
    tasks = plan.get("tasks", [])

    log(f"Generated plan with {len(tasks)} tasks")

    for task in tasks:
        log(f"\n=== TASK {task['id']}: {task['title']} ===")

        approved = False
        attempts = 0

        while not approved and attempts < MAX_RETRIES:
            attempts += 1
            log(f"Attempt {attempts} - Developer running")

            try:
                result = implement(task)
            except Exception as e:
                log(f"Developer failed: {e}")
                continue

            log("Reviewing changes")

            try:
                review_result = review(task, result)
            except Exception as e:
                log(f"Reviewer failed: {e}")
                continue

            if not review_result.get("approved"):
                issues = review_result.get("blocking_issues", [])
                log(f"Rejected: {issues}")
                task["feedback"] = issues
                continue

            log("Building patches")

            try:
                patches = build_patches(task, result.get("changes", []))
            except Exception as e:
                log(f"Patch build failed: {e}")
                task["feedback"] = [str(e)]
                continue

            if not patches:
                log("No patches to apply")
                approved = True
                continue

            log("Applying patches")

            try:
                for patch in patches:
                    apply_patch(patch, WORKSPACE)
            except Exception as e:
                log(f"Patch application failed: {e}")
                task["feedback"] = [str(e)]
                continue

            log("Running tests")

            test_result = run_tests()

            if not test_result["passed"]:
                log("Tests failed")
                log(test_result["output"])
                task["feedback"] = [test_result["output"]]
                continue

            log("Committing changes")

            try:
                git_commit(f"Task {task['id']}: {task['title']}")
            except Exception as e:
                log(f"Git commit failed: {e}")
                continue

            approved = True
            log("Task completed")

        if not approved:
            log(f"Task {task['id']} failed after {MAX_RETRIES} attempts")
            break

    log("Pipeline finished")
