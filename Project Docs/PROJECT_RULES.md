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

#### Version Management (CRITICAL - FOLLOW EXACTLY)
- **BOTH pyproject.toml AND backend/app/__init__.py** must have SAME version number
- **Automatic health endpoint** at root URL shows current version: `{"version": "X.Y.Z"}`
- **Version bumping** must update BOTH files before commit to ensure proper tracking

```bash
# MANDATORY VERSION UPDATE STEPS:
# 1. Update pyproject.toml: version = "0.1.XXX"
# 2. Update backend/app/__init__.py: __version__ = "0.1.XXX"  
# 3. Commit with version: git commit -m "v0.1.XXX: Description"
# 4. Verify deployment shows correct version at backend URL
# 5. If Render logs show wrong version = deployment failed, check both files
```

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

## 📊 Logging & Debugging (MANDATORY PROTOCOLS)

### ✅ WORKING Log Access Methods

#### Primary: Direct Render API Access (RECOMMENDED)
```bash
# STEP 1: Set environment variable  
$env:RENDER_API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

# STEP 2: Use PowerShell-compatible log analyzer (NO EMOJIS)
python scripts/render_api_logs.py                    # Show recent CaliBOT activity
python scripts/render_api_logs.py intent create     # Filter for specific terms
python scripts/render_api_logs.py error             # Show only errors

# This script provides:
# - Real-time intent extraction analysis
# - 'start_time' error detection  
# - Create/update intent verification
# - PowerShell Unicode compatibility
```

#### API Documentation Reference
- **Render API Logs Endpoint**: https://api-docs.render.com/openapi/6140fb3daeae351056086186
- **Service ID**: `srv-d1vqbkp5pdvs73echbeg`
- **Owner ID**: `tea-kks41ij4d82bpujdqv0g`

### ❌ BROKEN/PROBLEMATIC Log Methods

#### Unicode Issues in PowerShell
```bash
# BROKEN: These fail with UnicodeEncodeError in PowerShell
python scripts/recent_logs.py | findstr /i "intent"
python scripts/quick_logs.py | head -20

# CAUSE: Emoji characters (🔍, 📊, etc.) can't encode in Windows cp1252
# SOLUTION: Use scripts/render_api_logs.py (no emojis, PowerShell compatible)
```

#### Unreliable Health Checks
```bash
# BROKEN: Returns 404 errors inconsistently
python scripts/quick_version_check.py

# CAUSE: Health endpoint may not exist or have different path
# SOLUTION: Check logs directly for version confirmation
```

### 🔧 DEBUGGING WORKFLOW (LESSONS LEARNED)

#### Step 1: Version Verification
```bash
# 1. Check deployed version in logs (NOT health endpoint)
python scripts/render_api_logs.py | findstr "starting up\|Version:"

# 2. Verify both version files are synchronized
Get-Content pyproject.toml | Select-String "version"
Get-Content backend/app/__init__.py | Select-String "__version__"
```

#### Step 2: Real-Time Issue Analysis  
```bash
# 1. Monitor for specific issues
python scripts/render_api_logs.py error start_time    # Check for LLM failures
python scripts/render_api_logs.py intent create       # Verify intent extraction
python scripts/render_api_logs.py webhook             # Monitor user interactions

# 2. Test bot and immediately check logs
# Send message to bot in group -4627994150
# Then: python scripts/render_api_logs.py
```

#### Step 3: Root Cause Investigation
1. **Always check actual conversation logs** from Render API
2. **Look for patterns** in error messages (e.g., consistent "start_time" failures)
3. **Verify fixes in real-time** by testing bot and checking logs immediately
4. **Don't rely on assumptions** - actual user message processing tells the truth

### 📈 DEVELOPMENT INSIGHTS (v0.1.153 Lessons)

#### ✅ What WORKS for Development & Debugging

1. **Direct Render API Access** 
   - `scripts/render_api_logs.py` provides reliable, real-time log analysis
   - PowerShell compatible (no Unicode issues)
   - Structured filtering and analysis capabilities

2. **Version Synchronization Protocol**
   - ALWAYS update both `pyproject.toml` AND `backend/app/__init__.py`
   - Verify deployment via logs, not health endpoints
   - Use consistent `vX.Y.Z: Description` commit messages

3. **LLM Debugging Strategy**
   - Enhanced fallback logic preserves user intent when LLM fails
   - Detailed logging shows exact LLM responses and parsing failures
   - Robust pattern matching for intent extraction

4. **Real-Time Testing Workflow**
   - Deploy → Check logs for version → Test bot → Check logs immediately
   - Look for specific error patterns (e.g., "start_time" errors)
   - Verify intent extraction actually works vs assumed fixes

#### ❌ What DOESN'T WORK

1. **Emoji-Heavy Scripts in PowerShell**
   - Unicode encoding issues with Windows cp1252
   - `recent_logs.py` and `quick_logs.py` fail with UnicodeEncodeError

2. **Health Endpoint Reliance**
   - `quick_version_check.py` returns inconsistent 404 errors
   - Better to check deployment status via logs directly

3. **Assumption-Based Debugging**
   - "Fixes should work" ≠ fixes actually working
   - Must verify every change with actual bot testing + log analysis

4. **Terminal Commands That Block**
   - `curl -s https://calibot-utq6.onrender.com/` gets stuck in pager
   - `git log --oneline` enters pager mode
   - Use `--no-pager` flags or PowerShell-specific alternatives

#### 🎯 FUTURE DEVELOPMENT RECOMMENDATIONS

1. **Always Use `scripts/render_api_logs.py`** for debugging
2. **Test every fix immediately** with real bot interactions
3. **Check logs before and after** any code changes
4. **Maintain comprehensive changelog** with technical details
5. **Document both working AND broken methods** to save time

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

### 🚨 CRITICAL: AI Assistant Navigation Rules (PREVENT GETTING STUCK)
**LESSON LEARNED (2025-08-15)**: AI assistants can get confused by directory structure and use wrong paths.

#### Working Directory Rules (MANDATORY)
1. **Terminal starts in**: `G:\My Drive\Work\calibot` (parent directory)
2. **Project operations in**: `G:\My Drive\Work\calibot\calibot` (subdirectory)
3. **ALWAYS navigate first**: Use `cd calibot` before ANY project operations
4. **PowerShell syntax**: Use `;` not `&&` for command chaining
5. **Verify location**: Run `dir` after navigation to confirm `pyproject.toml` is visible

#### Prevention Commands
```powershell
# CORRECT WORKFLOW:
cd calibot                           # Navigate to project directory
dir                                  # Verify: should see pyproject.toml, backend/, tests/
python scripts/quick_version_check.py    # Now this will work

# WRONG: Operations from parent directory will fail
python scripts/quick_version_check.py    # ❌ "Could not find pyproject.toml"
```

#### File Path Rules (CRITICAL)
- **Relative paths**: Always from project root (`calibot/` subdirectory)
- **Examples**:
  - ✅ `backend/app/services/event_queue_handler.py`
  - ✅ `Project Docs/PROJECT_RULES.md`
  - ❌ `calibot/backend/app/services/event_queue_handler.py` (from parent dir)

#### Emergency Recovery Protocol
If confused about location:
1. Run `dir` or `pwd` to see current path
2. Look for `pyproject.toml` file
3. If not found, run `cd calibot`
4. Verify with `dir` again before continuing

### 🚨 CRITICAL: File Corruption Prevention
**LESSON LEARNED (2025-08-15)**: EventQueueHandler was corrupted with misplaced code at file start.

#### File Integrity Rules
1. **Always review file headers** after editing
2. **Check for misplaced code** at beginning of files
3. **Verify imports and class definitions** are intact
4. **Test deployment after any service file changes**

#### Early Detection Signs
- Import errors in logs
- 404 errors from backend health checks
- "File not found" or "Module not found" errors
- Unexpected syntax errors in working code

### Regular Cleanup Tasks
1. **Review .gitignore** to exclude generated files
2. **Move misplaced files** to correct folders
3. **Delete unnecessary files** from project root
4. **Update PROJECT_RULES.md** with new lessons learned
5. **Pull deployment logs** after every deployment using `scripts/pull_deployment_logs.py`

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

## 📁 LOGS AUTOMATION (NEW)

### Automatic Log Collection
**PROBLEM SOLVED**: Logs are hard to reach and analyze after deployment issues.

#### Solution: `scripts/pull_deployment_logs.py`
```bash
# Pull latest 2 hours of logs and save to logs/ folder
python scripts/pull_deployment_logs.py
```

#### Features:
- Pulls logs from Render API automatically
- Saves both JSON (raw) and TXT (readable) formats
- Timestamped files for easy tracking
- Auto-cleanup of logs older than 7 days
- Creates logs/ directory if missing

#### Integration with Deployment
Run after every deployment to capture deployment logs:
```bash
git push origin main          # Deploy
sleep 180                     # Wait 3 minutes for deployment
python scripts/pull_deployment_logs.py  # Capture logs
```

#### Environment Setup
Set your Render API key:
```bash
export RENDER_API_KEY=your_render_api_key
```

## 🚨 Emergency Procedures

### File Corruption Detection
1. **Check service files** for misplaced code at file start
2. **Verify imports and class definitions** are intact
3. **Look for syntax errors** in working files
4. **Test backend health** immediately after file changes

### Deployment Issues
1. **Check Render dashboard** for build errors
2. **Pull deployment logs** using `scripts/pull_deployment_logs.py`
3. **Force empty commit** to trigger rebuild
4. **Manual deploy button** in dashboard as backup
5. **Rollback via git revert** if needed

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
