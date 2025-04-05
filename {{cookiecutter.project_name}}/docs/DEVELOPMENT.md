# Development Guidelines for {{cookiecutter.project_name}}

This document outlines best practices, tools, and conventions for developing with this project.

## Development Environment Setup

1. Ensure you have Python 3.10+ installed
2. Clone the repository
3. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install the package with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Code Quality Tools

This project uses several tools to ensure code quality:

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used for fast Python linting and formatting.

Commands:
- Check code: `ruff check .`
- Format code: `ruff format .`

### MyPy

[MyPy](http://mypy-lang.org/) is used for static type checking.

Commands:
- Run type checking: `mypy src`

### Pytest

[Pytest](https://docs.pytest.org/) is used for testing.

Commands:
- Run all tests: `pytest`
- Run with coverage: `pytest --cov={{cookiecutter.project_slug}} tests/`
- Run specific test: `pytest tests/test_specific.py::test_function`
- Run tests marked as integration: `pytest -m integration`

## Coding Conventions

### Imports

- Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Within each group, sort imports alphabetically
- Use absolute imports for clarity

### Type Annotations

- Add type annotations to all function parameters and return values
- Use type aliases for complex types
- Use `Optional[Type]` for parameters that can be None

### Documentation

- Use docstrings for all public modules, classes, and functions
- Follow the [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings
- Keep comments up-to-date

### Error Handling

- Use specific exception types rather than catching general `Exception`
- Add context to raised exceptions with informative messages
- Log exceptions appropriately

## Working with Prefect Flows

- Keep flows and tasks in the `flows` directory
- Use `async` for Prefect flows and tasks when possible
- Configure appropriate logging in each flow
- Add descriptive names to tasks and flows
- Use Prefect's built-in retries for resilience

## Configuration Management

- Never hardcode secrets or environment-specific values
- Use the `config.py` module to define configuration
- Document all configuration options in both the code and README

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the conventions above
3. Run all quality checks (`ruff`, `mypy`, `pytest`)
4. Submit a PR with a clear description of the changes
5. Ensure all CI checks pass

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with the new version and changes
3. Tag the release in git
4. Build and publish to PyPI (if applicable) 