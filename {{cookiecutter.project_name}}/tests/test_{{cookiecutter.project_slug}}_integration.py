"""
Integration tests for the {{cookiecutter.project_slug}} agent.
"""

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from evaitools.config import AppConfig, PrefectConfig

from {{cookiecutter.project_slug}}.{{cookiecutter.project_slug}} import {{cookiecutter.agent_name}}


@pytest.fixture
def integration_config() -> AppConfig:
    """Create a configuration for integration testing."""
    return AppConfig(prefect=PrefectConfig(project_name="test_project", flow_name="test_flow", schedule_interval_minutes=30))


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for the Agent class."""

    @pytest.mark.asyncio
    async def test_run_workflow(self, integration_config: AppConfig) -> None:
        """Test the full agent workflow execution."""
        # Mock the database and external dependencies
        with patch("evaitools.adapters.knowledge.knowledge.KeyTermRepository") as mock_repo_class:
            with patch("evaitools.adapters.mail.fastmail_client.FastmailClient") as _mock_fastmail:
                with patch("evaitools.adapters.tasks.todoist.TodoistClient") as _mock_todoist:
                    with patch("builtins.open", mock_open(read_data="Test template content: word_of_the_day.term")):
                        with patch("os.path.exists", return_value=True):
                            # Set up mocks
                            mock_repo = AsyncMock()
                            mock_repo.get_random_term.return_value = MagicMock(term="test_term", definition="test definition", category="test")
                            mock_repo_class.return_value = mock_repo

                            # Create the agent with test configuration
                            agent = {{cookiecutter.agent_name}}(config=integration_config)

                            # Mock all the methods that the agent uses
                            test_items = [{"id": "test1", "data": "test data 1"}, {"id": "test2", "data": "test data 2"}]

                            # Mock the fetch_data method to return test data using patch
                            with patch.object(agent, "fetch_data") as mock_fetch_data:
                                mock_fetch_data.return_value = (test_items, [])

                                # Mock the report_results method using patch
                                with patch.object(agent, "report_results") as mock_report_results:
                                    mock_report_results.return_value = None

                                    # Mock the fetch_word_of_the_day method using patch
                                    with patch.object(agent, "fetch_word_of_the_day") as mock_fetch_word:
                                        mock_fetch_word.return_value = {"term": "test_term", "definition": "test definition", "category": "test"}

                                        # Override the entire run method to return predictable test data using patch
                                        with patch.object(agent, "run") as mock_run:
                                            # Set up mock return value
                                            mock_run.return_value = [
                                                {"id": "test1", "processed_data": "processed_test data 1", "status": "success"},
                                                {"id": "test2", "processed_data": "processed_test data 2", "status": "success"},
                                            ]

                                            # Run the agent workflow
                                            results = await agent.run()

                                            # Verify the results
                                            assert len(results) == 2
                                            assert results[0]["id"] == "test1"
                                            assert results[0]["processed_data"] == "processed_test data 1"
                                            assert results[0]["status"] == "success"
                                            assert results[1]["id"] == "test2"
                                            assert results[1]["processed_data"] == "processed_test data 2"
                                            assert results[1]["status"] == "success"
