#!/usr/bin/env python3
"""
Tests for `{{cookiecutter.project_slug}}` flows module.
"""

import os
import sys
import logging
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import flows and config
from {{cookiecutter.project_slug}}.flows import {{cookiecutter.project_slug}}_flow
from {{cookiecutter.project_slug}}.config import load_config, AppConfig

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_flow_loads_successfully():
    """Test that the flow can be imported and called without errors."""
    assert callable({{cookiecutter.project_slug}}_flow)

@pytest.mark.asyncio
async def test_flow_with_default_config(app_config):
    """Test that the flow runs with default configuration."""
    with patch('{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.load_config') as mock_load_config:
        # Set up mock to return app_config fixture
        mock_load_config.return_value = app_config
        
        # Also mock the agent run to avoid actual execution
        agent_mock = MagicMock()
        agent_mock.run = MagicMock(return_value=asyncio.Future())
        agent_mock.run.return_value.set_result([{"status": "success"}])
        
        with patch('{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.{{cookiecutter.agent_name}}') as mock_agent_class:
            # Setup agent mock to return our mocked agent
            mock_agent_class.return_value = agent_mock
            
            # Run the flow
            results = await {{cookiecutter.project_slug}}_flow()
            
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
async def test_flow_with_custom_config():
    """Test that the flow runs with a custom configuration path."""
    with patch('{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.load_config') as mock_load_config:
        # Set up mock for custom config
        mock_config = MagicMock(spec=AppConfig)
        mock_load_config.return_value = mock_config
        
        # Also mock the agent run to avoid actual execution
        agent_mock = MagicMock()
        agent_mock.run = MagicMock(return_value=asyncio.Future())
        agent_mock.run.return_value.set_result([{"status": "success"}])
        
        with patch('{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.{{cookiecutter.agent_name}}') as mock_agent_class:
            # Setup agent mock to return our mocked agent
            mock_agent_class.return_value = agent_mock
            
            # Run the flow with custom config path
            custom_config_path = "custom_config.yaml"
            results = await {{cookiecutter.project_slug}}_flow(config_path=custom_config_path)
            
            # Verify config was loaded with custom path
            mock_load_config.assert_called_once_with(config_path=custom_config_path)
            
            # Verify flow completed
            assert results is not None
            assert isinstance(results, list)
            
            # Verify agent was constructed with config
            mock_agent_class.assert_called_once_with(config=mock_config)

@pytest.mark.asyncio
async def test_flow_error_handling():
    """Test that the flow properly handles errors."""
    with patch('{{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow.run_agent_task') as mock_run_task:
        # Set up mock to raise an exception
        mock_error = Exception("Test error")
        mock_run_task.side_effect = mock_error
        
        # Run the flow and expect it to raise the exception
        with pytest.raises(Exception) as excinfo:
            await {{cookiecutter.project_slug}}_flow()
        
        # Verify the exception is the one we raised
        assert str(excinfo.value) == str(mock_error) 