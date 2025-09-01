# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## v0.1.197 - Current Version Testing

### 🔴 **ACTIVE BUGS**

#### **BUG-001: Multi-Event Button Functionality Broken**
- **Description**: Pressing any button (All/One by One/Cancel) on multi-event operations has no effect
- **Behavior**: Summary message disappears (shouldn't), no actual operations performed
- **Affects**: Both delete and update multi-event operations
- **User Report**: "pressing any of the buttons has no actual effect, the summary message dissapears (which it shouldnt) and nothing happens, regardless if pressing all or one by one"
- **Status**: 🟡 IN PROGRESS
- **Root Cause Found**: Chat ID type mismatch - queue stored as integer `-4627994150`, callback looks for string `"-4627994150"`
- **Previous Attempts**: v0.1.195 (global queue handler), v0.1.196 (global instances)
- **Current Fix**: v0.1.198 - Force consistent string chat_id in all queue operations

#### **BUG-002: Summary Message Disappearing**
- **Description**: When buttons are pressed, the entire summary message is replaced with "Processing..." instead of just removing buttons
- **Expected**: Summary should remain, only buttons should be removed
- **Actual**: Entire message content replaced
- **Status**: 🟡 IN PROGRESS
- **Current Fix**: v0.1.198 - Preserve original message content, only remove buttons

### 🔵 **LOW PRIORITY BUGS**

#### **BUG-003: Response Delay Performance**
- **Description**: 20-30 second delays between user message and bot response
- **Logs Show**: 2-3 seconds processing time
- **Hypothesis**: Telegram API delivery delays not reflected in logs
- **Status**: 🔵 LOW PRIORITY (per user request)

### 🔴 **ACTIVE BUGS**

#### **BUG-004: No Event Summary Message After Single Event Creation**
- **Description**: Single event creation only shows "event created successfully" message instead of event summary
- **User Report**: "no event summary message after a single event creation (likely also same on multiple) just an 'event created successfully' msg"
- **Expected**: Should show formatted event details like multi-event operations
- **Status**: 🔴 ACTIVE

#### **BUG-005: Calendar Query Not Checking All Available Calendars**
- **Description**: When querying today's schedule, service fails to check all available calendars in connected Google account
- **User Report**: "when querying todays schedule (likely any time range) the service fails to check all available calendars within google account that's connected even though there is access"
- **Affects**: All schedule/query operations
- **Status**: 🔴 ACTIVE

#### **BUG-006: Event ID Field Mapping Issue**
- **Description**: Event deletion/update failing due to missing event ID parameter
- **User Report**: "issue with eventid - check latest .198 logs from render mcp and fix"
- **Root Cause Found**: Events have `'id'` field but code looks for `'event_id'` field
- **Evidence**: Logs show `{'id': '6199a84ht1r9o26o5kr6u2v3r0'}` but error `"Missing required parameter 'eventId'"`
- **Status**: 🟡 IN PROGRESS
- **Current Fix**: v0.1.199 - Fix field mapping to use `event.get('id')` instead of `event.get('event_id')`

### 🟡 **NEEDS VERIFICATION**

#### **BUG-007: Delete Operations Not Appearing in Chat**
- **Description**: Delete operations show in logs but messages don't appear in Telegram
- **Last Status**: Possibly fixed with message length truncation in v0.1.195
- **Status**: 🟡 NEEDS TESTING

---

## Bug Tracking Rules

1. **Only mark bugs as FIXED after explicit user confirmation**
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
