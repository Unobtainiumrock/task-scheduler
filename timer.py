import json
import subprocess
import time
import sys

# --- CONFIGURATION ---
# A unique ID for notifications so that each new one replaces the last.
NOTIFICATION_ID = "9991"
# Path to a system sound for the alarm. This is a common one.
ALARM_SOUND_PATH = "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"

def send_notification(summary, body, urgency="normal"):
    """
    Sends a desktop notification using notify-send.
    Crucially, it uses a replacement ID to prevent spamming the desktop.
    """
    try:
        subprocess.run([
            "notify-send",
            summary,
            body,
            "--app-name=Task Timer",
            f"--urgency={urgency}",
            f"--replace-id={NOTIFICATION_ID}"
        ], check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: `notify-send` command not found.")
        print("Please install it with: `sudo apt-get install libnotify-bin`")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error sending notification: {e.stderr}")
        # This can happen if the notification service isn't running.

def play_alarm():
    """Plays the alarm sound using paplay."""
    try:
        subprocess.Popen(["paplay", ALARM_SOUND_PATH])
    except FileNotFoundError:
        print("\nWarning: `paplay` command not found. Cannot play alarm sound.")
        print("Install it with `sudo apt-get install pulseaudio-utils`")

def run_task_timer(task, next_task_info):
    """
    Handles the countdown logic for a single task.
    """
    task_name = task.get("task_name", "Unnamed Task")
    duration_minutes = task.get("duration_minutes", 0)
    
    if duration_minutes <= 0:
        print(f"Skipping task '{task_name}' with invalid duration.")
        return

    remaining_seconds = duration_minutes * 60

    print(f"\n---\nStarting task: '{task_name}' for {duration_minutes} minutes.")
    print(f"Next up: {next_task_info}")
    
    while remaining_seconds > 0:
        # divmod is perfect for getting minutes and seconds
        mins, secs = divmod(remaining_seconds, 60)
        
        # Format the time to always have two digits (e.g., 09:05)
        countdown_str = f"{mins:02d}:{secs:02d} remaining"
        
        notification_title = f"Current Task: {task_name}"
        notification_body = f"<b>{countdown_str}</b>\nNext: {next_task_info}"
        
        send_notification(notification_title, notification_body)
        
        # Print to terminal as well, using carriage return to overwrite the line
        print(f"\r⏳ {countdown_str}", end="")
        
        time.sleep(1)
        remaining_seconds -= 1

    # --- Time's up! ---
    print("\r✅ Time's up!                           ") # Clear the line
    final_title = f"Time's up for: {task_name}"
    final_body = f"Take a break! \nNext up is: {next_task_info}"
    send_notification(final_title, final_body, urgency="critical")
    play_alarm()
    
    # Wait for the user to acknowledge before moving to the next task
    input("🚨 ALARM! Press Enter to stop the alarm and start the next task...")


def main():
    """Main function to load schedule and run the timers."""
    if len(sys.argv) < 2:
        print("Usage: python3 timer.py <path_to_schedule.json>")
        sys.exit(1)

    schedule_file = sys.argv[1]

    try:
        with open(schedule_file, 'r') as f:
            schedule = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{schedule_file}' was not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: The file '{schedule_file}' is not a valid JSON file.")
        sys.exit(1)

    tasks = schedule.get("tasks", [])
    if not tasks:
        print("No tasks found in the schedule file.")
        return

    print(f"Loaded schedule for {schedule.get('schedule_date', 'today')}.")
    print("Press Ctrl+C to exit at any time.")

    for i, task in enumerate(tasks):
        # Determine the next task for the preview
        if i + 1 < len(tasks):
            next_task = tasks[i+1]
            next_name = next_task.get('task_name', 'Unnamed')
            next_dur = next_task.get('duration_minutes', 0)
            next_task_info = f"'{next_name}' ({next_dur} min)"
        else:
            next_task_info = "End of schedule!"
            
        run_task_timer(task, next_task_info)

    print("\n---\n🎉 All tasks completed! Great work. ---")
    send_notification("Schedule Finished!", "All tasks for today are complete.", "critical")


if __name__ == "__main__":
    main()
