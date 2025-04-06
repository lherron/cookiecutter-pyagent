"""Main module for the {{cookiecutter.project_name}} agent."""

import logging
import asyncio
from typing import Optional, List, Any, Dict

from {{cookiecutter.project_slug}}.config import load_config, AppConfig

# Set up logger
logger = logging.getLogger(__name__)

class {{cookiecutter.project_slug.replace('_', ' ').title().replace(' ', '')}}Agent:
    """Main agent class for the {{cookiecutter.project_name}} application."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Application configuration. If None, default configuration will be loaded.
        """
        self.config = config if config is not None else load_config()
        logger.info("{{cookiecutter.project_slug.replace('_', ' ').title().replace(' ', '')}}Agent initialized")
    
    async def fetch_data(self) -> List[Any]:
        """Fetch data from external sources.
        
        Returns:
            List of items to process
        """
        logger.info("Fetching data...")
        # In a real agent, this would interact with an API or data source
        # Example: Use self.config.service_client if defined
        await asyncio.sleep(1)  # Simulate async work
        fetched_items = [{"id": 1, "data": "item one"}, {"id": 2, "data": "item two"}]
        logger.info(f"Fetched {len(fetched_items)} items.")
        return fetched_items
    
    async def process_item(self, item: Any) -> Dict[str, Any]:
        """Process a single data item.
        
        Args:
            item: The item to process
            
        Returns:
            Processed result
        """
        item_id = item.get("id", "unknown")
        logger.info(f"Processing item {item_id}...")
        # In a real agent, this might involve LLM calls, calculations, etc.
        # Example: Use self.config.llm if defined
        await asyncio.sleep(0.5)  # Simulate async work
        result = {"id": item_id, "processed_data": f"processed_{item['data']}", "status": "success"}
        logger.info(f"Finished processing item {item_id}.")
        return result
    
    async def report_results(self, results: List[Dict[str, Any]]) -> None:
        """Report or store the processing results.
        
        Args:
            results: The processing results to report
        """
        logger.info(f"Reporting results for {len(results)} items...")
        # In a real agent, this might save to a DB, send a notification, etc.
        for result in results:
            logger.debug(f"Result: {result}")
        await asyncio.sleep(0.2)  # Simulate async work
        logger.info("Finished reporting results.")
    
    async def run(self) -> List[Dict[str, Any]]:
        """Run the full agent workflow.
        
        Returns:
            Processing results
        """
        try:
            # Fetch data
            items_to_process = await self.fetch_data()
            
            if not items_to_process:
                logger.info("No items to process. Finishing early.")
                return []
            
            # Process each item
            results = []
            for item in items_to_process:
                result = await self.process_item(item)
                results.append(result)
            
            # Report results
            await self.report_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            raise


