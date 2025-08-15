# Bot-to-Bot (B2B) Demo Automation Framework

## 🎯 Overview

This document formalizes the automated Bot-to-Bot testing procedures for CaliBOT multi-event operations, requiring ZERO user input and providing comprehensive validation of all scenarios.

## 🚨 Critical Requirements

### Pre-Demo Verification (MANDATORY)
1. **Group Chat ID Verification**: Must use `-4627994150` (YOUR actual group chat)
2. **Deployment Verification**: Run `python scripts/verify_deployment.py` before testing
3. **API Access**: Ensure Render API token is valid for log monitoring
4. **TestBot Ready**: Confirm TestBot can send messages to group chat

### Zero User Input Protocol
- **NO manual confirmations required** - All decisions automated
- **NO waiting for user responses** - Automated timeout handling
- **NO manual intervention** - Complete hands-free execution
- **AUTOMATED decision making** - Smart defaults for all scenarios

## 🤖 B2B Demo Framework Architecture

### TestBot Frontend (Message Sender)
```python
# Located in: tests/comprehensive_multi_event_demo.py
class TestBot:
    - Sends user messages to group chat (-4627994150)
    - Simulates real user interactions
    - Automated button press simulation
    - Handles webhook response capture
```

### CaliBOT Backend (Webhook Processor)
```python
# Production service running on Render.com
# Processes messages via webhook
# Responds with inline keyboards
# Logs all operations for verification
```

### Live Log Monitor (Verification System)
```python
# Fetches logs from Render API in real-time
# Validates backend processing
# Confirms webhook delivery and processing
# Tracks multi-event queue operations
```

## 📋 Complete Demo Scenarios

### 1. Multi-Event Creation
**User Input**: "Create math lesson from 8-9am and 10-11am on Monday"
- ✅ Intent extraction for multiple events
- ✅ Calendar selection (AI + rule-based fallback)  
- ✅ Event creation confirmation
- ✅ Success message formatting
- ✅ Backend log verification

### 2. Multi-Event Update (One by One)
**User Input**: "Update the math lessons" → Select "One by One"
- ✅ Event list display with clickable links
- ✅ "UPDATE Event 1 of 2" message and keyboard
- ✅ **CRITICAL**: "UPDATE Event 2 of 2" message (fixed in v0.1.134)
- ✅ Individual event update processing
- ✅ Queue state management verification

### 3. Multi-Event Update (All at Once)
**User Input**: "Update the math lessons" → Select "All at Once"
- ✅ Batch update processing
- ✅ Confirmation workflow
- ✅ Success message for all events
- ✅ Backend queue clearing

### 4. Multi-Event Delete (One by One)
**User Input**: "Delete the math lessons" → Select "One by One"
- ✅ Event list with deletion options
- ✅ Individual deletion confirmations
- ✅ Progressive deletion processing
- ✅ Queue cleanup verification

### 5. Multi-Event Delete (All at Once)
**User Input**: "Delete the math lessons" → Select "All at Once"
- ✅ Batch deletion confirmation
- ✅ Complete deletion processing
- ✅ Success confirmation
- ✅ API log verification

## 🔧 Automated Button Press Simulation

### Implementation Details
```python
# Webhook callback simulation
async def simulate_button_press(chat_id: int, callback_data: str):
    webhook_url = f"{BACKEND_URL}/telegram-webhook"
    callback_query = {
        "update_id": generate_update_id(),
        "callback_query": {
            "id": str(uuid.uuid4()),
            "from": {"id": chat_id, "is_bot": False},
            "message": {"message_id": get_last_message_id(), "chat": {"id": chat_id}},
            "data": callback_data
        }
    }
    # Send POST request to webhook
    # Wait for processing
    # Verify response via logs
```

### Button Press Scenarios
- **"One by One" Selection**: `callback_data: "update_one_by_one"`
- **"All at Once" Selection**: `callback_data: "update_all_at_once"`
- **Event Update Confirmation**: `callback_data: "confirm_update_[event_id]"`
- **Event Delete Confirmation**: `callback_data: "confirm_delete_[event_id]"`
- **Cancel Operations**: `callback_data: "cancel_[operation]"`

## 📊 Live Log Monitoring Protocol

### Render API Log Fetching
```python
# Use scripts/recent_logs.py (NOT live_logs.py - gets stuck)
async def fetch_recent_logs():
    # Fetch last 30 minutes of logs
    # Filter for webhook processing
    # Extract multi-event queue operations
    # Verify "UPDATE Event 2 of 2" appears
    # Confirm all scenarios complete successfully
```

### Log Verification Checkpoints
1. **Webhook Receipt**: `"Received webhook from Telegram"`
2. **Intent Extraction**: `"Intent extracted:"`
3. **Multi-Event Detection**: `"Multi-event operation detected"`
4. **Queue Processing**: `"Processing event queue for chat_id"`
5. **"UPDATE Event 2 of 2"**: `"UPDATE Event 2 of 2"` (CRITICAL)
6. **Operation Completion**: `"Multi-event operation completed"`

## ⚡ Execution Protocol

### Step-by-Step B2B Demo Execution
```bash
# 1. MANDATORY: Verify deployment
cd /workspaces/calibot
python scripts/verify_deployment.py

# 2. Run comprehensive B2B demo
python tests/comprehensive_multi_event_demo.py

# 3. Monitor execution (AUTOMATED - no user input required)
# - TestBot sends messages automatically
# - Button presses simulated automatically  
# - Log verification runs automatically
# - Success/failure reported automatically

# 4. Validate results
# - 80%+ success rate expected
# - All 5 scenarios should complete
# - "UPDATE Event 2 of 2" must appear in logs
# - No manual intervention required
```

### Success Criteria
- ✅ **All 5 scenarios execute** without manual intervention
- ✅ **"UPDATE Event 2 of 2" message appears** in logs (v0.1.134 fix)
- ✅ **Button presses work** via webhook simulation
- ✅ **Log verification successful** for all operations
- ✅ **80%+ success rate** across all scenarios
- ✅ **Zero user input required** throughout entire demo

## 🚨 Troubleshooting B2B Demo Issues

### Common Issues and Automated Resolutions
1. **Deployment Mismatch**: Auto-restart via `verify_deployment.py`
2. **Webhook Timeouts**: Automated retry with exponential backoff
3. **Log Fetching Stuck**: Use `recent_logs.py` instead of streaming logs
4. **Button Press Failures**: Validate callback_data format automatically
5. **Queue State Issues**: Auto-clear pending operations before testing

### Automated Recovery Procedures
- **Timeout Handling**: 30-second max wait per operation
- **Error Recovery**: Auto-retry failed operations once
- **State Cleanup**: Clear all pending queues before demo
- **Log Verification**: Fallback to manual log check if API fails

## 📝 Demo Results Documentation

### Automated Reporting Format
```
B2B DEMO RESULTS - [TIMESTAMP]
===============================
Deployment Version: [VERSION]
Group Chat: -4627994150
Success Rate: [X]/5 scenarios (XX%)

SCENARIO RESULTS:
✅ Multi-Event Creation: SUCCESS
✅ Update One by One: SUCCESS ("UPDATE Event 2 of 2" confirmed)
✅ Update All at Once: SUCCESS  
✅ Delete One by One: SUCCESS
❌ Delete All at Once: FAILED (timeout)

CRITICAL VERIFICATIONS:
✅ "UPDATE Event 2 of 2" message appeared
✅ Button press simulation working
✅ Log verification successful
✅ Zero user input required

NEXT ACTIONS:
- Investigate delete_all_at_once timeout issue
- No manual intervention needed for 4/5 scenarios
```

## 🔄 Continuous Integration

### Automated B2B Demo Triggers
- **After every deployment** - Verify multi-event functionality works
- **Before major releases** - Complete validation of all scenarios
- **Bug fix verification** - Targeted testing of specific fixes
- **Performance monitoring** - Regular health checks

### Integration with Development Workflow
1. Code change → Git push → Auto-deployment
2. `verify_deployment.py` confirms latest version deployed
3. `comprehensive_multi_event_demo.py` runs automatically
4. Results logged and reported
5. Failures trigger alerts for immediate investigation

This B2B demo framework ensures CaliBOT multi-event functionality remains reliable and fully automated, requiring zero user input while providing comprehensive validation of all critical scenarios.
