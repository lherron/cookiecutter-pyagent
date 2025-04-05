"""
Command line interface for {{cookiecutter.project_name}}.
"""

import logging
import traceback
import sys
import asyncio
import os
from typing import Optional
from functools import partial
from datetime import timedelta

import typer
from rich import print

# Import config loading and the main flow
from {{cookiecutter.project_slug}}.config import AppConfig, load_config
from pydantic import ValidationError
from {{cookiecutter.project_slug}}.flows import {{cookiecutter.project_slug}}_flow

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,  # Default level
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# Get the root logger for CLI messages
logger = logging.getLogger("{{cookiecutter.project_slug}}.cli")

# Create the Typer app
app = typer.Typer(
    name="{{cookiecutter.project_slug}}",
    help="{{cookiecutter.description}}",
    add_completion=False
)

def setup_logging(debug: bool):
    """Configure logging level."""
    level = logging.DEBUG if debug else logging.INFO
    # Configure root logger level
    logging.getLogger().setLevel(level)
    # Configure this app's logger level
    logging.getLogger("{{cookiecutter.project_slug}}").setLevel(level)
    logger.info(f"Logging level set to {logging.getLevelName(level)}")
    if debug:
        # Optionally enable deeper debugging for dependencies like prefect, httpx
        # logging.getLogger("prefect").setLevel(logging.DEBUG)
        # logging.getLogger("httpx").setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled.")


# --- CLI Commands ---

@app.command()
def run(
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to the configuration file (e.g., config.yaml)."
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Enable debug logging output."
    )
):
    """
    Run the {{cookiecutter.project_name}} agent flow once.
    """
    setup_logging(debug)
    logger.info(f"Running {{cookiecutter.project_name}} flow...")

    try:
        # Configuration is loaded implicitly by the flow if needed,
        # but we pass the path if specified.
        logger.info(f"Using config path: {config_path if config_path else 'Default (config.yaml or env vars)'}")

        # Run the async Prefect flow
        # Prefect flows are often async, use asyncio.run
        async def _run_flow():
             # The flow itself should handle config loading using load_config(config_path)
             await {{cookiecutter.project_slug}}_flow(config_path=config_path)

        asyncio.run(_run_flow())

        logger.info("Flow execution finished.")

    except FileNotFoundError:
        logger.error(f"Error: Configuration file not found at '{config_path}'.")
        if not config_path:
             logger.error("Specify the config file with --config or ensure config.yaml exists.")
        raise typer.Exit(code=1)
    except ValidationError as e: # Catch Pydantic validation errors
        logger.error(f"Configuration validation error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during flow execution: {e}")
        if debug:
            logger.error(traceback.format_exc()) # Print traceback if in debug mode
        raise typer.Exit(code=1)

@app.command()
def schedule(
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to the configuration file (e.g., config.yaml)."
    ),
    deploy: bool = typer.Option(
        False, "--deploy", "-d", help="Deploy the flow to run on the configured schedule."
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug logging output."
    )
):
    """
    Schedule the {{cookiecutter.project_name}} agent flow to run periodically.
    """
    setup_logging(debug)
    logger.info("Configuring flow schedule...")

    try:
        # Load configuration to get schedule details
        # Pass the path explicitly to load_config
        config = load_config(config_path=config_path)
        interval = config.prefect.schedule_interval_minutes

        logger.info(f"Configuration loaded. Schedule interval: {interval} minutes.")

        if deploy:
            logger.info("Attempting to deploy flow with schedule...")
            # --- Deployment Logic ---
            # This requires a deployment function. For now, it's a placeholder.
            # Replace 'register_flow_schedule' with your actual deployment mechanism.
            # Example using Prefect's serve (adjust imports and function signature):
            try:
                 from prefect import serve

                 # Create a partial function or use parameters with serve if flow needs config_path
                 flow_to_serve = partial({{cookiecutter.project_slug}}_flow, config_path=config_path)
                 # Alternatively, if flow loads config internally based on runtime context:
                 # flow_to_serve = {{cookiecutter.project_slug}}_flow

                 deployment = serve(
                     flow_to_serve.to_deployment( # type: ignore
                         name=f"{config.prefect.flow_name}-deployment",
                         schedule=timedelta(minutes=interval),
                         # Add tags, parameters, etc. as needed
                     )
                 )
                 # Note: serve() is typically blocking. You might run this in a separate process
                 # or use Prefect Cloud/Server agents for persistent scheduling.
                 # For a simple CLI trigger, the above might hang. Consider just logging intent.

                 logger.info(f"Prefect `serve` called for flow '{config.prefect.flow_name}' "
                             f"with interval {interval} minutes. Ensure an agent is running.")
                 # If serve is non-blocking or you adapt this:
                 # logger.info("Flow deployment command issued.")

            except ImportError:
                 logger.error("Prefect `serve` not available. Cannot deploy schedule directly from CLI this way.")
                 logger.error("Ensure Prefect is installed and consider alternative deployment methods (e.g., `prefect deploy`).")
                 raise typer.Exit(code=1)
            except Exception as deploy_exc:
                 logger.error(f"Error during flow deployment/serving: {deploy_exc}")
                 if debug:
                      logger.error(traceback.format_exc())
                 raise typer.Exit(code=1)

        else:
            logger.info(f"Flow schedule: Run every {interval} minutes.")
            logger.info("Run with the --deploy flag to activate the schedule (requires Prefect setup).")

    except FileNotFoundError:
        logger.error(f"Error: Configuration file not found at '{config_path}'.")
        if not config_path:
             logger.error("Specify the config file with --config or ensure config.yaml exists.")
        raise typer.Exit(code=1)
    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during scheduling setup: {e}")
        if debug:
            logger.error(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def info(
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to the configuration file (e.g., config.yaml)."
    )
):
    """
    Display loaded configuration information.
    """
    logger.info("Loading configuration to display...")
    try:
        config = load_config(config_path=config_path)

        print("\n[bold cyan]{{cookiecutter.project_name}} Configuration:[/bold cyan]")
        print("-" * 40)

        # Display Prefect Config (Required)
        print("[bold green]Prefect:[/bold green]")
        print(f"  Project Name: {config.prefect.project_name}")
        print(f"  Flow Name:    {config.prefect.flow_name}")
        print(f"  Schedule:     {config.prefect.schedule_interval_minutes} minutes")

        # Display LLM Config (Optional)
        if config.llm:
            print("\n[bold green]LLM:[/bold green]")
            print(f"  Provider:    {config.llm.provider or '[Not Set]'}")
            if config.llm.provider == "anthropic" and config.llm.anthropic:
                print(f"  Anthropic Model: {config.llm.anthropic.model}")
                print(f"  Anthropic Key:   {'Configured' if config.llm.anthropic.api_key else '[Not Set]'}")
            elif config.llm.provider == "gemini" and config.llm.gemini:
                print(f"  Gemini Model: {config.llm.gemini.model}")
                print(f"  Gemini Key:   {'Configured' if config.llm.gemini.api_key else '[Not Set]'}")
        else:
            print("\n[yellow]LLM:          [Not Configured][/yellow]")

        # Display Prompt Template Path
        print("\n[bold green]Prompt Template:[/bold green]")
        print(f"  Path: {config.prompt_template_path}")

        # Add other sections here if included in your template config.py
        # Example:
        # if config.service_client:
        #     print("\n[bold green]Service Client:[/bold green]")
        #     print(f"  Base URL: {config.service_client.base_url}")
        #     print(f"  API Key:  {'Configured' if config.service_client.api_key else '[Not Set]'}")
        # else:
        #     print("\n[yellow]Service Client: [Not Configured][/yellow]")

        print("-" * 40)
        print(f"Note: Configuration loaded considering '{config_path if config_path else 'Default (config.yaml or env vars)'}' and environment variables.")

    except FileNotFoundError:
        logger.error(f"Error: Configuration file not found at '{config_path}'.")
        if not config_path:
             logger.error("Specify the config file with --config or ensure config.yaml exists.")
        raise typer.Exit(code=1)
    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"An unexpected error occurred while displaying configuration: {e}")
        raise typer.Exit(code=1)

# --- Main Execution ---

def main():
    """Main entry point for the CLI application."""
    app()

if __name__ == "__main__":
    main() 