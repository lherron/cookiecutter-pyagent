#!/usr/bin/env python3
"""
Script to run the default ideation flow.
"""

import os
import traceback
import sys
import logging
import asyncio
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.append(str(src_dir))

from {{cookiecutter.project_slug}}.flows import {{cookiecutter.project_slug}}_flow
from {{cookiecutter.project_slug}}.config import load_config
from prefect import get_run_logger

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Remove Prefect-specific logging configuration
# logging.getLogger("prefect").setLevel(logging.DEBUG)
# logging.getLogger("prefect.flows").setLevel(logging.DEBUG)
# logging.getLogger("prefect.tasks").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

def main():
    """Run the ideation flow."""
    try:
        # Load configuration
        config = load_config()
        
        # Log configuration status
        logger.info("Configuration loaded successfully")
        
        # Run the flow
        asyncio.run({{cookiecutter.project_slug}}_flow())
        
    except Exception as e:
        print(f"Error running ideation flow: {str(e)}")
        stacktrace = traceback.format_exc()
        logger.error(f"Error running ideation flow: {str(e)}")
        logger.error(f"Stack trace: {stacktrace}")
        sys.exit(1)

if __name__ == "__main__":
    main() 