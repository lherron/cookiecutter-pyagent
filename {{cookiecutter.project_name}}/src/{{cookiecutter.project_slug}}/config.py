"""
Configuration management for {{ cookiecutter.project_name }}.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field, ValidationError
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# --- LLM Specific Config Models (Keep structure, make keys optional) ---
class AnthropicConfig(BaseModel):
    """Anthropic-specific configuration."""
    api_key: Optional[str] = Field(None, description="Anthropic API key (env: ANTHROPIC_API_KEY)")
    model: str = Field("claude-3-sonnet-20240229", description="Model to use")
    max_tokens: int = Field(2000, description="Maximum tokens in response")
    temperature: float = Field(0.7, description="Model temperature (0.0-1.0)")

class GeminiConfig(BaseModel):
    """Gemini-specific configuration."""
    api_key: Optional[str] = Field(None, description="Gemini API key (env: GEMINI_API_KEY)")
    model: str = Field("gemini-1.5-flash", description="Model to use")

class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: Optional[str] = Field(None, description="LLM provider ('anthropic' or 'gemini') (env: LLM_PROVIDER)")
    anthropic: Optional[AnthropicConfig] = Field(None, description="Anthropic settings")
    gemini: Optional[GeminiConfig] = Field(None, description="Gemini settings")

# --- Prefect Config Model (Keep as required) ---
class PrefectConfig(BaseModel):
    """Prefect configuration."""
    project_name: str = Field("{{ cookiecutter.project_slug }}", description="Prefect project name (env: PREFECT_PROJECT_NAME)")
    flow_name: str = Field("{{ cookiecutter.project_name }} Flow", description="Flow name (env: PREFECT_FLOW_NAME)")
    schedule_interval_minutes: int = Field(30, description="Schedule interval in minutes (env: PREFECT_SCHEDULE_INTERVAL_MINUTES)")

# --- Placeholder for Service Client Config (User can add specifics) ---
# class ServiceClientConfig(BaseModel):
#     """Example configuration for a specific service client."""
#     api_key: Optional[str] = Field(None, description="API key for the service")
#     base_url: str = Field("https://api.example.com", description="Service API base URL")

# --- Main Application Config Model ---
class AppConfig(BaseModel):
    """Main application configuration."""
    llm: Optional[LLMConfig] = Field(None, description="LLM configuration (optional)")
    prefect: PrefectConfig = Field(..., description="Prefect configuration (required)")
    # Add placeholders for other common optional configs
    # service_client: Optional[ServiceClientConfig] = Field(None, description="Example Service Client config")
    prompt_template_path: str = Field(
        "templates/prompt.jinja2",
        description="Path to the Jinja2 template for LLM prompts (env: PROMPT_TEMPLATE_PATH)"
    )
    # Add other top-level config items as needed

# --- Helper Functions (Adapted from email-triage-agent) ---

def _get_env_var(key: str, default: Any = None) -> Any:
    """Helper to get environment variable, returning default if not set or empty."""
    value = os.getenv(key)
    return value if value else default

def _load_section_config(section_key: str, model: Type[BaseModel], config_data: Dict[str, Any], env_prefix: str) -> Optional[BaseModel]:
    """Loads configuration for a specific section, overriding with env vars."""
    section_data = config_data.get(section_key, {})
    env_overrides: Dict[str, Any] = {} # Ensure type hint

    # Special handling for API keys directly from env
    if section_key == "llm":
        anthropic_api_key = _get_env_var("ANTHROPIC_API_KEY")
        gemini_api_key = _get_env_var("GEMINI_API_KEY")
        if anthropic_api_key or gemini_api_key:
            # Ensure provider is set if a key is found and provider isn't already set
            if "provider" not in section_data and "provider" not in env_overrides:
                 if anthropic_api_key and not gemini_api_key:
                     env_overrides["provider"] = "anthropic"
                 elif gemini_api_key and not anthropic_api_key:
                     env_overrides["provider"] = "gemini"
                 # If both keys are set, provider must be specified manually

            # Inject keys into nested config if not already present
            if anthropic_api_key:
                anthropic_conf = env_overrides.get("anthropic", section_data.get("anthropic", {}))
                if isinstance(anthropic_conf, dict) and "api_key" not in anthropic_conf:
                     anthropic_conf["api_key"] = anthropic_api_key
                     env_overrides["anthropic"] = anthropic_conf
            if gemini_api_key:
                gemini_conf = env_overrides.get("gemini", section_data.get("gemini", {}))
                if isinstance(gemini_conf, dict) and "api_key" not in gemini_conf:
                     gemini_conf["api_key"] = gemini_api_key
                     env_overrides["gemini"] = gemini_conf

    # Generic handling for model fields from environment variables
    for field_name, field_info in model.model_fields.items():
        # Handle nested models (like anthropic/gemini within llm)
        # Check if the annotation is a Type and a subclass of BaseModel
        is_basemodel_subclass = False
        if isinstance(field_info.annotation, type):
             try:
                 if issubclass(field_info.annotation, BaseModel):
                     is_basemodel_subclass = True
             except TypeError: # Handle cases like Optional[BaseModel] which aren't types
                 pass

        if is_basemodel_subclass:
            nested_model = field_info.annotation
            nested_env_prefix = f"{env_prefix}_{field_name.upper()}"
            nested_data = section_data.get(field_name, {})
            nested_env_overrides: Dict[str, Any] = {} # Ensure type hint

            for nested_field_name in nested_model.model_fields.keys():
                 nested_env_var = f"{nested_env_prefix}_{nested_field_name.upper()}"
                 env_val = _get_env_var(nested_env_var)
                 if env_val is not None:
                     # Attempt type conversion if needed (basic example)
                     nested_field_type = nested_model.model_fields[nested_field_name].annotation
                     try:
                         if nested_field_type == int:
                             env_val = int(env_val)
                         elif nested_field_type == float:
                             env_val = float(env_val)
                         elif nested_field_type == bool:
                             env_val = env_val.lower() in ['true', '1', 'yes']
                     except ValueError:
                         logger.warning(f"Could not convert env var {nested_env_var} value '{env_val}' to type {nested_field_type}.")
                         env_val = None
                 if env_val is not None:
                     nested_env_overrides[nested_field_name] = env_val

            # Merge env overrides into nested data from file
            merged_nested_data = {**nested_data, **nested_env_overrides}
            if merged_nested_data: # Only add nested config if it has data
                 env_overrides[field_name] = merged_nested_data

        else: # Handle simple fields
            env_var = f"{env_prefix}_{field_name.upper()}"
            env_val = _get_env_var(env_var)
            if env_val is not None:
                # Attempt type conversion
                field_type = field_info.annotation
                # Handle Optional types correctly
                origin = getattr(field_type, '__origin__', None)
                args = getattr(field_type, '__args__', [])

                actual_type = field_type
                if origin is Optional and args:
                     actual_type = args[0]

                try:
                    if actual_type == int:
                         env_val = int(env_val)
                    elif actual_type == float:
                         env_val = float(env_val)
                    elif actual_type == bool:
                         env_val = env_val.lower() in ['true', '1', 'yes']
                    # Add other type conversions as needed
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert env var {env_var} value '{env_val}' to type {actual_type}.")
                    env_val = None

            if env_val is not None:
                env_overrides[field_name] = env_val

    # Merge environment overrides into the data loaded from the file
    final_data = {**section_data, **env_overrides}

    # If after merging, there's no data for the section, return None
    # Exception: Prefect is required, so it should load even if empty initially to get defaults/fail validation
    if not final_data and section_key != "prefect":
        return None

    # Validate and create the model instance
    try:
        instance = model(**final_data)
        # Log successful load only if data was actually present or it's the required Prefect section
        if final_data:
             logger.debug(f"Successfully loaded and validated config for section '{section_key}'")
        return instance
    except ValidationError as e:
        # Log specific validation errors
        logger.error(f"Configuration validation error for section '{section_key}':")
        for error in e.errors():
             logger.error(f"  Field: {'.'.join(map(str, error['loc'])) if error['loc'] else 'N/A'}, Error: {error['msg']}")

        # For optional sections, return None if validation fails
        if section_key in ["llm", "service_client"]: # Update with actual optional sections
             logger.warning(f"Optional configuration section '{section_key}' failed validation, treating as disabled.")
             return None
        else: # Re-raise for mandatory sections like Prefect
             logger.error(f"Mandatory configuration section '{section_key}' failed validation.")
             raise e


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load configuration from a YAML file and environment variables.
    Environment variables take precedence. Optional sections are loaded only if found.

    Args:
        config_path: Path to the config.yaml file, or None to use default.

    Returns:
        AppConfig object.
    """
    # Default config path is in the project root relative to this file's location
    if config_path is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        config_path = base_dir / "config.yaml"
    else:
        config_path = Path(config_path) # Ensure it's a Path object

    config_data: Dict[str, Any] = {}
    if config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        try:
            with open(config_path, "r") as f:
                loaded_yaml = yaml.safe_load(f)
                if loaded_yaml:
                    config_data = loaded_yaml
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {config_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading config file {config_path}: {e}")
    else:
        logger.info(f"Config file '{config_path}' not found. Loading from environment variables and defaults.")

    # Load sections
    llm_config = _load_section_config("llm", LLMConfig, config_data, "LLM")
    prefect_config_obj = _load_section_config("prefect", PrefectConfig, config_data, "PREFECT")
    # Ensure PrefectConfig is not None (it's required)
    if prefect_config_obj is None:
         # This should ideally be caught by validation inside _load_section_config,
         # but double-check here. Load with defaults if somehow it ended up None.
         logger.warning("Prefect configuration was unexpectedly None, attempting to load defaults.")
         prefect_config_obj = PrefectConfig()


    # Load general settings
    prompt_template_path = _get_env_var(
        "PROMPT_TEMPLATE_PATH",
        config_data.get("prompt_template_path", "templates/prompt.jinja2")
    )

    # Create the final AppConfig object
    try:
        app_config = AppConfig(
            llm=llm_config,
            prefect=prefect_config_obj, # Use the loaded (or default) object
            prompt_template_path=prompt_template_path
            # Add other sections here if they become mandatory
        )
        logger.info("Configuration loaded successfully.")
        return app_config
    except ValidationError as e:
        logger.critical(f"FATAL: Final application configuration failed validation: {e}")
        raise

# Example usage within the module (for testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print("Testing configuration loading...")
    # Example: Set environment variables for testing
    # os.environ["LLM_PROVIDER"] = "anthropic"
    # os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key_from_env"
    # os.environ["PREFECT_PROJECT_NAME"] = "my-{{cookiecutter.project_slug}}-env-test"
    # os.environ["PREFECT_SCHEDULE_INTERVAL_MINUTES"] = "15"

    try:
        config = load_config()
        print("\n--- Loaded Configuration ---")
        print(config.model_dump_json(indent=2))
        print("--- Configuration Loading Test Complete ---")
    except Exception as e:
        print(f"\nError during configuration loading test: {e}")