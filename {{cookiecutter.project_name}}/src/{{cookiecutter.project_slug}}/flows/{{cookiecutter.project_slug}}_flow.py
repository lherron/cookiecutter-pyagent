"""
Generic Prefect flow for {{cookiecutter.project_name}}.
This serves as a template for creating specific flows.
"""

from prefect import flow, task, get_run_logger
from typing import Optional
import logging
from datetime import timedelta, datetime
import time
from prefect.schedules import Interval

# Assuming a basic config structure might exist, adjust as needed
# from ..config import load_config, AppConfig

# Set up logging
logger = logging.getLogger(__name__)

# Function to configure Prefect logging handler
def configure_prefect_logging():
    prefect_logger = get_run_logger()

    class PrefectHandler(logging.Handler):
        def emit(self, record):
            log_method_name = record.levelname.lower()
            if log_method_name == "warning":
                log_method_name = "warn"
            log_method = getattr(prefect_logger, log_method_name, prefect_logger.info)
            log_method(self.format(record))

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = PrefectHandler()
    handler.setFormatter(formatter)

    flow_logger = logging.getLogger(__name__)
    flow_logger.setLevel(logging.INFO)
    if not any(isinstance(h, PrefectHandler) for h in flow_logger.handlers):
        flow_logger.addHandler(handler)
    flow_logger.propagate = True

# Example task for loading configuration (optional, adjust as needed)
# @task(retries=0, cache_expiration=timedelta(seconds=0))
# def load_configuration(config_path: Optional[str] = None) -> AppConfig:
#     """
#     Load application configuration.
#     """
#     logger.info("Loading configuration")
#     # return load_config(config_path) # Replace with actual config loading if used
#     return {} # Placeholder

@task
def {{cookiecutter.project_slug}}_task(name: str = "world") -> str:
    """
    A generic example task for the flow.

    Args:
        name: A name to greet.

    Returns:
        A greeting message.
    """
    logger.info(f"Running the generic {{cookiecutter.project_slug}} task for '{name}'")
    # Replace with actual task logic
    result = f"Hello, {name} from the {{cookiecutter.project_slug}} task!"
    logger.info(f"Generic task finished with result: '{result}'")
    return result


@flow(name="{{ cookiecutter.project_name }}.{{ cookiecutter.project_slug }}_flow")
async def {{cookiecutter.project_slug}}_flow(config_path: Optional[str] = None) -> None:
    """
    Main generic flow orchestrating tasks.

    Args:
        config_path: Path to configuration file (optional).
    """
    configure_prefect_logging()
    logger.info("Starting {{ cookiecutter.project_slug }} flow")

    # Optional: Load configuration
    # config = load_configuration(config_path)
    # logger.info(f"Configuration loaded: {config}") # Adjust logging as needed

    # Example: Run the generic task
    try:
        task_result = {{cookiecutter.project_slug}}_task(name="{{cookiecutter.project_name}}")
        logger.info(f"Task completed with result: {task_result}")

    except Exception as e:
        logger.error(f"Flow failed during task execution: {e}")
        # Add more robust error handling if needed

    logger.info("{{ cookiecutter.project_slug | capitalize }} flow completed successfully")

# Example function to register flow schedule (optional)
# def register_flow_schedule():
#     """
#     Register the flow with a schedule (example).
#     """
#     # config = load_config() # Load config if schedule depends on it
#     schedule_interval_minutes = 15 # Example interval
#     schedule = Interval(
#         start_date=datetime.utcnow(),
#         interval=timedelta(minutes=schedule_interval_minutes)
#     )
#
#     # This requires interaction with a Prefect server/backend
#     # {{ cookiecutter.project_slug }}_flow.register(
#     #     project_name="{{cookiecutter.project_name}}", # Example project name
#     #     schedule=schedule
#     # )
#
#     logger.info(f"Flow registration setup for schedule: every {schedule_interval_minutes} minutes")

if __name__ == "__main__":
    # Example of running the flow manually
    {{cookiecutter.project_slug}}_flow() 