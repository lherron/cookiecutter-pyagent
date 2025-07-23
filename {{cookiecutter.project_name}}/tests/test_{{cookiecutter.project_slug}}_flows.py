#!/usr/bin/env python3
"""
Tests for `{{cookiecutter.project_slug}}` flows module.
"""

import asyncio
import logging
import sys
from unittest.mock import MagicMock, patch

import pytest
from evaitools.config import AppConfig

# Import flows and config
from {{cookiecutter.project_slug}}.flows import {{cookiecutter.project_slug}}_flow

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_flow_loads_successfully() -> None:
    """Test that the flow can be imported and called without errors."""
    assert callable({{cookiecutter.project_slug}}_flow)


@pytest.mark.asyncio
async def test_flow_with_default_config(app_config: AppConfig) -> None:
    """Test that the flow runs with default configuration."""
    # Test the underlying task function directly instead of the full flow
    from {{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow import run_agent_task

    with patch("{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.load_config") as mock_load_config:
        # Set up mock to return app_config fixture
        mock_load_config.return_value = app_config

        # Also mock the agent run to avoid actual execution
        agent_mock = MagicMock()
        agent_mock.run = MagicMock(return_value=asyncio.Future())
        agent_mock.run.return_value.set_result([{"status": "success"}])

        with patch("{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.{{cookiecutter.agent_name}}") as mock_agent_class:
            # Setup agent mock to return our mocked agent
            mock_agent_class.return_value = agent_mock

            # Call the task function directly
            results = await run_agent_task.fn()  # Use .fn to get the unwrapped function

            # Verify flow completed
            assert results is not None
            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0]["status"] == "success"

            # Verify agent was constructed
            mock_agent_class.assert_called_once()
            # Verify agent run was called
            agent_mock.run.assert_called_once()


@pytest.mark.asyncio
async def test_flow_with_custom_config() -> None:
    """Test that the flow runs with a custom configuration path."""
    # Test the underlying task function directly instead of the full flow
    from {{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow import run_agent_task

    with patch("{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.load_config") as mock_load_config:
        # Set up mock for custom config
        mock_config = MagicMock(spec=AppConfig)
        mock_load_config.return_value = mock_config

        # Also mock the agent run to avoid actual execution
        agent_mock = MagicMock()
        agent_mock.run = MagicMock(return_value=asyncio.Future())
        agent_mock.run.return_value.set_result([{"status": "success"}])

        with patch("{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.{{cookiecutter.agent_name}}") as mock_agent_class:
            # Setup agent mock to return our mocked agent
            mock_agent_class.return_value = agent_mock

            # Call with custom config path
            custom_config_path = "custom_config.yaml"
            results = await run_agent_task.fn(config_path=custom_config_path)  # Use .fn to get the unwrapped function

            # Verify config was loaded with custom path
            mock_load_config.assert_called_once_with(config_path=custom_config_path)

            # Verify flow completed
            assert results is not None
            assert isinstance(results, list)

            # Verify agent was constructed with config
            mock_agent_class.assert_called_once_with(config=mock_config)


@pytest.mark.asyncio
async def test_flow_error_handling() -> None:
    """Test that the flow properly handles errors."""
    # Test the underlying task function directly
    from {{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow import run_agent_task

    with patch("{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.{{cookiecutter.agent_name}}") as mock_agent_class:
        # Set up mock to raise an exception
        mock_error = Exception("Test error")
        mock_agent_class.side_effect = mock_error

        # Test the task function directly
        with pytest.raises(Exception) as excinfo:
            await run_agent_task.fn()  # Use .fn to get the unwrapped function

        # Verify the exception is the one we raised
        assert str(excinfo.value) == str(mock_error)
