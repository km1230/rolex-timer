"""Storage layer for persisting timer data to JSON."""

import json
import os
from pathlib import Path
from typing import Optional, List
from models import Project, Task


class DataStore:
    """Handles JSON file operations for timer data."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / '.rolex-timer'
        self.data_file = self.data_dir / 'data.json'
        self._ensure_data_file()

    def _ensure_data_file(self):
        """Create data directory and file if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.data_file.exists():
            self._save_data({
                'projects': [],
                'tasks': []
            })

    def _load_data(self) -> dict:
        """Load data from JSON file with migration."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)

            # MIGRATION: Remove active_task_id if present
            if 'active_task_id' in data:
                active_id = data.pop('active_task_id')

                # If there was an active task, mark it appropriately
                if active_id:
                    for task in data.get('tasks', []):
                        if task['id'] == active_id:
                            # Check if it was running or paused
                            if task.get('time_entries'):
                                last_entry = task['time_entries'][-1]
                                if not last_entry.get('end_time'):
                                    # Was running -> mark as running
                                    task['state'] = 'running'
                                else:
                                    # Was paused -> mark as stopped
                                    task['state'] = 'stopped'

            # MIGRATION: Add state to tasks that don't have it
            for task in data.get('tasks', []):
                if 'state' not in task:
                    # Determine state based on existing data
                    if task.get('time_entries'):
                        last_entry = task['time_entries'][-1]
                        if last_entry.get('end_time'):
                            task['state'] = 'stopped'
                        else:
                            task['state'] = 'running'
                    else:
                        task['state'] = 'stopped'

                # MIGRATION: Remove paused_at from time entries
                for entry in task.get('time_entries', []):
                    if 'paused_at' in entry:
                        # If it was paused, use paused_at as end_time if no end_time
                        if entry['paused_at'] and not entry.get('end_time'):
                            entry['end_time'] = entry['paused_at']
                        del entry['paused_at']

            return data

        except (json.JSONDecodeError, FileNotFoundError):
            return {
                'projects': [],
                'tasks': []
            }

    def _save_data(self, data: dict):
        """Save data to JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_projects(self) -> List[Project]:
        """Get all projects."""
        data = self._load_data()
        return [Project.from_dict(p) for p in data.get('projects', [])]

    def add_project(self, project: Project) -> bool:
        """Add a new project."""
        data = self._load_data()

        # Check if project name already exists
        if any(p['name'].lower() == project.name.lower() for p in data['projects']):
            return False

        data['projects'].append(project.to_dict())
        self._save_data(data)
        return True

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get a project by name (case-insensitive)."""
        projects = self.get_projects()
        for project in projects:
            if project.name.lower() == name.lower():
                return project
        return None

    def delete_project(self, name: str) -> bool:
        """Delete a project and its tasks."""
        data = self._load_data()

        # Find project
        project = None
        for p in data['projects']:
            if p['name'].lower() == name.lower():
                project = p
                break

        if not project:
            return False

        # Remove project
        data['projects'] = [p for p in data['projects'] if p['id'] != project['id']]

        # Remove associated tasks
        data['tasks'] = [t for t in data['tasks'] if t['project_id'] != project['id']]

        self._save_data(data)
        return True

    def get_tasks(self, project_id: Optional[str] = None) -> List[Task]:
        """Get all tasks, optionally filtered by project."""
        data = self._load_data()
        tasks = [Task.from_dict(t) for t in data.get('tasks', [])]

        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        return tasks

    def add_task(self, task: Task):
        """Add a new task."""
        data = self._load_data()
        data['tasks'].append(task.to_dict())
        self._save_data(data)

    def update_task(self, task: Task):
        """Update an existing task."""
        data = self._load_data()

        for i, t in enumerate(data['tasks']):
            if t['id'] == task.id:
                data['tasks'][i] = task.to_dict()
                break

        self._save_data(data)

    def get_running_task(self) -> Optional[Task]:
        """Get the currently running task (if any)."""
        tasks = self.get_tasks()
        running_tasks = [t for t in tasks if t.is_running()]

        if len(running_tasks) > 1:
            # Data corruption - multiple running tasks
            raise ValueError("Data corruption: Multiple running tasks found")

        return running_tasks[0] if running_tasks else None

    def get_stopped_tasks(self) -> List[Task]:
        """Get all stopped tasks, sorted by last activity time (most recent first)."""
        tasks = self.get_tasks()
        stopped_tasks = [t for t in tasks if t.is_stopped()]

        # Sort by last activity time, most recent first
        stopped_tasks.sort(key=lambda t: t.last_activity_time() or '', reverse=True)

        return stopped_tasks

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        data = self._load_data()
        for t in data.get('tasks', []):
            if t['id'] == task_id:
                return Task.from_dict(t)
        return None
