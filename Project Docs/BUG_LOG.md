# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## v0.1.226 - Critical Duplicate Confirmation Message Fix

**CRITICAL BUG FIX**: Fixed duplicate confirmation messages not being sent to users.

### Root Cause
- CreateOperation correctly returned `requires_user_action: True` with message and keyboard
- Routes.py had incorrect logic: when `requires_user_action` was True, it did nothing (`pass`)
- This caused duplicate confirmation messages to never be sent to Telegram
- Users received NO response for duplicate event creation requests
- Subsequent messages then failed with "I'm experiencing technical difficulties"

### Fixes Applied
1. **Fixed requires_user_action handling**: Updated routes.py to actually send messages when `requires_user_action` is True
2. **Added proper message sending**: Now sends both message and keyboard to Telegram
3. **Added conversation state tracking**: Stores assistant messages for proper conversation flow
4. **Restored duplicate callback handler**: Added back the `handle_duplicate_confirmation_callback` function

### Technical Details
- The issue was in `process_user_message()` function in routes.py
- When CreateOperation returned `requires_user_action: True`, the code did `pass` instead of sending the message
- Now properly extracts message and keyboard from result and sends to Telegram
- This fixes the exact issue: "add a 'test event' today at 7pm" now shows duplicate confirmation buttons

### Testing Required
- Test duplicate event creation: "add a 'test event' today at 7pm"
- Should now show: "Found 1 potential duplicate event(s): ... Do you want to create these events anyway?"
- With buttons: "✅ Create Anyway" and "❌ Cancel"
- Subsequent messages should work normally

## v0.1.225 - Duplicate Confirmation Callback Fix

---

## Bug Tracking Rules

1. **🚨 ONLY USER CAN MARK BUGS AS FIXED** - Assistant cannot change status to 🟢 FIXED
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
