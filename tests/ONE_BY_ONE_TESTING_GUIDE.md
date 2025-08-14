# ONE-BY-ONE WORKFLOW TESTING PROCEDURE
**Manual Testing Guide for Edit/Create/Delete Events**

## 🚨 BEFORE TESTING - MANDATORY STEPS

### Step 1: Verify Deployment
```bash
# Check backend health manually:
# Visit: https://calibot-utq6.onrender.com/health
# Expected: {"status": "healthy", "version": "0.1.123", ...}

# Or run verification script:
python scripts/verify_deployment.py
```

### Step 2: Ensure Latest Version
- Local version in pyproject.toml: **0.1.123**
- Deployed version from /health endpoint: **Should match 0.1.123**
- If mismatch: Use force deployment in verification script

---

## 🧪 TEST SCENARIOS

### TEST 1: EDIT Events One-by-One ⭐ **CRITICAL**
**Scenario**: "move the last 2 lessons today to tomorrow 5 and 6 pm"

**Expected Flow**:
1. **Initial Response**: "Found 2 events to update (move to 2025-08-14, specific times):"
   - Event 1: lesson on 2025-08-13 at 21:00 (Tonya)
   - Event 2: lesson on 2025-08-13 at 22:00 (Tonya)
   - Buttons: [All] [One by One] [Cancel]

2. **Click "One by One"**: Should show:
   - "1️⃣ **One by One Selected** - Processing events individually..."
   - Then immediately show individual event confirmation

3. **Individual Event 1**: Should show:
   ```
   UPDATE Event 1 of 2:
   
   Current Event: lesson
   Current Date: Tuesday, August 13, 2025
   Current Time: 09:00 PM - 10:00 PM
   Calendar: Tonya
   
   📋 Proposed Changes:
   📅 Move to: 2025-08-14
   🕐 New time: 17:00 - 18:00
   ```
   - Buttons: [Yes] [Skip] [Stop All]

4. **Click "Yes"**: Should show:
   - Event 1 updated successfully
   - Then show Event 2 confirmation

5. **Individual Event 2**: Should show:
   ```
   UPDATE Event 2 of 2:
   
   Current Event: lesson
   Current Date: Tuesday, August 13, 2025  
   Current Time: 10:00 PM - 11:00 PM
   Calendar: Tonya
   
   📋 Proposed Changes:
   📅 Move to: 2025-08-14
   🕐 New time: 18:00 - 19:00
   ```
   - Buttons: [Yes] [Skip] [Stop All]

6. **Click "Yes"**: Should show:
   - Event 2 updated successfully
   - "All events processed!"

**❌ FAILURE INDICATORS**:
- "No pending operation found" error
- Showing batch options again instead of individual event
- Missing proposed changes details
- Wrong operation type (delete instead of update)

---

### TEST 2: DELETE Events One-by-One
**Scenario**: "delete my tennis lessons tomorrow"

**Expected Flow**:
1. **Initial Response**: "Found X events to delete:"
   - List of tennis lessons
   - Buttons: [All] [One by One] [Cancel]

2. **Click "One by One"**: Should show individual delete confirmation:
   ```
   DELETE Event 1 of X:
   
   Event: Tennis Lesson
   Date: Wednesday, August 14, 2025
   Time: XX:XX AM/PM
   Calendar: [Calendar Name]
   ```
   - Buttons: [Yes] [Skip] [Stop All]

3. **Continue Process**: Each event confirmed individually

---

### TEST 3: CREATE Events (Batch Processing)
**Scenario**: "create lessons tomorrow at 3pm and 4pm"

**Expected Flow**:
1. **Initial Response**: May show batch creation options or individual confirmations
2. **Process**: Should handle multiple event creation smoothly
3. **Completion**: All events created successfully

---

## 🔍 VALIDATION CHECKLIST

### ✅ Critical Success Criteria:
- [ ] Multi-event requests show proper confirmation options
- [ ] "One by One" selection shows individual event details immediately
- [ ] Individual confirmations show complete proposed changes
- [ ] Each event shows current state vs. proposed changes
- [ ] No "operation not found" errors occur
- [ ] Workflow completes successfully for all events
- [ ] Proper operation type maintained (update vs delete)

### ❌ Critical Failure Indicators:
- [ ] "One by One" shows batch options again
- [ ] "No pending operation found" error
- [ ] Missing change details in confirmations
- [ ] Wrong operation type (delete when should be update)
- [ ] Workflow gets stuck or fails to progress

---

## 🚀 AUTOMATED TESTING (When Terminal Works)

```bash
# Comprehensive test suite
cd tests
python comprehensive_one_by_one_test.py

# Specific one-by-one tests
python test_one_by_one_workflow.py

# General conversation tests
python real_webhook_conversation.py
```

---

## 🔧 TROUBLESHOOTING

### If Tests Fail:
1. **Check deployment version** - ensure latest code is deployed
2. **Review backend logs** - use `python scripts/simple_logs.py`
3. **Verify webhook connectivity** - test basic health endpoint
4. **Check pending operations** - may need to clear cached operations

### Common Issues:
- **Version mismatch**: Use `python scripts/verify_deployment.py` to force restart
- **Stale operations**: Restart backend to clear pending operation cache
- **Network issues**: Verify https://calibot-utq6.onrender.com/health is accessible

---

## 📊 SUCCESS METRICS

- **≥90%**: Excellent - one-by-one workflow fully functional
- **70-89%**: Good - minor issues, ready for production with monitoring
- **<70%**: Needs attention - significant workflow issues detected

**Current Focus**: The "move the last 2 lessons today to tomorrow 5 and 6 pm" scenario should work flawlessly with proper time assignments (5 PM and 6 PM) for each event.
