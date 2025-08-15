# Tests Directory

This directory contains all test files and demo scripts for the Calibot project.

## 🚨 CRITICAL TESTING RULES 🚨

### GROUP CHAT TESTING REQUIREMENTS
**MANDATORY**: Always verify you're testing on the CORRECT group chat before running any real tests!

1. **Check Last Message Time**: Last message should be recent (within current session)
2. **Verify Group Identity**: Confirm you're in the right CaliBOT test group  
3. **Check Chat History**: Look for recent test interactions to confirm correct group
4. **Time Verification**: User mentioned last message at 07:57 - if older, check group selection
5. **Send Test Command**: Use `/status` to verify bot is active and responsive

**DETAILED VERIFICATION**: See `GROUP_CHAT_VERIFICATION.md` for complete group verification protocol

### MULTI-EVENT FIX TESTING PROTOCOL
**For "UPDATE Event 2 of 2" verification:**

1. **Pre-Test Verification** (MANDATORY):
   ```bash
   python scripts/quick_version_check.py
   ```
   Must show version 0.1.133 and operational status

2. **Group Chat Verification** (MANDATORY):
   - Verify recent message activity (not 07:57 from hours ago)
   - Send `/status` command to confirm bot responsiveness
   - Check you're in correct CaliBOT test group
   - Only proceed if group verification passes

3. **Multi-Event Test Workflow**:
   - Send: "update my lessons tomorrow"  
   - Bot should show multi-event confirmation
   - Click: "1️⃣ One by One"
   - Bot shows: "UPDATE Event 1 of 2"
   - Click: "✅ Yes"
   - Bot should show: "UPDATE Event 2 of 2" ← KEY VERIFICATION
   - Complete workflow

4. **Fix Verification Points**:
   - Event 2 appears after Event 1 confirmation
   - No "nothing happened" behavior
   - Complete one-by-one progression works

### DOCUMENTATION REFERENCES
- **Fix Details**: `MULTI_EVENT_FIX_PROCEDURE.md`
- **Group Verification**: `GROUP_CHAT_VERIFICATION.md`
- **Test Rules**: This README.md

## Organization Rules

To maintain a clean project structure, **ALL** test files and demo files must be placed in this `tests/` folder:

- `test_*.py` - Test files
- `*_test.py` - Alternative test file naming
- `*demo*.py` - Demo and example scripts
- `queue_demo.py` - Queue system demonstrations
- `simple_queue_demo.py` - Simple queue examples

## File Organization Script

Use the provided script to automatically move misplaced test files:

```bash
./scripts/organize_files.sh
```

This script will:
- Find any test or demo files in the project root
- Find any test files in the backend directory  
- Move them to this `tests/` folder
- Show the final organization

## Current Test Files

### Bug Fix Tests
- `test_bug_fix_validation.py` - Validates fixes for the 'list' object has no attribute 'get' error

### Integration Tests
- `test_all_fixes.py` - Comprehensive fix validation
- `test_batch_events.py` - Batch event processing tests
- `test_calendar_context_memory.py` - Calendar context and memory tests
- `test_comprehensive_validation.py` - Full system validation
- `test_context_and_calendar_selection.py` - Context and calendar selection tests
- `test_delete_multi_events.py` - Multi-event deletion tests
- `test_exact_scenario.py` - Specific scenario tests
- `test_json_prompt.py` - JSON prompt processing tests
- `test_production_scenario.py` - Production environment tests
- `test_time_handling.py` - Time and date handling tests

### Backend Tests
- `test_final_validation.py` - Final validation tests
- `test_intent_validation.py` - Intent extraction validation
- `test_simple_delete.py` - Simple deletion operation tests

### Demo Files
- `queue_demo.py` - Queue system demonstration
- `simple_queue_demo.py` - Simple queue usage examples

## Running Tests

Run individual tests:
```bash
python tests/test_bug_fix_validation.py
```

Run all tests (when test runner is available):
```bash
python -m pytest tests/
```

## GitIgnore Rules

The project `.gitignore` is configured to:
- Prevent test files from being placed outside this folder
- Allow test files only within `tests/`
- Help maintain project organization

## Guidelines

1. **New test files**: Always create them directly in this `tests/` folder
2. **Demo scripts**: Place all demo and example scripts here
3. **File naming**: Use clear, descriptive names with appropriate prefixes
4. **Documentation**: Update this README when adding new test categories

## Bug Fixes Tested

### Fixed: 'list' object has no attribute 'get' Error

**Problem**: The application was crashing with the error `'list' object has no attribute 'get'` when processing events for deletion.

**Root Cause**: The code assumed that event data from Google Calendar API would always be dictionaries, but sometimes the API returns lists or other data types.

**Solution**: Added comprehensive type checking and validation:
- Validate that `events` is a list before processing
- Check each `event` is a dictionary before calling `.get()`
- Skip invalid events with warning logs instead of crashing
- Validate required fields like `id` exist before processing

**Files Modified**:
- `backend/app/api/routes.py` - Added type checking for event processing

**Test Coverage**:
- `test_bug_fix_validation.py` - Comprehensive validation of the fix
