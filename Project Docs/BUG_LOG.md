# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

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
