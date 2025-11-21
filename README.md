# Task Scheduler & Desktop Timer

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)
[![GitHub release](https://img.shields.io/github/v/release/Unobtainiumrock/task-scheduler?include_prereleases&sort=semver)](https://github.com/Unobtainiumrock/task-scheduler/releases)
[![GitHub Actions CI](https://img.shields.io/github/actions/workflow/status/Unobtainiumrock/task-scheduler/coverage.yml?branch=nicholas&label=CI)](https://github.com/Unobtainiumrock/task-scheduler/actions/workflows/coverage.yml)
[![codecov](https://codecov.io/gh/Unobtainiumrock/task-scheduler/branch/nicholas/graph/badge.svg)](https://codecov.io/gh/Unobtainiumrock/task-scheduler)
[![Maintained](https://img.shields.io/badge/Maintained-yes-green.svg)](https://github.com/Unobtainiumrock/task-scheduler/graphs/commit-activity)
[![GitHub issues](https://img.shields.io/github/issues/Unobtainiumrock/task-scheduler.svg)](https://github.com/Unobtainiumrock/task-scheduler/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/Unobtainiumrock/task-scheduler.svg)](https://github.com/Unobtainiumrock/task-scheduler/pulls)

A two-script system to parse an unstructured to-do list using an LLM and run a live countdown timer on your Linux desktop with synchronized desktop notifications.

## Features

- **AI-Powered Scheduling**: Uses GPT-4o to intelligently prioritize and schedule tasks based on deadlines and importance
- **Live Countdown Timer**: Real-time countdown with desktop notifications that update every second
- **Timeline View**: Queue all tasks for the day as persistent notifications showing your complete schedule
- **Notification Synchronization**: Properly manages notification state between terminal and notification daemon
- **Early Task Skipping**: Press Enter at any time to skip to the next task without waiting for the timer
- **Smart Task Management**: Automatically handles breaks, prioritizes urgent tasks, and creates realistic time blocks

## Getting Started

### Prerequisites & Setup

This guide is tailored for Debian/Ubuntu-based Linux distributions.

#### System Dependencies

First, ensure you have the necessary system tools for desktop notifications and sound.

**Install tools for notifications and the recommended notification daemon (dunst):**

```bash
sudo apt-get update && sudo apt-get install -y libnotify-bin pulseaudio-utils dunst
```

**Important:** After installing `dunst`, you may need to log out and log back in to ensure the notification service is running correctly.

#### Python Environment & Packages

It is highly recommended to use a Python virtual environment to manage dependencies.

**Create and activate a virtual environment (example using venv):**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Or if using pyenv:**

```bash
pyenv activate nlp  # or your preferred environment name
```

**Install the required Python packages:**

```bash
pip install openai python-dotenv notify2
```

### Configuration

**Note:** This project is currently Linux-only. Feel free to make a PR adding adaptations for Windows and Mac users.

1. **Get your OpenAI API key** and store it in an `.env` file at the root of the project:

```bash
echo "OPENAI_API_KEY=your-key-here" > .env
```

2. **Create a markdown file** (e.g., `tasks.md`) with your natural language set of tasks and accompanying deadlines. Markdown format is preferred. See `tasks.md` for an example.

   The scheduler will analyze your tasks and create a structured schedule based on:
   - Task deadlines and urgency
   - Current date and time
   - Realistic time estimates
   - Workday constraints (schedules up to 11:00 PM)

3. **Run both scripts together.** This is ideal so that the generated schedule is synchronized with the intended time of day. If you generate a schedule but start the timer later, there will be a disconnect between scheduled times and actual execution.

```bash
python3 scheduler.py tasks.md && python3 timer.py schedule.json
```

**Note:** You can run each script individually to inspect the generated schedule before starting the timer.

## Usage

### Generating a Schedule

The scheduler (`scheduler.py`) reads your markdown task file and generates a JSON schedule:

```bash
python3 scheduler.py tasks.md
```

This creates `schedule.json` with:
- Task names with deadlines included
- Start and end times for each task
- Duration in minutes
- Logical breaks between tasks

### Running the Timer

The timer (`timer.py`) reads the generated schedule and runs countdown timers for each task:

```bash
python3 timer.py schedule.json
```

**What happens when you run the timer:**

1. **Startup**: Clears any pre-existing notifications and queues timeline notifications showing all tasks for the day
2. **Timeline Notifications**: All tasks appear as notifications showing:
   - ✅ Completed tasks (green, low urgency)
   - ⏳ Active task (critical urgency)
   - 📅 Upcoming tasks (normal urgency)
3. **Active Timer**: A live countdown notification updates every second showing:
   - Current task name
   - Time remaining (MM:SS)
   - Next task information
4. **Task Completion**: When time runs out:
   - Alarm sound plays
   - Completion notification appears
   - Press Enter to acknowledge and start the next task

### Interactive Controls

- **Skip Task Early**: Press `Enter` at any time during a task to skip to the next task immediately (no alarm)
- **Exit Gracefully**: Press `Ctrl+C` between tasks to stop the timer cleanly

### Notification Behavior

The timer uses two types of notifications:

1. **Timeline Notifications**: Persistent notifications that show your complete schedule. These remain visible throughout the day and update as tasks complete.
2. **Active Timer Notification**: A single notification that replaces itself, showing the current task countdown.

Notifications are synchronized using:
- Replacement IDs to prevent stacking
- Different stack tags for timeline vs. active timer
- Force-close functionality via `dunstctl` when needed

## How It Works

### Scheduling Algorithm

The scheduler uses GPT-4o with a zero-shot prompt that:
- Analyzes task priorities based on deadlines
- Allocates focused work blocks (typically 60-90 minutes)
- Places strategic breaks (15 min short breaks, longer meal breaks)
- Ensures tasks fit within working hours (up to 11:00 PM)
- Enriches task names with deadline information

### Timer System

The timer:
- Loads the JSON schedule
- Creates timeline notifications for all tasks
- Runs countdown loops with 1-second precision
- Updates notifications in real-time
- Handles early skipping gracefully
- Manages notification state to prevent conflicts

## File Structure

```
task-prioritizer/
├── scheduler.py        # AI-powered schedule generator
├── timer.py            # Desktop timer with notifications
├── tasks.md            # Your task list (markdown format)
├── schedule.json       # Generated schedule (auto-created)
├── .env                # API keys (not in git)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Troubleshooting

### Notifications Not Appearing

- Ensure `dunst` is running: `pgrep dunst`
- If not running, start it: `dunst &`
- Check D-Bus is available: `echo $DBUS_SESSION_BUS_ADDRESS`

### Notification Synchronization Issues

- The timer uses replacement IDs to prevent notification stacking
- If notifications queue up, the timer will clear them at startup
- Timeline notifications use different stack tags and won't interfere with the active timer

### OpenAI API Errors

- Verify your `.env` file contains: `OPENAI_API_KEY=your-key-here`
- Check your API key is valid and has credits
- Ensure you have internet connectivity

### Sound Not Playing

- Install pulseaudio-utils: `sudo apt-get install pulseaudio-utils`
- Check sound system is working: `paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga`

## Future Improvements

Potential enhancements for future versions:

1. **Task Completion Tracking**: 
   - Add buttons to mark tasks as complete early or extend time
   - Track actual vs. estimated completion times for ML model training
   - Collect data on task duration patterns

2. **Cross-Platform Support**:
   - Windows notification support
   - macOS notification support
   - Electron app for better UI/UX across platforms

3. **Enhanced Features**:
   - Pause/resume functionality
   - Task notes and context
   - Schedule export/import
   - Integration with calendar apps
   - Mobile companion app

4. **ML Integration**:
   - Learn from completion patterns
   - Auto-adjust time estimates
   - Suggest optimal scheduling based on historical data

## Contributing

Contributions are welcome! This project is Linux-focused but PRs adding Windows/Mac support would be appreciated.

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

```
Copyright (C) 2024 Task Prioritizer Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

See the [LICENSE](LICENSE) file for the full license text.
