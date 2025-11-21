#!/usr/bin/env python3
"""
Task Timer - Desktop timer with synchronized notifications

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
"""

import json
import subprocess
import time
import sys
import select

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

def close_all_notifications():
    """
    Force-close all notifications using dunstctl.
    This actually removes notifications from the screen, unlike notify2.close()
    """
    try:
        # Try to close all notifications via dunstctl
        result = subprocess.run(
            ["dunstctl", "close-all"],
            capture_output=True,
            timeout=1
        )
        if result.returncode == 0:
            time.sleep(0.1)  # Give dunst time to process
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # dunstctl not available or timed out - that's okay
        pass
    except Exception:
        # Any other error - silently fail
        pass
    return False

def queue_timeline_notifications(tasks, current_index=0):
    """
    Queue all tasks for the day as a sequence of notifications.
    This creates a timeline view that persists while the timer runs.
    
    Args:
        tasks: List of all tasks in the schedule
        current_index: Index of the currently active task
    """
    timeline_notifications = []
    
    for i, task in enumerate(tasks):
        task_name = task.get("task_name", "Unnamed Task")
        start_time = task.get("start_time", "??:??")
        duration = task.get("duration_minutes", 0)
        
        # Determine status
        if i < current_index:
            status = "✅ Completed"
            icon = "emblem-ok"
            urgency = notify2.URGENCY_LOW
        elif i == current_index:
            status = "⏳ Active Now"
            icon = "dialog-information"
            urgency = notify2.URGENCY_CRITICAL
        else:
            status = "📅 Upcoming"
            icon = "appointment-soon"
            urgency = notify2.URGENCY_NORMAL
        
        # Create timeline notification
        timeline_notif = notify2.Notification(
            f"{status}: {task_name}",
            f"Time: {start_time} | Duration: {duration} min",
            icon=icon
        )
        timeline_notif.set_urgency(urgency)
        # Set a longer timeout so timeline notifications persist
        timeline_notif.set_timeout(0)  # Never expire - we'll manage them
        
        # Use a different stack tag so timeline notifications don't interfere
        # with the active timer notification
        try:
            timeline_notif.set_hint("x-dunst-stack-tag", f"timeline-{i}")
            # Don't use replacement ID - we want these to stack/queue
        except AttributeError:
            pass
        
        timeline_notif.show()
        timeline_notifications.append(timeline_notif)
        
        # Small delay between notifications to prevent overwhelming the daemon
        time.sleep(0.1)
    
    return timeline_notifications

def update_timeline_notification(tasks, completed_index):
    """
    Update a specific timeline notification to mark it as completed.
    This is called when a task finishes.
    """
    if completed_index >= len(tasks):
        return
    
    task = tasks[completed_index]
    task_name = task.get("task_name", "Unnamed Task")
    start_time = task.get("start_time", "??:??")
    duration = task.get("duration_minutes", 0)
    
    # Create updated notification for completed task
    completed_notif = notify2.Notification(
        f"✅ Completed: {task_name}",
        f"Time: {start_time} | Duration: {duration} min",
        icon="emblem-ok"
    )
    completed_notif.set_urgency(notify2.URGENCY_LOW)
    completed_notif.set_timeout(0)
    
    try:
        # Use the same stack tag to replace the old notification
        completed_notif.set_hint("x-dunst-stack-tag", f"timeline-{completed_index}")
        completed_notif.set_hint("x-dunst-replace-id", completed_index)
    except AttributeError:
        pass
    
    completed_notif.show()

def run_task_timer(task, next_task_info, notification_id=None):
    """
    Handles the countdown logic for a single task using the notify2 library.
    Now allows skipping the current task by pressing Enter.
    
    Args:
        task: Dictionary containing task information
        next_task_info: String describing the next task
        notification_id: Optional persistent ID for notification replacement
    """
    task_name = task.get("task_name", "Unnamed Task")
    duration_minutes = task.get("duration_minutes", 0)
    
    if duration_minutes <= 0:
        print(f"Skipping task '{task_name}' with invalid duration.")
        return None

    remaining_seconds = duration_minutes * 60

    print(f"\n---\nStarting task: '{task_name}' for {duration_minutes} minutes.")
    print(f"Next up: {next_task_info}")
    print("Press [Enter] at any time to finish this task early and move on.")
    
    # --- DYNAMIC NOTIFICATION LOGIC using notify2 ---
    # Use a persistent notification ID to replace previous notifications
    if notification_id is None:
        notification_id = 0
    
    # Don't close timeline notifications - they should persist
    # Replacement IDs ensure the active timer notification replaces itself
    
    notification = notify2.Notification(
        f"Starting Task: {task_name}",
        f"Time remaining: {duration_minutes:02d}:00\nNext: {next_task_info}",
        icon="dialog-information"
    )
    notification.set_urgency(notify2.URGENCY_CRITICAL)
    # Set timeout to 0 (never expire) so we control when it closes
    notification.set_timeout(0)
    # Use replacement hint to replace previous notifications with same ID
    # This makes notifications replace each other instead of stacking
    try:
        # Use a consistent replacement ID so notifications replace each other
        notification.set_hint("x-dunst-stack-tag", "task-timer")
        notification.set_hint("x-dunst-replace-id", notification_id)
    except AttributeError:
        # Some notification daemons don't support hints, that's okay
        pass
    notification.show()
    # Small delay to ensure notification is processed
    time.sleep(0.1)

    alarm_notification = None
    task_skipped = False  # Track if task was skipped early
    
    try:
        while remaining_seconds > 0:
            # Use select to wait for 1 second OR for user input
            ready_to_read, _, _ = select.select([sys.stdin], [], [], 1)
            
            if ready_to_read:
                print("\n⏩ Skipping to the next task!")
                # Consume the input from the buffer
                sys.stdin.readline()
                # Mark that task was skipped
                task_skipped = True
                # Close the notification object (replacement IDs will handle screen cleanup)
                notification.close()
                # Give the daemon time to process
                time.sleep(0.2)
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
        if notification:
            # Close the notification object
            # Replacement IDs will ensure the next active timer replaces this one
            notification.close()
            # Give the daemon time to process the close before creating new notification
            time.sleep(0.2)

    # Only show alarm if task completed normally (not skipped)
    if not task_skipped:
        # --- Time's up! ---
        print("\r✅ Task complete!                     ")
        
        final_title = f"Finished: {task_name}"
        final_body = f"Take a break! \nNext up is: {next_task_info}"
        
        alarm_notification = notify2.Notification(
            final_title, final_body, icon="dialog-warning"
        )
        alarm_notification.set_urgency(notify2.URGENCY_CRITICAL)
        # Set a timeout for the alarm notification (10 seconds)
        alarm_notification.set_timeout(10000)
        # Use a different ID for alarm notifications
        try:
            alarm_notification.set_hint("x-dunst-stack-tag", f"alarm-{notification_id}")
        except AttributeError:
            pass
        alarm_notification.show()

        play_alarm()
        
        input("🚨 ALARM! Press Enter to stop the alarm and start the next task...")
        
        # Close the alarm notification before starting the next task
        # Alarm notifications use a different stack tag, so closing is safe
        if alarm_notification:
            # Close the alarm - it uses a different stack tag so won't affect timeline
            alarm_notification.close()
            # Give the daemon time to process before next notification
            time.sleep(0.2)
    
    return notification_id + 1


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

    # Clear any pre-existing notifications at startup (except our timeline)
    # This ensures our timer notifications appear on top
    print("Clearing any pre-existing notifications...")
    close_all_notifications()
    time.sleep(0.3)

    # Queue all tasks as timeline notifications at startup
    # This creates a persistent sequence showing the day's schedule
    print("Queueing timeline notifications for today's schedule...")
    timeline_notifications = queue_timeline_notifications(tasks, current_index=0)
    time.sleep(0.5)  # Give time for all timeline notifications to appear

    # Track notification ID to ensure proper replacement
    notification_id = 0
    
    try:
        for i, task in enumerate(tasks):
            if i + 1 < len(tasks):
                next_task = tasks[i + 1]
                next_name = next_task.get('task_name', 'Unnamed')
                next_dur = next_task.get('duration_minutes', 0)
                next_task_info = f"'{next_name}' ({next_dur} min)"
            else:
                next_task_info = "End of schedule!"
            
            # Update timeline to mark current task as active
            if i > 0:
                # Mark previous task as completed in timeline
                update_timeline_notification(tasks, i - 1)
            
            notification_id = run_task_timer(task, next_task_info, notification_id)
            
            # After task completes, update timeline
            update_timeline_notification(tasks, i)
    except KeyboardInterrupt:
        # This catches Ctrl+C if it's pressed between tasks.
        print("\n\nTimer stopped by user. Exiting gracefully.")
        sys.exit(0)

    print("\n---\n🎉 All tasks completed! Great work. ---")
    
    # Mark the last task as completed in timeline
    if tasks:
        update_timeline_notification(tasks, len(tasks) - 1)
    
    # The active timer notification is already closed via notify2.close()
    # Timeline notifications persist to show the completed schedule
    time.sleep(0.3)
    
    final_notification = notify2.Notification(
        "Schedule Finished!", "All tasks for today are complete.", icon="emblem-ok"
    )
    final_notification.set_urgency(notify2.URGENCY_CRITICAL)
    final_notification.set_timeout(5000)  # 5 second timeout
    final_notification.show()


if __name__ == "__main__":
    main()
