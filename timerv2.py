import json
import subprocess
import time
import sys
import select # MODIFICATION: Import the select module for non-blocking input

try:
    import notify2
except ImportError:
    print("Error: The `notify2` library is required for desktop notifications.")
    print("Please install it with: `pip install notify2`")
    sys.exit(1)

# --- CONFIGURATION ---
# Path to a system sound for the alarm. This is a common one.
ALARM_SOUND_PATH = "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"

def play_alarm():
    """Plays the alarm sound using paplay."""
    try:
        # Use Popen to play sound in the background without blocking
        subprocess.Popen(["paplay", ALARM_SOUND_PATH])
    except FileNotFoundError:
        print("\nWarning: `paplay` command not found. Cannot play alarm sound.")
        print("Install it with `sudo apt-get install pulseaudio-utils`")

def run_task_timer(task, next_task_info):
    """
    Handles the countdown logic for a single task using the notify2 library.
    Now allows skipping the current task by pressing Enter.
    """
    task_name = task.get("task_name", "Unnamed Task")
    duration_minutes = task.get("duration_minutes", 0)
    
    if duration_minutes <= 0:
        print(f"Skipping task '{task_name}' with invalid duration.")
        return

    remaining_seconds = duration_minutes * 60

    print(f"\n---\nStarting task: '{task_name}' for {duration_minutes} minutes.")
    print(f"Next up: {next_task_info}")
    # MODIFICATION: Add instruction for the user
    print("Press [Enter] at any time to finish this task early and move on.")
    
    # --- DYNAMIC NOTIFICATION LOGIC using notify2 ---
    notification = notify2.Notification(
        f"Starting Task: {task_name}",
        f"Time remaining: {duration_minutes:02d}:00\nNext: {next_task_info}",
        icon="dialog-information" # You can change the icon
    )
    notification.set_urgency(notify2.URGENCY_CRITICAL)
    notification.show()

    try:
        while remaining_seconds > 0:
            # MODIFICATION: Use select to wait for 1 second OR for user input
            # The '1' at the end is the timeout in seconds.
            ready_to_read, _, _ = select.select([sys.stdin], [], [], 1)
            
            # MODIFICATION: If sys.stdin is in the ready_to_read list, the user hit Enter
            if ready_to_read:
                print("\n⏩ Skipping to the next task!")
                # Consume the input from the buffer
                sys.stdin.readline()
                break # Exit the countdown loop

            remaining_seconds -= 1
            mins, secs = divmod(remaining_seconds, 60)
            countdown_str = f"{mins:02d}:{secs:02d} remaining"
            
            # Update the single notification object in place
            notification.update(
                f"Current Task: {task_name}",
                f"<b>{countdown_str}</b>\nNext: {next_task_info}"
            )
            notification.show()
            
            # Use carriage return '\r' to print on the same line
            print(f"\r⏳ {countdown_str}", end="")
            
    finally:
        # This block ALWAYS runs, even if you press Ctrl+C or skip early.
        # This guarantees the notification is closed cleanly.
        notification.close()

    # --- Time's up! ---
    # MODIFICATION: Clear the countdown line before printing the final message
    print("\r✅ Task complete!                     ")
    
    final_title = f"Finished: {task_name}"
    final_body = f"Take a break! \nNext up is: {next_task_info}"
    
    alarm_notification = notify2.Notification(
        final_title, final_body, icon="dialog-warning"
    )
    alarm_notification.set_urgency(notify2.URGENCY_CRITICAL)
    alarm_notification.show()

    play_alarm()
    
    input("🚨 ALARM! Press Enter to stop the alarm and start the next task...")


def main():
    """Main function to load schedule and run the timers."""
    if len(sys.argv) < 2:
        print("Usage: python timer.py <path_to_schedule.json>")
        sys.exit(1)

    schedule_file = sys.argv[1]

    try:
        # Initialize the D-Bus connection for notify2
        notify2.init("Task Countdown Timer")
    except Exception as e:
        print(f"Failed to initialize notification system (D-Bus): {e}")
        print("Ensure a notification daemon like 'dunst' is running.")
        sys.exit(1)

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
    print("Press Ctrl+C to exit at any time for a clean shutdown.")

    try:
        for i, task in enumerate(tasks):
            if i + 1 < len(tasks):
                next_task = tasks[i+1]
                next_name = next_task.get('task_name', 'Unnamed')
                next_dur = next_task.get('duration_minutes', 0)
                next_task_info = f"'{next_name}' ({next_dur} min)"
            else:
                next_task_info = "End of schedule!"
                
            run_task_timer(task, next_task_info)
    except KeyboardInterrupt:
        # This catches Ctrl+C if it's pressed between tasks.
        print("\n\nTimer stopped by user. Exiting gracefully.")
        sys.exit(0)

    print("\n---\n🎉 All tasks completed! Great work. ---")
    
    final_notification = notify2.Notification(
        "Schedule Finished!", "All tasks for today are complete.", icon="emblem-ok"
    )
    final_notification.set_urgency(notify2.URGENCY_CRITICAL)
    final_notification.show()


if __name__ == "__main__":
    main()
