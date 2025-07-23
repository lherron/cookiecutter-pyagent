"""Main module for the {{cookiecutter.project_name}} agent."""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from evaitools.adapters.knowledge.knowledge import KeyTermRepository
from evaitools.adapters.mail.fastmail_client import FastmailClient
from evaitools.adapters.tasks.base import TaskProvider
from evaitools.adapters.tasks.todoist import TodoistClient
from evaitools.config import AppConfig, load_config
from evaitools.db import AsyncPGDatabase
from evaitools.models.key_terms import KeyTerm
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich import print

# Set up logger
logger = logging.getLogger(__name__)


class {{cookiecutter.agent_name}}:
    """Main agent class for the {{cookiecutter.project_name}} application."""

    def __init__(self, config: AppConfig | None = None):
        """
        Initialize the agent with configuration.

        Args:
            config: Application configuration. If None, default configuration will be loaded.
        """
        self.config = config if config is not None else load_config()
        logger.info("{{cookiecutter.agent_name}} initialized")

    async def fetch_data(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch Todoist Inbox tasks from external source (Todoist).

        Returns:
            Tuple of (Inbox tasks, Workout tasks) from Todoist
        """
        logger.info("Fetching Todoist Inbox tasks...")
        inbox_tasks: list[dict[str, Any]] = []
        workout_tasks: list[dict[str, Any]] = []
        todoist_cfg = getattr(self.config, "todoist", None)
        if todoist_cfg and todoist_cfg.api_key:
            try:
                client: TaskProvider = TodoistClient(api_key=todoist_cfg.api_key)

                inbox_project = client.get_project(name="Inbox")
                if not inbox_project:
                    logger.error("Todoist 'Inbox' project not found.")
                    return [], []
                tasks_result = client.list_tasks(project_id=inbox_project.id)
                inbox_tasks = []
                for task in tasks_result:
                    task_id = getattr(task, "id", "unknown")
                    task_content = getattr(task, "content", "")
                    task_due = getattr(task, "due", None)
                    task_due_str = task_due.string if task_due else None
                    inbox_tasks.append({"id": task_id, "content": task_content, "due": task_due_str})

                workout_project = client.get_project(name="Workouts")
                if not workout_project:
                    logger.error("Todoist 'Workouts' project not found.")
                    return inbox_tasks, []
                tasks_result = client.list_tasks(project_id=workout_project.id)
                workout_tasks = []
                for task in tasks_result:
                    task_id = getattr(task, "id", "unknown")
                    task_content = getattr(task, "content", "")
                    task_due = getattr(task, "due", None)
                    task_due_str = task_due.string if task_due else None
                    workout_tasks.append({"id": task_id, "content": task_content, "due": task_due_str})
                logger.info(f"Fetched {len(inbox_tasks)} tasks from Todoist Inbox.")
            except ValueError as ve:
                logger.error(f"Todoist operation error: {ve}")
            except Exception as e:
                logger.error(f"Error fetching Todoist tasks: {e}", exc_info=True)
        else:
            logger.info("Todoist config or API key not set; skipping Inbox task fetch.")
        return inbox_tasks, workout_tasks

    async def fetch_unread_emails(self) -> list[dict[str, Any]]:
        """Fetch unread emails from Fastmail via JMAP."""
        logger.info("Fetching unread emails from Fastmail...")
        messages: list[dict[str, Any]] = []
        jmap_cfg = getattr(self.config, "jmap", None)
        if not jmap_cfg or not jmap_cfg.api_key:
            logger.info("Fastmail config or API key not set; skipping email fetch.")
            return messages
        try:
            client = FastmailClient(jmap_config=jmap_cfg)
            folder_id = client.get_email_folder_id(jmap_cfg.inbox_folder)
            messages = client.get_unread_email_messages(folder_id=folder_id)[:5]
            logger.info(f"Fetched {len(messages)} unread messages from Fastmail.")
        except ValueError as ve:
            logger.error(f"Fastmail operation error: {ve}")
        except Exception as e:
            logger.error(f"Error fetching Fastmail messages: {e}", exc_info=True)
        return messages

    async def fetch_word_of_the_day(self) -> KeyTerm | None:
        """Return a random key term from the database if available."""
        dsn = getattr(self.config, "database", None)
        if not dsn:
            logger.info("Database configuration missing; skipping word of the day.")
            return None

        repo = KeyTermRepository(db=AsyncPGDatabase(dsn.dsn))
        await repo.open()
        try:
            return await repo.get_random_term()
        except Exception as exc:  # pragma: no cover - failure not expected in tests
            logger.error("Failed to fetch word of the day: %s", exc)
            return None
        finally:
            await repo.close()

    async def process_item(self, item: Any) -> dict[str, Any]:
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

    async def report_results(self, results: list[dict[str, Any]]) -> None:
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

    async def run(self) -> list[dict[str, Any]]:
        """Run the full agent workflow.

        Returns:
            Processing results
        """
        try:
            results: list[dict[str, Any]] = []

            # --- Fetch Todoist Inbox tasks ---
            inbox_tasks, workout_tasks = await self.fetch_data()
            unread_emails = await self.fetch_unread_emails()
            word_of_the_day = await self.fetch_word_of_the_day()

            # --- Jinja2 template rendering ---
            template_path = "AutomatedDailyTemplate.md"
            output_path = "/Users/lherron/Library/Mobile Documents/iCloud~md~obsidian/Documents/Unhobbled/Daily Plan/" + datetime.now().strftime("%Y-%m-%d") + ".md"

            # DO NOT REMOVE THIS COMMENT: template_path = "/Users/lherron/Library/Mobile Documents/iCloud~md~obsidian/Documents/Unhobbled/Templates/AutomatedDailyTemplate.md"
            if not template_path:
                logger.error("No template_path specified in config.")
                return results
            if not os.path.isfile(template_path):
                logger.error(f"Template file not found: {template_path}")
                return results

            template_dir, template_file = os.path.split(template_path)
            env = Environment(loader=FileSystemLoader(template_dir or "."), autoescape=select_autoescape(["html", "xml", "md"]))
            try:
                template = env.get_template(template_file)
            except Exception as e:
                logger.error(f"Failed to load template: {e}")
                return results

            rendered = template.render(
                results=results,
                inbox_tasks=inbox_tasks,
                workout_tasks=workout_tasks,
                unread_emails=unread_emails,
                word_of_the_day=word_of_the_day,
                now=datetime.now,
                timedelta=timedelta,
            )
            print("\n[bold green]Rendered Template:[/bold green]\n")
            print(rendered)
            output_filename = os.path.join(os.getcwd(), output_path)
            try:
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.write(rendered)
                logger.info(f"Rendered template written to {output_filename}")
            except Exception as e:
                logger.error(f"Failed to write rendered output: {e}")

            # --- Send email with rendered template ---
            jmap_cfg = getattr(self.config, "jmap", None)
            if jmap_cfg and jmap_cfg.api_key and jmap_cfg.user_email_address:
                try:
                    client = FastmailClient(jmap_config=jmap_cfg)
                    today = datetime.now().strftime("%Y-%m-%d")
                    subject = f"Daily Template for {today}"
                    success = client.send_email(
                        to_addresses=[{"name": "Lance", "email": jmap_cfg.user_email_address}],
                        subject=subject,
                        markdown_content=rendered,
                        from_email=jmap_cfg.agent_email_address,
                    )
                    if success:
                        logger.info(f"Successfully sent daily template email to {jmap_cfg.user_email_address}")
                    else:
                        logger.error("Failed to send daily template email")
                except Exception as e:
                    logger.error(f"Error sending daily template email: {e}", exc_info=True)
            else:
                logger.info("Fastmail config, API key, or user email address not set; skipping email send.")

            return results
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            raise
