import os
import shutil
import tempfile


def create_temp_workspace(source_workspace):
    temp_root = os.path.join("workspace", "temp")

    os.makedirs(temp_root, exist_ok=True)

    temp_dir = tempfile.mkdtemp(dir=temp_root)

    for item in os.listdir(source_workspace):
        src = os.path.join(source_workspace, item)
        dst = os.path.join(temp_dir, item)

        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    return temp_dir


def cleanup_temp_workspace(path):
    if os.path.exists(path):
        shutil.rmtree(path)
