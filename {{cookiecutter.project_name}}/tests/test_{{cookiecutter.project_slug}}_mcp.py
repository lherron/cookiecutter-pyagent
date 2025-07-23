"""
Integration tests for the MCP client functionality.
"""

import logging
import os
from typing import Any

import pytest
from evaitools.adapters.llm.llm_session import LLMSession
from evaitools.config import AppConfig, PrefectConfig


@pytest.fixture
def mcp_integration_config() -> AppConfig:
    """Create a configuration for MCP integration testing."""
    return AppConfig(prefect=PrefectConfig(project_name="{{cookiecutter.project_slug}}", flow_name="test_flow", schedule_interval_minutes=30))


def load_mcp_servers(config_path: str = "servers_config.json") -> list[Any]:
    """Load MCP servers configuration from JSON file."""
    import json

    try:
        if os.path.exists(config_path):
            with open(config_path) as f:
                _config = json.load(f)
                # For now, just return an empty list to avoid server loading in tests
                # This can be enhanced later with proper MCP server loading logic
                return []
        else:
            return []
    except Exception:
        return []


@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for direct MCP client interaction with LLM."""

    @pytest.mark.asyncio
    async def test_direct_llm_message_processing(self, mcp_integration_config: AppConfig) -> None:
        """Test direct use of LLMSession to process an email message."""
        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        logger = logging.getLogger("test_mcp_integration")
        logger.setLevel(logging.DEBUG)

        # Load server configurations (for reference, but not used in initialization)
        servers: list[Any] = []
        mcp_servers_config_path = os.getenv("EVAI_SERVERS_CONFIG", "servers_config.json")

        servers = load_mcp_servers(mcp_servers_config_path)
        if not servers:
            logger.warning("No MCP servers found in configuration. Proceeding without tools.")

        # Initialize LLM session correctly
        llm_session = LLMSession()

        try:
            # Initialize the session
            await llm_session.initialize()

            # Create a test message
            from_email = "sender@example.com"
            subject = "Test Email for Direct MCP Integration"
            message_text = "This is a test email for direct MCP integration testing."

            # Create the prompt
            prompt = f"""Here is an email message:

From: {from_email}
Subject: {subject}

{message_text}

Please respond to the user using the send_user_email tool. Be concise, no need for conversational tone. Use markdown formatting.
"""

            # Send request to LLM
            result = await llm_session.send_request(user_prompt=prompt, debug=True)

            # Verify the result
            assert result["success"] is True, f"LLM request failed: {result.get('error', 'Unknown error')}"

            # Check that we have a response
            assert result["response"], "No response was generated"

            # Log the result
            logger.info(f"Received response from LLM (length: {len(result['response'])})")
            logger.debug(f"Response: {result['response'][:100]}...")  # Log first 100 chars

            # Check if we have any tool calls (if tools are available)
            if "tool_calls" in result and result["tool_calls"]:
                logger.info(f"Number of tool calls: {len(result['tool_calls'])}")
                for call in result["tool_calls"]:
                    logger.info(f"Tool {call['tool_name']} called with args: {call['tool_args']}")
                    # If we have a send_user_email tool call, verify it has the expected parameters
                    if call["tool_name"] == "send_user_email":
                        assert "subject" in call["tool_args"], "Missing 'subject' field in send_user_email args"
                        assert "markdown_content" in call["tool_args"], "Missing 'markdown_content' field in send_user_email args"

        finally:
            # Clean up LLM session (if cleanup method exists)
            logger.debug("LLM session test completed")

    @pytest.mark.asyncio
    async def test_structured_email_response(self, mcp_integration_config: AppConfig) -> None:
        """Test LLMSession with structured output for email processing."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("test_mcp_integration")

        # Define structured output schema for email responses
        email_response_schema = {
            "name": "email_response",
            "description": "Generate a structured response to an email",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Brief summary of the email content"},
                    "response": {"type": "string", "description": "The response text to send to the user"},
                    "action_items": {"type": "array", "items": {"type": "string"}, "description": "List of action items extracted from the email"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "The priority level of this email"},
                },
                "required": ["summary", "response", "priority"],
            },
        }

        # Load server configurations (for reference)
        _servers = load_mcp_servers()

        # Initialize LLM session correctly
        llm_session = LLMSession()

        try:
            # Initialize the session
            await llm_session.initialize()

            # Create a test message with action items
            from_email = "client@example.com"
            subject = "Project Update Request"
            message_text = """Hello,

Could you please provide me with an update on the current project status? I need the following information:

1. Current progress on the implementation phase
2. Any blockers or issues you're facing
3. Expected completion date for the next milestone

Also, please schedule a meeting for next week to discuss these items in detail.

Thank you,
Client
"""

            # Create the prompt
            prompt = f"""Here is an email message:

From: {from_email}
Subject: {subject}

{message_text}

Extract key information from this email and generate a structured response.
"""

            # Send request to LLM with structured output
            result = await llm_session.send_request(user_prompt=prompt, structured_output_tool=email_response_schema, debug=True)

            # Verify the result
            assert result["success"] is True, f"LLM request failed: {result.get('error', 'Unknown error')}"

            # Check that we have a structured response
            assert result["structured_response"], "No structured response was generated"

            # Verify structured response format
            structured_resp = result["structured_response"]
            assert "summary" in structured_resp, "Missing 'summary' in structured response"
            assert "response" in structured_resp, "Missing 'response' in structured response"
            assert "priority" in structured_resp, "Missing 'priority' in structured response"

            # Validate priority is one of the allowed values
            assert structured_resp["priority"] in ["high", "medium", "low"], f"Invalid priority value: {structured_resp['priority']}"

            # Log the structured response
            logger.info(f"Received structured response from LLM: {structured_resp}")

        finally:
            # Clean up LLM session
            logger.debug("LLM session test completed")
