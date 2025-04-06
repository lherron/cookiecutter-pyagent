"""
Integration tests for the {{ cookiecutter.project_slug }} agent.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from {{ cookiecutter.project_slug }}.{{ cookiecutter.project_slug }} import {{ cookiecutter.agent_name }}
from {{ cookiecutter.project_slug }}.config import AppConfig, LLMConfig, AnthropicConfig, PrefectConfig

@pytest.fixture
def integration_config():
    """Create a configuration for integration testing."""
    return AppConfig(
        llm=LLMConfig(
            provider="anthropic",
            anthropic=AnthropicConfig(
                api_key="test_anthropic_key",
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.7
            )
        ),
        prefect=PrefectConfig(
            project_name="test_project",
            flow_name="test_flow",
            schedule_interval_minutes=30
        )
    )

@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for the Agent class."""
    
    @pytest.mark.asyncio
    async def test_run_workflow(self, integration_config):
        """Test the full agent workflow execution."""
        # Create the agent with test configuration
        agent = {{ cookiecutter.agent_name }}(config=integration_config)
        
        # Mock the fetch_data method to return test data
        test_items = [{"id": "test1", "data": "test data 1"}, {"id": "test2", "data": "test data 2"}]
        agent.fetch_data = AsyncMock(return_value=test_items)
        
        # Mock the report_results method
        agent.report_results = AsyncMock()
        
        # Run the agent workflow
        results = await agent.run()
        
        # Verify the results
        assert len(results) == 2
        assert results[0]["id"] == "test1"
        assert results[0]["processed_data"] == "processed_test data 1"
        assert results[0]["status"] == "success"
        
        # Verify mocked method calls
        agent.fetch_data.assert_called_once()
        agent.report_results.assert_called_once() 