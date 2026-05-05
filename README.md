# Rolex Timer

A terminal-based time tracking tool for logging time against projects.
[勞力士無止境](https://youtu.be/URUIcYDq3_I)

## Features

- 📊 Project management (add, list, delete)
- ⏱️ Timer controls (start, pause, resume, stop)
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

# Pause the timer
rolex pause

# Resume the timer
rolex resume

# Stop the timer
rolex stop
```

### Reporting

```bash
# View all time logs
rolex log

# View logs for a specific project
rolex log --project "Client Work"

# View today's logs
rolex log --today

# View this week's logs
rolex log --week

# View summary of all tracked time
rolex summary
```

## Data Storage

Time tracking data is stored in `~/.rolex-timer/data.json`

## Example Workflow

```bash
# Setup
rolex project add "Client Work"
rolex project add "Internal"

# Track time
rolex start "Client Work" -d "Implementing authentication"
# ... work for a while ...
rolex pause
# ... take a break ...
rolex resume
# ... continue working ...
rolex stop

# View logs
rolex log
rolex summary
```

## Requirements

- Python 3.7+
- click library

## License

MIT
