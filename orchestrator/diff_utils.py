import os


WORKSPACE = os.path.realpath(
    os.path.abspath("workspace/project")
)


def resolve_safe_path(path):
    """
    Ensures all filesystem access remains
    strictly inside workspace/project.
    """

    candidate = os.path.realpath(
        os.path.join(WORKSPACE, path)
    )

    if not candidate.startswith(WORKSPACE + os.sep):
        raise Exception(
            f"Blocked path escape: {path}"
        )

    return candidate


def validate_relative_path(path):
    if os.path.isabs(path):
        raise Exception(
            f"Absolute paths forbidden: {path}"
        )

    normalized = os.path.normpath(path)

    if normalized.startswith(".."):
        raise Exception(
            f"Parent traversal forbidden: {path}"
        )

    return normalized


def apply_changes(changes):
    for change in changes:
        relative_path = validate_relative_path(
            change["file"]
        )

        full_path = resolve_safe_path(
            relative_path
        )

        parent = os.path.dirname(full_path)

        os.makedirs(parent, exist_ok=True)

        with open(
            full_path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(change["content"])
