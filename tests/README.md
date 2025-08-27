# CaliBOT Tests

This folder contains essential test files for CaliBOT functionality. All experimental and duplicate test files have been removed per PROJECT_RULES.md.

## 🟢 Essential Test Files (Working)

### **`telegram_like_tester.py`** - Visual Testing
**Purpose**: End-to-end visual testing of bot functionality
- Sends real TestBot messages to group chat (`-4627994150`)
- Tests complete conversation flows
- Manual verification of bot responses in Telegram
- Used for: Multi-event creation, updates, deletes

**Usage**:
```bash
python tests/telegram_like_tester.py
```
**Then check**: Group chat for bot responses

### **`test_one_by_one_workflow.py`** - Queue Testing
**Purpose**: Automated testing of EventQueueHandler functionality
- Tests the critical "UPDATE Event 2 of 2" workflow
- Simulates button presses for queue advancement
- Automated verification of one-by-one processing
- Used for: Queue processing, event advancement, completion

**Usage**:
```bash
python tests/test_one_by_one_workflow.py
```
**Then check**: Logs for "UPDATE Event 2 of 2" confirmation
```bash
python scripts/render_api_logs.py
```

## 📋 Test Categories (Removed)

### Experimental B2B Demos (Deleted)
- ❌ `comprehensive_b2b_demo.py` - Experimental demo
- ❌ `complete_b2b_demo.py` - Experimental demo
- ❌ `real_b2b_demo.py` - Experimental demo
- ❌ `real_testbot_b2b_demo.py` - Experimental demo
- ❌ `real_visible_b2b_demo.py` - Experimental demo
- ❌ `manual_b2b_test.py` - Manual testing variant
- ❌ `proper_b2b_webhook_demo.py` - Demo variant
- ❌ `proper_full_b2b_demo.py` - Demo variant
- ❌ `proper_testbot_message.py` - Demo variant

### Debug/Test Scripts (Deleted)
- ❌ `quick_format_test.py` - Formatting test (covered by main tests)
- ❌ `test_queue_callback.py` - Debug script (integrated into workflow test)

## 🎯 Testing Workflow (per PROJECT_RULES.md)

### Pre-Testing Checklist
- [ ] Latest version deployed: `python scripts/verify_deployment.py`
- [ ] Backend health check: Visit backend URL
- [ ] Correct group chat: `-4627994150` for real testing
- [ ] Run tests: `python tests/telegram_like_tester.py`

### Visual Testing
1. Run `telegram_like_tester.py`
2. Check group chat for bot responses
3. Verify message formatting and button behavior
4. Test multi-event operations manually

### Queue Testing
1. Run `test_one_by_one_workflow.py`
2. Check logs: `python scripts/render_api_logs.py`
3. Verify "UPDATE Event 2 of 2" appears (CRITICAL)
4. Confirm queue completion without hanging

## 📝 Success Criteria

### ✅ Working Indicators
- Bot responds to TestBot messages in group chat
- Multi-event operations show confirmation keyboards
- One-by-one processing advances: "UPDATE Event 1 of 2" → "UPDATE Event 2 of 2"
- Buttons disappear after interaction
- Queue completes without errors

### ❌ Failure Indicators
- No response from bot in group chat
- Missing "UPDATE Event 2 of 2" in logs
- Buttons remain visible after interaction
- Queue hangs or gets stuck
- 500 errors in callback processing

## 🔧 Environment Setup

### Required for Testing
- **TestBot Token**: Configured in test files
- **Group Chat ID**: `-4627994150` (from PROJECT_RULES.md)
- **Backend URL**: `https://calibot-utq6.onrender.com`
- **Python Packages**: `aiohttp` for async testing

### Installation
```bash
pip install aiohttp
```

---

**Total Test Files**: 2 essential files (from 11+ experimental files)
**Duplicates Removed**: 9+ experimental B2B demo variations
**Debug Scripts Removed**: 2 debug/test scripts
**Maintainability**: ✅ Improved - Clear purpose, no confusion

**REMEMBER**: These are the ONLY test files referenced in PROJECT_RULES.md. All others were experimental and have been removed.
