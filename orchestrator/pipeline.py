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
from orchestrator.static_checks import (
    validate_python_syntax
)

WORKSPACE = "workspace/project"


def collect_multiline_input():
    print("Describe your app (finish with EOF / Ctrl-D):")

    lines = []

    try:
        while True:
            line = input()
            print(f"[debug] received line: {line}")
            lines.append(line)

    except EOFError:
        print("[debug] EOF received")

    result = "\n".join(lines)

    print("[debug] final input collected")
    print(result)

    return result

def detect_duplicate_function_signatures(changes):
    signatures = {}

    for change in changes:
        content = change.get("content", "")
        file_path = change.get("file", "")

        # naive but effective heuristic
        for line in content.splitlines():
            if line.strip().startswith("def "):
                func_name = (
                    line.split("(")[0]
                    .replace("def ", "")
                    .strip()
                )

                if func_name in signatures:
                    raise Exception(
                        f"Duplicate function '{func_name}' found in "
                        f"{signatures[func_name]} and {file_path}"
                    )

                signatures[func_name] = file_path


def validate_required_files(
    workspace,
    required_files
):
    missing = []

    for file_path in required_files:
        full_path = os.path.join(
            workspace,
            file_path
        )

        if not os.path.exists(full_path):
            missing.append(file_path)

    if missing:
        raise Exception(
            "Missing required files: "
            + ", ".join(missing)
        )


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


def validate_changes(changes, required_files):
    if not isinstance(changes, list):
        raise Exception("Changes must be a list")

    if not changes:
        raise Exception("No changes returned")

    if len(changes) > 20:
        raise Exception("Too many modified files")

    required_set = set(required_files)

    for change in changes:
        if not isinstance(change, dict):
            raise Exception("Invalid change object")

        file_path = change.get("file")
        content = change.get("content")

        if not file_path:
            raise Exception("Missing file path")

        # enforce allowed files
        if required_files and file_path not in required_set:
            raise Exception(
                f"Unauthorized file modification: {file_path}"
            )

        # security checks
        if ".." in file_path:
            raise Exception(
                f"Path traversal detected: {file_path}"
            )

        if os.path.isabs(file_path):
            raise Exception(
                f"Absolute path detected: {file_path}"
            )

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

        full_path = os.path.join(
            workspace,
            file_path
        )

        old_content = get_existing_content(
            full_path
        )

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

    log("RAW USER REQUEST:")
    log(idea)

    log("Calling generate_plan()")
    plan = generate_plan(idea)
    log("generate_plan() returned")

    log("PLAN AFTER VALIDATION:")
    log(str(plan))

    log("FULL PLAN:")
    log(str(plan))

    tasks = plan.get("tasks", [])

    for task in tasks:
        log(f"Running task {task['id']}")

        log(
            "TASK REQUIRED FILES: "
            + str(task.get("required_files", []))
        )

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

                repo_index = build_repo_index(
                    WORKSPACE
                )

                required_files = task.get(
                    "required_files",
                    []
                )

                if not required_files:
                    raise Exception(
                        "Task missing required_files"
                    )

                log(
                    "PIPELINE REQUIRED FILES: "
                    + str(required_files)
                )

                relevant_files = select_relevant_files(
                    WORKSPACE,
                    repo_index,
                    task["description"]
                )

                if relevant_files is None:
                    relevant_files = {}

                for file_path in required_files:
                    if file_path not in relevant_files:
                        full_path = os.path.join(
                            WORKSPACE,
                            file_path
                        )

                        if os.path.exists(full_path):
                            try:
                                with open(
                                    full_path,
                                    "r",
                                    encoding="utf-8"
                                ) as f:
                                    relevant_files[file_path] = (
                                        f.read()
                                    )

                            except Exception:
                                relevant_files[file_path] = ""

                        else:
                            relevant_files[file_path] = ""

                result = implement(
                    task=task,
                    repo_index=repo_index,
                    relevant_files=relevant_files,
                    required_files=required_files
                )

                changes = result.get(
                    "changes",
                    []
                )

                log(
                    "DEVELOPER RETURNED FILES: "
                    + str([
                        c.get("file")
                        for c in changes
                    ])
                )

                detect_duplicate_function_signatures(
                    changes
                )

                validate_changes(
                    changes,
                    required_files
                )

                patches = build_patches(
                    WORKSPACE,
                    changes
                )

                temp_workspace = create_temp_workspace(
                    WORKSPACE
                )

                for patch in patches:
                    log("GENERATED PATCH:")
                    log(patch["diff"])

                    apply_patch(
                        temp_workspace,
                        patch["diff"]
                    )

                validate_required_files(
                    temp_workspace,
                    required_files
                )

                validate_python_syntax(
                    temp_workspace,
                    required_files
                )

                test_result = run_tests(
                    temp_workspace
                )

                if not test_result["passed"]:
                    raise Exception(
                        test_result["output"]
                    )

                updated_repo_index = build_repo_index(
                    temp_workspace
                )

                updated_context = (
                    select_relevant_files(
                        temp_workspace,
                        updated_repo_index,
                        task["description"]
                    )
                )

                review_result = review(
                    task=task,
                    patches=patches,
                    test_output=test_result["output"],
                    file_context=updated_context
                )

                if not review_result.get("approved"):
                    raise Exception(
                        str(
                            review_result.get(
                                "blocking_issues",
                                []
                            )
                        )
                    )

                ensure_clean_workspace()

                for patch in patches:
                    apply_patch(
                        WORKSPACE,
                        patch["diff"]
                    )

                git_commit(
                    f"Task {task['id']}: "
                    f"{task['title']}"
                )

                approved = True

                log("Task completed")

            except Exception as e:
                log(f"Attempt failed: {e}")

                task["history"].append({
                    "attempt": attempts,
                    "error": str(e)
                })

                task["feedback"].append(
                    str(e)
                )

            finally:
                if temp_workspace:
                    cleanup_temp_workspace(
                        temp_workspace
                    )

        if not approved:
            log(
                f"Task failed after "
                f"{MAX_RETRIES} attempts"
            )

    log("Pipeline finished")
