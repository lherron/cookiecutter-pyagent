"""
Prefect flow definition for {{cookiecutter.project_name}}.
"""

from prefect import flow, task, get_run_logger
from typing import Optional, List, Dict, Any
import logging
import asyncio
import sys
from datetime import timedelta

# Import configuration loading
from {{cookiecutter.project_slug}}.config import load_config
from {{cookiecutter.project_slug}}.{{cookiecutter.project_slug}} import {{cookiecutter.project_name.replace('-', ' ').title().replace(' ', '')}}Agent
from prefect.schedules import Interval

# Get a logger for this flow module
logger = logging.getLogger(__name__)

def configure_prefect_logging():
    """Configures Python logging to integrate with Prefect's run logger."""
    prefect_logger = get_run_logger()

    class PrefectHandler(logging.Handler):
        def emit(self, record):
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
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
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
async def run_agent_task(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
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
            agent = {{cookiecutter.project_name.replace('-', ' ').title().replace(' ', '')}}Agent(config=config)
        else:
            agent = {{cookiecutter.project_name.replace('-', ' ').title().replace(' ', '')}}Agent()
        
        # Run the agent
        results = await agent.run()
        logger.info(f"Agent run completed with {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error in {{cookiecutter.project_slug}} agent task: {e}")
        raise

@flow(name="{{cookiecutter.project_slug}}.{{cookiecutter.project_slug}}_flow", log_prints=True)
async def {{cookiecutter.project_slug}}_flow(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
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
        results = await run_agent_task(config_path)
        logger.info(f"{{cookiecutter.project_slug}} flow completed with {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Flow failed: {e}")
        raise

def register_flow_schedule(config_path: Optional[str] = None) -> None:
    """
    Register the flow with a schedule based on configuration.
    
    Args:
        config_path: Path to configuration file (optional)
    """
    config = load_config(config_path=config_path) if config_path else load_config()
    schedule_interval_minutes = config.prefect.schedule_interval_minutes
    
    schedule=Interval(
        timedelta(minutes=schedule_interval_minutes),
        timezone="UTC"
    )    

    {{cookiecutter.project_slug}}_flow.serve(
        name="{{cookiecutter.project_slug}}",
        schedule=schedule
    )
    
    logger.info(f"Flow scheduled to run every {schedule_interval_minutes} minutes")

if __name__ == "__main__":
    # Run flow directly
    asyncio.run({{cookiecutter.project_slug}}_flow()) 