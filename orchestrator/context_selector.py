import os


MAX_FILE_SIZE = 30000


def select_relevant_files(
    workspace,
    repo_index,
    task_description
):
    relevant = {}

    keywords = set(
        task_description.lower().split()
    )

    for relative_path in repo_index:
        filename = relative_path.lower()

        if any(
            keyword in filename
            for keyword in keywords
        ):
            full_path = os.path.join(
                workspace,
                relative_path
            )

            try:
                with open(
                    full_path,
                    "r",
                    encoding="utf-8"
                ) as f:
                    content = f.read()

                if len(content) <= MAX_FILE_SIZE:
                    relevant[relative_path] = content

            except Exception:
                pass

    return relevant
