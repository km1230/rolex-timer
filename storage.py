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
                'tasks': [],
                'active_task_id': None
            })

    def _load_data(self) -> dict:
        """Load data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                'projects': [],
                'tasks': [],
                'active_task_id': None
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

        # Clear active task if it belonged to this project
        if data.get('active_task_id'):
            active_task = next((t for t in data['tasks'] if t['id'] == data['active_task_id']), None)
            if not active_task:
                data['active_task_id'] = None

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

    def get_active_task_id(self) -> Optional[str]:
        """Get the ID of the currently active task."""
        data = self._load_data()
        return data.get('active_task_id')

    def set_active_task_id(self, task_id: Optional[str]):
        """Set the active task ID."""
        data = self._load_data()
        data['active_task_id'] = task_id
        self._save_data(data)

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        data = self._load_data()
        for t in data.get('tasks', []):
            if t['id'] == task_id:
                return Task.from_dict(t)
        return None
