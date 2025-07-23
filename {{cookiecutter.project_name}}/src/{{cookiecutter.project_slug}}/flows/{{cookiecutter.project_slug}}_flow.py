"""
Prefect flow definition for {{cookiecutter.project_name}}.
"""

import asyncio
import logging
import sys
from typing import Any

# Import configuration loading
from evaitools.config import load_config
from prefect import flow, get_run_logger, task
from prefect.schedules import Cron
from rich import print

from {{cookiecutter.project_slug}}.{{cookiecutter.project_slug}} import {{cookiecutter.agent_name}}

# Get a logger for this flow module
logger = logging.getLogger(__name__)


def configure_prefect_logging() -> None:
    """Configures Python logging to integrate with Prefect's run logger."""
    prefect_logger = get_run_logger()

    class PrefectHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log_entry = self.format(record)
            # Map standard levels to Prefect levels
            level = record.levelname.lower()
            if level == "warning":
                level = "warn"
            elif level == "critical":
                level = "critical"  # Prefect uses critical
            # Use getattr to safely get the log method
            log_method = getattr(prefect_logger, level, prefect_logger.info)
            try:
                log_method(log_entry)
            except Exception as e:
                # Fallback in case of issues with Prefect logger itself
                print(f"Error logging to Prefect: {e}\nOriginal log: {log_entry}", file=sys.stderr)

    # Configure formatter
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler = PrefectHandler()
    handler.setFormatter(formatter)

    # Configure the root logger for the package
    package_logger = logging.getLogger("{{cookiecutter.project_slug}}")

    # Clear existing handlers to avoid duplicates if flow runs multiple times
    package_logger.handlers.clear()

    # Add the Prefect handler
    package_logger.addHandler(handler)

    # Set level (can be controlled by global settings or debug flags later)
    # Let the root logger control the effective level for now
    package_logger.setLevel(logging.DEBUG)  # Log DEBUG and above from the package

    # Prevent logs from propagating to the root logger's handlers (like basicConfig)
    package_logger.propagate = False

    logger.info("Prefect logging configured for '{{cookiecutter.project_slug}}' package.")


@task(retries=3, retry_delay_seconds=60, log_prints=True)
async def run_agent_task(config_path: str | None = None) -> list[dict[str, Any]]:
    """
    Task to run the {{cookiecutter.project_name}} agent.

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        List[Dict[str, Any]]: Results of the agent run
    """
    logger.info("Starting {{cookiecutter.project_slug}} agent task")

    try:
        # Initialize the agent with config if provided
        if config_path:
            config = load_config(config_path=config_path)
            agent = {{cookiecutter.agent_name}}(config=config)
        else:
            agent = {{cookiecutter.agent_name}}()

        # Run the agent
        results: list[dict[str, Any]] = await agent.run()
        logger.info(f"Agent run completed with {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Error in {{cookiecutter.project_slug}} agent task: {e}")
        raise


@flow(name="{{cookiecutter.project_slug}}.{{cookiecutter.project_slug}}_flow", log_prints=True)
async def {{cookiecutter.project_slug}}_flow(config_path: str | None = None) -> list[dict[str, Any]]:
    """
    Main flow for the {{cookiecutter.project_name}} agent.

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        List[Dict[str, Any]]: Results from the agent run
    """
    configure_prefect_logging()
    logger.info("Starting {{cookiecutter.project_slug}} flow")

    try:
        # Run the agent
        results: list[dict[str, Any]] = await run_agent_task(config_path)
        logger.info(f"{{cookiecutter.project_slug}} flow completed with {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Flow failed: {e}")
        raise


def register_flow_schedule(config_path: str | None = None) -> None:
    """
    Register the flow with a schedule based on configuration.

    Args:
        config_path: Path to configuration file (optional)
    """
    # config = load_config(config_path=config_path) if config_path else load_config() # No longer needed for schedule
    # schedule_interval_minutes = config.prefect.schedule_interval_minutes # No longer needed

    schedule = Cron(
        "0 4 * * *",  # Run daily at 4:00 AM
        timezone="America/Chicago",  # Updated timezone
    )

    {{cookiecutter.project_slug}}_flow.serve(name="{{cookiecutter.project_slug}}", schedule=schedule)

    logger.info("Flow scheduled to run daily at 4:00 AM America/Chicago")  # Updated log message


if __name__ == "__main__":
    # Run flow directly
    asyncio.run({{cookiecutter.project_slug}}_flow())
