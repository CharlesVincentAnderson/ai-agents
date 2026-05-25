import ast
import os



def validate_python_syntax(workspace, required_files):
    for file_path in required_files:
        if not file_path.endswith(".py"):
            continue

        full_path = os.path.join(workspace, file_path)

        if not os.path.exists(full_path):
            continue

        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            ast.parse(source)
        except SyntaxError as e:
            raise Exception(
                f"Syntax error in {file_path}: {e}"
            )

def get_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append(name.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def file_contains_function(file_path, function_name):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == function_name:
                return True

    return False
