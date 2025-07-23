# run --with mcp mcp run src/{{cookiecutter.project_slug}}/mcp/server.py
# # Add lifespan support for startup/shutdown with strong typing
import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from evaitools.adapters.mail.fastmail_client import FastmailClient
from evaitools.config import JMAPConfig
from mcp.server.fastmcp import Context, FastMCP

# add debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    fastmail_client: FastmailClient | None = None


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    # read config file
    try:
        # Load environment variables from .env file
        load_dotenv()

        # Get configuration from environment variables
        api_key = os.environ.get("JMAP_API_KEY")
        sender_email = os.environ.get("AGENT_EMAIL_ADDRESS")
        server_url = os.environ.get("JMAP_HOST", "api.fastmail.com")

        if not api_key:
            logger.error("JMAP_API_KEY environment variable is not set.")
            sys.exit(1)

        if not sender_email:
            logger.error("AGENT_EMAIL_ADDRESS environment variable is not set.")
            sys.exit(1)

        # Create JMAPConfig instance
        jmap_config = JMAPConfig(
            api_key=api_key,
            AGENT_EMAIL_ADDRESS=sender_email,
            USER_EMAIL_ADDRESS=sender_email,  # Can be the same for this example
            JMAP_HOST=server_url,
            source_folder="Triage",  # Default value
            archive_folder="Archive",  # Default value
        )
        fastmail_client = FastmailClient(jmap_config)
        yield AppContext(fastmail_client=fastmail_client)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise
    finally:
        # Cleanup on shutdown
        pass


# Pass lifespan to server
mcp = FastMCP("{{cookiecutter.project_slug}}_mcp", lifespan=app_lifespan)


@mcp.tool()
def send_user_email(subject: str, markdown_content: str, ctx: Context[Any, AppContext] | None = None) -> str:
    """Send an email to the chat user.

    Args:
        subject: Subject line of the email
        markdown_content: Markdown content of the email (will be rendered as HTML)
        ctx: MCP context containing FastmailClient

    Returns:
        str: Success message or error description
    """
    if not ctx or not ctx.request_context.lifespan_context.fastmail_client:
        return "Error: FastmailClient not initialized"

    client: FastmailClient = ctx.request_context.lifespan_context.fastmail_client

    try:
        success = client.send_email(
            to_addresses=[{"name": "Lance", "email": "lance@notlevel.com"}], subject=subject, markdown_content=markdown_content, from_email="triage@notlevel.com"
        )

        if success:
            return "Email successfully sent"
        else:
            return "Failed to send email"
    except Exception as e:
        return f"Error sending email: {str(e)}"
