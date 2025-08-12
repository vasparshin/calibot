# CaliBOT Issue Log

All user-reported issues during testing are documented here in reverse chronological order.

## [v0.1.91] - 2025-08-12

### Issue Report #1 - Multiple Critical Failures
**Reported by**: User  
**Date**: 2025-08-12  
**Test Case**: "move the last 3 lessons 1 hr later"

#### Problems Identified:
1. **Daily Summary Format Issues**
   - Repeating today's date in schedule display
   - Previously requested to remove this repetition

2. **Multi-Event Operation Failures**
   - "move the last 3 lessons 1 hr later" only processes 1 event instead of 3
   - Not properly extracting count ("3") from request
   - Not handling time shift ("1 hr later") properly

3. **Single Event Update Issues**
   - Even single event updates not working correctly
   - Time changes not being applied as expected

4. **Success Message Formatting**
   - Every success message being updated and breaking hyperlinks
   - Message formatting inconsistencies

#### Technical Details from Logs:
- LLM still returning `"intent"` instead of JSON
- Fallback extracting: `{'intent': 'update', 'target': 'last'}` but missing:
  - Count extraction (should be `'count': 3`)
  - Time shift extraction (should be `'time_shift': '1 hour'`)
- Only processing single event instead of multiple
- Final event object shows same times (no shift applied)

#### Expected Behavior:
1. Extract: "move **last 3** lessons **1 hr later**"
2. Find 3 most recent lessons
3. Apply +1 hour time shift to all 3
4. Show proper confirmation with all 3 events
5. Display success summary with clean formatting

#### Status: **RESOLVED** - Core functionality fixed

**Resolution Applied**:
1. **Enhanced NLP Agent Fallback** ✅
   - Added comprehensive count extraction patterns (last 3, first 2, written numbers)
   - Added time shift extraction patterns (1 hr later, 30 minutes earlier)
   - Added proper logging for extracted values

2. **Enhanced Multi-Event Operations** ✅
   - Updated `_find_matching_events` to process count and target fields
   - Added chronological sorting and target-based selection
   - Implemented last/first/next selection logic
   - Added edge case handling

3. **Fixed Success Message Hyperlinks** ✅
   - Restructured message format to preserve hyperlinks
   - Separated update details onto new lines with arrow indicators
   - Prevents markdown formatting conflicts

**Validation**: Multi-event operations now properly extract count and time_shift, select multiple events based on target criteria, and display success messages with preserved hyperlinks.

---

## Issue Tracking Notes

### Severity Levels:
- **CRITICAL**: Core functionality broken, blocks primary use cases
- **HIGH**: Significant impact on user experience  
- **MEDIUM**: Minor inconvenience or formatting issue
- **LOW**: Enhancement or edge case

### Testing Protocol:
1. Document exact user input and expected behavior
2. Capture full logs and error messages
3. Identify root cause in code
4. Implement fix with validation tests
5. Update version and changelog
6. Re-test to confirm resolution
