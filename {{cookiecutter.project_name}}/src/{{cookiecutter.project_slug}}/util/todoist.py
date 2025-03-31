"""
Todoist API client for fetching and updating tasks.
"""

from typing import List, Dict, Optional, Any, Tuple
import logging
import time
import re
import os
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task, Project, Section
from requests.exceptions import RequestException as TodoistRequestError
from requests.exceptions import HTTPError

# Set up logging
logger = logging.getLogger(__name__)

# Constants
MAX_COMMENT_LENGTH = 14000

class TodoistClient:
    """Client for interacting with Todoist API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Todoist client with API key.
        
        Args:
            api_key: Todoist API key
        """
        if not api_key:
            raise ValueError("Todoist API key is required")
        
        self.api = TodoistAPI(api_key)
        logger.info("Todoist client initialized")
    
    def _split_content_at_sections(self, content: str, max_length: int = MAX_COMMENT_LENGTH) -> List[str]:
        """
        Split content at markdown section boundaries while respecting max length.
        
        Args:
            content: The content to split
            max_length: Maximum length for each part
            
        Returns:
            List of content parts, each within max_length
        """
        logger.info(f"Splitting content of length {len(content)} at {max_length}")
        if len(content) <= max_length:
            return [content]
            
        # Find all markdown section headers (h1-h6)
        section_pattern = r'^(#{1,6}\s.+)$'
        sections = re.finditer(section_pattern, content, re.MULTILINE)
        
        # Convert to list of (position, header) tuples
        section_positions = [(m.start(), m.group(1)) for m in sections]
        
        if not section_positions:
            # If no sections found, split at max_length
            return [content[i:i + max_length] for i in range(0, len(content), max_length)]
            
        parts = []
        current_pos = 0
        
        logger.info(f"Found {len(section_positions)} sections")
        while current_pos < len(content):
            # Find the last section that fits within max_length
            last_valid_section = None
            for pos, header in section_positions:
                if pos < current_pos:  # Skip sections we've already processed
                    continue
                if pos - current_pos > max_length:
                    break
                last_valid_section = pos
                
            if last_valid_section is None:
                # If no section fits, split at max_length
                parts.append(content[current_pos:current_pos + max_length])
                current_pos += max_length
            else:
                # Split at the last valid section
                parts.append(content[current_pos:last_valid_section])
                current_pos = last_valid_section
                
            logger.info(f"Current position: {current_pos}, Content length: {len(content)}")
            
            # If we've processed all sections but still have content left
            if current_pos >= len(content):
                break
                
            # If we're at the end of the content
            if current_pos >= len(content) - 1:
                break
                
            # If we've processed all sections
            if all(pos < current_pos for pos, _ in section_positions):
                # Add any remaining content
                if current_pos < len(content):
                    parts.append(content[current_pos:])
                break
                
            # If we're stuck at the same position, force a split
            if current_pos == last_valid_section:
                parts.append(content[current_pos:current_pos + max_length])
                current_pos += max_length
                if current_pos >= len(content):
                    break
        
        logger.info(f"Split content into {len(parts)} parts")
        return parts

    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def get_dev_project(self) -> Optional[Project]:
        """
        Get the dev project.
        
        Returns:
            Project object for dev project or None if not found
        """
        logger.info("Fetching dev project")
        projects = self.api.get_projects()
        
        for project in projects:
            if project.name == "dev":
                return project
        
        return None

    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def get_sub_projects(self, parent_id: str) -> List[Project]:
        """
        Get all sub-projects under a parent project.
        
        Args:
            parent_id: ID of the parent project
            
        Returns:
            List of Project objects
        """
        logger.info(f"Fetching sub-projects for parent {parent_id}")
        all_projects = self.api.get_projects()
        return [p for p in all_projects if getattr(p, 'parent_id', None) == parent_id]

    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def get_project_by_name(self, project_name: str) -> Project:
        """
        Get a project by name.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project object
            
        Raises:
            ValueError: If project not found
        """
        logger.info(f"Fetching project: {project_name}")
        projects = self.api.get_projects()
        
        for project in projects:
            if project.name == project_name:
                return project
        
        raise ValueError(f"Project '{project_name}' not found")
    
    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def get_section_by_name(self, project_id: str, section_name: str) -> Optional[Section]:
        """
        Get a section by name within a project.
        
        Args:
            project_id: ID of the project
            section_name: Name of the section
            
        Returns:
            Section object or None if not found
        """
        logger.info(f"Fetching section '{section_name}' in project {project_id}")
        sections = self.api.get_sections(project_id=project_id)
        
        for section in sections:
            if section.name == section_name:
                return section
        
        return None
    
    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def fetch_tasks(self, project_name: Optional[str] = None, section_name: Optional[str] = None, search_dev_subprojects: bool = True) -> List[Task]:
        """
        Fetch tasks from Todoist for a specific project and section.
        If search_dev_subprojects is True, it will search for tasks in the specified section
        across all sub-projects under the dev project.
        
        Args:
            project_name: Name of the project, or None if searching dev sub-projects
            section_name: Name of the section, or None for all sections
            search_dev_subprojects: Whether to search all sub-projects under dev
            
        Returns:
            List of Task objects
        """
        all_tasks = []
        
        if search_dev_subprojects:
            logger.info("Searching for tasks in dev sub-projects")
            dev_project = self.get_dev_project()
            if not dev_project:
                logger.warning("Dev project not found")
                return []
                
            sub_projects = self.get_sub_projects(dev_project.id)
            logger.info(f"Found {len(sub_projects)} sub-projects under dev")
            
            for project in sub_projects:
                if section_name:
                    section = self.get_section_by_name(project.id, section_name)
                    if section:
                        tasks = self.api.get_tasks(project_id=project.id, section_id=section.id)
                        all_tasks.extend(tasks)
                else:
                    tasks = self.api.get_tasks(project_id=project.id)
                    all_tasks.extend(tasks)
        else:
            if not project_name:
                raise ValueError("project_name is required when not searching dev sub-projects")
                
            project = self.get_project_by_name(project_name)
            if section_name:
                section = self.get_section_by_name(project.id, section_name)
                if section:
                    all_tasks = self.api.get_tasks(project_id=project.id, section_id=section.id)
                else:
                    logger.warning(f"Section '{section_name}' not found in project '{project_name}', fetching all tasks")
                    all_tasks = self.api.get_tasks(project_id=project.id)
            else:
                all_tasks = self.api.get_tasks(project_id=project.id)
        
        logger.info(f"Found {len(all_tasks)} tasks total")
        return all_tasks
    
    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def fetch_non_ideated_tasks(self, project_name: str, section_name: Optional[str] = None, ideated_label: str = "ideated") -> List[Task]:
        """
        Fetch tasks that don't have the ideated label.
        
        Args:
            project_name: Name of the project
            section_name: Name of the section, or None for all sections
            ideated_label: Label that marks tasks as already ideated
            
        Returns:
            List of Task objects without the ideated label
        """
        tasks = self.fetch_tasks(project_name, section_name)
        
        # Filter out tasks that already have the ideated label
        non_ideated_tasks = [task for task in tasks if not any(label == ideated_label for label in task.labels)]
        
        logger.info(f"Found {len(non_ideated_tasks)} tasks without the '{ideated_label}' label")
        return non_ideated_tasks
    
    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def update_task(self, task_id: str, **kwargs) -> Task:
        """
        Update a task with new attributes.
        
        Args:
            task_id: ID of the task to update
            **kwargs: Attributes to update (content, description, etc.)
            
        Returns:
            Updated Task object
        """
        logger.info(f"Updating task {task_id}")
        return self.api.update_task(task_id=task_id, **kwargs)
    
    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def add_comment(self, task_id: str, content: str) -> List[Dict[str, Any]]:
        """
        Add a comment to a task. If content exceeds MAX_COMMENT_LENGTH,
        splits it into multiple comments at markdown section boundaries.
        
        Args:
            task_id: ID of the task
            content: Comment content
            
        Returns:
            List of comment dictionaries
            
        Raises:
            HTTPError: If the API request fails
        """
        logger.info(f"Adding comment(s) to task {task_id}")
        
        # Split content if needed
        content_parts = self._split_content_at_sections(content)
        logger.info(f"Split content into {len(content_parts)} parts")
        comments = []
        
        try:
            for i, part in enumerate(content_parts, 1):
                if len(content_parts) > 1:
                    # Add part number to header if multiple parts
                    if part.startswith('# '):
                        part = f"# Part {i}\n\n{part}"
                    else:
                        part = f"# Part {i}\n\n{part}"
                
                logger.info(f"Adding comment {i} of {len(content_parts)}")
                comment = self.api.add_comment(task_id=task_id, content=part)
                comments.append(comment)
                
                # Add small delay between comments to avoid rate limiting
                if i < len(content_parts):
                    time.sleep(1)
                    
            return comments
            
        except HTTPError as e:
            # Log the error details including the payload
            error_msg = f"Failed to add comment to task {task_id}. Status code: {e.response.status_code}"
            if hasattr(e.response, 'text'):
                error_msg += f"\nResponse text: {e.response.text}"
            logger.error(error_msg)
            logger.error(f"Comment content that caused error (length: {len(content)}):\n{content}")
            raise
    
    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def update_task_with_ideation(self, task_id: str, ideation_result: str, ideated_label: str = "ideated") -> None:
        """
        Update a task with ideation results:
        1. Add ideation to description
        2. Add comment with ideation
        3. Add ideated label
        
        Args:
            task_id: ID of the task
            ideation_result: Result from LLM ideation
            ideated_label: Label to add to the task
        """
        logger.info(f"Updating task {task_id} with ideation results")
        
        # Get current task to get labels
        task = self.api.get_task(task_id=task_id)
        
        # Add ideated label if not already present
        labels = task.labels.copy() if task.labels else []
        if ideated_label not in labels:
            labels.append(ideated_label)
        
        # Update task with ideation
        self.update_task(
            task_id=task_id,
            labels=labels
        )
        
        # Add comment with ideation
        self.add_comment(task_id=task_id, content=f"# Ideation Results\n\n{ideation_result}")
        
        # Small delay to avoid rate limiting
        time.sleep(1)

    @retry(
        retry=retry_if_exception_type(TodoistRequestError),
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3)
    )
    def update_task_with_error(self, task_id: str, error_type: str, error_message: str) -> None:
        """
        Update a task with error information:
        1. Add error comment
        2. Do not add ideated label
        
        Args:
            task_id: ID of the task
            error_type: Type of error that occurred
            error_message: Detailed error message
        """
        logger.info(f"Updating task {task_id} with error information")
        
        # Add comment with error details
        error_comment = f"""# Error During Ideation

**Error Type:** {error_type}
**Error Message:** {error_message}

The ideation process failed after multiple retries. Please try again later or contact support if the issue persists."""
        
        self.add_comment(task_id=task_id, content=error_comment)
        
        # Small delay to avoid rate limiting
        time.sleep(1)

def main():
    """Test the add_comment functionality."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Get API key from environment
    api_key = os.getenv("TODOIST_API_KEY")
    if not api_key:
        raise ValueError("TODOIST_API_KEY environment variable is required")
    
    # Initialize client
    client = TodoistClient(api_key)
    
    # Read test content
    with open("test.txt", "r") as f:
        test_content = f.read()
    
    # Test task ID
    task_id = "9006602349"
    
    try:
        # Add comment
        logger.info(f"Testing add_comment with content length: {len(test_content)}")
        comments = client.add_comment(task_id, test_content)
        logger.info(f"Successfully added {len(comments)} comments")
        
        # Log each comment's length
        for i, comment in enumerate(comments, 1):
            logger.info(f"Comment {i} length: {len(comment.content)}")
            
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    main() 