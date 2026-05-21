import os


EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "node_modules"
}


def build_repo_index(workspace):
    repo_map = {}

    for root, dirs, files in os.walk(workspace):
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED_DIRS
        ]

        for file_name in files:
            full_path = os.path.join(root, file_name)

            relative_path = os.path.relpath(
                full_path,
                workspace
            )

            try:
                with open(
                    full_path,
                    "r",
                    encoding="utf-8"
                ) as f:
                    content = f.read()

                repo_map[relative_path] = {
                    "size": len(content),
                    "preview": content[:1000]
                }

            except Exception:
                repo_map[relative_path] = {
                    "size": 0,
                    "preview": "[binary-or-unreadable]"
                }

    return repo_map
