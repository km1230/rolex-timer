#!/usr/bin/env python3
"""Rolex - Terminal Time Tracker CLI."""

import click
from datetime import datetime, timedelta
from typing import Optional
from timer import TimerManager
from storage import DataStore
from models import Project


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format (HH:MM:SS)."""
    if seconds < 0:
        seconds = 0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


@click.group()
def cli():
    """Rolex - Terminal Time Tracker"""
    pass


@cli.group()
def project():
    """Manage projects."""
    pass


@project.command('add')
@click.argument('name')
def project_add(name):
    """Add a new project."""
    store = DataStore()
    proj = Project(name=name)

    if store.add_project(proj):
        click.echo(click.style(f"✓ Project '{name}' added successfully.", fg='green'))
    else:
        click.echo(click.style(f"✗ Project '{name}' already exists.", fg='red'))


@project.command('list')
def project_list():
    """List all projects."""
    store = DataStore()
    projects = store.get_projects()

    if not projects:
        click.echo("No projects found. Add one with 'rolex project add <name>'")
        return

    click.echo(click.style("\nProjects:", bold=True))
    click.echo(click.style("─" * 50, dim=True))

    for proj in projects:
        created = datetime.fromisoformat(proj.created_at).strftime("%Y-%m-%d")
        click.echo(f"  • {click.style(proj.name, fg='cyan')} (created: {created})")

    click.echo()


@project.command('delete')
@click.argument('name')
@click.confirmation_option(prompt='Are you sure you want to delete this project and all its tasks?')
def project_delete(name):
    """Delete a project and all its tasks."""
    store = DataStore()

    if store.delete_project(name):
        click.echo(click.style(f"✓ Project '{name}' deleted.", fg='green'))
    else:
        click.echo(click.style(f"✗ Project '{name}' not found.", fg='red'))


@cli.command()
@click.argument('project_name')
@click.option('-d', '--description', required=True, help='Task description')
def start(project_name, description):
    """Start a timer for a task."""
    manager = TimerManager()
    success, message = manager.start_timer(project_name, description)

    if success:
        click.echo(click.style(f"✓ {message}", fg='green'))
    else:
        click.echo(click.style(f"✗ {message}", fg='red'))


@cli.command()
def pause():
    """Pause the current timer."""
    manager = TimerManager()
    success, message = manager.pause_timer()

    if success:
        click.echo(click.style(f"✓ {message}", fg='yellow'))
    else:
        click.echo(click.style(f"✗ {message}", fg='red'))


@cli.command()
def resume():
    """Resume a paused timer."""
    manager = TimerManager()
    success, message = manager.resume_timer()

    if success:
        click.echo(click.style(f"✓ {message}", fg='green'))
    else:
        click.echo(click.style(f"✗ {message}", fg='red'))


@cli.command()
def stop():
    """Stop and finalize the current timer."""
    manager = TimerManager()
    success, message, task = manager.stop_timer()

    if success:
        duration = format_duration(task.total_duration)
        click.echo(click.style(f"✓ {message}", fg='green'))
        click.echo(f"  Total time: {click.style(duration, fg='cyan', bold=True)}")
    else:
        click.echo(click.style(f"✗ {message}", fg='red'))


@cli.command()
def status():
    """Show current timer status."""
    manager = TimerManager()
    has_active, status_text, task, project = manager.get_status()

    if not has_active:
        click.echo(click.style("No active timer.", dim=True))
        return

    # Display status
    click.echo(click.style("\nTimer Status:", bold=True))
    click.echo(click.style("─" * 50, dim=True))

    if project:
        click.echo(f"  Project: {click.style(project.name, fg='cyan', bold=True)}")

    click.echo(f"  Task: {task.description}")

    if status_text == "running":
        status_display = click.style("RUNNING", fg='green', bold=True)
    elif status_text == "paused":
        status_display = click.style("PAUSED", fg='yellow', bold=True)
    else:
        status_display = click.style("STOPPED", fg='red', bold=True)

    click.echo(f"  Status: {status_display}")

    # Show elapsed time
    duration = task.get_current_duration()
    formatted_duration = format_duration(duration)
    click.echo(f"  Elapsed: {click.style(formatted_duration, fg='cyan', bold=True)}")
    click.echo()


@cli.command()
@click.option('--project', help='Filter by project name')
@click.option('--today', is_flag=True, help='Show only today\'s entries')
@click.option('--week', is_flag=True, help='Show only this week\'s entries')
def log(project, today, week):
    """View time logs."""
    store = DataStore()
    tasks = store.get_tasks()

    # Filter by project if specified
    if project:
        proj = store.get_project_by_name(project)
        if not proj:
            click.echo(click.style(f"✗ Project '{project}' not found.", fg='red'))
            return
        tasks = [t for t in tasks if t.project_id == proj.id]

    # Filter by date if specified
    if today or week:
        now = datetime.utcnow()

        if today:
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tasks = [t for t in tasks if t.time_entries and
                    datetime.fromisoformat(t.time_entries[0].start_time) >= start_of_day]
        elif week:
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            tasks = [t for t in tasks if t.time_entries and
                    datetime.fromisoformat(t.time_entries[0].start_time) >= start_of_week]

    # Only show completed tasks (with total_duration > 0)
    tasks = [t for t in tasks if t.total_duration > 0]

    if not tasks:
        click.echo("No completed tasks found.")
        return

    # Get all projects for display
    projects = {p.id: p for p in store.get_projects()}

    click.echo(click.style("\nTime Log:", bold=True))
    click.echo(click.style("─" * 80, dim=True))

    for task in sorted(tasks, key=lambda t: t.time_entries[0].start_time if t.time_entries else "", reverse=True):
        proj = projects.get(task.project_id)
        project_name = proj.name if proj else "Unknown"

        start_time = ""
        if task.time_entries:
            start_dt = datetime.fromisoformat(task.time_entries[0].start_time)
            start_time = start_dt.strftime("%Y-%m-%d %H:%M")

        duration = format_duration(task.total_duration)

        click.echo(f"  [{start_time}] {click.style(project_name, fg='cyan')} - {task.description}")
        click.echo(f"    Duration: {click.style(duration, fg='green', bold=True)}")
        click.echo()


@cli.command()
def summary():
    """Summary of all time tracked."""
    store = DataStore()
    tasks = store.get_tasks()
    projects = {p.id: p for p in store.get_projects()}

    # Only include completed tasks
    completed_tasks = [t for t in tasks if t.total_duration > 0]

    if not completed_tasks:
        click.echo("No completed tasks found.")
        return

    # Calculate totals per project
    project_totals = {}
    for task in completed_tasks:
        project_id = task.project_id
        if project_id not in project_totals:
            project_totals[project_id] = 0
        project_totals[project_id] += task.total_duration

    click.echo(click.style("\nTime Summary:", bold=True))
    click.echo(click.style("─" * 50, dim=True))

    total_time = 0
    for project_id, duration in sorted(project_totals.items(), key=lambda x: x[1], reverse=True):
        proj = projects.get(project_id)
        project_name = proj.name if proj else "Unknown"

        formatted = format_duration(duration)
        click.echo(f"  {click.style(project_name, fg='cyan')}: {click.style(formatted, fg='green', bold=True)}")
        total_time += duration

    click.echo(click.style("─" * 50, dim=True))
    click.echo(f"  {click.style('Total', bold=True)}: {click.style(format_duration(total_time), fg='green', bold=True)}")
    click.echo()


if __name__ == '__main__':
    cli()
