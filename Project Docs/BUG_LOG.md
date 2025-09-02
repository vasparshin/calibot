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