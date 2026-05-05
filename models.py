"""Data models for the Rolex timer application."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class TaskState(str, Enum):
    """Enum for task states."""
    RUNNING = "running"
    STOPPED = "stopped"


class TimeEntry:
    """Represents a single time entry (start/end)."""

    def __init__(self, start_time: Optional[str] = None, end_time: Optional[str] = None):
        self.start_time = start_time or datetime.utcnow().isoformat()
        self.end_time = end_time

    def to_dict(self):
        return {
            'start_time': self.start_time,
            'end_time': self.end_time
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )

    def duration(self) -> float:
        """Calculate duration in seconds."""
        if not self.end_time:
            return 0

        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        return (end - start).total_seconds()

    def current_duration(self) -> float:
        """Calculate current duration including running time."""
        start = datetime.fromisoformat(self.start_time)

        if self.end_time:
            end = datetime.fromisoformat(self.end_time)
        else:
            end = datetime.utcnow()

        return (end - start).total_seconds()


class Task:
    """Represents a task with time tracking."""

    def __init__(self, project_id: str, description: str, task_id: Optional[str] = None,
                 time_entries: Optional[List[TimeEntry]] = None, total_duration: float = 0,
                 state: Optional[TaskState] = None):
        self.id = task_id or str(uuid.uuid4())
        self.project_id = project_id
        self.description = description
        self.time_entries = time_entries or []
        self.total_duration = total_duration
        self.state = state or TaskState.RUNNING

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'description': self.description,
            'time_entries': [entry.to_dict() for entry in self.time_entries],
            'total_duration': self.total_duration,
            'state': self.state.value
        }

    @classmethod
    def from_dict(cls, data):
        state_value = data.get('state', 'stopped')
        try:
            state = TaskState(state_value)
        except ValueError:
            state = TaskState.STOPPED

        return cls(
            task_id=data.get('id'),
            project_id=data['project_id'],
            description=data['description'],
            time_entries=[TimeEntry.from_dict(e) for e in data.get('time_entries', [])],
            total_duration=data.get('total_duration', 0),
            state=state
        )

    def start_entry(self):
        """Start a new time entry."""
        entry = TimeEntry()
        self.time_entries.append(entry)
        self.state = TaskState.RUNNING
        return entry

    def stop(self):
        """Stop the current running entry (keeps task resumable)."""
        if self.time_entries:
            last_entry = self.time_entries[-1]
            if not last_entry.end_time:
                last_entry.end_time = datetime.utcnow().isoformat()

        self.state = TaskState.STOPPED

    def resume(self):
        """Resume a stopped task by creating a new entry."""
        entry = TimeEntry()
        self.time_entries.append(entry)
        self.state = TaskState.RUNNING
        return entry

    def get_total_duration(self) -> float:
        """Dynamically calculate total duration from all entries."""
        return sum(entry.duration() for entry in self.time_entries)

    def get_current_duration(self) -> float:
        """Get current running duration including active time."""
        return sum(entry.current_duration() for entry in self.time_entries)

    def last_activity_time(self) -> Optional[str]:
        """Get the timestamp of the last activity."""
        if not self.time_entries:
            return None
        last_entry = self.time_entries[-1]
        return last_entry.end_time or last_entry.start_time

    def is_running(self) -> bool:
        """Check if task is currently running."""
        return self.state == TaskState.RUNNING

    def is_stopped(self) -> bool:
        """Check if task is currently stopped."""
        return self.state == TaskState.STOPPED


class Project:
    """Represents a project."""

    def __init__(self, name: str, project_id: Optional[str] = None,
                 created_at: Optional[str] = None):
        self.id = project_id or str(uuid.uuid4())
        self.name = name
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            project_id=data.get('id'),
            created_at=data.get('created_at')
        )
