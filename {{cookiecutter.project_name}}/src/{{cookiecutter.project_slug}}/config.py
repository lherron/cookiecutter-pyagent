"""
Configuration management for {{ cookiecutter.project_name }}.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class TodoistConfig(BaseModel):
    """Todoist API configuration."""
    api_key: Optional[str] = Field(None, description="Todoist API key") # Made optional
    project_name: str = Field("MyProject", description="Default Todoist project name")
    section_name: str = Field("Ideas", description="Default Todoist section name")
    ideated_label: str = Field("ideated", description="Label to add to ideated tasks")

class GitHubConfig(BaseModel):
    """GitHub configuration."""
    username: Optional[str] = Field(None, description="GitHub username") # Made optional
    token: Optional[str] = Field(None, description="GitHub API token")
    repo_path: str = Field("./repos", description="Path to store repositories")

class AnthropicConfig(BaseModel):
    """Anthropic-specific configuration."""
    api_key: Optional[str] = Field(None, description="Anthropic API key") # Made optional
    model: str = Field("claude-3-sonnet-20240229", description="Model to use for ideation")
    max_tokens: int = Field(2000, description="Maximum tokens in response")
    temperature: float = Field(0.7, description="Model temperature (0.0-1.0)")

class GeminiConfig(BaseModel):
    """Gemini-specific configuration."""
    api_key: Optional[str] = Field(None, description="Gemini API key") # Made optional
    model: str = Field("gemini-2.0-flash-thinking-exp", description="Model to use for ideation")

class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: Optional[str] = Field(None, description="LLM provider to use ('anthropic' or 'gemini')") # Made optional
    anthropic: Optional[AnthropicConfig] = Field(None, description="Anthropic configuration if provider is 'anthropic'")
    gemini: Optional[GeminiConfig] = Field(None, description="Gemini configuration if provider is 'gemini'")

class PrefectConfig(BaseModel):
    """Prefect configuration."""
    # Use cookiecutter variables for defaults
    project_name: str = Field("{{ cookiecutter.project_slug }}", description="Prefect project name")
    flow_name: str = Field("{{ cookiecutter.project_name }} Flow", description="Flow name") 
    schedule_interval_minutes: int = Field(30, description="Schedule interval in minutes")

class AppConfig(BaseModel):
    """Main application configuration."""
    # Make Todoist, GitHub, LLM optional
    todoist: Optional[TodoistConfig] = None
    github: Optional[GitHubConfig] = None
    llm: Optional[LLMConfig] = None 
    prefect: PrefectConfig # Prefect remains required
    prompt_template_path: str = Field(
        "templates/ideation_prompt.jinja2", 
        description="Path to the Jinja2 template for LLM prompts"
    )

def _get_env_var(key: str, default: Any = None) -> Any:
    """Helper to get environment variable, returning default if not set or empty."""
    value = os.getenv(key)
    return value if value else default

def _load_section_config(section_key: str, model: type[BaseModel], config_data: Dict[str, Any], env_prefix: str) -> Optional[BaseModel]:
    """Loads configuration for a specific section, overriding with env vars."""
    section_data = config_data.get(section_key, {})
    env_overrides = {}
    
    # Dynamically get fields from the model and check corresponding env vars
    for field_name in model.model_fields.keys():
        # Handle nested models like anthropic/gemini within llm
        if isinstance(model.model_fields[field_name].annotation, type) and issubclass(model.model_fields[field_name].annotation, BaseModel):
             nested_model = model.model_fields[field_name].annotation
             nested_env_prefix = f"{env_prefix}_{field_name.upper()}"
             nested_data = section_data.get(field_name, {})
             
             nested_env_overrides = {}
             for nested_field_name in nested_model.model_fields.keys():
                 nested_env_var = f"{nested_env_prefix}_{nested_field_name.upper()}"
                 env_val = _get_env_var(nested_env_var)
                 if env_val is not None:
                     # Attempt type conversion for nested fields based on model type hints
                     field_type = nested_model.model_fields[nested_field_name].annotation
                     try:
                         if field_type == int:
                             env_val = int(env_val)
                         elif field_type == float:
                             env_val = float(env_val)
                     except ValueError:
                          logger.warning(f"Could not convert env var {nested_env_var} value '{env_val}' to type {field_type}. Using default.")
                          env_val = None # Reset to None if conversion fails
                 
                 if env_val is not None: # Only add if env var was set and conversion succeeded (or wasn't needed)
                    nested_env_overrides[nested_field_name] = env_val

             # Merge env overrides into nested data from file
             nested_data.update(nested_env_overrides)
             if nested_data: # Only add nested config if it has data
                 env_overrides[field_name] = nested_data

        else: # Handle simple fields
            env_var = f"{env_prefix}_{field_name.upper()}"
            env_val = _get_env_var(env_var)
            if env_val is not None:
                 # Attempt type conversion based on model type hints
                 field_type = model.model_fields[field_name].annotation
                 # Handle Optional types
                 if hasattr(field_type, '__origin__') and field_type.__origin__ is Optional:
                      # Get the actual type argument from Optional[T] -> T
                      field_type = field_type.__args__[0]

                 try:
                     if field_type == int:
                         env_val = int(env_val)
                     elif field_type == float:
                          env_val = float(env_val)
                 except ValueError:
                     logger.warning(f"Could not convert env var {env_var} value '{env_val}' to type {field_type}. Using default.")
                     env_val = None # Reset to None if conversion fails

            if env_val is not None: # Only add if env var was set and conversion succeeded (or wasn't needed)
                 env_overrides[field_name] = env_val

    # Merge environment overrides into the data loaded from the file
    final_data = {**section_data, **env_overrides}
    
    # If after merging, there's no data for the section, return None
    if not final_data:
        return None
        
    # Validate and create the model instance
    try:
        return model(**final_data)
    except ValidationError as e:
        logger.error(f"Configuration validation error for section '{section_key}': {e}")
        # For optional sections, return None if validation fails due to missing required fields
        # that weren't provided by file or env vars (e.g. api_key if it were mandatory)
        # Check if errors are due to missing fields that are now optional at the AppConfig level.
        # A more robust check might be needed depending on specific validation rules.
        # For now, let's return None if *any* validation error occurs for an optional section.
        # Prefect is mandatory, so errors there should likely propagate or halt.
        if section_key in ["todoist", "github", "llm"]: 
             logger.warning(f"Optional configuration section '{section_key}' failed validation, treating as disabled.")
             return None
        else: # Re-raise for mandatory sections like Prefect if validation fails
             raise e

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load configuration from a YAML file and environment variables.
    Environment variables take precedence over the config file.
    Optional sections (Todoist, GitHub, LLM) are loaded only if configuration
    is found in the file or environment variables. Prefect config is required.

    Args:
        config_path: Path to the config.yaml file, or None to use default

    Returns:
        AppConfig object with all configuration settings
    """
    # Default config path is in the project root
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    
    config_path = Path(config_path)
    
    config_data = {}
    # Load config from file if it exists
    if config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        try:
            with open(config_path, "r") as f:
                loaded_yaml = yaml.safe_load(f)
                if loaded_yaml: # Ensure file is not empty
                     config_data = loaded_yaml
        except yaml.YAMLError as e:
             logger.error(f"Error parsing config file {config_path}: {e}")
        except Exception as e:
             logger.error(f"Error reading config file {config_path}: {e}")
    else:
        logger.info(f"Config file {config_path} not found. Loading from environment variables and defaults.")

    # --- Load individual sections ---
    
    # Optional Sections: Load only if data exists in file or env vars
    todoist_config = _load_section_config("todoist", TodoistConfig, config_data, "TODOIST")
    github_config = _load_section_config("github", GitHubConfig, config_data, "GITHUB")
    llm_config = _load_section_config("llm", LLMConfig, config_data, "LLM")

    # Required Section: Prefect (Load with specific defaults from model)
    prefect_file_data = config_data.get("prefect", {})
    prefect_env_overrides = {}
    prefect_defaults = {
        "project_name": "{{ cookiecutter.project_slug }}",
        "flow_name": "{{ cookiecutter.project_name }} Flow",
        "schedule_interval_minutes": 30,
    }
    for field_name, default_value in prefect_defaults.items():
        env_var = f"PREFECT_{field_name.upper()}"
        # Special case for schedule interval env var name
        if field_name == "schedule_interval_minutes":
             env_var = "PREFECT_SCHEDULE_INTERVAL"
             
        env_val = _get_env_var(env_var)
        if env_val is not None:
             try:
                 # Ensure correct type for interval
                 if field_name == "schedule_interval_minutes":
                      prefect_env_overrides[field_name] = int(env_val)
                 else:
                      prefect_env_overrides[field_name] = env_val
             except ValueError:
                 logger.warning(f"Could not convert env var {env_var} value '{env_val}' to expected type. Using default.")
        elif field_name not in prefect_file_data: # Use default if not in file and no env var
             prefect_env_overrides[field_name] = default_value
             
    # Merge file data and env overrides for Prefect
    final_prefect_data = {**prefect_file_data, **prefect_env_overrides}
    # Ensure defaults are present if not overridden
    for field_name, default_value in prefect_defaults.items():
         if field_name not in final_prefect_data:
              final_prefect_data[field_name] = default_value
              
    try:
        prefect_config = PrefectConfig(**final_prefect_data)
    except ValidationError as e:
        logger.critical(f"FATAL: Required Prefect configuration failed validation: {e}")
        raise # Halt execution if Prefect config is invalid


    # --- Load general settings ---
    prompt_template_path = _get_env_var(
        "PROMPT_TEMPLATE_PATH", 
        config_data.get("prompt_template_path", "templates/ideation_prompt.jinja2") # Default from original code
    )

    # Create the final AppConfig object
    try:
         app_config = AppConfig(
             todoist=todoist_config,
             github=github_config,
             llm=llm_config,
             prefect=prefect_config,
             prompt_template_path=prompt_template_path
         )
         return app_config
    except ValidationError as e:
         logger.critical(f"FATAL: Final application configuration failed validation: {e}")
         raise # Halt execution if final config is invalid

# Example usage (optional, for testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example: Set some env vars for testing
    # os.environ["TODOIST_API_KEY"] = "test_todoist_key_from_env"
    # os.environ["GITHUB_USERNAME"] = "test_github_user_from_env"
    # os.environ["LLM_PROVIDER"] = "gemini"
    # os.environ["GEMINI_API_KEY"] = "test_gemini_key_from_env"
    # os.environ["PREFECT_PROJECT_NAME"] = "my-{{cookiecutter.project_slug}}-env"
    
    print("Loading configuration...")
    try:
        config = load_config()
        print("\nLoaded Configuration:")
        print(config.model_dump_json(indent=2))

        # Example checks for optional configs
        if config.todoist:
            print("\nTodoist Config Loaded:")
            print(f"  API Key Set: {'Yes' if config.todoist.api_key else 'No'}")
            print(f"  Project: {config.todoist.project_name}")
        else:
            print("\nTodoist Config: Not Loaded/Disabled")

        if config.github:
            print("\nGitHub Config Loaded:")
            print(f"  Username: {config.github.username or 'Not Set'}")
            print(f"  Token Set: {'Yes' if config.github.token else 'No'}")
        else:
             print("\nGitHub Config: Not Loaded/Disabled")

        if config.llm:
            print("\nLLM Config Loaded:")
            print(f"  Provider: {config.llm.provider or 'Not Set'}")
            if config.llm.provider == "anthropic" and config.llm.anthropic:
                print(f"  Anthropic Key Set: {'Yes' if config.llm.anthropic.api_key else 'No'}")
            elif config.llm.provider == "gemini" and config.llm.gemini:
                 print(f"  Gemini Key Set: {'Yes' if config.llm.gemini.api_key else 'No'}")
        else:
            print("\nLLM Config: Not Loaded/Disabled")
            
        print("\nPrefect Config (Required):")
        print(f"  Project Name: {config.prefect.project_name}")
        print(f"  Flow Name: {config.prefect.flow_name}")
        print(f"  Interval (min): {config.prefect.schedule_interval_minutes}")
        
        print(f"\nPrompt Template Path: {config.prompt_template_path}")

    except Exception as e:
        print(f"\nError loading or validating configuration: {e}") 