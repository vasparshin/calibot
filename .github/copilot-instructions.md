# CaliBOT - AI Calendar Bot Development Guide

## Project Overview

## ⚠️ CRITICAL REMINDERS
- **🚨 MANDATORY CHANGELOG UPDATE 🚨** - EVERY code change MUST be documented in CHANGELOG.md IMMEDIATELY before task completion
- **🤖 MANDATORY BOT RULES COMPLIANCE 🤖** - ALL user-facing messages MUST follow formatting rules in BOT_RULES.md
- **🚀 MANDATORY DEPLOYMENT VERIFICATION 🚀** - ALWAYS verify latest version is deployed before testing using `python scripts/verify_deployment.py`
- **📱 YOUR ACTUAL GROUP CHAT ID 📱** - ALWAYS use `-4627994150` for testing - this is documented in PROJECT_RULES.md and must not be lost again
- **🎯 MULTI-EVENT DEMO PROTOCOL 🎯** - Follow comprehensive demo standards in PROJECT_RULES.md: bot-to-bot conversation + live log monitoring + all scenarios
- **⏱️ MANDATORY RENDER RESTART 📋** - If auto-deployment fails, use `verify_deployment.py` force restart or manual Render dashboard restart
- **📊 LOG FETCHING RULES 📊** - NEVER use streaming log scripts (`live_logs.py`) - they get stuck. ALWAYS use `recent_logs.py` to fetch last 30 minutes of logs and exit cleanly
- **📋 PROJECT RULES COMPLIANCE 📋** - ALWAYS check PROJECT_RULES.md for critical information like group ID, demo protocols, and deployment procedures
- **🚫 NO USER INPUT PROMPTS 🚫** - NEVER create scripts that wait for user input on simple decisions - always auto-decide based on context
- **NO EXCEPTIONS TO CHANGELOG RULE** - Even the smallest bug fix, file organization, or code tweak requires CHANGELOG.md update
- **CHANGELOG UPDATE IS PART OF THE FIX** - A change is NOT complete until CHANGELOG.md is updated
- **ALWAYS UPDATE CHANGELOG.MD** - Every code change MUST be documented in CHANGELOG.md before task completion
- **NO EMOTICONS IN BACKEND FILES** - Scripts, Python files, configuration files must use professional text only
- **NO UNNECESSARY FILES** - Don't create summary files, use existing documentation structure
- **NO TEST FILES IN PROJECT ROOT** - ALL test files must be in tests/ folder, NEVER in project root
- **NO SUMMARY FILES EVER** - NEVER create FIXES_SUMMARY.md, MULTI_EVENT_IMPLEMENTATION_SUMMARY.md or similar files

## 🤖 USER INTERFACE CONSISTENCY
**CRITICAL: All user-facing messages must follow BOT_RULES.md**
- **Mandatory Reference**: Always consult `/workspaces/calibot/BOT_RULES.md` for message formatting
- **Event Display Format**: Must include clickable links, full dates, proper calendar names
- **Calendar Names**: Always fetch and display actual calendar names, never technical names
- **Title Capitalization**: All event titles must be properly capitalized
- **Confirmation Handling**: Support all specified confirmation responses (yes/no/cancel/all/one)
- **Message Consistency**: Use centralized formatting functions for all similar operations

## 🚫 ABSOLUTELY FORBIDDEN FILE PATTERNS
- **NEVER CREATE**: Any file ending with `_SUMMARY.md`, `SUMMARY.md`, `FIXES.md`, `STATUS.md`
- **NEVER CREATE**: Test files in project root (test_*.py, *_test.py, *_demo.py)
- **NEVER CREATE**: Documentation files that duplicate CHANGELOG.md functionality
- **NEVER CREATE**: Deployment scripts (service uses Render auto-deploy via GitHub)
- **NEVER CREATE**: Utility scripts unless explicitly requested
- **IMMEDIATELY DELETE**: Any summary files found during task execution

## 📦 DEPLOYMENT SIZE OPTIMIZATION
**CRITICAL: Keep Render deployment lean - currently at 4/1GB, optimize aggressively**

### .gitignore Management Rules
- **ALL test result files MUST be ignored**: `tests/*_results_*.json`, `tests/logs/`, etc.
- **Development utilities excluded**: Non-essential scripts, debug tools, analysis scripts
- **Media files prohibited**: `*.mp4`, `*.tgz`, large assets in `info/` directory
- **Temporary files ignored**: `*.tmp`, `*.temp`, IDE files, backup files
- **Test artifacts excluded**: Generated test reports, simulation results, debug outputs

### File Size Monitoring
- **Monitor deployment size** regularly via Render dashboard
- **Large file detection**: Any file >1MB should be reviewed for necessity
- **Asset optimization**: Compress or exclude large development assets
- **Log file cleanup**: Exclude all generated log files and test results from repository

### Essential vs. Non-Essential Files
**Essential (included)**:
- Core application code (`backend/`)
- Configuration files (`pyproject.toml`, `Dockerfile`, etc.)
- Documentation (`README.md`, `CHANGELOG.md`, `BOT_RULES.md`)
- Production scripts (`scripts/verify_deployment.py`, `scripts/quick_version_check.py`)

**Non-Essential (excluded)**:
- Test result files and logs
- Development debugging tools
- Large media assets
- Temporary analysis scripts
- Generated documentation

## 🛡️ DEPLOYMENT ARCHITECTURE
**CRITICAL: CaliBOT is deployed via Render.com with GitHub integration**
- **Auto-deployment**: Render automatically deploys from GitHub main branch
- **NO MANUAL DEPLOYMENT SCRIPTS**: Never create deploy scripts - Render handles this
- **Environment Variables**: Set in Render dashboard, not in scripts
- **Docker**: Render uses the existing Dockerfile automatically
- **Dependencies**: Render installs from requirements.txt and pyproject.toml
- **NEVER create deployment documentation** - this information is sufficient

## 🚀 MANDATORY DEPLOYMENT VERIFICATION WORKFLOW
**CRITICAL: ALWAYS verify deployment before testing - Render auto-deployment can fail**

### Pre-Testing Verification (MANDATORY)
```bash
# Step 1: Quick version check
python scripts/quick_version_check.py

# Step 2: If version mismatch, use automated verification
python scripts/verify_deployment.py
```

### Deployment Verification Rules
- **ALWAYS check version match** before running any tests
- **Use automated tools** - `verify_deployment.py` handles restart if needed
- **Wait 2-3 minutes** after git push for Render deployment
- **Force restart if auto-deploy fails** - tool handles this automatically
- **Manual Render dashboard restart** as backup option
- **Health check required** before testing to ensure service is responsive

### Automated Restart Process
- `verify_deployment.py` compares local vs deployed versions
- Automatically offers to force deployment via empty commit + push
- Waits appropriate time for Render to redeploy
- Re-verifies version after restart
- Ensures backend health before proceeding

### When Auto-Deployment Fails
1. **Use `verify_deployment.py`** - handles most cases automatically
2. **Manual Render dashboard restart** - if automated restart fails
3. **Check Render logs** - for deployment errors or build failures
4. **Verify environment variables** - in Render dashboard if service won't start

**NO TESTING WITHOUT VERIFICATION** - Testing old code wastes time and gives false results

## 🛡️ MANDATORY PRE-TASK FILE ORGANIZATION CHECK
**BEFORE ANY TASK EXECUTION, SCAN FOR:**
1. IMMEDIATELY delete any `*SUMMARY*.md`, `*STATUS*.md`, `FIXES_*.md` files
2. IMMEDIATELY move any `test_*.py`, `*_demo.py` files to `tests/`
3. IMMEDIATELY delete any deployment scripts (service uses Render auto-deploy)
4. Update CHANGELOG.md documenting the cleanup
5. NEVER proceed without fixing file organization first

## File Organization Rules (MANDATORY)

### Project Root - ONLY These Files Allowed:
```
/workspaces/calibot/
├── .dockerignore
├── .gitignore  
├── CHANGELOG.md          # ONLY place for change documentation
├── Dockerfile
├── LICENSE
├── README.md             # Project overview only
├── WORKFLOW_ARCHITECTURE.md  # System design only
├── pyproject.toml        # Dependencies and version
├── uv.lock              # Lock file
├── backend/             # Application code
├── tests/               # ALL test files go here
├── scripts/             # Utility scripts only
└── info/                # Documentation assets
```

### Strictly Forbidden in Project Root:
- `test_*.py` files
- `*_demo.py` files  
- `queue_demo.py`
- `simple_queue_demo.py`
- `*SUMMARY*.md` files
- `FIXES_*.md` files
- `version_check.py` (belongs in scripts/)

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
- **ABSOLUTELY NO SUMMARY FILES** - NEVER create any file with "SUMMARY", "FIXES", or similar in the name
- **MANDATORY FILE LOCATION CHECK** - Before creating ANY file, verify it goes in the correct location:
  - Tests/demos: MUST go in `tests/` folder
  - Utility scripts: MUST go in `scripts/` folder  
  - Documentation: MUST go in CHANGELOG.md or existing docs
- **PRE-TASK FILE SCAN** - At the start of every task, scan for and DELETE any misplaced files
- **CHANGELOG.md is the ONLY place for version logs** - never create separate summary files
- **IMMEDIATE CLEANUP** - If you find any summary files or misplaced test files, delete them immediately

### Mandatory File Organization Enforcement
**BEFORE any task execution:**
1. Scan project root for forbidden files
2. Delete any `*SUMMARY*.md`, `FIXES_*.md` files immediately  
3. Move any `test_*.py`, `*_demo.py` files to `tests/`
4. Move any utility scripts to `scripts/`
5. Update CHANGELOG.md with cleanup actions

**File Location Rules:**
- **tests/**: ALL test files, demo files, validation scripts
- **scripts/**: Utility scripts like version_check.py, organize_files.sh  
- **Project root**: ONLY core project files (see approved list above)
- **backend/**: Application source code only

### Frontend/User-Facing Content
- Emoticons are acceptable in README.md, user documentation, and Telegram bot responses to users
- Keep professional in all backend code and system logs

## Changelog Rules

- **MANDATORY: Every commit or PR must update `CHANGELOG.md` AFTER testing is complete.**
- **MANDATORY: Every code change, bug fix, or feature implementation MUST be documented in CHANGELOG.md AFTER verifying tests pass.**
- **TESTING FIRST: Always run tests and verify functionality before updating changelog.**
- **NO EXCEPTIONS: If you make any change to code, configuration, or documentation, you MUST update the changelog AFTER testing.**
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

### Complete Implementation Process
**🚨 CRITICAL: Follow this exact sequence for EVERY feature/fix - NO EXCEPTIONS:**

#### Phase 1: Analysis & Planning
1. **Analyze Requirements**: Break down feature into specific components and acceptance criteria
2. **Identify Dependencies**: Check what files, functions, and services need modification  
3. **Architecture Assessment**: Ensure changes align with existing patterns and don't break current functionality
4. **Create Implementation Plan**: Step-by-step approach with specific files and functions to modify

#### Phase 2: Implementation
5. **Implement Core Functionality**: Write the actual feature code following project patterns
6. **Add Error Handling**: Ensure graceful failure modes and user-friendly error messages
7. **Integration Points**: Connect new functionality with existing systems (routes, services, agents)
8. **Code Review**: Verify code follows project conventions and is maintainable

#### Phase 3: Testing & Validation
9. **MANDATORY: Pre-Testing Deployment Verification**: Run `python scripts/verify_deployment.py` to ensure latest version is deployed
10. **Unit Testing**: Test individual functions and components in isolation
11. **Integration Testing**: Test feature works with existing system components
12. **Real-World Scenario Testing**: Test with actual user scenarios and edge cases using `tests/test_one_by_one_workflow.py` for multi-event features
13. **Performance Testing**: Verify feature doesn't degrade system performance
14. **User Experience Testing**: Ensure feature provides good UX and follows BOT_RULES.md

#### Phase 4: Optimization & Polish
15. **Code Optimization**: Refactor for efficiency, readability, and maintainability
16. **Documentation Update**: Update relevant documentation and code comments
17. **Error Message Improvement**: Ensure all error messages are helpful and actionable
18. **Final Validation**: Complete end-to-end testing of the entire feature

#### Phase 5: Release & Documentation
19. **Version Increment**: Update version in pyproject.toml, backend/app/__init__.py
20. **CHANGELOG.md Update**: Document what was implemented, why, and impact
21. **Git Commit**: Commit all changes with descriptive commit message
22. **Push to Repository**: Deploy changes to trigger auto-deployment
23. **MANDATORY Deployment Verification**: Use `python scripts/verify_deployment.py` to ensure latest version is deployed
24. **Final Testing**: Run complete test suite on deployed version to confirm functionality

**🚨 NO FEATURE IS COMPLETE UNTIL ALL 24 STEPS ARE FINISHED 🚨**
**🚨 CLAIMING IMPLEMENTATION WITHOUT COMPLETING ALL PHASES IS FORBIDDEN 🚨**
**🚨 TESTING MUST BE REAL-WORLD SCENARIOS, NOT JUST SYNTAX CHECKS 🚨**
**🚨 DEPLOYMENT VERIFICATION IS MANDATORY BEFORE FINAL TESTING 🚨**

### Changelog Update Workflow
**🚨 CRITICAL: Changelog update is STEP 19 and happens ONLY after testing verification 🚨**

### Changelog Update Examples
**Good changelog entry:**
```
### Fixed
- **Critical: Confirmation Handler Bug**: Fixed multi-event delete confirmations failing by adding proper text normalization
### Technical Details  
- **routes.py**: Updated confirmation intent handler to normalize confirmation text and check event queue system first
```

**Bad changelog entry (missing):**
- Making code changes without any changelog update
- Saying "I'll update the changelog later"
- Creating separate summary files instead of using CHANGELOG.md

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

**CRITICAL VERSION ITERATION RULES:**
- **EVERY single code change, bug fix, or feature MUST increment the version number**
- **NO DUPLICATE VERSIONS EVER** - Each version number can only be used once
- **VERSION SEQUENCE MUST BE INCREMENTAL** - 0.1.0 → 0.1.1 → 0.1.2 → 0.1.3, etc.
- **ALL VERSION REFERENCES MUST MATCH** across pyproject.toml, backend/app/__init__.py, and CHANGELOG.md
- **VERSION INCREMENT IS MANDATORY** - Even the smallest bug fix requires a version bump
- **🚨 CHANGELOG.MD UPDATE IS REQUIRED WITH EVERY VERSION BUMP 🚨**

**Version Update Process (MANDATORY FOR EVERY CHANGE):**
1. Before any code change, identify the next version number (increment from current)
2. Update ALL three files: pyproject.toml, backend/app/__init__.py, CHANGELOG.md  
3. Use the NEW version in CHANGELOG.md entry header
4. **VERIFY CHANGELOG.MD HAS BEEN UPDATED** before completing task
5. Commit with version-specific message: "v0.1.11: Description of change"

**Example Version Progression:**
- v0.1.0: Initial release
- v0.1.1: Fix confirmation bug
- v0.1.2: Add mermaid diagram
- v0.1.3: Fix dependency issues
- v0.1.4: Next change... (and so on)

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

## Project Overview

CaliBOT is an intelligent Telegram bot that manages Google Calendar through natural language. Built with FastAPI, it uses GPT-4.1-mini for intent extraction and conversation management, implementing a sophisticated multi-agent architecture.

## 🎯 Feature Development Guidelines

### PLANNED_FEATURES.md Integration
- **ALWAYS consult PLANNED_FEATURES.md** before implementing new features
- **MANDATORY: Log new feature requests** to PLANNED_FEATURES.md with implementation analysis
- **Architecture Assessment Required**: Analyze impact on current system before coding
- **Priority-Based Development**: Follow the priority order defined in PLANNED_FEATURES.md
- **Implementation Analysis**: Include technology stack, integration points, dependencies, and effort estimates

### Feature Request Workflow
1. **Log Request**: Add feature to PLANNED_FEATURES.md with detailed analysis
2. **Architecture Review**: Assess impact on existing systems and services
3. **Dependency Check**: Identify required libraries, APIs, and system changes
4. **Implementation Plan**: Create step-by-step development approach
5. **Update Documentation**: Keep PLANNED_FEATURES.md current with status updates

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

### Local Development and Testing (Testing Purposes Only)
**IMPORTANT: Local hosting is ONLY for testing and validation purposes. Production deployment happens automatically via Render.com when changes are pushed to GitHub.**

```bash
# For testing EventQueueHandler fixes, time shift logic, etc.
cd backend
python -m app.main

# For webhook testing (development only):
# 1. Set BACKEND_URL in environment
# 2. Use ngrok: ngrok http 8060
# 3. Update webhook URL in main.py
```

**Note**: Once testing is complete and fixes are validated, push changes to GitHub for automatic production deployment via Render.com. No manual deployment needed.


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

**🚨 MANDATORY CHANGELOG UPDATE FOR EVERY COMMIT 🚨**

- **CRITICAL: Every single commit that touches ANY code file MUST update CHANGELOG.md**
- **NO EXCEPTIONS: Even smallest bug fixes, formatting changes, or single-line edits require changelog entry**
- **COMMIT IS INCOMPLETE without changelog update - this is a hard requirement**
- **Format: [Version] - YYYY-MM-DD with detailed technical explanations**

### Required Changelog Format:
```markdown
## [X.Y.Z] - YYYY-MM-DD

### 🚨 **CATEGORY - BRIEF DESCRIPTION**

**file/path/changed.py**: Detailed technical explanation of what changed
- **Root Cause**: Why the change was needed (for fixes)
- **Fix Applied**: Exact technical change made
- **Impact**: ✅ Specific improvement or fix achieved

### 📝 **VERSION FILES UPDATED**
- **calibot/pyproject.toml**: Version X.Y.Z-1 → X.Y.Z
- **calibot/backend/app/__init__.py**: __version__ X.Y.Z-1 → X.Y.Z
```

### Changelog Categories:
- **🚨 CRITICAL BUG FIXES**: Runtime errors, crashes, data loss
- **🔧 BUG FIXES**: Non-critical issues, unexpected behavior
- **✨ NEW FEATURES**: New functionality added
- **📈 ENHANCEMENTS**: Improvements to existing features
- **🛠️ TECHNICAL IMPROVEMENTS**: Code quality, performance, architecture
- **📝 DOCUMENTATION**: README, comments, docs updates
- **🔄 REFACTORING**: Code restructuring without behavior change

### Technical Detail Requirements:
- **File paths**: Always include specific files changed
- **Method/function names**: Reference exact functions modified
- **Root cause analysis**: For fixes, explain what was broken
- **Impact measurement**: Quantify improvements where possible
- **Testing notes**: Mention testing requirements or verification steps

## Bug Tracking Rules (MANDATORY)

### Bug Log Management
- **MANDATORY**: Maintain `Project Docs/BUG_LOG.md` for all user-reported issues
- **CRITICAL**: Only mark bugs as FIXED after explicit user confirmation
- **REQUIRED**: Update bug status based on user feedback, not assumptions
- **PROCESS**: Log all bugs immediately when reported, track attempted fixes

### Bug Status Workflow
1. **User reports bug** → Add to BUG_LOG.md as 🔴 ACTIVE
2. **Attempt fix** → Update to 🟡 IN PROGRESS with fix details
3. **User confirms fix** → Update to 🟢 FIXED
4. **User reports still broken** → Return to 🔴 ACTIVE with new details

### Bug Documentation Format
```markdown
#### **BUG-XXX: Brief Description**
- **Description**: Detailed bug description
- **User Report**: Exact user quote describing the issue
- **Status**: 🔴 ACTIVE / 🟡 IN PROGRESS / 🟢 FIXED / 🔵 LOW PRIORITY
- **Previous Attempts**: List of version attempts and what was tried
```

**NEVER assume a bug is fixed without user confirmation - this prevents repeated failed attempts**

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
