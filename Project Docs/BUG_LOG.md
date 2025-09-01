# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## v0.1.228 - Conversation State Corruption Fix

**CRITICAL BUG FIX**: Fixed conversation state corruption causing LLM failures after duplicate confirmations.

### Root Cause
- After duplicate confirmation callback processing, conversation state was being corrupted
- The `set_data()` method was adding `None` entries to conversation history when clearing data
- This corrupted the conversation context that LLM uses for processing subsequent messages
- Result: LLM failed with `'content'` error on all messages after duplicate confirmation

### Fixes Applied
1. **Fixed conversation state clearing**: Modified `set_data()` to not add `None` entries when clearing data
2. **Improved confirmation processing**: Only clear pending data AFTER successful event creation
3. **Prevented state corruption**: Conversation state now properly maintains integrity during confirmations

### Technical Details
- **Issue**: `set_data(chat_id, "pending_duplicates", None)` was adding `{"data": None}` entries to conversation
- **Fix**: Only add data entries when `data is not None`, otherwise just remove existing entries
- **Timing**: Clear pending data only after successful event creation, not before
- **Impact**: LLM can now process subsequent messages normally after duplicate confirmations

### Testing Required
- Test duplicate event creation: "add a 'test event' today at 7pm"
- Click "✅ Create Anyway" - should show "✅ Creating duplicates" and proceed
- Send subsequent message - should work normally without "technical difficulties"

## v0.1.227 - Duplicate Callback Routing Fix

**CRITICAL BUG FIX**: Fixed duplicate confirmation callback routing priority.

### Root Cause
- Duplicate confirmation callbacks (`confirm_duplicates`, `cancel_duplicates`) were being routed to the wrong handler
- The callback routing logic checked `cancel_*` pattern before checking for exact `cancel_duplicates` match
- This caused `cancel_duplicates` to be processed as a multi-event callback instead of duplicate confirmation callback
- Result: "I'm experiencing technical difficulties" after clicking duplicate confirmation buttons

### Fixes Applied
1. **Fixed callback routing priority**: Moved duplicate callback check to the top of the routing logic
2. **Exact pattern matching**: Now checks for exact `["confirm_duplicates", "cancel_duplicates"]` before generic `cancel_*` patterns
3. **Proper handler routing**: Duplicate callbacks now go to `handle_duplicate_confirmation_callback` instead of multi-event handler

### Technical Details
- The issue was in the callback routing order in `handle_callback_query()`
- `cancel_duplicates` matched `cancel_*` pattern and was routed to multi-event handler
- Now checks for exact duplicate callback matches first, then falls back to pattern matching
- This ensures duplicate confirmations are processed by the correct handler

### Testing Required
- Test duplicate event creation: "add a 'test event' today at 7pm"
- Click "✅ Create Anyway" - should show "✅ Creating duplicates" and proceed
- Click "❌ Cancel" - should show "❌ Cancelled" and cancel operation
- Subsequent messages should work normally

## v0.1.226 - Critical Duplicate Confirmation Message Fix

---

## Bug Tracking Rules

1. **🚨 ONLY USER CAN MARK BUGS AS FIXED** - Assistant cannot change status to 🟢 FIXED
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
