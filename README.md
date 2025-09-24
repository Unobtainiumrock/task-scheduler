# Task Scheduler & Desktop Timer

A two-script system to parse an unstructured to-do list using an LLM and run a live countdown timer on your Linux desktop.
Getting Started

## Prerequisites & Setup

This guide is tailored for Debian/Ubuntu-based Linux distributions.
System Dependencies

First, ensure you have the necessary system tools for desktop notifications and sound.

### Install tools for notifications and the recommended notification daemon (dunst)

```bash
sudo apt-get update && sudo apt-get install -y libnotify-bin pulseaudio-utils dunst
```

Important: After installing `dunst`, you may need to log out and log back in to ensure the notification service is running correctly.
Python Environment & Packages

It is highly recommended to use a Python virtual environment to manage dependencies.

### Create and activate a virtual environment (example using venv)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install the required Python packages using pip

```bash
pip install openai python-dotenv notify2
```

### Configuration

I won't bother to make this work for non-linux users. Feel free to make a PR adding adaptions so that this can work for Windows and Mac users.

1. Get your OpenAI API key and store it in an `.env` file at the root of the project

```bash
OPENAI_API_KEY=your-key-here
```

2. Paste in your natural language set of tasks with accompanying deadlines into the string in the main method towards the bottom of the scheduler.py file. I have an example of mine in Markdown, which is the preferred format.

**note: Can easily make some UI for this later, but for now this is sufficient**

3. Run both scripts together. This is ideal so that the generated set of tasks are synchronized with the intended time of day to complete them. This is because if you were to generate a schedule, but initiate the timer half an hour later, then there will be a disconnect between the two.

```bash
python3 scheduler.py && python3 timer.py schedule.json
```

**note: you can still run each individually to inspect the plans generated in the first stage if you'd like**

# Future Improvements

It's all very rough around the edges:

1. We can't assume all tasks are complete simply bnecause the timer is elapsed
2. There needs to be a way to click a button to extend time in 15 minute blocks
    - These should be tracked because its valuable data in fine tuning the estimated time to completion for tasks for an ML model.
    - The user should also be able to click a button to flag the task as complete and again, this is valuiable data to track when a user happens to complete a task faster than completed (further model improvement)
3. Its using system notifications on Linux. Maybe whip together a simple electron app so it can be distributed across multiple systems and have better UI/UX.
