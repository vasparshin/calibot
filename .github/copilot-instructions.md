# CaliBOT - AI Calendar Bot Development Guide

## Project Overview

## Code Style Rules

### Backend Files (Strict Professional Style)
- **NO emoticons or emoji in any backend files** (.py files, CHANGELOG.md, configuration files, scripts)
- **Scripts are backend files**: All files in `scripts/` folder are considered backend files and must follow professional style
- Use clear, descriptive text instead of emoticons in log messages and user-facing text
- Examples: 
  - Use `"Event created successfully"` not `"✅ Event created successfully"`
  - Use `"Error: Failed to delete"` not `"❌ Failed to delete"`
  - Use `"Processing user request"` not `"🔄 Processing user request"`
  - Use `"INFO: Preparing to commit"` not `"📤 Preparing to commit"`
- **Exception**: README.md may contain emoticons for user-friendly presentation

### File Creation Rules
- **DO NOT create unnecessary files** unless explicitly requested by user
- **CHANGELOG.md is the ONLY place for version logs** - never create separate summary files like "FIXES_SUMMARY.md"
- **DO NOT create redundant documentation files** like "QUICK_SCRIPTS.md" when comprehensive documentation already exists in proper locations (e.g., scripts/README.md)
- **Ask before creating new files** unless they are essential for the requested functionality
- **Delete any summary files and integrate their content into CHANGELOG.md**

### Frontend/User-Facing Content
- Emoticons are acceptable in README.md, user documentation, and Telegram bot responses to users
- Keep professional in all backend code and system logs

## Changelog Rules

- **Every commit or PR must update `CHANGELOG.md`.**
- **DO NOT create separate fixes summary files** - document all changes directly in CHANGELOG.md
- **CHANGELOG.md is the ONLY place for version history** - never create additional summary files
- **Delete any existing summary files** and integrate their content into CHANGELOG.md
- Use reverse chronological order (most recent at top).
- Summarize the change, affected files, and motivation/problem solved.
- Reference any related summary or design doc if relevant.
- If a change is a bugfix, describe the bug and how it was fixed.
- If a change is a refactor, describe the before/after and why.
- If a change is a new feature, describe the user impact and integration points.
- Keep entries concise but specific.

### Changelog Categories
- **Added**: New features
- **Enhanced**: Improvements to existing functionality  
- **Fixed**: Bug fixes
- **Security**: Security-related changes
- **Technical Details**: Implementation specifics for developers

### Version Numbering
- **Major (X.0.0)**: Breaking changes or major feature releases
- **Minor (X.Y.0)**: New features, backward compatible
- **Patch (X.Y.Z)**: Bug fixes, backward compatible

### Version Control Workflow
**Critical: Version numbers must be synchronized across all files**

#### Git Development Workflow
**Every development session must end with proper git commits:**

1. **Stage Changes**: `git add .` (after validating with tests)
2. **Commit with Clear Message**: Use conventional commit format
   - `feat: description` - New features
   - `fix: description` - Bug fixes  
   - `docs: description` - Documentation changes
   - `refactor: description` - Code refactoring
   - `test: description` - Test additions/updates
   - `chore: description` - Maintenance tasks
3. **Push to Remote**: `git push origin main`
4. **Update CHANGELOG.md**: Every commit must update changelog

#### Files Requiring Version Updates:
1. **`pyproject.toml`** - Primary version source (line 3: `version = "X.Y.Z"`)
2. **`CHANGELOG.md`** - Version history with release dates
3. **`backend/app/__init__.py`** - Package version variable: `__version__ = "X.Y.Z"`

#### Release Process:
1. **Update pyproject.toml version** (this is the source of truth)
2. **Update CHANGELOG.md**: Move [Unreleased] content to new [X.Y.Z] section with date
3. **Add __version__ variable** to `backend/app/__init__.py` 
4. **Commit with message**: `chore: bump version to X.Y.Z`
5. **Tag the release**: `git tag vX.Y.Z`
6. **Push everything**: `git push origin main --tags`

#### Version Synchronization Rule:
- **ALL version numbers must match across pyproject.toml, CHANGELOG.md, and __init__.py**
- **pyproject.toml is the authoritative source** - other files follow this version
- **Never increment versions in individual files** - always update all three together

#### Current Version Status:
- pyproject.toml: 0.1.0 (needs to be updated to match changelog)
- CHANGELOG.md: Shows 1.2.0 development (needs release date when finalized)

### Required Information
Each entry should include:
- **What changed**: Clear description of the change
- **Why it changed**: Business or technical reason
- **Impact**: How it affects users or developers
- **Files affected**: Key files modified (for technical changes)

## File Organization Rules

### Test Files
- **ALL test files must be in the `tests/` folder** - NO test files in project root or backend folder
- Test files should follow naming convention: `test_*.py`
- Demo/example files (like `queue_demo.py`) are acceptable in tests folder to demonstrate functionality
- Use `scripts/organize_files.sh` to automatically move misplaced test/demo files

### Scripts and Tools
- **ALL utility scripts must be in the `scripts/` folder**
- Examples: `organize_files.sh`, `version_check.py`, deployment scripts
- Scripts should be executable and well-documented
- Include brief description of script purpose in filename or header

### Docker Build Optimization
- **tests/ folder must be excluded from Docker builds** to reduce image size and deployment time
- Development files, demos, and documentation should not be included in production images
- Only essential application code should be copied to Docker containers

## Performance Considerations

CaliBOT is an intelligent Telegram bot that manages Google Calendar through natural language. Built with FastAPI, it uses GPT-4.1-mini for intent extraction and conversation management, implementing a sophisticated multi-agent architecture.

## Critical Architecture Patterns

### 1. Multi-Agent Intent Processing Pipeline
The core workflow follows this pattern: `Telegram → NLP Agent → Calendar Agent → Services → Response`

**Key Components:**
- **NLP Agent** (`app/agent/nlp_agent.py`): Extracts structured intent from conversational input
- **Calendar Agent** (`app/agent/calendar_agent.py`): Handles intelligent calendar selection using AI + rule-based fallbacks
- **Routes** (`app/api/routes.py`): Orchestrates the complete workflow with multi-event operation support

**Critical Pattern:** Always check relevancy before intent extraction to separate calendar tasks from small talk.

### 2. Prompt Engineering System
All LLM interactions use structured prompts in `app/prompts/`:
- `intent_extraction_prompt.py`: Core intent extraction with JSON-formatted examples
- `agent_system_prompt.py`: Conversation management 
- `relevancy_classifier_prompt.py`: Calendar vs small talk classification

**Convention:** Prompts include explicit warnings (`🚨`) and multiple examples for edge cases. When adding new intents, update both the prompt examples AND the route handlers.

### 3. Multi-Event Operations
Recent major feature supporting batch operations (delete/update multiple events):
- `MultiEventOperationHandler` (`app/services/multi_event_operations.py`): Queue-based confirmation workflow
- **Pattern:** Store pending operations by chat_id, require explicit user confirmation
- **Integration:** Routes check for pending operations before processing new intents

### 4. Calendar Intelligence
Automatic calendar selection using dual approach:
- **AI-first:** LLM analyzes event content against available calendars
- **Rule-based fallback:** Keyword matching when AI fails
- **Cache system:** Calendar metadata with themes extracted from names

## Development Workflows

### Running the Application
```bash
# From project root
cd backend
python -m app.main

# For webhook mode (production):
# 1. Set BACKEND_URL in environment
# 2. Use ngrok: ngrok http 8060
# 3. Update webhook URL in main.py
```


### Testing Strategy
**Critical:** Always run the comprehensive test suite before committing changes:
```bash
cd /workspaces/calibot
python tests/test_all_fixes.py  # Runs complete validation suite
```

**Test Categories:**
- `tests/test_production_scenario.py`: Real user scenarios that previously failed
- `tests/test_context_and_calendar_selection.py`: Conversation memory and calendar extraction
- `tests/test_multi_event_*`: Batch operation workflows
- `tests/test_comprehensive_validation.py`: End-to-end validation

**Pattern:** Each test validates specific components AND their integration. Test files include detailed validation with success/failure reporting.
## Changelog Rules

- **Every commit or PR must update `CHANGELOG.md`.**
- Use reverse chronological order (most recent at top).
- Summarize the change, affected files, and motivation/problem solved.
- Reference any related summary or design doc if relevant.
- If a change is a bugfix, describe the bug and how it was fixed.
- If a change is a refactor, describe the before/after and why.
- If a change is a new feature, describe the user impact and integration points.
- Keep entries concise but specific.
- If merging a summary file, include its highlights and then delete/rename the summary file.

## Project-Specific Conventions

### 1. Intent Extraction Format
LLM responses must be valid JSON. Multi-event requests return multiple JSON objects (one per line):
```json
{"intent": "create", "event_name": "lesson", "start_time": "08:00", "end_time": "09:00"}
{"intent": "create", "event_name": "lesson", "start_time": "10:00", "end_time": "11:00"}
```

**Critical:** NLP agent has custom parsing to handle both single JSON and multiple JSON objects.

### 2. Conversation State Management
- **Service:** `ConversationState` (`app/services/conversation.py`) maintains chat history
- **Pattern:** Always add both user and assistant messages to maintain context
- **Formatting:** Use `format_conversation_history()` for LLM consumption

### 3. Error Handling Philosophy
- **Graceful degradation:** AI failures fall back to rule-based systems
- **User-friendly:** Always provide actionable error messages
- **Logging:** Extensive logging at INFO level for debugging production issues

### 4. Configuration Management
- **File:** `app/config.py` - centralizes all environment variables
- **Model:** Uses `gpt-4.1-mini` for cost efficiency (user preference)
- **Security:** OAuth 2.0 flow for Google Calendar API

## Integration Points

### Google Calendar API
- **Authentication:** OAuth 2.0 with stored tokens per user
- **Service:** `GoogleCalendarService` handles all Calendar API interactions
- **Pattern:** Always check authentication before processing calendar operations

### Telegram Bot API
- **Webhook mode:** Production setup with FastAPI endpoints
- **Polling fallback:** Development/debugging mode
- **Service:** `TelegramBotService` manages bot lifecycle

### LiteLLM Integration
- **Library:** Abstraction layer over OpenAI API
- **Pattern:** All LLM calls use `acompletion()` with consistent error handling
- **Configuration:** Model selection via `LITELLM_MODEL` environment variable

## Common Debugging Patterns

### Intent Extraction Issues
1. Check raw LLM response in logs: `Raw LLM response: '{result}'`
2. Validate prompt formatting with current date/history
3. Test with `test_production_scenario.py` for regression

### Calendar Selection Problems
1. Verify calendar cache is populated: `update_calendar_cache()`
2. Check AI suggestion vs rule-based fallback paths
3. Validate calendar name extraction from user messages

### Multi-Event Operation Debugging
1. Check pending operations: `has_pending_operation(chat_id)`
2. Validate confirmation workflow state
3. Test batch operation parsing logic

## Performance Considerations
- **LLM Costs:** Uses gpt-4.1-mini for efficiency while maintaining quality
- **Calendar API:** Intelligent caching of calendar metadata
- **Conversation History:** Formatted efficiently for token optimization

## Security Notes
- **Credentials:** Never log Google credentials or tokens
- **OAuth:** Proper scope limitation for Calendar API access
- **Environment:** All secrets via environment variables, never hardcoded

---

*This guide reflects the current architecture after recent major enhancements for multi-event operations and improved calendar selection. Always check test results to validate functionality after changes.*
