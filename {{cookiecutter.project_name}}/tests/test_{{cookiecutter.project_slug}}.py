#!/usr/bin/env python

"""Tests for `{{ cookiecutter.project_slug }}` package."""

import pytest
from {{cookiecutter.project_slug}}.config import AppConfig

# Example test using the app_config fixture from conftest.py
def test_config_loading(app_config: AppConfig):
    """Test that the AppConfig fixture loads correctly."""
    assert app_config is not None
    assert isinstance(app_config, AppConfig)
    # Add more specific assertions about the loaded config if needed
    assert app_config.prefect is not None
    assert app_config.prefect.project_name == "{{cookiecutter.project_slug}}" # Check default

# Placeholder test function
def test_placeholder():
    """A basic placeholder test."""
    assert True

# Example async test (requires pytest-asyncio)
@pytest.mark.asyncio
async def test_async_placeholder():
    """A basic placeholder for an async test."""
    import asyncio
    await asyncio.sleep(0.01)
    assert True

# Add more specific tests for your template's core functionality
