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

    with tempfile.TemporaryDirectory() as tmpdir:
        old_path = os.path.join(tmpdir, "old")
        new_path = os.path.join(tmpdir, "new")

        if old_content is not None:
            with open(old_path, "w") as f:
                f.write(old_content)
        else:
            open(old_path, "w").close()

        with open(new_path, "w") as f:
            f.write(new_content)

        result = subprocess.run(
            [
                "git",
                "diff",
                "--no-index",
                "--",
                old_path,
                new_path
            ],
            capture_output=True,
            text=True
        )

        diff = result.stdout

        old_label = f"a/{file_path}"
        new_label = f"b/{file_path}"

        diff = diff.replace(old_path, old_label)
        diff = diff.replace(new_path, new_label)

        return diff
