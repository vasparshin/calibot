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

### BUG-029 - Technical Difficulties Loop After Duplicate Confirmations
- **Status**: 🟡 **IN PROGRESS**
- **Description**: After duplicate event creation/editing logic is used, subsequent messages get "I'm experiencing technical difficulties. Please try again in a moment." response
- **Pattern**: First message works → duplicate confirmation shown → after confirmation, all subsequent messages fail
- **Root Cause**: Conversation state corruption from multi-line assistant messages containing formatting
- **Fix Applied**: Added message cleaning before adding to conversation state to prevent LLM prompt corruption
- **Testing Required**: Test duplicate event creation followed by normal messages

### BUG-030 - No Small Talk Responses  
- **Status**: 🟡 **IN PROGRESS**
- **Description**: CaliBOT not responding to messages like "hey" or "what's ur name" with proper small talk reply
- **Root Cause**: Relevancy checking not integrated into message processing flow
- **Fix Applied**: Added relevancy checking and small talk response handling before intent extraction
- **Testing Required**: Test messages like "hey", "hello", "what's your name", "how are you"

---

## Bug Tracking Rules

1. **🚨 ONLY USER CAN MARK BUGS AS FIXED** - Assistant cannot change status to 🟢 FIXED
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
6. **Reference bugs by number only - no version history in bug log**
7. **Once bug is resolved, remove from bug log and add details to changelog**