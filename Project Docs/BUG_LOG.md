# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## v0.1.201 - Current Version Testing

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
- **Status**: 🟢 FIXED
- **User Confirmation**: "the summary message disappearing bug seems to have been fixed"

### 🔵 **LOW PRIORITY BUGS**

#### **BUG-003: Response Delay Performance**
- **Description**: 20-30 second delays between user message and bot response
- **Logs Show**: 2-3 seconds processing time
- **Hypothesis**: Telegram API delivery delays not reflected in logs
- **Status**: 🔵 LOW PRIORITY (per user request)

### 🔴 **ACTIVE BUGS**

#### **BUG-007: Calendar Query Only Accessing Primary Calendar**
- **Description**: Query operations only access 'primary' calendar instead of all available calendars in Google account
- **User Report**: "there are multiple calendars attached to the google account calendar and primary is just the name of one of the. we've previously created code to check and edit all available calendars and we currently have working capability to write to any of them. for example a calendar called 'tonya' ofc each calendar typically has a backend id but anyway currently on query we only access the primary calendar"
- **Evidence**: All events show `'calendar_name': 'primary'` instead of actual calendar names like "Tonya"
- **Expected**: Should query all calendars by default unless specifically requested
- **Status**: 🔴 ACTIVE

#### **BUG-008: Processing Message Flow Issues**
- **Description**: "Processing all option" text added to summary message instead of being a separate message
- **User Report**: "the 'processing all option' text thats being added to the summary message should be a new message while its processing and after the 'successfully deleted x events on x' message should replace this 'processing.. message'"
- **Expected**: Separate processing message that gets replaced with success message
- **Actual**: Processing text appended to summary message
- **Affects**: Both delete and update operations
- **Status**: 🟡 IN PROGRESS
- **Current Fix**: v0.1.202 - Send separate processing message, replace with success message

#### **BUG-009: One-by-One Logic Broken**
- **Description**: One-by-one processing shows strange "Action: confirm_0" message instead of proper event confirmation
- **User Report**: "one by one logic is broken, the first event comes up after the one by one button is pressed but after i click yes i get a strange 'Action: confirm_0' message instead of summary of event x being deleted and the next event in queue for deletion to process"
- **Expected**: "DELETE Event X of Y" with proper event details and progression
- **Actual**: Strange "Action: confirm_0" message
- **Root Cause Found**: `queue_confirm_0` callbacks handled by wrong handler showing "Action: confirm_0" instead of proper queue processing
- **Affects**: Both delete and update operations
- **Status**: 🟡 IN PROGRESS
- **Current Fix**: v0.1.202 - Fixed queue callback routing to use proper EventQueueHandler

#### **BUG-010: Update Operations Not Actually Executing**
- **Description**: Update operations show success messages but don't actually modify events in Google Calendar
- **User Report**: "update/edit multiple event - all functionality isn't working properly in the backend, the events aren't ACTUALLY being edited on my google calendar. this is a major bug"
- **Expected**: Events should be modified in Google Calendar
- **Actual**: Success message shown but no actual changes made
- **Status**: 🔴 ACTIVE - MAJOR BUG

#### **BUG-004: No Event Summary Message After Single Event Creation**
- **Description**: Single event creation only shows "event created successfully" message instead of event summary
- **User Report**: "no event summary message after a single event creation (likely also same on multiple) just an 'event created successfully' msg"
- **Expected**: Should show formatted event details like multi-event operations
- **Status**: 🟡 IN PROGRESS
- **Current Fix**: v0.1.200 - Updated CreateOperation to format event summary like other operations

#### **BUG-005: Calendar Query Not Checking All Available Calendars**
- **Description**: When querying today's schedule, service fails to check all available calendars in connected Google account
- **User Report**: "when querying todays schedule (likely any time range) the service fails to check all available calendars within google account that's connected even though there is access"
- **Affects**: All schedule/query operations
- **Status**: 🟡 IN PROGRESS
- **Investigation**: v0.1.200 - Added debug logging to track calendar discovery and search coverage

#### **BUG-006: Event ID Field Mapping Issue**
- **Description**: Event deletion/update failing due to missing event ID parameter
- **User Report**: "issue with eventid - check latest .198 logs from render mcp and fix"
- **Root Cause Found**: Events have `'id'` field but code looks for `'event_id'` field
- **Evidence**: Logs show `{'id': '6199a84ht1r9o26o5kr6u2v3r0'}` but error `"Missing required parameter 'eventId'"`
- **Status**: 🟡 IN PROGRESS
- **Current Fix**: v0.1.199 - Fix field mapping to use `event.get('id')` instead of `event.get('event_id')`

### 🟡 **NEEDS VERIFICATION**

#### **BUG-011: Delete Operations Large Message Issue**
- **Description**: Delete operations don't appear in chat when there are massive amounts of events/text
- **User Report**: "delete operations bug appears to only occur when there is a massive amount of events/text due to telegram msg limit or something. works fine on 10-20 events at a time"
- **Status**: 🔵 LOW PRIORITY
- **User Classification**: "lets mark as low priority"

---

## Bug Tracking Rules

1. **Only mark bugs as FIXED after explicit user confirmation**
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
