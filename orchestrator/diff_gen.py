import difflib
import os


def get_existing_content(full_path):
    if not os.path.exists(full_path):
        return None

    with open(full_path, "r") as f:
        return f.read()


def generate_diff(old_content, new_content, file_path):
    if old_content is None:
        old_lines = []
        from_file = "/dev/null"
    else:
        old_lines = old_content.splitlines(keepends=True)
        from_file = f"a/{file_path}"

    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=from_file,
            tofile=f"b/{file_path}",
            lineterm=""
        )
    )

    diff = []

    diff.append(
        f"diff --git a/{file_path} b/{file_path}"
    )

    if old_content is None:
        diff.append("new file mode 100644")

    diff.extend(diff_lines)

    return "\n".join(diff) + "\n"
