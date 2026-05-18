import os


def load_file_context(workspace, files):
    context = {}

    for file_path in files:
        full_path = os.path.join(workspace, file_path)

        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                context[file_path] = f.read()

    return context
