# CaliBOT Project Rules & Lessons Learned

## � CRITICAL INFORMATION - DO NOT LOSE AGAIN

### YOUR ACTUAL GROUP CHAT ID
**MANDATORY REFERENCE**: Your actual Telegram group where you see messages is:
- **Group ID**: `-4627994150`
- **Context**: This is where you saw the last message at 07:57
- **Usage**: Use this ID for ALL real testing and demos
- **Location**: Found in conversation history and multiple test files

### MULTI-EVENT DEMO RESULTS (LATEST)
**Date**: 2025-08-15
**Success Rate**: 80% (4/5 scenarios)
**Scenarios Tested**:
1. ✅ UPDATE MULTIPLE EVENTS - ONE BY ONE (Core "UPDATE Event 2 of 2" fix)
2. ✅ UPDATE MULTIPLE EVENTS - ALL AT ONCE (Batch processing)
3. ✅ DELETE MULTIPLE EVENTS - ONE BY ONE (Mixed yes/skip responses)
4. ✅ MOVE MULTIPLE EVENTS (Complex date changes)
5. ❌ UPDATE MULTIPLE EVENTS - CANCEL (500 error on cancel_update callback)

**Proven Working**: "UPDATE Event 2 of 2" message, one-by-one queue processing, webhook responses (200 status), button callbacks

## �🚀 Deployment Lessons Learned

### ✅ What Works for Render.com Deployment

#### Git-Based Auto-Deployment
- **Push to main branch** triggers automatic deployment
- **Render monitors GitHub** and rebuilds on new commits
- **Environment variables** set in Render dashboard persist across deployments
- **Docker builds** work reliably when Dockerfile is properly configured

#### Version Management
- **pyproject.toml version field** is the source of truth
- **Automatic health endpoint** at root URL shows current version: `{"version": "X.Y.Z"}`
- **Version bumping** must be done before commit to ensure proper tracking

#### Force Deployment Methods
```bash
# Method 1: Empty commit (most reliable)
git commit --allow-empty -m "Force deployment: trigger restart"
git push origin main

# Method 2: Render dashboard manual deploy button
# Visit dashboard.render.com -> service -> Manual Deploy
```

### ❌ What Doesn't Work / Common Issues

#### API-Based Deployment Control
- **Render API deployment endpoints** are unreliable or limited
- **Direct service restart via API** often fails with permission errors
- **Programmatic deployment triggering** is not well-supported

#### Health Check Endpoints
- **`/health` endpoint** often returns 404 - not consistently available
- **Root URL `/`** is more reliable for version checking
- **Custom health endpoints** may not be accessible depending on routing

#### Deployment Timing
- **Auto-deployment can take 3-5 minutes** even for small changes
- **No reliable completion notification** - must poll manually
- **Build failures are silent** - check Render dashboard for errors

## 📊 Logging Lessons Learned

### ✅ What Works for Log Retrieval

#### Batch Log Fetching
```python
# CORRECT: Fetch recent logs and exit
def get_recent_logs():
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)
    # Fetch logs for time range, return results, exit
```

#### Log Filtering
- **Filter logs by keywords** after fetching to reduce noise
- **Time-based filtering** works better than limit-based
- **Structured log formats** make parsing more reliable

### ❌ What Doesn't Work / Gets Stuck

#### Streaming Log Scripts
```python
# WRONG: This gets stuck indefinitely
while True:
    logs = get_logs()
    time.sleep(3)  # Never exits, hangs terminal
```

#### Large Log Requests
- **Limit > 100** often returns "too large" error
- **No time range** can return massive datasets
- **Real-time streaming** is unreliable and gets stuck

#### Terminal Blocking Operations
- **Long-running scripts** get interrupted in VS Code PowerShell
- **Interactive prompts** fail in automated environments
- **Background streaming** blocks other terminal operations

## 🗂️ File Organization Rules

### ✅ Correct File Locations

#### Project Root (Essential Files Only)
```
/calibot/
├── .gitignore
├── CHANGELOG.md
├── README.md
├── PROJECT_RULES.md        # This file
├── pyproject.toml
├── Dockerfile
├── backend/                # Application code
├── scripts/               # Utility scripts
└── tests/                 # ALL test files
```

#### Scripts Folder
- **Deployment verification**: `verify_deployment.py`
- **Log fetching**: `recent_logs.py` (NOT `live_logs.py`)
- **Version checking**: `quick_version_check.py`
- **Utility scripts**: Database management, file organization

#### Tests Folder
- **ALL test files** regardless of type
- **Demo scripts**: `telegram_demo.py`, `webhook_test.py`
- **Validation scripts**: `test_one_by_one_workflow.py`
- **Results files**: `*_results.json` (excluded from git)

### ❌ Forbidden in Project Root
- **Test files**: `test_*.py`, `*_demo.py`, `*_test.py`
- **Temporary scripts**: `check_deployment_status.py`
- **Batch files**: `DEPLOY_AND_TEST.bat`
- **Status files**: `DEPLOYMENT_STATUS_REPORT.md`
- **Summary files**: Any file ending with `_SUMMARY.md`

## 🔧 Development Workflow Rules

### ✅ Effective Practices

#### Version Management
1. **Update pyproject.toml version** first
2. **Document in CHANGELOG.md** after testing
3. **Commit with version in message**: `v0.1.124: Description`
4. **Push to trigger deployment**
5. **Verify deployment** before testing

#### Testing Workflow
1. **Deploy first**, then test (never test old versions)
2. **Use batch log fetching** to debug issues
3. **Test real scenarios** with actual webhook calls
4. **Document issues** in PROJECT_RULES.md

#### Code Changes
1. **Every change requires CHANGELOG update**
2. **Test in deployed environment** before claiming completion
3. **Version increment required** for every change
4. **No exceptions to documentation rule**

### ❌ Ineffective Practices

#### Testing Old Versions
- **Testing before deployment** gives false results
- **Assuming auto-deployment worked** without verification
- **Running tests on wrong version** wastes time

#### File Management
- **Creating summary files** instead of using CHANGELOG.md
- **Leaving test files in root** makes project messy
- **Not using .gitignore properly** bloats deployment

#### Terminal Usage
- **Using streaming scripts** that get stuck
- **Running long operations** in VS Code terminal
- **Not using batch operations** for multiple commands


## 🤖 Bot-to-Bot Demo Protocol (MANDATORY)

### Purpose
To verify multi-event and queue-based workflows, a true bot-to-bot (B2B) demo is required. This means:
- Using a real test bot (not just webhook simulation)
- Running the demo in the documented test group (`-4627994150`)
- Simulating a real user and a test bot interacting, including button presses and all confirmation flows
- Monitoring logs in real time to verify correct queue and event processing

### Required Setup
- **Test Group ID**: `-4627994150` (see top of this file)
- **User Bot**: CaliBOT (production bot)
- **Test Bot**: A separate Telegram bot with its own token, able to send messages and press buttons in the group
- **Log Monitoring**: Use `python scripts/recent_logs.py` to fetch and analyze logs during the demo

### Step-by-Step Protocol
1. **Preparation**
    - Ensure both bots are in the test group and have permission to send messages and interact with inline keyboards.
    - Deploy the latest version and verify with `python scripts/verify_deployment.py`.
    - Open a terminal to run `python scripts/recent_logs.py` for live log monitoring.

2. **Conversation Flow**
    - The test bot sends commands to create multiple events (e.g., `create TestB2B_001 tomorrow 14:00-15:00`, etc.).
    - The test bot requests a multi-event operation (e.g., `delete all TestB2B events tomorrow`).
    - The test bot (or user) selects the desired mode (e.g., presses "One by One").
    - The test bot simulates button presses for each event ("Yes", "Skip", "Cancel", etc.), verifying that each step advances the queue as expected.
    - The test bot verifies that after each confirmation, the correct next event is shown, and no bulk deletion occurs unless "All" is selected.

3. **Log Monitoring**
    - During the demo, run `python scripts/recent_logs.py` after each critical step (especially after each "Yes" click) to verify:
      - Only one "Processing single event" log per confirmation
      - "DELETE Event X of Y" appears for each event in sequence
      - No premature "Successfully deleted X events!" message
    - If any issues are found (e.g., multiple events processed at once, missing confirmations), document them immediately.

4. **Cleanup**
    - After the demo, the test bot should delete any remaining test events to leave the calendar clean.

5. **Documentation**
    - Update this section with any new lessons learned, issues encountered, or changes to the protocol.
    - All changes must be reflected in both `CHANGELOG.md` and here.

### Success Criteria
- Each "Yes" click processes only the current event
- Buttons disappear after each click
- Next event confirmation appears for remaining events
- No bulk "Successfully deleted X events!" message after individual confirmations
- Proper event-by-event flow is maintained throughout

### Failure Indicators
- First "Yes" click deletes all remaining events
- No second event confirmation shown
- Immediate "Successfully deleted X events!" message
- Buttons remain visible after clicking
- Queue jumps to completion instead of next event

### Lessons Learned (2025-08-15)
- Webhook-only simulation is NOT sufficient for true B2B demo; must use a real test bot
- Log monitoring is essential for verifying queue and event processing
- Unicode in logs can cause encoding errors in PowerShell; use plain text for log analysis
- Always verify the deployed version before testing
- Document all issues and protocol changes here, not in separate summary files


### Render.com Specifics
- **Free tier has limitations** on API access
- **Build logs** only visible in dashboard, not via API
- **Environment variables** persist but service restart may be needed
- **Custom domains** require verification and DNS setup

### VS Code Terminal Limitations
- **PowerShell in VS Code** gets interrupted (^C)
- **Long-running processes** fail or hang
- **Background operations** don't work reliably
- **Interactive scripts** should be avoided

### Python Script Reliability
- **Timeout all network requests** (default 30s too long)
- **Handle HTTP errors gracefully** (404, 429, 500)
- **Exit cleanly** instead of looping indefinitely
- **Use absolute paths** for file operations

## 📋 Project Maintenance Rules

### Regular Cleanup Tasks
1. **Review .gitignore** to exclude generated files
2. **Move misplaced files** to correct folders
3. **Delete unnecessary files** from project root
4. **Update PROJECT_RULES.md** with new lessons learned

### Documentation Updates
1. **CHANGELOG.md** for all code changes
2. **PROJECT_RULES.md** for process improvements
3. **README.md** for user-facing changes
4. **Copilot instructions** for AI development rules

### Version Control Hygiene
1. **Keep commits atomic** and well-described
2. **Use semantic versioning** (X.Y.Z format)
3. **Tag releases** for important milestones
4. **Branch protection** for critical files

## 🚨 Emergency Procedures

### Deployment Issues
1. **Check Render dashboard** for build errors
2. **Force empty commit** to trigger rebuild
3. **Manual deploy button** in dashboard as backup
4. **Rollback via git revert** if needed

### Service Down
1. **Check root URL** for basic health
2. **Review recent commits** for breaking changes
3. **Check environment variables** in Render dashboard
4. **Contact Render support** if platform issue

### Testing Failures
1. **Verify correct version** is deployed first
2. **Check logs** for error details
3. **Test individual components** to isolate issues
4. **Document findings** in PROJECT_RULES.md

This document should be updated whenever new issues are discovered or solutions are found.
