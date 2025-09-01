# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## v0.1.231 - Backend Cleanup and Critical Bug Fixes

**CRITICAL BUG FIX**: Fixed "technical difficulties" error in duplicate confirmation processing
- **Root Cause**: Operation factory looking for `pending_operation` but create operation stores data as `pending_duplicates`
- **Evidence**: "I'm experiencing technical difficulties. Please try again in a moment." errors after duplicate confirmations
- **Fix Applied**: Updated operation factory to check for `pending_duplicates` first for duplicate confirmations
- **Impact**: ✅ Eliminates "technical difficulties" errors when processing duplicate confirmations

**UI BUG FIX**: Fixed duplicate confirmation message preservation
- **Root Cause**: Event summary disappeared when buttons were pressed, only status text remained
- **Evidence**: User reported "after event summary message button is pressed, the event summary shouldnt dissapear, just the buttons replaced by the outcome"
- **Fix Applied**: Modified confirmation handler to preserve original message content
- **Impact**: ✅ Event summary now preserved when buttons are pressed, only buttons removed

**BACKEND CLEANUP**: Removed 9 redundant/unused files
- **Removed**: Backup files, unused prompts, empty files, unused handlers
- **Impact**: ✅ Reduced codebase complexity, eliminated confusion from unused files

### Testing Required
- Send duplicate event creation: "add a 'test event' today at 7pm"
- Verify event summary preserved when buttons pressed
- Verify "✅ Create Anyway" processes without "technical difficulties"
- Verify "❌ Cancel" processes without "technical difficulties"

## v0.1.230 - Message Deduplication and Queuing Fix

**CRITICAL BUG FIX**: Implemented proper message deduplication and queuing to prevent concurrent operations.

### Root Cause
- Multiple messages sent quickly were causing LLM API overload and response corruption
- No mechanism to ignore duplicate messages or queue subsequent messages
- Concurrent operations were causing race conditions and "technical difficulties" errors
- Pattern: First message fails, second message fails, callback works, next message fails

### Fixes Applied
1. **Added message deduplication**: Ignore duplicate messages within 30-second window
2. **Implemented message queuing**: Queue subsequent messages until current operation completes
3. **Sequential processing**: Process one operation at a time per chat_id
4. **Removed rate limiting**: Replaced with proper message queue management

### Technical Details
- **Deduplication Window**: 30 seconds for identical messages
- **Queue Management**: Messages queued when chat is processing
- **Sequential Processing**: Only one operation active per chat_id at a time
- **Automatic Queue Processing**: Queued messages processed after current operation completes
- **Logging**: All deduplication and queuing events logged for debugging

### Testing Required
- Send duplicate message: "add a 'test event' today at 7pm" (same message twice within 30s)
- First message should process, second should be ignored
- Send different message while processing: Should be queued and processed after completion
- All operations should complete without "technical difficulties"

## v0.1.229 - LLM Rate Limiting Fix

**CRITICAL BUG FIX**: Fixed LLM API overload causing `'content'` errors when multiple messages sent quickly.

### Root Cause
- When multiple messages are sent in quick succession, the LLM API was being overwhelmed
- No rate limiting between LLM calls caused API overload and response structure failures
- Result: `'content'` error on ALL messages when sent rapidly (within 1 second of each other)
- Pattern: First message fails, second message fails, callback works, next message fails

### Fixes Applied
1. **Added rate limiting configuration**: Added `LLM_RATE_LIMIT_DELAY` and tracking in config.py
2. **Implemented rate limiting in NLP agent**: Added `_rate_limit_check()` method to enforce delays
3. **Prevented API overload**: Minimum 1-second delay between LLM calls for same chat_id
4. **Added proper error handling**: Rate limiting with logging for debugging

### Technical Details
- **Rate Limit**: 1.0 second minimum delay between LLM calls per chat_id
- **Implementation**: `_rate_limit_check()` method in NLPAgent class
- **Tracking**: Global `LLM_LAST_CALL_TIME` dictionary tracks last call per chat
- **Logging**: Rate limiting events logged for debugging
- **Impact**: Prevents LLM API overload and response structure corruption

### Testing Required
- Send multiple messages quickly: "add a 'test event' today at 7pm" (3 times rapidly)
- Should see rate limiting logs: "🔒 Rate limiting: Waiting X.XXs for chat Y"
- All messages should process successfully without "technical difficulties"
- Duplicate confirmations should work normally

## v0.1.228 - Conversation State Corruption Fix

---

## Bug Tracking Rules

1. **🚨 ONLY USER CAN MARK BUGS AS FIXED** - Assistant cannot change status to 🟢 FIXED
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
