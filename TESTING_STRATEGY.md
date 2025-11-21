# Testing Strategy

This document outlines the testing approach for the Task Prioritizer project, following a layered testing pyramid strategy.

## Testing Pyramid

```
        /\
       /  \     E2E Tests (few, slow, expensive)
      /____\    - Full user workflows
     /      \   - Real integrations
    /________\  Integration Tests (some, medium speed)
   /          \ - Test components working together
  /____________\ Unit Tests (many, fast, cheap)
                 - Test individual functions
                 - Use mocks for dependencies
```

## Layer 1: Unit Tests (Current Implementation)

**Status:** ✅ Implemented

**Purpose:** Test individual functions and methods in isolation.

**Characteristics:**
- Fast execution (< 5 seconds)
- Many tests (7+ tests currently)
- Use mocks for external dependencies
- Run on every commit/PR
- Work in CI environments

**What We Test:**
- Function logic and correctness
- Input validation
- Error handling paths
- Function calls with correct arguments
- Data transformations

**What We Mock:**
- `notify2` (requires D-Bus, not available in CI)
- `subprocess` calls (paplay, dunstctl)
- OpenAI API calls (expensive, rate-limited)
- File I/O operations

**Example:**
```python
def test_play_alarm_calls_paplay(self, mock_popen):
    """Verifies play_alarm() calls subprocess.Popen with correct args."""
    from timer import play_alarm
    play_alarm()
    mock_popen.assert_called_once()
    assert mock_popen.call_args[0][0][0] == "paplay"
```

**Why Mock?**
- **Speed:** Real dependencies are slow (API calls, system calls)
- **Reliability:** External systems may be unavailable or flaky
- **Cost:** Real API calls cost money
- **Isolation:** Test YOUR code, not third-party libraries
- **CI Compatibility:** CI environments don't have desktop services

**Coverage Goal:** 70%+ overall coverage

**Current Status:**
- ✅ 7 unit tests passing
- ✅ 33% overall coverage (scheduler: 62%, timer: 29%)
- ✅ All tests run in CI via GitHub Actions

## Layer 2: Integration Tests (Future Enhancement)

**Status:** ⏳ Not Yet Implemented

**Purpose:** Test components working together with real dependencies.

**Characteristics:**
- Medium execution time (10-30 seconds)
- Fewer tests (5-10 tests)
- Use real dependencies where possible
- Run on scheduled basis (nightly) or before releases
- May require special CI setup

**What We Should Test:**
- `scheduler.py` → `schedule.json` → `timer.py` workflow
- Real file I/O operations
- Real notification system (if CI supports it)
- Error handling with real dependencies
- Data flow between components

**Potential Tests:**
```python
def test_scheduler_creates_valid_schedule_json():
    """Test that scheduler creates valid JSON that timer can read."""
    # Real OpenAI API call (or use test API key)
    schedule = create_timeline("Test tasks")
    assert schedule is not None
    assert "tasks" in schedule
    
    # Verify timer can read it
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(schedule, f)
        temp_file = f.name
    
    # Timer should be able to load it
    with open(temp_file, 'r') as f:
        loaded = json.load(f)
    assert loaded == schedule
```

**Challenges:**
- Requires real OpenAI API key (costs money)
- Requires D-Bus/notification daemon (complex CI setup)
- Slower execution
- May be flaky

**When to Add:**
- Before major releases
- When adding new integrations
- When critical bugs are found in production

## Layer 3: End-to-End Tests (Manual + Optional Automated)

**Status:** 📝 Manual Testing (Recommended)

**Purpose:** Test complete user workflows from start to finish.

**Characteristics:**
- Slow execution (minutes)
- Very few tests (1-3 workflows)
- Full system with all real dependencies
- Manual testing or expensive automated setup
- Run before releases or major changes

**What We Test:**
- Complete user journey: tasks.md → schedule.json → timer execution
- Real notifications appear on screen
- Real sounds play
- User interactions (pressing Enter, skipping tasks)
- Notification synchronization
- Timeline notifications display correctly

**Manual Testing Checklist:**
- [ ] Run `python3 scheduler.py tasks.md`
- [ ] Verify `schedule.json` is created and valid
- [ ] Run `python3 timer.py schedule.json`
- [ ] Verify timeline notifications appear
- [ ] Verify active timer notification updates
- [ ] Test skipping a task early (press Enter)
- [ ] Verify alarm sound plays when task completes
- [ ] Verify notifications close properly
- [ ] Test full day's schedule

**Optional Automated E2E:**
If you want automated E2E tests, you'd need:
- Docker container with D-Bus and notification daemon
- Headless browser or desktop automation
- Screenshot comparison for notifications
- Audio capture/verification for sounds

**Recommendation:** Manual testing is sufficient for this project size.

## Testing Philosophy

### What Unit Tests (with mocks) Verify:
✅ Your code logic is correct  
✅ Functions are called with right arguments  
✅ Error handling works  
✅ Data transformations are correct  
✅ Code paths execute as expected  

### What Unit Tests DON'T Verify:
❌ Real integrations work  
❌ External systems behave correctly  
❌ End-to-end user experience  
❌ System-level interactions  

### The Trade-off:
- **Unit tests (mocked):** Fast, reliable, catch logic bugs
- **Integration/E2E tests:** Slow, expensive, catch integration bugs

**Best Practice:** Use unit tests for rapid feedback, manual testing for E2E validation.

## Current Test Suite

### Scheduler Tests (`tests/test_scheduler.py`)
- ✅ `test_create_timeline_returns_dict`
- ✅ `test_create_timeline_handles_empty_input`
- ✅ `test_create_timeline_includes_required_fields`

### Timer Tests (`tests/test_timer.py`)
- ✅ `test_play_alarm_calls_paplay`
- ✅ `test_close_all_notifications_calls_dunstctl`
- ✅ `test_queue_timeline_notifications_creates_notifications`
- ✅ `test_update_timeline_notification_updates_correctly`

**Total:** 7 unit tests, all passing

## Running Tests

### Local Development
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scheduler --cov=timer --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_scheduler.py

# Run specific test
pytest tests/test_timer.py::TestTimerFunctions::test_play_alarm_calls_paplay
```

### CI/CD
Tests run automatically on:
- Every push to `nicholas`, `main`, or `master`
- Every pull request
- Via GitHub Actions workflow (`.github/workflows/coverage.yml`)

## Coverage Goals

**Current:** 33% overall
- `scheduler.py`: 62%
- `timer.py`: 29%

**Target:** 70%+ overall
- Focus on increasing `timer.py` coverage
- Add tests for error paths
- Add tests for edge cases

## Adding New Tests

### When to Add Unit Tests:
- New functions or features
- Bug fixes (test the fix)
- Edge cases discovered
- Error handling improvements

### Test Naming Convention:
- `test_<function_name>_<what_it_tests>`
- Example: `test_play_alarm_calls_paplay`

### Mock Strategy:
- Mock external dependencies (APIs, system calls)
- Mock expensive operations
- Test your code's logic, not third-party libraries

## Future Enhancements

1. **Increase Coverage:**
   - Add tests for error paths in `timer.py`
   - Test notification update logic
   - Test task skipping edge cases

2. **Integration Tests (Optional):**
   - Test scheduler → timer workflow
   - Test with real file I/O
   - Consider Docker-based testing environment

3. **E2E Automation (Optional):**
   - Docker container with full desktop environment
   - Automated notification verification
   - Screenshot-based regression testing

## Conclusion

The current unit test suite provides a solid foundation for catching bugs quickly. For a desktop application like this, combining automated unit tests with manual end-to-end testing is a practical and effective approach.

**Remember:** The goal isn't 100% test coverage—it's confidence that your code works correctly and catches regressions early.

