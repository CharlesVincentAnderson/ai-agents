import os
import subprocess
import time

from agents.manager import generate_plan
from agents.developer import implement
from agents.reviewer import review

from orchestrator.test_runner import run_tests
from orchestrator.logger import log
from orchestrator.config import MAX_RETRIES

WORKSPACE = "workspace/project"


def normalize_content(content):
    if not isinstance(content, str):
        return content

    try:
        return content.encode("utf-8").decode("unicode_escape")
    except Exception:
        return content

def resolve_safe_path(base, path):
    joined = os.path.join(base, path)
    real = os.path.realpath(joined)

    base_real = os.path.realpath(base)

    if not real.startswith(base_real):
        raise Exception(f"Blocked path escape: {path}")

    return real


def git_commit(message):
    subprocess.run(["git", "add", "."], cwd=WORKSPACE)
    subprocess.run(["git", "commit", "-m", message], cwd=WORKSPACE)


# ---------------------------
# VALIDATION
# ---------------------------

def validate_plan(tasks):
    if not isinstance(tasks, list) or not tasks:
        raise Exception("Manager returned invalid or empty task list")

    for task in tasks:
        files = task.get("files", [])
        criteria = task.get("acceptance_criteria", [])
        desc = task.get("description", "")

        combined = " ".join(criteria) + " " + desc

        # enforce exact file
        for f in files:
            if f != "app.py":
                raise Exception(f"Manager violated file constraint: {f}")

        # enforce correct function name
        if "hello_world" in combined:
            raise Exception("Manager used wrong function name")

        # enforce no print behavior
        if "print" in combined.lower():
            raise Exception("Manager introduced print behavior")

        # enforce exact casing
        if "Hello, World!" in combined:
            raise Exception("Manager used wrong casing")


def validate_change(task, change):
    file_path = change.get("file")
    content = change.get("content")

    if file_path == "workspace/project/app.py":
        file_path = "app.py"
        change["file"] = "app.py"

    if not file_path or not isinstance(file_path, str):
        raise Exception("Invalid file path in change")

    if file_path not in task["files"]:
        raise Exception(f"Unauthorized file change: {file_path}")

    if not isinstance(content, str) or not content.strip():
        raise Exception(f"Empty or invalid content for {file_path}")

    # convert escaped newlines into real newlines
    content = normalize_content(content)
    change["content"] = content

    if "print(" in content:
        raise Exception("Do not use print()")

    if "def hello(" not in content:
        raise Exception("Missing hello() function")

    if 'return "Hello, world!"' not in content and \
       "return 'Hello, world!'" not in content:
        raise Exception("Incorrect return value")

# ---------------------------
# FILE WRITES
# ---------------------------

def apply_changes(changes):
    for change in changes:
        file_path = resolve_safe_path(WORKSPACE, change["file"])

        parent = os.path.dirname(file_path)

        if parent:
            os.makedirs(parent, exist_ok=True)

        content = change["content"].encode("utf-8").decode("unicode_escape")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

# ---------------------------
# PIPELINE
# ---------------------------

def run_pipeline(idea):
    log("Starting pipeline")

    # ---- PLAN ----
    plan = generate_plan(idea)
    tasks = plan.get("tasks", [])

    validate_plan(tasks)

    log(f"Generated plan with {len(tasks)} tasks")

    # ---- TASK LOOP ----
    for task in tasks:
        log(f"\n=== TASK {task['id']}: {task['title']} ===")

        approved = False
        attempts = 0

        while not approved and attempts < MAX_RETRIES:
            attempts += 1

            log(f"Attempt {attempts} - Developer running")

            # ---- IMPLEMENT ----
            try:
                result = implement(task)
            except Exception as e:
                log(f"Developer failed: {e}")
                time.sleep(5)
                continue

            # ---- VALIDATE OUTPUT ----
            log("Validating changes")

            try:
                changes = result.get("changes")

                if not isinstance(changes, list) or not changes:
                    raise Exception("Developer returned no valid changes")

                for change in changes:
                    validate_change(task, change)

            except Exception as e:
                log(f"Validation failed: {e}")
                task["feedback"] = [str(e)]
                time.sleep(5)
                continue

            # ---- REVIEW ----
            log("Reviewing changes")

            try:
                review_result = review(task, result)
            except Exception as e:
                log(f"Reviewer failed: {e}")
                time.sleep(5)
                continue

            if not review_result.get("approved"):
                issues = review_result.get("blocking_issues", [])

                log(f"Rejected: {issues}")

                task["feedback"] = issues

                time.sleep(5)
                continue

            # ---- APPLY FILES ----
            log("Applying changes")

            try:
                apply_changes(result["changes"])
            except Exception as e:
                log(f"Apply failed: {e}")
                task["feedback"] = [str(e)]
                time.sleep(5)
                continue

            # ---- TEST ----
            log("Running tests")

            test_result = run_tests()

            if not test_result["passed"]:
                log("Tests failed")
                log(test_result["output"])

                task["feedback"] = [test_result["output"]]

                time.sleep(5)
                continue

            # ---- COMMIT ----
            log("Committing changes")

            try:
                git_commit(f"Task {task['id']}: {task['title']}")
            except Exception as e:
                log(f"Git commit failed: {e}")

            approved = True

            log("Task completed")

        if not approved:
            log(f"Task {task['id']} failed after {MAX_RETRIES} attempts")
            break

    log("Pipeline finished")
