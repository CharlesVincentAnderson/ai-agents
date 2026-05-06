import json
import os


MODEL_MAP_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "models",
    "model_map.json"
)


with open(MODEL_MAP_PATH, "r") as f:
    MODELS = json.load(f)


def get_model(role: str) -> str:
    return MODELS.get(role)
