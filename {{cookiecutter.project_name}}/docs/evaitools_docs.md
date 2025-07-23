TITLE: evaitools Configuration System
DESCRIPTION: Hierarchical configuration management system supporting YAML files, environment variables, and Consul KV store with Pydantic models for validation and type safety.
SOURCE: evaitools.config module

LANGUAGE: python
CODE:
```
from evaitools.config import load_config

# Load configuration with hierarchical precedence:
# Consul KV < Environment Variables < YAML file
config = load_config(config_path="config.yaml")

# Access provider configurations
if config.llm:
    print(f"LLM Provider: {config.llm.provider}")
if config.todoist:
    print(f"Todoist Project: {config.todoist.project_name}")
```

----------------------------------------

TITLE: evaitools CLI Application Entry Point
DESCRIPTION: Typer-based command-line interface providing commands for running flows, scheduling tasks, displaying configuration, and interacting with LLM sessions.
SOURCE: evaitools.cli.cli module

LANGUAGE: python
CODE:
```
import typer

# Create CLI application
app = typer.Typer(name="evaitools")

# Example CLI command structure
@app.command()
def run(
    config_path: str | None = typer.Option(None, "--config", "-c"),
    debug: bool = typer.Option(False, "--debug", "-d")
) -> None:
    """Run the evaitools agent flow once."""
    pass
```

----------------------------------------

TITLE: Database Connection Pool with AsyncPG
DESCRIPTION: Async PostgreSQL database connection pool wrapper providing helper methods for query execution and transaction management using asyncpg.
SOURCE: evaitools.db.core module

LANGUAGE: python
CODE:
```
from evaitools.db.core import AsyncPGDatabase

# Initialize database connection
async with AsyncPGDatabase(
    dsn="postgresql://postgres@/postgres?host=/tmp",
    min_size=1,
    max_size=10
) as db:
    # Execute queries
    result = await db.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
    
    # Use transactions
    async with db.transaction() as conn:
        await conn.execute("INSERT INTO ...", values)
```

----------------------------------------

TITLE: LLM Provider Abstract Base Class
DESCRIPTION: Abstract interface defining the contract for LLM providers with support for multiple backends (Anthropic Claude, Google Gemini) and rate limiting.
SOURCE: evaitools.adapters.llm.llm module

LANGUAGE: python
CODE:
```
from evaitools.adapters.llm.llm import LLMProvider, AnthropicProvider, create_llm_provider
from evaitools.config import LLMConfig

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a response from the LLM provider given a prompt."""
        pass

# Create provider from configuration
provider = create_llm_provider(llm_config)
response = await provider.generate_response("Hello, world!")
```

----------------------------------------

TITLE: Task Provider Interface with Pydantic Models
DESCRIPTION: Abstract base class for task management systems (Todoist, Asana, etc.) with standardized operations for projects, sections, tasks, and comments.
SOURCE: evaitools.adapters.tasks.base and evaitools.models.tasks modules

LANGUAGE: python
CODE:
```
from evaitools.adapters.tasks.base import TaskProvider
from evaitools.models.tasks import Task, Project, Section, Comment

class TaskProvider(ABC):
    @abstractmethod
    def get_project(self, *, name: str | None = None, id: str | None = None) -> Project | None:
        """Return the project identified by name or id."""
        pass
    
    @abstractmethod
    def list_tasks(
        self, 
        *, 
        project_id: str | None = None,
        section_id: str | None = None,
        include_comments: bool = False
    ) -> list[Task | dict[str, Any]]:
        """Generic task query with optional filtering."""
        pass
```

----------------------------------------

TITLE: Pydantic Task Models
DESCRIPTION: Type-safe data models for task management entities including tasks, projects, sections, and comments with validation and serialization support.
SOURCE: evaitools.models.tasks module

LANGUAGE: python
CODE:
```
from evaitools.models.tasks import Task, Project, Section, Comment, Due

class Task(BaseModel):
    """Task item representing actionable work."""
    assignee_id: str | None
    content: str
    created_at: str
    due: Due | None = None
    id: str
    labels: list[str] | None = None
    priority: int
    project_id: str
    section_id: str | None = None
    
    model_config = ConfigDict(extra="forbid")
```

----------------------------------------

TITLE: Chat Provider Abstract Interface
DESCRIPTION: Platform-agnostic chat provider interface supporting message sending, channel management, user operations, and event handling for Discord, Slack, etc.
SOURCE: evaitools.adapters.chat.base and evaitools.models.chat modules

LANGUAGE: python
CODE:
```
from evaitools.adapters.chat.base import ChatProvider
from evaitools.models.chat import ChatMessage, ChatChannel, ChatUser

class ChatProvider(ABC):
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the chat service."""
        pass
    
    @abstractmethod
    async def send_chat_message(self, channel_id: str, content: str) -> ChatMessage:
        """Send a message to a specific channel."""
        pass
    
    @abstractmethod
    async def list_chat_channels(self, guild_id: str | None = None) -> list[ChatChannel]:
        """List available channels."""
        pass
```

----------------------------------------

TITLE: Chat Models for Platform Abstraction
DESCRIPTION: Pydantic models representing chat entities (users, channels, messages, attachments) in a platform-agnostic way with type safety and validation.
SOURCE: evaitools.models.chat module

LANGUAGE: python
CODE:
```
from evaitools.models.chat import ChatUser, ChatChannel, ChatMessage, ChatAttachment
from datetime import datetime
from typing import Literal

class ChatMessage(BaseModel):
    """Represents a message sent in a chat."""
    id: str
    channel_id: str
    author: ChatUser
    content: str
    timestamp: datetime
    attachments: list[ChatAttachment] = Field(default_factory=list)

class ChatChannel(BaseModel):
    """Represents a channel or chat room."""
    id: str
    name: str
    type: Literal["text", "voice", "dm", "group", "unknown"] = "unknown"
    guild_id: str | None = None
```

----------------------------------------

TITLE: Mail Provider Abstract Interface
DESCRIPTION: Provider-agnostic interface for email operations including folder management, message retrieval, marking as read, archiving, and sending emails.
SOURCE: evaitools.adapters.mail.base module

LANGUAGE: python
CODE:
```
from evaitools.adapters.mail.base import MailProvider

class MailProvider(ABC):
    @abstractmethod
    def get_email_folder_id(self, folder_name: str) -> str:
        """Get the ID of a folder by its name."""
        pass
    
    @abstractmethod
    def get_unread_email_messages(self, folder_id: str) -> list[dict[str, Any]]:
        """Fetch unread messages from the specified folder."""
        pass
    
    @abstractmethod
    def send_email(
        self,
        to_addresses: list[dict[str, str]],
        subject: str,
        markdown_content: str
    ) -> bool:
        """Send a generic email."""
        pass
```

----------------------------------------

TITLE: LLM Session with Tool Integration
DESCRIPTION: Orchestrates interactions between users, LLMs, and tools using FastMCP server integration with retry logic, conversation management, and structured output support.
SOURCE: evaitools.adapters.llm.llm_session module

LANGUAGE: python
CODE:
```
from evaitools.adapters.llm.llm_session import LLMSession

# Initialize and use LLM session
session = LLMSession()
await session.initialize()

# Send request with tool access
result = await session.send_request(
    user_prompt="List available terms in the knowledge base",
    system_prompt="You are a helpful assistant",
    debug=True
)

if result["success"]:
    print(result["response"])
    print(f"Tool calls: {result['tool_calls']}")
```

----------------------------------------

TITLE: MCP Server Integration
DESCRIPTION: FastMCP server providing evaitools functionality as tools including email operations, task management, chat integration, and knowledge base access.
SOURCE: evaitools.mcp.evaitools_server module

LANGUAGE: python
CODE:
```
from evaitools.mcp.evaitools_server import mcp
from fastmcp import FastMCP

# MCP server with lifecycle management
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    config = load_config()
    
    # Initialize providers
    fastmail_client = FastmailClient(config.jmap) if config.jmap else None
    todoist_client = TodoistClient(api_key=config.todoist.api_key) if config.todoist else None
    
    yield AppContext(
        fastmail_client=fastmail_client,
        todoist_client=todoist_client
    )

# Tools automatically registered
mcp = FastMCP("evaitools_mcp", lifespan=app_lifespan)
```

----------------------------------------

TITLE: Configuration Model Classes
DESCRIPTION: Pydantic configuration models for different service providers with validation, aliasing, and environment variable support using hierarchical loading.
SOURCE: evaitools.config module

LANGUAGE: python
CODE:
```
from evaitools.config import TodoistConfig, AnthropicConfig, DiscordConfig

class TodoistConfig(BaseModel):
    """Settings for the Todoist task provider."""
    api_key: str | None = None
    project_name: str = "MyProject"
    section_name: str = "Ideas"
    ideated_label: str = "ideated"

class AnthropicConfig(BaseModel):
    """Anthropic LLM provider settings."""
    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY")
    )
    model: str = Field(default="claude-3-sonnet-20240229")
    max_tokens: int = Field(2000)
    temperature: float = Field(0.7)
```

----------------------------------------

TITLE: Evaitools CLI Sampler Commands
DESCRIPTION: Sample command implementations demonstrating usage of different providers and adapters through the CLI interface with debug output and error handling.
SOURCE: evaitools.cli.cli module

LANGUAGE: python
CODE:
```
# CLI sample commands for testing providers
@sample_app.command("tasks")
def sample_tasks_cmd(
    config_path: str | None = typer.Option(None, "--config", "-c"),
    debug: bool = typer.Option(False, "--debug", "-d")
) -> None:
    """Sample Todoist task provider: Fetches tasks from Inbox."""
    _run_sample(EvaiToolsSampler.sample_tasks, config_path, debug)

@sample_app.command("llm")
def sample_llm_cmd(
    config_path: str | None = typer.Option(None, "--config", "-c"),
    prompt: str = typer.Option("Explain APIs in one sentence.", "--prompt", "-p"),
    debug: bool = typer.Option(False, "--debug", "-d")
) -> None:
    """Sample LLM provider functionality."""
    _run_sample(EvaiToolsSampler.sample_llm, config_path, debug, prompt=prompt)
```

----------------------------------------

TITLE: Asynchronous Context Manager Pattern
DESCRIPTION: Common pattern used throughout evaitools for resource management with proper initialization, cleanup, and error handling using Python's async context manager protocol.
SOURCE: evaitools.db.core module

LANGUAGE: python
CODE:
```
class AsyncPGDatabase(AbstractAsyncContextManager["AsyncPGDatabase"]):
    """Connection-pool wrapper for asyncpg with helper methods."""
    
    async def __aenter__(self) -> AsyncPGDatabase:
        await self.open()
        return self
    
    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

# Usage pattern
async with AsyncPGDatabase(dsn="postgresql://...") as db:
    result = await db.fetchrow("SELECT * FROM table")
```

----------------------------------------

TITLE: Environment Variable and Configuration Loading
DESCRIPTION: Utility functions for loading configuration from multiple sources with type conversion, prefix handling, and hierarchical merging for flexible deployment scenarios.
SOURCE: evaitools.config module

LANGUAGE: python
CODE:
```
def _get_env_vars(prefix: str) -> dict[str, Any]:
    """Extract environment variables with the given prefix."""
    result: dict[str, Any] = {}
    prefix_len = len(prefix)
    
    for env_key, env_value in os.environ.items():
        if env_key.startswith(prefix):
            # Strip prefix and convert to snake_case
            config_key = env_key[prefix_len:].lower()
            result[config_key] = env_value
    
    return result

# Example: TODOIST_API_KEY=abc123 -> {"api_key": "abc123"}
env_vars = _get_env_vars("TODOIST_")
```

----------------------------------------

TITLE: Retry Pattern with Tenacity
DESCRIPTION: Robust retry mechanisms for external API calls using tenacity library with exponential backoff, error classification, and comprehensive logging.
SOURCE: evaitools.adapters.llm.llm_session module

LANGUAGE: python
CODE:
```
from tenacity import (
    retry, stop_after_attempt, wait_random_exponential,
    retry_if_exception_type, before_sleep_log, after_log
)

@retry(
    retry=retry_if_exception_type((
        anthropic.RateLimitError,
        anthropic.APIConnectionError
    )),
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO)
)
def _call_anthropic_api(self, messages: list, tools: list) -> Any:
    """Make a retryable call to the Anthropic API."""
    return self.anthropic_client.messages.create(...)
```

----------------------------------------

TITLE: Tool Result Extraction and Processing
DESCRIPTION: Utility function for parsing and extracting meaningful results from MCP tool execution responses with JSON handling and structured data formatting.
SOURCE: evaitools.adapters.llm.llm_session module

LANGUAGE: python
CODE:
```
def extract_tool_result_value(result_str: str) -> str:
    """Extract the actual result value from MCP tool result string."""
    try:
        # Check if the result contains TextContent
        if "TextContent" in result_str and "text='" in result_str:
            match = re.search(r"text='([^']*)'", result_str)
            if match:
                extracted_text = match.group(1)
                
                # Check if extracted text is JSON
                if extracted_text.strip().startswith('{'):
                    json_obj = json.loads(extracted_text)
                    return json.dumps(json_obj, indent=2)
                
                return extracted_text
        
        return result_str
    except Exception:
        return result_str
```

----------------------------------------

TITLE: Structured Output with Pydantic Schema
DESCRIPTION: Integration pattern for generating structured responses from LLMs using Pydantic model schemas as tool definitions for type-safe data extraction.
SOURCE: evaitools.adapters.llm.llm_session module

LANGUAGE: python
CODE:
```
from pydantic import BaseModel, Field

class ProjectInfo(BaseModel):
    project_count: int = Field(description="The total number of projects")
    first_project_name: str | None = Field(description="The name of the first project, if any")

# Generate schema from Pydantic model
project_schema = {
    "name": "extract_project_info",
    "description": "Extract structured information about projects",
    "input_schema": ProjectInfo.model_json_schema()
}

# Use as structured output tool
result = await session.send_request(
    user_prompt=prompt,
    structured_output_tool=project_schema
)

# Parse structured response
if result["structured_response"]:
    parsed = ProjectInfo(**result["structured_response"])
```

----------------------------------------

TITLE: Rate Limiting Implementation
DESCRIPTION: Token bucket-style rate limiting for API calls with configurable limits per provider and model, including automatic delay calculation and request tracking.
SOURCE: evaitools.adapters.llm.llm module

LANGUAGE: python
CODE:
```
# Rate limiting configuration
RATE_LIMITS: dict[tuple[str, str], tuple[int, int]] = {
    ("gemini", "gemini-2.5-pro-exp-03-25"): (2, 60),  # 2 requests per minute
}

def _check_rate_limit(self) -> None:
    """Check and enforce rate limiting for the model."""
    rate_limit = RATE_LIMITS.get((self.provider, self.model))
    if not rate_limit:
        return
    
    requests_per_window, window_seconds = rate_limit
    current_time = time.time()
    
    # Remove timestamps older than the rate limit window
    self.request_timestamps = [
        ts for ts in self.request_timestamps 
        if current_time - ts < window_seconds
    ]
    
    # Check if we've exceeded the rate limit
    if len(self.request_timestamps) >= requests_per_window:
        wait_time = window_seconds - (current_time - self.request_timestamps[0])
        if wait_time > 0:
            time.sleep(wait_time)
    
    self.request_timestamps.append(current_time)
```