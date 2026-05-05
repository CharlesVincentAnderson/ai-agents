from agents.manager import generate_plan
from agents.developer import implement
from agents.reviewer import review
from orchestrator.patch_utils import apply_patch
from orchestrator.test_runner import run_tests
from orchestrator.logger import log
from orchestrator.config import MAX_RETRIES

import subprocess

REPO_DIR = "workspace/project"


def git_commit(message):
    subprocess.run(["git", "add", "."], cwd=REPO_DIR)
    subprocess.run(["git", "commit", "-m", message], cwd=REPO_DIR)


def run_pipeline(idea):
    log("Starting pipeline")

    plan = generate_plan(idea)
    log(f"Generated plan with {len(plan['tasks'])} tasks")

    for task in plan["tasks"]:
        log(f"Starting task {task['id']}: {task['title']}")

        approved = False
        attempts = 0

        while not approved and attempts < MAX_RETRIES:
            log(f"Attempt {attempts+1} - Developer running")

            result = implement(task)

            log("Reviewing changes")
            review_result = review(task, result)

            if not review_result["approved"]:
                log(f"Rejected: {review_result['blocking_issues']}")
                task["feedback"] = review_result["blocking_issues"]
                attempts += 1
                continue

            log("Applying patch")

            try:
                for change in result["changes"]:
                    apply_patch(change["diff"], REPO_DIR)
            except Exception as e:
                log(f"Patch failed: {e}")
                attempts += 1
                continue

            log("Running tests")
            test_result = run_tests()

            if not test_result["passed"]:
                log("Tests failed")
                task["feedback"] = [test_result["output"]]
                attempts += 1
                continue

            log("Committing changes")
            git_commit(f"Task {task['id']}: {task['title']}")

            approved = True
            log("Task completed")

        if not approved:
            log(f"Task {task['id']} failed after retries")
            break

    log("Pipeline finished")
