from orchestrator.pipeline import run_pipeline
from orchestrator.pipeline import collect_multiline_input

if __name__ == "__main__":
    idea = collect_multiline_input()
    run_pipeline(idea)
