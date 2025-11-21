#!/usr/bin/env python3
"""
Tests for timer.py

Copyright (C) 2024 Task Prioritizer Contributors
This program is free software under the GPL-3.0 license.
"""

import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock, call
import tempfile

# Mock notify2 BEFORE importing timer to prevent sys.exit() on import failure
# This is needed because notify2 requires dbus which isn't available in CI
mock_notify2 = MagicMock()
mock_notification = MagicMock()
mock_notify2.Notification = MagicMock(return_value=mock_notification)
mock_notify2.URGENCY_LOW = 0
mock_notify2.URGENCY_NORMAL = 1
mock_notify2.URGENCY_CRITICAL = 2
sys.modules['notify2'] = mock_notify2

# Add parent directory to path to import timer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTimerFunctions:
    """Test cases for timer module functions."""
    
    @patch('timer.subprocess.Popen')
    def test_play_alarm_calls_paplay(self, mock_popen):
        """Test that play_alarm calls paplay."""
        from timer import play_alarm
        play_alarm()
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == "paplay"
    
    @patch('timer.subprocess.run')
    def test_close_all_notifications_calls_dunstctl(self, mock_run):
        """Test that close_all_notifications calls dunstctl close-all."""
        from timer import close_all_notifications
        mock_run.return_value.returncode = 0
        result = close_all_notifications()
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "dunstctl"
        assert call_args[1] == "close-all"
    
    def test_queue_timeline_notifications_creates_notifications(self):
        """Test that queue_timeline_notifications creates notifications."""
        from timer import queue_timeline_notifications
        
        # Reset the mock to track new calls
        mock_notify2.Notification.reset_mock()
        mock_notif = MagicMock()
        mock_notify2.Notification.return_value = mock_notif
        
        tasks = [
            {
                "task_name": "Task 1",
                "start_time": "10:00",
                "duration_minutes": 30
            },
            {
                "task_name": "Task 2",
                "start_time": "11:00",
                "duration_minutes": 60
            }
        ]
        
        result = queue_timeline_notifications(tasks, current_index=0)
        
        # Should create notifications for all tasks
        assert len(result) == 2
        assert mock_notify2.Notification.call_count == 2
        assert mock_notif.show.call_count == 2
    
    def test_update_timeline_notification_updates_correctly(self):
        """Test that update_timeline_notification updates notifications."""
        from timer import update_timeline_notification
        
        # Reset the mock to track new calls
        mock_notify2.Notification.reset_mock()
        mock_notif = MagicMock()
        mock_notify2.Notification.return_value = mock_notif
        
        tasks = [
            {
                "task_name": "Task 1",
                "start_time": "10:00",
                "duration_minutes": 30
            }
        ]
        
        update_timeline_notification(tasks, 0)
        
        mock_notif.show.assert_called_once()
        # Check that it was called with completed status
        assert mock_notify2.Notification.called
        call_args = mock_notify2.Notification.call_args[0]
        assert "Completed" in call_args[0] or "✅" in call_args[0]

