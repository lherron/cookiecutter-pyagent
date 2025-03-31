"""
Command line interface for {{cookiecutter.project_name}}.
"""

import logging
import sys
import asyncio
import os
from typing import Optional
import yaml
from datetime import timedelta
from functools import partial
from prefect.schedules import Interval
from prefect import serve, flow
from prefect import flow


import typer

from {{cookiecutter.project_slug}}.flows.{{cookiecutter.project_slug}}_flow import {{cookiecutter.project_slug}}_flow
from {{cookiecutter.project_slug}}.config import load_config, AppConfig
# Note: Assuming register_flow_schedule is defined elsewhere or needs implementation
# from {{cookiecutter.project_slug}}.flows.registration import register_flow_schedule 

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="{{cookiecutter.project_name}} CLI")

# Placeholder for the registration function if not defined elsewhere
# def register_flow_schedule(config_path: Optional[str] = None):
#    logger.warning(f"Placeholder function called for register_flow_schedule with config: {config_path}")
#    # Implement actual registration logic here
#    pass

@app.command()
def run(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file")
):
    """
    Run the {{cookiecutter.project_slug}} flow.
    """
    logger.info("Running {{cookiecutter.project_slug}} flow")
    # Typer handles running async functions
    async def run_flow_async(config_path: Optional[str] = None):
        """Run the {{cookiecutter.project_slug}} flow asynchronously."""
        await {{cookiecutter.project_slug}}_flow(config_path=config_path)

    asyncio.run(run_flow_async(config_path=config))


@app.command()
def schedule(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file. If not provided, attempts to load 'config.yaml'.")
):
    """
    Schedule the {{cookiecutter.project_slug}}_flow based on config.
    """
    logger.info("Scheduling flow")
    config_path = config if config else "config.yaml"  # Determine potential config path

    try:
        # Load configuration
        if config and os.path.exists(config_path):
            # If a specific config path was provided and exists, load it
            logger.debug(f"Loading configuration from provided path: {config_path}")
            app_config: AppConfig = load_config(config_path=config_path)
            effective_config_path = config_path # Use the provided path
        elif not config and os.path.exists(config_path):
            # If no config path provided, but default 'config.yaml' exists, load it
            logger.debug(f"Loading configuration from default path: {config_path}")
            app_config: AppConfig = load_config(config_path=config_path)
            effective_config_path = config_path # Use the default path
        else:
            # If path doesn't exist (or wasn't provided and default doesn't exist)
            if config:
                 logger.warning(f"Configuration file specified at '{config_path}' not found. Attempting to load default configuration.")
            else:
                 logger.info(f"Default configuration file '{config_path}' not found. Attempting to load default configuration settings.")
            app_config: AppConfig = load_config() # Call without arguments
            effective_config_path = None # No specific config file used for schedule

        logger.debug("Configuration loaded successfully.")

        {{cookiecutter.project_slug}}_flow.serve(name="flowing", cron="* * * * *")
    except Exception as e:
        logger.error(f"An unexpected error occurred during scheduling: {e}")
        # logger.exception("Detailed error:") # Uncomment for detailed traceback
        raise typer.Exit(code=1)

    # TODO: Implement the schedule logic here


def main():
    """Main entry point for the CLI."""
    # Typer handles command parsing and execution
    app()

if __name__ == "__main__":
    main() 