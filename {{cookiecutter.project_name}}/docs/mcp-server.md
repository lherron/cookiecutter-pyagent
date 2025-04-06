# {{cookiecutter.project_name}} MCP Server

The Message Control Protocol (MCP) server provides a simple interface for sending emails from the agent. 

## Setup

### Prerequisites

- Python 3.12+
- Fastmail API access or similar JMAP provider
- MCP client

### Configuration

The MCP server requires the following environment variables:

- `JMAP_API_KEY`: Your JMAP API key for authentication
- `AGENT_EMAIL_ADDRESS`: The email address that will be used as the sender
- `JMAP_HOST` (optional): The JMAP server host (defaults to api.fastmail.com)
- `RECIPIENT_NAME` (optional): Default recipient name
- `RECIPIENT_EMAIL` (optional): Default recipient email

You can set these in a `.env` file in the project root or configure them in your `config.yaml` file.

## Running the MCP Server

To run the MCP server:

```bash
mcp run src/{{cookiecutter.project_slug}}/mcp/server.py
```

Or using the MCP command-line:

```bash
mcp run --with mcp src/{{cookiecutter.project_slug}}/mcp/server.py
```

## Available Tools

### send_user_email

Sends an email to a specified recipient with markdown content.

**Parameters:**
- `subject`: Subject line of the email
- `markdown_content`: Markdown formatted content for the email body
- `ctx`: (automatically provided) The MCP context

**Example:**

```python
# This would be called from another system using the MCP client
result = await mcp_client.call("send_user_email", {
    "subject": "Task completed", 
    "markdown_content": "# Task Completed\n\nYour task has been completed successfully."
})
```

## Integration with Other Systems

The MCP server is designed to be called from other systems like LLM agents or automation tools. It provides a standardized way to send emails without exposing the underlying email implementation details. 