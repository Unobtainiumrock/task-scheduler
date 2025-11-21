#!/usr/bin/env python3
"""
Tests for scheduler.py

Copyright (C) 2024 Task Prioritizer Contributors
This program is free software under the GPL-3.0 license.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import scheduler
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scheduler import create_timeline


class TestScheduler:
    """Test cases for the scheduler module."""
    
    def test_create_timeline_returns_dict(self):
        """Test that create_timeline returns a dictionary."""
        with patch('scheduler.client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "schedule_date": "2024-01-01",
                "tasks": []
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            result = create_timeline("Test task list")
            assert isinstance(result, dict)
            assert "schedule_date" in result
            assert "tasks" in result
    
    def test_create_timeline_handles_empty_input(self):
        """Test that create_timeline handles empty input gracefully."""
        with patch('scheduler.client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "schedule_date": "2024-01-01",
                "tasks": []
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            result = create_timeline("")
            assert isinstance(result, dict)
    
    def test_create_timeline_includes_required_fields(self):
        """Test that the returned schedule includes required fields."""
        with patch('scheduler.client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "schedule_date": "2024-01-01",
                "tasks": [
                    {
                        "task_name": "Test Task",
                        "start_time": "10:00",
                        "end_time": "11:00",
                        "duration_minutes": 60
                    }
                ]
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            result = create_timeline("Test task")
            assert "schedule_date" in result
            assert "tasks" in result
            if result["tasks"]:
                task = result["tasks"][0]
                assert "task_name" in task
                assert "start_time" in task
                assert "end_time" in task
                assert "duration_minutes" in task

