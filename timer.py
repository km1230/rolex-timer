"""Timer logic and state management."""

from typing import Optional, Tuple
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
        # Check if there's already an active task
        active_task_id = self.store.get_active_task_id()
        if active_task_id:
            active_task = self.store.get_task_by_id(active_task_id)
            if active_task and (active_task.is_running() or active_task.is_paused()):
                return False, "A timer is already running. Stop or pause it first."

        # Validate project exists
        project = self.store.get_project_by_name(project_name)
        if not project:
            return False, f"Project '{project_name}' not found. Create it first with 'rolex project add'."

        # Create new task
        task = Task(project_id=project.id, description=description)
        task.start_entry()

        # Save task and set as active
        self.store.add_task(task)
        self.store.set_active_task_id(task.id)

        return True, f"Timer started for '{project_name}': {description}"

    def pause_timer(self) -> Tuple[bool, str]:
        """
        Pause the currently running timer.

        Returns:
            Tuple of (success: bool, message: str)
        """
        active_task_id = self.store.get_active_task_id()
        if not active_task_id:
            return False, "No active timer to pause."

        task = self.store.get_task_by_id(active_task_id)
        if not task:
            return False, "Active task not found."

        if not task.is_running():
            if task.is_paused():
                return False, "Timer is already paused."
            else:
                return False, "No running timer to pause."

        task.pause_current_entry()
        self.store.update_task(task)

        return True, "Timer paused."

    def resume_timer(self) -> Tuple[bool, str]:
        """
        Resume a paused timer.

        Returns:
            Tuple of (success: bool, message: str)
        """
        active_task_id = self.store.get_active_task_id()
        if not active_task_id:
            return False, "No active timer to resume."

        task = self.store.get_task_by_id(active_task_id)
        if not task:
            return False, "Active task not found."

        if not task.is_paused():
            if task.is_running():
                return False, "Timer is already running."
            else:
                return False, "No paused timer to resume."

        task.resume_current_entry()
        self.store.update_task(task)

        return True, "Timer resumed."

    def stop_timer(self) -> Tuple[bool, str, Optional[Task]]:
        """
        Stop and finalize the current timer.

        Returns:
            Tuple of (success: bool, message: str, task: Optional[Task])
        """
        active_task_id = self.store.get_active_task_id()
        if not active_task_id:
            return False, "No active timer to stop.", None

        task = self.store.get_task_by_id(active_task_id)
        if not task:
            return False, "Active task not found.", None

        if not task.is_running() and not task.is_paused():
            return False, "No running or paused timer to stop.", None

        task.stop_current_entry()
        self.store.update_task(task)
        self.store.set_active_task_id(None)

        return True, "Timer stopped.", task

    def get_status(self) -> Tuple[bool, str, Optional[Task], Optional[Project]]:
        """
        Get the current timer status.

        Returns:
            Tuple of (has_active: bool, status: str, task: Optional[Task], project: Optional[Project])
        """
        active_task_id = self.store.get_active_task_id()
        if not active_task_id:
            return False, "No active timer.", None, None

        task = self.store.get_task_by_id(active_task_id)
        if not task:
            return False, "Active task not found.", None, None

        # Get project info
        projects = self.store.get_projects()
        project = next((p for p in projects if p.id == task.project_id), None)

        if task.is_running():
            status = "running"
        elif task.is_paused():
            status = "paused"
        else:
            status = "stopped"

        return True, status, task, project
