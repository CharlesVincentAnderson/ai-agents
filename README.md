# AI Agents

An autonomous multi-agent software development system that can plan, implement, test, review, and commit code changes from a natural language specification.

**Status:** Early-stage personal project.

This project is currently being developed and maintained by a single author. The architecture, workflows, prompts, and interfaces may change significantly between versions.

Issues and pull requests may not receive a response, but the project is available under the Apache 2.0 license for anyone who wishes to study, use, or fork it.

---

## Overview

AI Agents uses multiple specialized AI roles to collaborate on software development tasks:

* **Manager Agent** – Analyzes requirements and creates an implementation plan.
* **Developer Agent** – Generates code changes for each task.
* **Reviewer Agent** – Reviews generated code and provides approval or feedback.
* **Pipeline Orchestrator** – Coordinates planning, implementation, testing, validation, review, and commits.

The system is designed to automate common software engineering workflows while maintaining quality controls through testing and review.

---

## Features

### Multi-Agent Development Workflow

* Requirement analysis and task planning
* Automated code generation
* AI-powered code review
* Retry-based task execution
* Feedback loop between agents

### Validation and Safety

* Python syntax validation
* Required file validation
* Duplicate function detection
* Path traversal protection
* File modification restrictions
* Temporary workspace testing before applying changes

### Automated Testing

* Runs project tests before applying changes
* Blocks failing implementations
* Supports iterative retries when tests fail

### Git Integration

* Patch-based code application
* Automatic commits for completed tasks
* Workspace cleanliness verification
* Diff generation and review

### Repository Awareness

* Repository indexing
* Context-aware file selection
* Relevant file retrieval for implementation tasks

---

## Architecture

```text
User Request
      |
      v
 Manager Agent
      |
      v
 Developer Agent
      |
      v
 Temporary Workspace
      |
      +--> Validation
      +--> Syntax Checks
      +--> Test Execution
      |
      v
 Reviewer Agent
      |
      v
 Apply Approved Changes
      |
      v
 Git Commit
```

---

## Project Structure

```text
ai-agents/
├── agents/
│   ├── manager.py
│   ├── developer.py
│   └── reviewer.py
│
├── orchestrator/
│   ├── main.py
│   ├── pipeline.py
│   ├── patcher.py
│   ├── diff_gen.py
│   ├── test_runner.py
│   ├── workspace_utils.py
│   └── ...
│
├── workspace/
│   └── project/
│
├── tests/
│
└── .venv/
```

---

## Requirements

* Python 3.11+
* Git
* Ollama
* One or more local language models installed in Ollama

Example models:

* mistral-small:24b
* deepseek-coder-v2:16b

---

## Installation

### Clone the Repository

```bash
git clone <repository-url>
cd ai-agents
```

### Create a Virtual Environment

```bash
python -m venv .venv
```

### Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Verify Ollama Installation

```bash
ollama list
```

Ensure the models referenced by your configuration are installed and available.

---

## Usage

### Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### Start the Application

```bash
python -m orchestrator.main
```

You will see:

```text
Describe your app (finish with EOF / Ctrl-D):
```

Enter your requirements over one or more lines.

Example:

```text
Create a simple calculator library.

Requirements:
- Create calculator.py containing:
  - add(a, b)
  - subtract(a, b)
  - multiply(a, b)
  - divide(a, b)

- Create app.py exposing:
  - calculate(operation, a, b)

- Create pytest tests
```

### Finishing Input

When you have finished entering requirements:

* **Linux/macOS:** Press `Ctrl-D` on a blank line
* **Windows:** Press `Ctrl-Z` then Enter

The pipeline will then begin processing your request.

### What Happens Next

The system will:

1. Generate a development plan
2. Break work into tasks
3. Generate code changes
4. Apply changes in a temporary workspace
5. Run validation checks
6. Execute tests
7. Perform AI code review
8. Apply approved patches
9. Commit completed work to git

---

## Configuration

Application settings can be adjusted in:

```text
orchestrator/config.py
```

Examples include:

* Maximum retry count
* Model selection
* Workspace settings
* Execution limits

---

## Logging

The pipeline logs major events including:

* User requests
* Generated plans
* Task execution
* Generated patches
* Validation results
* Test output
* Review decisions
* Commit operations

These logs help diagnose failures and improve agent behavior.

---

## Safety Mechanisms

The system includes several safeguards:

* Rejects path traversal attempts
* Rejects absolute file paths
* Validates generated file content
* Detects duplicate function definitions
* Runs tests before applying changes
* Uses temporary workspaces for validation
* Prevents commits when the workspace is dirty

---

## Known Limitations

* Output quality depends on the selected models.
* Large prompts may increase processing time.
* Planning quality varies across models.
* Complex projects may require multiple retries.
* Some validation logic relies on heuristics.

---

## Future Improvements

* Parallel task execution
* Smarter repository indexing
* Improved context selection
* Enhanced review capabilities
* Better acceptance-criteria validation
* Support for additional programming languages
* Performance optimizations

---

## Disclaimer

This software is experimental. Generated code should be reviewed by a human before use in production environments.

---

## License

This project is licensed under the Apache License 2.0.

### Apache License 2.0 Summary

You are free to:

* Use the software commercially
* Modify the software
* Distribute the software
* Use the software privately

Under the following conditions:

* Include the license and copyright notice
* State significant changes made to the software

The license also provides an explicit patent grant from contributors.

For the full license text, see the `LICENSE` file.

Copyright 2026 Charles Anderson

Licensed under the Apache License, Version 2.0.

