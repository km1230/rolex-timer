# Rolex Timer

A terminal-based time tracking tool for logging time against projects.
[勞力士無止境](https://youtu.be/URUIcYDq3_I)

## Features

- 📊 Project management (add, list, delete)
- ⏱️ Timer controls (start, stop, resume)
- 📝 Task descriptions
- 📈 Time logs and summaries
- 💾 JSON file storage

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Option 1: Global Installation (Recommended)

Install `rolex` as a global command available from anywhere:

```bash
# Clone the repository first
git clone <repository-url>
cd rolex-timer

# Install globally
uv tool install --editable .
```

Now you can use `rolex`:

```bash
rolex project add "My Project"
rolex start "My Project" -d "Working on features"
```

To uninstall:
```bash
uv tool uninstall rolex-timer
```

### Option 2: Local Development

For development work within the project directory:

```bash
cd rolex-timer
uv sync

# Use via the virtual environment
.venv/bin/rolex --help

# Or activate the venv
source .venv/bin/activate
rolex --help
```

## Usage

### Project Management

```bash
# Add a new project
rolex project add "Client Work"

# List all projects
rolex project list

# Delete a project
rolex project delete "Client Work"
```

### Timer Operations

```bash
# Start a timer
rolex start "Client Work" -d "Implementing new feature"

# Check timer status
rolex status

# Stop the timer (keeps it resumable)
rolex stop

# Resume a stopped timer (interactive menu with ↑↓ arrow keys)
rolex resume

# The arrow key menu will appear if you have multiple stopped tasks:
# → [Client Work] Implementing new feature | 2h 30m | 2026-05-05 14:30
#   [Internal] Code review | 45m | 2026-05-05 13:15
# Use ↑↓ to navigate, Enter to select, q to quit
```

### Reporting

```bash
# View all time logs
rolex log

# View compact one-line format with task IDs
rolex log --compact

# View logs for a specific project
rolex log --project "Client Work"

# View today's logs
rolex log --today

# View this week's logs
rolex log --week

# View summary of all tracked time
rolex summary

# View summary for a single project
rolex summary --project "Client Work"

# Break the summary down by day, week or month
rolex summary --weekly
rolex summary --daily --project "Client Work"
rolex summary --monthly

# Combine with --today / --week to limit the range
rolex summary --week --daily
```

### Task Management

```bash
# Delete a stopped task interactively (arrow key menu)
rolex delete

# The arrow key menu lets you select which task to delete:
# → [Client Work] Old task | 30m | 2026-05-05 10:00
#   [Internal] Finished work | 1h | 2026-05-05 09:00
# Use ↑↓ to navigate, Enter to select, q to quit

# Or delete by ID directly (use first 8 characters from compact log)
rolex delete <task-id>

# Example workflow:
rolex log --compact          # Find task ID
rolex delete 7e9585ef        # Delete specific task
```

## Data Storage

Time tracking data is stored in `~/.rolex-timer/data.json`

## Example Workflow

### Single Task Workflow
```bash
# Setup
rolex project add "Client Work"
rolex project add "Internal"

# Track time on one task
rolex start "Client Work" -d "Implementing authentication"
# ... work for a while ...
rolex stop
# ... take a break ...
rolex resume
# ... continue working ...
rolex stop

# View logs
rolex log
rolex summary
```

### Multiple Task Workflow (Harvest-style)
```bash
# Work on first task
rolex start "Client Work" -d "Implementing authentication"
# ... work for 2 hours ...
rolex stop

# Switch to different task
rolex start "Internal" -d "Code review"
# ... work for 30 minutes ...
rolex stop

# Resume first task (arrow key menu appears)
rolex resume
# Shows interactive menu:
# → [Client Work] Implementing authentication | 2h 15m | 2026-05-05 14:30
#   [Internal] Code review | 30m | 2026-05-05 16:00
# Use ↑↓ to navigate, Enter to select

# Continue working on first task
rolex stop

# View all tracked time
rolex summary
```

## Requirements

- Python 3.7+
- click library
- simple-term-menu library

## License

MIT
