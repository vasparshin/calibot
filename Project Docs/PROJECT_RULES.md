# CaliBOT Development Rules

## 🚨 CRITICAL PROJECT INFO

### Essential References
- **Group Chat ID**: `-4627994150` (NEVER LOSE - used for testing)
- **Backend URL**: `https://calibot-utq6.onrender.com`
- **Version Source**: `pyproject.toml` and `backend/app/__init__.py` (BOTH required)
- **TestBot Token**: `8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA` (@calibot_testbot)

## 🏗️ CORE ARCHITECTURE

### Key Services
- `GoogleCalendarService`: Calendar API operations, OAuth management
- `TelegramBotService`: Message sending, webhook management
- `EventQueueHandler`: One-by-one event processing (CRITICAL COMPONENT)
- `MultiEventOperationHandler`: Batch operations with confirmations
- `NLPAgent`: Intent extraction using GPT-4.1-mini
- `CalendarAgent`: AI-powered calendar selection

### File Structure (MANDATORY)
```
calibot/
├── backend/app/           # All application code
├── Project Docs/          # ALL documentation files
├── tests/                 # ALL test files and demos
├── scripts/               # Utility scripts only
├── pyproject.toml         # Version source of truth
└── requirements.txt       # Dependencies
```

## 🔧 MANDATORY WORKFLOW

### Version Management (CRITICAL)
1. **Update BOTH `pyproject.toml` AND `backend/app/__init__.py`** with SAME version
2. **Commit with version**: `git commit -m "v0.1.XXX: Description"`
3. **Deploy to Render**: `git push origin main` (auto-deploys)
4. **Verify deployment**: Check logs for correct version

### Pre-Testing Protocol
1. **Verify version deployed**: `python scripts/render_api_logs.py`
2. **Check backend health**: Visit backend URL
3. **Use correct group chat**: `-4627994150` for real testing
4. **Run tests**: `python tests/telegram_like_tester.py`

## 🤖 BOT BEHAVIOR RULES (MANDATORY)

### Message Formatting (EXACT FORMAT REQUIRED)
```
• [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
```

### Button Behavior (ABSOLUTE RULE)
- **ALL inline keyboards MUST be temporary** and removed immediately after interaction
- Use `edit_message_text()` with `reply_markup={}` to remove keyboards
- ALWAYS add status text after button removal ("✅ Processing...", "❌ Cancelled")

### Multi-Event Operations
- Show confirmation with "🔄 All", "1️⃣ One by One", "❌ Cancel" buttons
- One-by-one processing: "UPDATE/DELETE Event X of Y" for each confirmation
- NEVER process multiple events on single "Yes" click in one-by-one mode

## 🧪 B2B TESTING PROTOCOL (CRITICAL)

### Essential Setup
- **Test Group**: `-4627994150` (your actual group chat)
- **TestBot**: `@calibot_testbot` with token above
- **Demo Script**: `tests/comprehensive_multi_event_demo.py`
- **Log Monitor**: `python scripts/render_api_logs.py`

### Testing Workflow
1. **Deploy latest version** and verify
2. **Run B2B demo**: TestBot sends messages to group
3. **Monitor logs**: Check for "UPDATE Event 2 of 2" in one-by-one mode
4. **Verify buttons**: All keyboards removed after interaction
5. **Success rate**: 80%+ scenarios must pass

### Critical Test Scenarios
1. Multi-event creation with batch confirmation
2. One-by-one updates (verify "UPDATE Event 2 of 2" appears)
3. One-by-one deletes with mixed yes/skip responses
4. Cancel operations (check for 500 errors)

## 🚨 ANTI-STUCK RULES

1. **NO ENDLESS DEBUGGING**: Max 2 debug iterations before fixing root cause
2. **NO DEPLOYMENT WAITING**: Deploy only when you have concrete fix
3. **FIX ACTUAL PROBLEMS**: Analyze code and fix logic, don't add logging
4. **SYSTEMATIC APPROACH**: Identify root cause first, then targeted fix
5. **COMPLETE TASKS**: Finish work, update todos, report results

## 🛠️ WORKING TOOLS

### Log Analysis (RECOMMENDED)
```bash
# Primary tool - PowerShell compatible, no Unicode issues
python scripts/render_api_logs.py                    # Recent activity
python scripts/render_api_logs.py intent create     # Filter terms
python scripts/render_api_logs.py error             # Errors only
```

### Other Essential Scripts
- `python scripts/verify_deployment.py` - Deployment verification  
- `python scripts/verify_test_group.py` - B2B demo group verification
- `python scripts/pull_deployment_logs.py` - Automated log archiving

## 📁 FILE ORGANIZATION

### Forbidden in Project Root
- Test files (`test_*.py`, `*_demo.py`)
- Summary files (`*_SUMMARY.md`, `STATUS_*.md`)
- Temporary scripts (`check_*.py`, `deploy_*.py`)

### Required Locations
- **ALL tests**: `tests/` folder (no exceptions)
- **ALL docs**: `Project Docs/` folder (except root README.md)
- **Version info**: `pyproject.toml` is source of truth

## 🎯 CURRENT STATUS

### Working Features (v0.1.136+)
- ✅ Event creation (single and batch)
- ✅ One-by-one event queue advancement
- ✅ Multi-event processing with confirmations
- ✅ Calendar selection via AI
- ✅ Button removal after confirmations
- ✅ OAuth 2.0 authentication flow

### Known Issues
- Cancel operation callbacks (some 500 errors)
- Complex time formatting edge cases
- Large event list handling performance

---

**REMEMBER**: This is a production system. Always test thoroughly, update CHANGELOG.md, and maintain high quality standards. Bot reliability and user experience are paramount.
