import os

PROJECT_ROOT = os.path.abspath(".")
WORKSPACE = os.path.abspath("workspace/project")


def resolve_safe_path(base, path):
    joined = os.path.join(base, path)
    real = os.path.realpath(joined)

    if not real.startswith(WORKSPACE):
        raise Exception(f"Blocked path escape: {path}")

    if not real.startswith(PROJECT_ROOT):
        raise Exception(f"Blocked outside project: {path}")

    return real


def apply_changes(changes, allowed_files):
    if len(changes) > 5:
        raise Exception("Too many files modified in one task")

    for change in changes:
        file_path = change["file"]
        content = change["content"]

        # basic path sanity
        if ".." in file_path or file_path.startswith("/"):
            raise Exception(f"Suspicious path: {file_path}")

        # enforce manager-defined scope
        if file_path not in allowed_files:
            raise Exception(f"File not allowed: {file_path}")

        full_path = resolve_safe_path(WORKSPACE, file_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # backup
        if os.path.exists(full_path):
            os.replace(full_path, full_path + ".bak")

        with open(full_path, "w") as f:
            f.write(content)

        print(f"Applied: {full_path}")
