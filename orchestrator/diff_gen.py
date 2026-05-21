import difflib
import os


def get_existing_content(full_path):
    if not os.path.exists(full_path):
        return None

    with open(full_path, "r") as f:
        return f.read()
def generate_diff(old_content, new_content, file_path):
    import tempfile
    import subprocess
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        old_path = os.path.join(tmpdir, "old")
        new_path = os.path.join(tmpdir, "new")

        # Only create old file if it actually existed
        if old_content is not None:
            with open(old_path, "w") as f:
                f.write(old_content)

            old_arg = old_path

        else:
            # nonexistent file -> proper new-file diff
            old_arg = "/dev/null"

        with open(new_path, "w") as f:
            f.write(new_content)

        result = subprocess.run(
            [
                "git",
                "diff",
                "--no-index",
                "--",
                old_arg,
                new_path
            ],
            capture_output=True,
            text=True
        )

        diff = result.stdout

        diff = diff.replace(
            old_path,
            f"a/{file_path}"
        )

        diff = diff.replace(
            new_path,
            f"b/{file_path}"
        )

        # Fix /dev/null new file header
        diff = diff.replace(
            "--- /dev/null",
            "--- /dev/null"
        )

        return diff
