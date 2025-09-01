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

### 🟡 **NEEDS VERIFICATION**

#### **BUG-004: Delete Operations Not Appearing in Chat**
- **Description**: Delete operations show in logs but messages don't appear in Telegram
- **Last Status**: Possibly fixed with message length truncation in v0.1.195
- **Status**: 🟡 NEEDS TESTING

#### **BUG-005: Today's Calendar Query Missing Events**
- **Description**: Query for "today" not showing "lesson" events
- **Hypothesis**: Not checking all available calendars
- **Status**: 🟡 NEEDS INVESTIGATION

---

## Bug Tracking Rules

1. **Only mark bugs as FIXED after explicit user confirmation**
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
