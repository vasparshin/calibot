# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## v0.1.225 - Duplicate Confirmation Callback Fix

**CRITICAL BUG FIX**: Fixed duplicate event confirmation callbacks not being processed.

### Root Cause
- Duplicate confirmation keyboards were created with `confirm_duplicates` and `cancel_duplicates` callback data
- The callback handling code in `routes.py` only handled specific patterns but missed these exact callback types
- When users clicked duplicate confirmation buttons, the callbacks fell through to "Unknown callback data" warning
- This caused the bot to break after duplicate detection, showing "technical difficulties" for subsequent messages

### Fixes Applied
1. **Added duplicate callback handler**: Added `handle_duplicate_confirmation_callback()` function in `routes.py`
2. **Added callback routing**: Updated `handle_callback_query()` to route `confirm_duplicates` and `cancel_duplicates` to the new handler
3. **Added confirmation handler method**: Added `handle_duplicate_confirmation()` method to `ConfirmationHandler`
4. **Added operation confirmation handling**: Added `handle_confirmation()` method to `CreateOperation` to process duplicate confirmations
5. **Proper status updates**: Added status text updates when buttons are clicked ("✅ Creating duplicates" / "❌ Cancelled")

### Technical Details
- Callbacks now properly remove inline keyboards and show status text
- Confirmed duplicates proceed with event creation using stored pending operation data
- Cancelled duplicates clear pending data and show cancellation message
- All subsequent messages work normally after duplicate handling

### Testing Required
- Test duplicate event creation in group chat -4627994150
- Verify "✅ Create Anyway" and "❌ Cancel" buttons work correctly
- Confirm subsequent messages process normally after duplicate interaction

## v0.1.224 - Current Version Testing

### 🟡 **IN PROGRESS BUGS**

#### **BUG-024: LLM Response Structure Error** - 🟡 **IN PROGRESS**
- **Description**: "I'm experiencing technical difficulties" error for simple messages
- **Evidence**: `ERROR:app.agent.nlp_agent:Error extracting intent: 'content'` for messages like "hello", "whats the plan today"
- **Pattern**: Simple messages fail, complex calendar commands work
- **Fix Applied**: Updated ALL LLM response access points (`check_message_relevancy`, `generate_response`, `suggest_calendar_for_event`)
- **Implementation**: Replaced dict access with ModelResponse object handling across all functions
- **Status**: 🟡 **IN PROGRESS** - Comprehensive fix applied (v0.1.224), awaiting user confirmation

#### **BUG-027: Event Name Capitalization Issues** - 🟡 **IN PROGRESS**
- **Description**: Event names not preserving Google Calendar format or auto-capitalizing properly
- **Evidence**: Inconsistent capitalization between Google Calendar and CaliBOT
- **Expected**: Preserve Google Calendar format, auto-capitalize user input appropriately
- **Fix Applied**: Capitalization rules already implemented in LLM prompt (lines 77-80)
- **Implementation**: "test meeting" → "Test Meeting", preserve "test event" if quoted
- **Status**: 🟡 **IN PROGRESS** - Awaiting user confirmation (rules working as designed)

#### **BUG-028: Hyperlink Formatting Still Broken** - 🟡 **IN PROGRESS**
- **Description**: Hyperlinks showing as visible text instead of clickable links
- **Evidence**: `[Test Meeting](https://calendar.google.com/calendar/event?eid=...)` showing as text in duplicate detection
- **Fix Applied**: Updated duplicate detection to use master formatter with hyperlinks
- **Implementation**: Used `MessageFormatter.format_event_with_hyperlink()` for consistent display
- **Status**: 🟡 **IN PROGRESS** - Awaiting user confirmation (fixed in duplicate detection)

---

## Bug Tracking Rules

1. **🚨 ONLY USER CAN MARK BUGS AS FIXED** - Assistant cannot change status to 🟢 FIXED
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
