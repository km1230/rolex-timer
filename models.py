"""Data models for the Rolex timer application."""

from datetime import datetime
from typing import Optional, List
import uuid


class TimeEntry:
    """Represents a single time entry (start/end/pause)."""

    def __init__(self, start_time: Optional[str] = None, end_time: Optional[str] = None,
                 paused_at: Optional[str] = None):
        self.start_time = start_time or datetime.utcnow().isoformat()
        self.end_time = end_time
        self.paused_at = paused_at

    def to_dict(self):
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'paused_at': self.paused_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            paused_at=data.get('paused_at')
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

        if self.paused_at:
            end = datetime.fromisoformat(self.paused_at)
        elif self.end_time:
            end = datetime.fromisoformat(self.end_time)
        else:
            end = datetime.utcnow()

        return (end - start).total_seconds()


class Task:
    """Represents a task with time tracking."""

    def __init__(self, project_id: str, description: str, task_id: Optional[str] = None,
                 time_entries: Optional[List[TimeEntry]] = None, total_duration: float = 0):
        self.id = task_id or str(uuid.uuid4())
        self.project_id = project_id
        self.description = description
        self.time_entries = time_entries or []
        self.total_duration = total_duration

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'description': self.description,
            'time_entries': [entry.to_dict() for entry in self.time_entries],
            'total_duration': self.total_duration
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            task_id=data.get('id'),
            project_id=data['project_id'],
            description=data['description'],
            time_entries=[TimeEntry.from_dict(e) for e in data.get('time_entries', [])],
            total_duration=data.get('total_duration', 0)
        )

    def start_entry(self):
        """Start a new time entry."""
        entry = TimeEntry()
        self.time_entries.append(entry)
        return entry

    def pause_current_entry(self):
        """Pause the current running entry."""
        if self.time_entries and not self.time_entries[-1].paused_at:
            now = datetime.utcnow().isoformat()
            self.time_entries[-1].paused_at = now
            self.time_entries[-1].end_time = now

    def resume_current_entry(self):
        """Resume a paused entry by creating a new one."""
        entry = TimeEntry()
        self.time_entries.append(entry)
        return entry

    def stop_current_entry(self):
        """Stop the current running entry and calculate total duration."""
        if self.time_entries:
            last_entry = self.time_entries[-1]
            if not last_entry.end_time:
                last_entry.end_time = datetime.utcnow().isoformat()

            # Calculate total duration from all entries
            self.total_duration = sum(entry.duration() for entry in self.time_entries)

    def get_current_duration(self) -> float:
        """Get current running duration including active time."""
        return sum(entry.current_duration() for entry in self.time_entries)

    def is_running(self) -> bool:
        """Check if task is currently running."""
        if not self.time_entries:
            return False
        last_entry = self.time_entries[-1]
        return last_entry.end_time is None and last_entry.paused_at is None

    def is_paused(self) -> bool:
        """Check if task is currently paused."""
        if not self.time_entries:
            return False
        last_entry = self.time_entries[-1]
        return last_entry.paused_at is not None


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
