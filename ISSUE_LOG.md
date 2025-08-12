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

#### Status: **IN PROGRESS** - Critical positioning fix deployed, enhanced debugging added

**Additional Fix Applied (v0.1.93)**:
4. **Count Extraction Logic Position Fix** ✅
   - **Issue**: Count extraction being overridden by later target extraction logic
   - **Fix**: Moved count and time shift extraction to final processing stage
   - **Enhancement**: Added comprehensive debug logging with fire markers
   - **Result**: Count extraction now happens after all other extractions to prevent override

**Enhanced Debugging Added**:
- 🔥 🔢 Final count extraction debug logs with step-by-step pattern testing
- Pattern testing against user input with match/no-match results
- Enhanced time shift patterns including "late" for "1 hr late" variations
- Final enhanced fallback result logging

**Next Test Expected**:
- Debug logs should now show: "🔥 🔢 FINAL COUNT EXTRACTION: Starting for 'move the last 3 lessons today 1 hr late'"
- Should extract count=3 and time_shift="1 hour"
- Should process exactly 3 events chronologically

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
