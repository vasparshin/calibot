# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## ACTIVE BUGS

### BUG-039 - Duplicate Event Summary Still Missing Hyperlinks and Wrong Calendar Names
- **Status**: 🔴 **ACTIVE**
- **Description**: Despite BUG-035 fix, duplicate confirmation messages still show events without hyperlinks and "Default" instead of actual calendar names
- **User Report**: "in this sumamry message the hyperlinks are missing and calendar name is wrong - you need ot make sure that all summary messages follow the SAME logic/function for formatting"
- **Evidence**: Message shows "• Test Event on Wednesday, September 03, 2025 at 03:00 (Default)" instead of proper hyperlinks and calendar names
- **Root Cause**: The fix in v0.1.244 may not be fully working or there's a different code path being used
- **Fix Required**: Ensure ALL summary messages use same MessageFormatter logic regardless of operation type
- **Testing Required**: Create duplicate events and verify summary has hyperlinks and correct calendar names

### BUG-040 - Technical Difficulties After Duplicate Cancellation
- **Status**: 🔴 **ACTIVE**
- **Description**: After cancelling duplicate confirmation, subsequent messages trigger "technical difficulties" response
- **User Report**: "after i pressed cancel and so the conversation state in the backneed should reset. after i send another message to test duplication logic and got the technical difficulties reponse"
- **Root Cause**: Conversation state or duplicate handling not properly reset after cancellation, causing LLM processing errors
- **Fix Required**: Ensure proper cleanup of duplicate state after cancellation
- **Testing Required**: Cancel duplicate confirmation, then send new message and verify normal processing

### BUG-041 - One by One Duplicate Creation Not Working
- **Status**: 🔴 **ACTIVE**
- **Description**: "One by One" button for duplicate creation behaves same as "All" button instead of individual confirmations
- **User Report**: "I tested the logic of 'one by one' duplicate event creation hwoever it did not work, the functionality is the same as pressing 'all button'"
- **Expected Behavior**: Should show individual confirmation for each duplicate like edit/delete one-by-one processing
- **Root Cause**: One-by-one duplicate creation logic not implemented or incorrectly routed to "all" processing
- **Fix Required**: Implement proper one-by-one duplicate creation flow matching edit/delete patterns
- **Testing Required**: Create multiple duplicates, press "One by One", verify individual confirmations

### BUG-035 - Duplicate Event Summary Missing Hyperlinks and Incorrect Calendar Names
- **Status**: 🔴 **ACTIVE**
- **Description**: Duplicate event confirmation message shows events without hyperlinks and incorrect calendar names (should be same formatting as edit/delete summaries)
- **User Report**: "its missing the hyperlink to event and the name of the calendar isnt correct. so it seems its using some different fomatting logic to other summary messages"
- **Root Cause**: Duplicate confirmation using different formatting logic than multi-event summaries
- **Fix Required**: Use same MessageFormatter as used for edit/delete operations
- **Testing Required**: Create duplicate event and verify summary has hyperlinks and correct calendar names

### BUG-036 - Duplicate Confirmation Button Behavior Inconsistent with Edit/Delete Operations
- **Status**: 🔴 **ACTIVE**
- **Description**: Duplicate confirmation buttons change message text instead of showing processing message then success
- **User Report**: "once i press one of the buttons the message text changes, but this isnt in line with the logic for editing/deleting events"
- **Expected Behavior**: Buttons → "Processing..." → "Successfully created" with event details
- **Root Cause**: Different button handling logic for duplicate confirmations
- **Fix Required**: Use same processing flow as edit/delete operations
- **Testing Required**: Press duplicate confirmation buttons and verify processing flow

### BUG-037 - Multiple Duplicate Events Using Wrong Button Options
- **Status**: 🔴 **ACTIVE**
- **Description**: Multiple duplicate events show "Create Anyway"/"Cancel" instead of "All"/"One by One"/"Cancel" buttons
- **User Report**: "when dealing with multiple dplicate events the button options should be the same as dealing with multiple events editing or deleting"
- **Expected Behavior**: Same button options as multi-event edit/delete operations
- **Root Cause**: Duplicate confirmation logic doesn't handle multiple events properly
- **Fix Required**: Implement multi-event duplicate handling with proper button options
- **Testing Required**: Create multiple duplicate events and verify button options

### BUG-038 - Stale Buttons Not Removed When User Sends New Message
- **Status**: 🔴 **ACTIVE**
- **Description**: Previous operation buttons remain active when user sends new message instead of pressing buttons
- **User Report**: "if the user decides not to press either of the buttons on ANY message and instead type something... the buttons for the previous operation should disappear"
- **Root Cause**: No mechanism to clean up stale inline keyboards when new messages are processed
- **Fix Required**: Remove all active inline keyboards when new user message is processed
- **Testing Required**: Leave buttons unpressed, send new message, verify old buttons disappear

### BUG-031 - Google Workspace Link Preview Inconsistency in One-by-One Process
- **Status**: 🟡 **IN PROGRESS**
- **Description**: Google Workspace link preview appears for 2nd+ events in one-by-one process but not first event
- **Pattern**: First event shows clean hyperlink → subsequent events show "Google Workspace (link) Google Calendar - Easier Time Management..." preview
- **Root Cause**: Telegram link preview behavior inconsistency, likely a client-side setting issue
- **Fix Required**: Investigation of link preview suppression or consistent behavior
- **Testing Required**: One-by-one event processing with multiple events

### BUG-032 - "Current Event:" Prefix Still Appearing
- **Status**: 🟡 **IN PROGRESS**
- **Description**: One-by-one messages still show "Current Event: [Event]..." instead of clean event display
- **User Request**: Remove "Current Event: " prefix, show only event details like "UPDATE Event 3 of 3: [Event details]"
- **Root Cause**: `_format_event_summary` method in event_queue_handler.py still includes this prefix
- **Fix Required**: Remove prefix from one-by-one event formatting
- **Testing Required**: One-by-one event processing

### BUG-033 - One-by-One Final Summary Still Shows "All Events Processed!"
- **Status**: 🟡 **IN PROGRESS**
- **Description**: After one-by-one completion, shows "All events processed!" instead of detailed summary with NEW updated details
- **Pattern**: MessageFormatter available but fallback still triggered
- **Root Cause**: Logic issue in one-by-one completion even after v0.1.238 fixes
- **Fix Required**: Debug why MessageFormatter summary generation fails
- **Testing Required**: Complete one-by-one process and check final message

### BUG-034 - Summary Messages Show Original Details Instead of NEW Updated Details
- **Status**: 🟡 **IN PROGRESS**
- **Description**: Both "All" button and one-by-one summaries show original event details instead of updated details
- **Evidence**: Events updated to Sept 10 but summary shows Sept 03 dates
- **Root Cause**: Summary formatter uses original event structure instead of updated event data from calendar response
- **Fix Required**: Use updated event data from calendar service response for summaries
- **Testing Required**: Multi-event updates with date changes, verify summary shows new dates

---

## Bug Tracking Rules

1. **🚨 ONLY USER CAN MARK BUGS AS FIXED** - Assistant cannot change status to 🟢 FIXED
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
6. **Reference bugs by number only - no version history in bug log**
7. **Once bug is resolved, remove from bug log and add details to changelog**