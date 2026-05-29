#!/usr/bin/env python3
"""Rolex - Terminal Time Tracker CLI."""

import click
from datetime import datetime, timedelta
from typing import Optional
from simple_term_menu import TerminalMenu
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
@click.option('--task-id', help='Specific task ID to resume')
def resume(task_id):
    """Resume a stopped timer (use ↑↓ arrows to select)."""
    manager = TimerManager()
    store = DataStore()

    # If no task_id provided, show stopped tasks and prompt
    if not task_id:
        stopped_tasks = store.get_stopped_tasks()

        if not stopped_tasks:
            click.echo(click.style("✗ No stopped tasks to resume.", fg='red'))
            return

        if len(stopped_tasks) == 1:
            # Auto-select if only one stopped task
            task_id = stopped_tasks[0].id
        else:
            # Build menu options
            projects = {p.id: p for p in store.get_projects()}
            menu_items = []

            for task in stopped_tasks:
                proj = projects.get(task.project_id)
                project_name = proj.name if proj else "Unknown"
                duration = format_duration(task.get_total_duration())

                # Show last activity time
                last_time = ""
                if task.time_entries:
                    last_entry = task.time_entries[-1]
                    if last_entry.end_time:
                        last_dt = datetime.fromisoformat(last_entry.end_time)
                        last_time = last_dt.strftime("%Y-%m-%d %H:%M")

                menu_items.append(f"[{project_name}] {task.description} | {duration} | {last_time}")

            # Show interactive menu
            click.echo(click.style("\nSelect task to resume (use ↑↓ arrows, Enter to select, q to quit):", bold=True))
            terminal_menu = TerminalMenu(
                menu_items,
                title="Stopped Tasks:",
                menu_cursor="→ ",
                menu_cursor_style=("fg_green", "bold"),
                menu_highlight_style=("bg_green", "fg_black"),
                cycle_cursor=True,
                clear_screen=False,
            )

            menu_entry_index = terminal_menu.show()

            if menu_entry_index is None:
                click.echo("\nCancelled.")
                return

            task_id = stopped_tasks[menu_entry_index].id

    # Resume the selected task
    success, message = manager.resume_timer(task_id=task_id)

    if success:
        task = store.get_task_by_id(task_id)
        projects = {p.id: p for p in store.get_projects()}
        project = projects.get(task.project_id)

        click.echo(click.style(f"✓ Timer resumed", fg='green'))
        click.echo(f"  Project: {click.style(project.name if project else 'Unknown', fg='cyan')}")
        click.echo(f"  Task: {task.description}")
    else:
        click.echo(click.style(f"✗ {message}", fg='red'))


@cli.command()
def stop():
    """Stop the current timer (keeps it resumable)."""
    manager = TimerManager()
    success, message, task = manager.stop_timer()

    if success:
        duration = format_duration(task.get_total_duration())
        click.echo(click.style(f"✓ Timer stopped", fg='yellow'))
        click.echo(f"  Time tracked: {click.style(duration, fg='cyan', bold=True)}")
        click.echo(click.style("  (Use 'rolex resume' to continue this task)", dim=True))
    else:
        click.echo(click.style(f"✗ {message}", fg='red'))


@cli.command()
def status():
    """Show current timer status and stopped tasks."""
    manager = TimerManager()
    store = DataStore()
    has_running, status_text, running_task, project, stopped_tasks = manager.get_status()

    # Display running task (if any)
    if has_running:
        click.echo(click.style("\nRunning Timer:", bold=True))
        click.echo(click.style("─" * 50, dim=True))

        if project:
            click.echo(f"  Project: {click.style(project.name, fg='cyan', bold=True)}")

        click.echo(f"  Task: {running_task.description}")
        click.echo(f"  Status: {click.style('RUNNING', fg='green', bold=True)}")

        duration = running_task.get_current_duration()
        formatted_duration = format_duration(duration)
        click.echo(f"  Elapsed: {click.style(formatted_duration, fg='cyan', bold=True)}")
        click.echo()
    else:
        click.echo(click.style("No running timer.", dim=True))
        click.echo()

    # Display stopped tasks
    if stopped_tasks:
        click.echo(click.style(f"Stopped Tasks ({len(stopped_tasks)}):", bold=True))
        click.echo(click.style("─" * 80, dim=True))

        projects = {p.id: p for p in store.get_projects()}

        for task in stopped_tasks[:5]:  # Show max 5 recent stopped tasks
            proj = projects.get(task.project_id)
            project_name = proj.name if proj else "Unknown"
            duration = format_duration(task.get_total_duration())

            click.echo(f"  [{click.style(project_name, fg='cyan')}] {task.description}")
            click.echo(f"    Time: {click.style(duration, fg='green')} | {click.style('Use resume to continue', dim=True)}")

        if len(stopped_tasks) > 5:
            click.echo(click.style(f"  ... and {len(stopped_tasks) - 5} more", dim=True))

        click.echo()


@cli.command()
@click.option('--project', help='Filter by project name')
@click.option('--today', is_flag=True, help='Show only today\'s entries')
@click.option('--week', is_flag=True, help='Show only this week\'s entries')
@click.option('--compact', is_flag=True, help='Show compact one-line format with task IDs')
def log(project, today, week, compact):
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

    # Show all tasks with time entries
    tasks = [t for t in tasks if t.time_entries]

    if not tasks:
        click.echo("No tasks found.")
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

        duration = format_duration(task.get_total_duration())

        if compact:
            # Compact one-line format with task ID
            state_indicator = "RUN" if task.is_running() else "STOP"
            state_color = 'green' if task.is_running() else 'yellow'

            click.echo(f"  {click.style(task.id[:8], dim=True)} | "
                      f"{click.style(state_indicator, fg=state_color)} | "
                      f"{click.style(duration, fg='green').ljust(15)} | "
                      f"[{click.style(project_name, fg='cyan')}] {task.description}")
        else:
            # Show task state
            state_indicator = ""
            if task.is_running():
                state_indicator = click.style(" [RUNNING]", fg='green')
            elif task.is_stopped():
                state_indicator = click.style(" [STOPPED]", fg='yellow')

            click.echo(f"  [{start_time}] {click.style(project_name, fg='cyan')} - {task.description}{state_indicator}")
            click.echo(f"    Duration: {click.style(duration, fg='green', bold=True)}")
            click.echo()


@cli.command()
@click.argument('task_id', required=False)
def delete(task_id):
    """Delete a stopped task by ID or select interactively (use ↑↓ arrows)."""
    store = DataStore()

    # If no task_id provided, show stopped tasks and prompt
    if not task_id:
        stopped_tasks = store.get_stopped_tasks()

        if not stopped_tasks:
            click.echo(click.style("✗ No stopped tasks to delete.", fg='red'))
            return

        # Build menu options
        projects = {p.id: p for p in store.get_projects()}
        menu_items = []

        for task in stopped_tasks:
            proj = projects.get(task.project_id)
            project_name = proj.name if proj else "Unknown"
            duration = format_duration(task.get_total_duration())

            # Show last activity time
            last_time = ""
            if task.time_entries:
                last_entry = task.time_entries[-1]
                if last_entry.end_time:
                    last_dt = datetime.fromisoformat(last_entry.end_time)
                    last_time = last_dt.strftime("%Y-%m-%d %H:%M")

            menu_items.append(f"[{project_name}] {task.description} | {duration} | {last_time}")

        # Show interactive menu
        click.echo(click.style("\nSelect task to delete (use ↑↓ arrows, Enter to select, q to quit):", bold=True))
        terminal_menu = TerminalMenu(
            menu_items,
            title="Stopped Tasks:",
            menu_cursor="→ ",
            menu_cursor_style=("fg_red", "bold"),
            menu_highlight_style=("bg_red", "fg_black"),
            cycle_cursor=True,
            clear_screen=False,
        )

        menu_entry_index = terminal_menu.show()

        if menu_entry_index is None:
            click.echo("\nCancelled.")
            return

        task_id = stopped_tasks[menu_entry_index].id

    # Find task by full or partial ID
    all_tasks = store.get_tasks()
    matching_tasks = [t for t in all_tasks if t.id.startswith(task_id)]

    if not matching_tasks:
        click.echo(click.style(f"✗ Task not found.", fg='red'))
        return

    if len(matching_tasks) > 1:
        click.echo(click.style(f"✗ Ambiguous task ID. Multiple tasks match '{task_id}':", fg='red'))
        for t in matching_tasks:
            click.echo(f"  {t.id[:8]} - {t.description}")
        return

    task = matching_tasks[0]

    # Check if task is running
    if task.is_running():
        click.echo(click.style(f"✗ Cannot delete a running task. Stop it first.", fg='red'))
        return

    # Confirm deletion
    if not click.confirm(click.style("Are you sure you want to delete this task?", fg='yellow')):
        click.echo("Cancelled.")
        return

    # Delete the task
    data = store._load_data()
    data['tasks'] = [t for t in data['tasks'] if t['id'] != task.id]
    store._save_data(data)

    # Get project name for display
    projects = {p.id: p for p in store.get_projects()}
    project = projects.get(task.project_id)
    project_name = project.name if project else "Unknown"

    click.echo(click.style(f"✓ Task deleted", fg='green'))
    click.echo(f"  [{click.style(project_name, fg='cyan')}] {task.description}")


@cli.command()
@click.option('--today', is_flag=True, help='Show only today\'s summary')
@click.option('--week', is_flag=True, help='Show only this week\'s summary')
def summary(today, week):
    """Summary of time tracked (use --today or --week to filter)."""
    store = DataStore()
    tasks = store.get_tasks()
    projects = {p.id: p for p in store.get_projects()}

    # Include all tasks with time entries
    all_tasks = [t for t in tasks if t.time_entries]

    if not all_tasks:
        click.echo("No tasks found.")
        return

    # Determine date cutoff for filtering
    cutoff = None
    if today or week:
        now = datetime.utcnow()
        if today:
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif week:
            start_of_week = now - timedelta(days=now.weekday())
            cutoff = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate totals per project
    project_totals = {}
    for task in all_tasks:
        project_id = task.project_id
        if project_id not in project_totals:
            project_totals[project_id] = 0

        if cutoff:
            # Only count entries that started within the date range
            for entry in task.time_entries:
                entry_start = datetime.fromisoformat(entry.start_time)
                if entry_start >= cutoff:
                    project_totals[project_id] += entry.current_duration()
        else:
            project_totals[project_id] += task.get_total_duration()

    # Remove projects with no time in the filtered range
    if cutoff:
        project_totals = {k: v for k, v in project_totals.items() if v > 0}

    if not project_totals:
        period = "today" if today else "this week" if week else ""
        click.echo(f"No time tracked {period}.")
        return

    # Header
    if today:
        title = "Today's Summary:"
    elif week:
        title = "This Week's Summary:"
    else:
        title = "Time Summary:"

    click.echo(click.style(f"\n{title}", bold=True))
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
