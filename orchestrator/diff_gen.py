import difflib
import os


def get_existing_content(full_path):
    if not os.path.exists(full_path):
        return ""
    with open(full_path, "r") as f:
        return f.read()


def generate_diff(old_content, new_content, file_path):
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    )

    return "\n".join(diff) + "\n"
