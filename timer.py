"""Timer logic and state management."""

from typing import Optional, Tuple, List
from models import Task, Project
from storage import DataStore


class TimerManager:
    """Manages timer operations."""

    def __init__(self, store: Optional[DataStore] = None):
        self.store = store or DataStore()

    def start_timer(self, project_name: str, description: str) -> Tuple[bool, str]:
        """
        Start a timer for a new task.

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if there's already a running task
        running_task = self.store.get_running_task()
        if running_task:
            return False, "A timer is already running. Stop it first."

        # Validate project exists
        project = self.store.get_project_by_name(project_name)
        if not project:
            return False, f"Project '{project_name}' not found. Create it first with 'rolex project add'."

        # Create new task
        task = Task(project_id=project.id, description=description)
        task.start_entry()

        # Save task
        self.store.add_task(task)

        return True, f"Timer started for '{project_name}': {description}"

    def resume_timer(self, task_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Resume a stopped timer.

        Args:
            task_id: Specific task to resume. If None, returns list of stopped tasks.

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if there's already a running task
        running_task = self.store.get_running_task()
        if running_task:
            return False, "A timer is already running. Stop it first."

        # If task_id provided, resume that specific task
        if task_id:
            task = self.store.get_task_by_id(task_id)
            if not task:
                return False, f"Task not found."
            if not task.is_stopped():
                return False, "Task is not in stopped state."

            task.resume()
            self.store.update_task(task)
            return True, "Timer resumed."

        # No task_id provided - caller should handle task selection
        stopped_tasks = self.store.get_stopped_tasks()
        if not stopped_tasks:
            return False, "No stopped tasks to resume."

        # Signal to CLI that task selection is needed
        return False, "Task selection needed."

    def stop_timer(self) -> Tuple[bool, str, Optional[Task]]:
        """
        Stop the currently running timer (keeps it resumable).

        Returns:
            Tuple of (success: bool, message: str, task: Optional[Task])
        """
        running_task = self.store.get_running_task()
        if not running_task:
            return False, "No running timer to stop.", None

        if not running_task.is_running():
            return False, "Task is not running.", None

        running_task.stop()
        self.store.update_task(running_task)

        return True, "Timer stopped.", running_task

    def get_status(self) -> Tuple[bool, str, Optional[Task], Optional[Project], List[Task]]:
        """
        Get timer status including running task and stopped tasks.

        Returns:
            Tuple of (has_running: bool, status: str, running_task: Optional[Task],
                      project: Optional[Project], stopped_tasks: List[Task])
        """
        running_task = self.store.get_running_task()
        stopped_tasks = self.store.get_stopped_tasks()

        if not running_task:
            return False, "No running timer.", None, None, stopped_tasks

        # Get project info
        projects = self.store.get_projects()
        project = next((p for p in projects if p.id == running_task.project_id), None)

        return True, "running", running_task, project, stopped_tasks
