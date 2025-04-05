# {{ cookiecutter.project_name }}

{% for _ in cookiecutter.project_name %}={% endfor %}

{{ cookiecutter.description }}

## Features

*   (Add key features of agents built with this template)
*   Configuration via `config.yaml` and environment variables.
*   CLI powered by Typer.
*   Workflow orchestration with Prefect.
*   Ready for testing with Pytest.
*   Code quality enforced by Ruff and Mypy.

## Installation

```bash
# Clone your generated project repository
# git clone ...
# cd your-project-name

# Recommended: Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate # On Windows use `.venv\Scripts\activate`

# Install the package with development dependencies
pip install -e ".[dev]"
```

## Quick Start

1.  Copy `config.yaml.sample` to `config.yaml`.
2.  Edit `config.yaml` with your specific settings (API keys, etc.). Alternatively, set corresponding environment variables (see `src/{{cookiecutter.project_slug}}/config.py` for details).
3.  Run the agent:
    ```bash
    {{cookiecutter.project_slug}} run --config config.yaml
    ```
    Or to see options:
    ```bash
    {{cookiecutter.project_slug}} --help
    ```

## Configuration

Configuration is managed via:
1.  A `config.yaml` file (recommended). See `config.yaml.sample`.
2.  Environment variables (override values from the file). Refer to `src/{{cookiecutter.project_slug}}/config.py` for variable names and structure.

Key configuration sections often include:
*   `prefect`: For scheduling and workflow management.
*   `llm`: (Optional) For configuring Large Language Models like Anthropic or Gemini.
*   *(Add sections for any other default service integrations)*

## Development

### Setup

Ensure you have installed development dependencies:
```bash
pip install -e ".[dev]"
```

### Running Tools

*   **Linting:** `ruff check .`
*   **Formatting:** `ruff format .`
*   **Type Checking:** `mypy src`
*   **Testing:** `pytest` or `python -m pytest`
    *   Verbose tests: `pytest -v`
    *   Tests with coverage: `pytest --cov={{cookiecutter.project_slug}} tests/`

*(Optional: Link to DEVELOPMENT.md if created)*
*   See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for more detailed guidelines.

## Project Structure

```
{{cookiecutter.project_name}}/
├── config.yaml.sample      # Sample configuration file
├── docs/                   # Documentation (like DEVELOPMENT.md)
├── scripts/                # Utility scripts
├── src/
│   └── {{cookiecutter.project_slug}}/
│       ├── cli/            # Command Line Interface (Typer)
│       ├── flows/          # Prefect flows and tasks
│       ├── util/           # Utility modules (e.g., http_logging)
│       ├── config.py       # Pydantic configuration models
│       └── ...             # Core agent logic modules
├── tests/                  # Pytest tests
├── .gitignore
├── .env.sample             # Sample environment variables (optional)
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # This file
```
