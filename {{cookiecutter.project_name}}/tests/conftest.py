"""
Common fixtures for testing {{cookiecutter.project_name}}.
"""

import os

import pytest
from evaitools.config import AppConfig, load_config

# Determine the root directory of the project based on conftest.py location
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def test_config_path() -> str:
    """Returns the path to the test configuration file."""
    # Example: Use a dedicated test config or a sample config
    # Adjust path as needed
    return os.path.join(PROJECT_ROOT, "config.yaml")  # Or a dedicated test.yaml


@pytest.fixture(scope="session")
def app_config(test_config_path: str) -> AppConfig:
    """
    Provides an AppConfig instance loaded from the test config file.
    Uses session scope to load only once per test session.
    """
    # You might want to override certain settings using environment variables
    # for testing purposes, e.g., mock API keys
    # os.environ["PREFECT_API_URL"] = "http://mock-prefect-server:4200/api" # Example
    print(f"Loading test configuration from: {test_config_path}")
    return load_config(config_path=test_config_path)


# Add other common fixtures here, e.g., mock clients
# @pytest.fixture
# def mock_llm_client():
#     """Provides a mocked LLM client."""
#     # Replace with your actual mocking logic
#     from unittest.mock import MagicMock
#     mock_client = MagicMock()
#     mock_client.generate_response.return_value = "Mocked LLM response."
#     return mock_client
