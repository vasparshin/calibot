# CaliBOT Development Rules
### Essential References
- **Backend URL**: `https://calibot-utq6.onrender.com`
- **Version Source**: `pyproject.toml` and `backend/app/__init__.py` (BOTH required)
- **TestBot Token**: `8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA` (@calibot_testbot)

### Key Services
- `GoogleCalendarService`: Calendar API operations, OAuth management
- `TelegramBotService`: Message sending, webhook management
- `EventQueueHandler`: One-by-one event processing (CRITICAL COMPONENT)
- `MultiEventOperationHandler`: Batch operations with confirmations
- `NLPAgent`: Intent extraction using GPT-4.1-mini (NO FALLBACK FUNCTIONALITY)
- `CalendarAgent`: AI-powered calendar selection

### 🚨 CRITICAL: NO FALLBACK FUNCTIONALITY
**MANDATORY RULE**: User messages are ALWAYS processed by the LLM. There is NO fallback functionality, keyword-based parsing, or manual intent extraction. All responses must be formatted by the LLM prompt only. If the LLM fails, the system should return an error rather than implementing fallback logic.

- ❌ **FORBIDDEN**: Keyword-based intent detection
- ❌ **FORBIDDEN**: Manual parsing of user messages
- ❌ **FORBIDDEN**: Fallback to hardcoded responses
- ✅ **REQUIRED**: All processing through LLM with proper prompt engineering
- ✅ **REQUIRED**: LLM handles all edge cases and formatting

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

### Version Management 
1. **Update BOTH `pyproject.toml` AND `backend/app/__init__.py`** with SAME version
2. **Commit with version**: `git commit -m "v0.1.XXX: Description"`
3. **Deploy to Render**: `git push origin main` (auto-deploys)
4. **Verify deployment**: Check logs via Render MCP server

### Before Starting New Feature:
1. **Document Requirements** in Project Docs/
2. **Update version numbers** in both files
3. **Add comprehensive tests** to tests/ folder
4. **Test via B2B protocol** in group chat
5. **Update CHANGELOG.md** with feature details

### Feature Checklist:
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] B2B testing completed
- [ ] Performance impact assessed
- [ ] Error handling implemented

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

### Core Concept
B2B (Bot-to-Bot) testing uses `@calibot_testbot` in group chat `-4627994150` as the frontend interface. Since Telegram bots cannot communicate directly, actual bot responses are sent via webhook while the testbot provides visual demo and validation feedback.

### Complete Testing Workflow
1. **Frontend Demo**: TestBot sends scenario message to group chat (shows what user would type)
2. **Expected Response**: TestBot immediately shows expected bot response for validation
3. **Webhook Simulation**: Send equivalent webhook request to backend
5. **Log Validation**: Use Render MCP server to verify successful webhook processing
6. **Response Validation**: Check actual bot response against expected criteria
7. **TestBot Feedback**: TestBot reports success/failure with specific validation details
8. **Proceed**: Continue to next test step or scenario

### Test File Structure
All test files reside in `tests/` folder

#### Critical: Functionality Test Log
**MANDATORY**: Maintain `tests/functionality_test_log.md` for systematic debugging
- **Tracks all bugs** discovered during testing with root cause analysis
- **Prevents repeating mistakes** by documenting fix attempts and results
- **Provides debugging history** for complex issues
- **Update after every test run** with findings, fixes, and verification results
- **Essential for**: Multi-event processing, button behavior, response validation

#### Critical: B2B Test Message Requirements
**MANDATORY**: Every test case must send TestBot messages for complete B2B validation
- **Expected Response Messages**: TestBot MUST send expected CaliBOT response immediately after user input
- **Test Verification Messages**: TestBot MUST send pass/fail verification immediately after each test
- **Button Press Messages**: TestBot MUST send messages showing backend button interactions
- **Complete Coverage**: ALL test cases must have expected responses and verification messages
- **No Exceptions**: Messages must be sent regardless of webhook success/failure status 

### Critical Validation Points
- ✅ Webhook processed successfully (confirmed via Render MCP logs)
- ✅ Bot response matches expected format and content
- ✅ One-by-one processing shows "UPDATE Event X of Y" progression
- ✅ All inline keyboards removed after interaction
- ✅ No 500 errors or failed operations
- ✅ Response time within acceptable limits

## 🚨 ANTI-STUCK RULES

1. **NO ENDLESS DEBUGGING**: Max 2 debug iterations before fixing root cause
2. **NO DEPLOYMENT WAITING**: Deploy only when you have concrete fix
3. **FIX ACTUAL PROBLEMS**: Analyze code and fix logic, don't add logging
4. **SYSTEMATIC APPROACH**: Identify root cause first, then targeted fix
5. **COMPLETE TASKS**: Finish work, update todos, report results

## 🛠️ LOG MONITORING VIA RENDER MCP

### Primary Log Monitoring
Use Render MCP server tools for all log analysis:
- `mcp_render_list_logs` - View recent logs with filtering
- `mcp_render_get_metrics` - Monitor performance and errors
- `mcp_render_list_deploys` - Check deployment status

### Log Analysis Best Practices
- Filter by resource ID for CaliBOT-specific logs
- Monitor webhook processing and response times
- Check for "UPDATE Event X of Y" in one-by-one processing
- Validate intent extraction and error patterns
- Track deployment success and version updates

## 📁 FILE ORGANIZATION

### Forbidden in Project Root
- Test files (`test_*.py`, `*_demo.py`)
- Summary files (`*_SUMMARY.md`, `STATUS_*.md`)
- Temporary scripts (`check_*.py`, `deploy_*.py`)


**REMEMBER**: This is a production system. Always test thoroughly, update CHANGELOG.md, and maintain high quality standards. Bot reliability and user experience are paramount.
