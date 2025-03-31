"""
Anthropic LLM client for generating ideation content.
"""

import os
import logging
import time
from typing import Dict, Any, Optional, Tuple
import anthropic
from jinja2 import Template
from tenacity import retry, wait_exponential, stop_after_attempt
from abc import ABC, abstractmethod
from google import genai
from ..config import LLMConfig

# Set up logging
logger = logging.getLogger(__name__)

# Rate limiting configuration
# Format: (provider, model): (requests_per_window, window_seconds)
RATE_LIMITS: Dict[Tuple[str, str], Tuple[int, int]] = {
    ("gemini", "gemini-2.5-pro-exp-03-25"): (2, 60),  # 2 requests per minute
}

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a response from the LLM provider given a prompt.

        Args:
            prompt (str): The input prompt to send to the LLM.

        Returns:
            str: The response text from the LLM.
        """
        pass

class AnthropicProvider(LLMProvider):
    """Provider for Anthropic's Claude API."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "claude-3-7-sonnet-latest", 
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """Initialize the Anthropic provider.

        Args:
            api_key (str): Anthropic API key.
            model (str): Model name (e.g., 'claude-3-sonnet-20240229').
            max_tokens (int): Maximum tokens in the response.
            temperature (float): Temperature for generation (0.0-1.0).
        """
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.request_timestamps = []
        logger.info(f"Anthropic provider initialized with model {model}")

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting for the model.
        
        Raises:
            Exception: If rate limit is exceeded.
        """
        rate_limit = RATE_LIMITS.get(("anthropic", self.model))
        if not rate_limit:
            return
            
        requests_per_window, window_seconds = rate_limit
        current_time = time.time()
        
        # Remove timestamps older than the rate limit window
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                 if current_time - ts < window_seconds]
        
        # Check if we've exceeded the rate limit
        if len(self.request_timestamps) >= requests_per_window:
            oldest_request = self.request_timestamps[0]
            wait_time = window_seconds - (current_time - oldest_request)
            if wait_time > 0:
                logger.warning(f"Rate limit reached for Anthropic model {self.model}. Waiting {wait_time:.2f} seconds.")
                time.sleep(wait_time)
                # Update timestamps after waiting
                self.request_timestamps = [ts for ts in self.request_timestamps 
                                         if current_time - ts < window_seconds]
        
        # Add current request timestamp
        self.request_timestamps.append(current_time)

    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the Anthropic API.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: The generated response text.
        """
        try:
            logger.info(f"Generating response from Anthropic model {self.model}")
            # Check and enforce rate limiting
            self._check_rate_limit()
            
            logger.info(f"Sending request to Anthropic API: model={self.model}, max_tokens={self.max_tokens}, temperature={self.temperature}")
            logger.debug(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise

class GeminiProvider(LLMProvider):
    """Provider for Google's Gemini API."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-thinking-exp"):
        """Initialize the Gemini provider.

        Args:
            api_key (str): Gemini API key.
            model (str): Model name (e.g., 'gemini-2.0-flash-thinking-exp').
        """
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
        self.model = model
        self.request_timestamps = []
        logger.info(f"Gemini provider initialized with model {model}")

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting for the model.
        
        Raises:
            Exception: If rate limit is exceeded.
        """
        rate_limit = RATE_LIMITS.get(("gemini", self.model))
        if not rate_limit:
            return
            
        requests_per_window, window_seconds = rate_limit
        current_time = time.time()
        
        # Remove timestamps older than the rate limit window
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                 if current_time - ts < window_seconds]
        
        # Check if we've exceeded the rate limit
        if len(self.request_timestamps) >= requests_per_window:
            oldest_request = self.request_timestamps[0]
            wait_time = window_seconds - (current_time - oldest_request)
            if wait_time > 0:
                logger.warning(f"Rate limit reached for Gemini model {self.model}. Waiting {wait_time:.2f} seconds.")
                time.sleep(wait_time)
                # Update timestamps after waiting
                self.request_timestamps = [ts for ts in self.request_timestamps 
                                         if current_time - ts < window_seconds]
        
        # Add current request timestamp
        self.request_timestamps.append(current_time)

    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the Gemini API.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: The generated response text.
        """
        try:
            logger.info(f"Generating response from Gemini model {self.model}")
            # Check and enforce rate limiting
            self._check_rate_limit()
            
            logger.info(f"Sending request to Gemini API: model={self.model}")
            logger.debug(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            response = self.client.models.generate_content(model=self.model, contents=prompt)
            logger.info(f"Gemini generated response of length {len(response.text)}")
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise

def create_llm_provider(llm_config: LLMConfig) -> LLMProvider:
    """Create an LLM provider instance based on configuration.

    Args:
        llm_config (LLMConfig): The LLM configuration specifying the provider and settings.

    Returns:
        LLMProvider: An instance of the selected LLM provider.

    Raises:
        ValueError: If the provider is unknown or required config is missing.
    """
    if llm_config.provider == "anthropic":
        if not llm_config.anthropic:
            raise ValueError("Anthropic config is required when provider is 'anthropic'")
        return AnthropicProvider(**llm_config.anthropic.dict())
    elif llm_config.provider == "gemini":
        if not llm_config.gemini:
            raise ValueError("Gemini config is required when provider is 'gemini'")
        return GeminiProvider(**llm_config.gemini.dict())
    else:
        raise ValueError(f"Unknown LLM provider: {llm_config.provider}")

class LLMClient:
    """Client for interacting with LLM providers."""
    
    def __init__(self, provider: LLMProvider):
        """Initialize LLM client with a provider.

        Args:
            provider (LLMProvider): The LLM provider instance to use.
        """
        self.provider = provider
        logger.info("LLM client initialized with provider")

    @retry(
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    async def generate_ideation(self, task_content: str, repo_context: str, prompt_template_path: Optional[str] = None) -> str:
        """Generate ideation using the configured LLM provider.

        Args:
            task_content (str): Content of the task.
            repo_context (str): Repository context.
            prompt_template_path (Optional[str]): Path to Jinja2 template for prompt.

        Returns:
            str: Ideation output from the LLM provider.
        """
        logger.info(f"Generating ideation for task: '{task_content}'")

        # Render prompt from template or use default
        if prompt_template_path and os.path.exists(prompt_template_path):
            prompt = self._render_prompt(prompt_template_path, task_content, repo_context)
        else:
            prompt = f"""You are an AI development assistant helping to generate ideas for coding tasks.

Here is a task that needs ideation:
TASK: {task_content}

Here is context from the repository to help you understand the project:
REPOSITORY CONTEXT: 
{repo_context}

Please generate the following:
1. A clear understanding of what the task is asking for
2. 3-5 specific implementation ideas for this task
3. Potential challenges and how to address them
4. Suggested next steps

Focus on being practical and specific. Provide code examples where appropriate.
Make sure your ideas are directly relevant to the task and project context.
Be innovative but realistic given the constraints of the codebase and task requirements."""

        logger.debug(f"Using prompt: {prompt}")

        # Generate response using the provider
        response = await self.provider.generate_response(prompt)
        logger.info(f"Generated ideation of length {len(response)}")
        return response

    def _render_prompt(self, template_path: str, task_content: str, repo_context: str) -> str:
        """Render a prompt from a Jinja2 template.

        Args:
            template_path (str): Path to Jinja2 template.
            task_content (str): Content of the task.
            repo_context (str): Repository context.

        Returns:
            str: Rendered prompt string.

        Raises:
            Exception: If rendering fails.
        """
        try:
            logger.info(f"Rendering prompt template from {template_path}")
            with open(template_path, "r") as f:
                template_content = f.read()
            template = Template(template_content)
            return template.render(task=task_content, repo_context=repo_context)
        except Exception as e:
            logger.error(f"Error rendering prompt template: {e}")
            raise 