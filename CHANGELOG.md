# CaliBOT Changelog

All notable changes to the CaliBOT project are documented here in reverse chronological order.

## [Unreleased]

### Fixed
- **Critical: Docker Deployment Failure**: Fixed missing requirements.txt file causing Render deployment failures
### Technical Details
- **requirements.txt**: Created from pyproject.toml dependencies for Render compatibility
- **Dockerfile**: Fixed COPY instruction to properly reference requirements.txt
- **Render Deployment**: Service should now deploy successfully via GitHub auto-deploy

## [0.1.6] - 2025-08-08

### Fixed
- **Critical: File Organization Violation Cleanup**: Removed unnecessary files that violated copilot instructions
### Technical Details
- **Deleted Files**: PRODUCTION_DEPLOYMENT_STATUS.md, scripts/deploy_production.sh, scripts/enforce_file_organization.sh
- **Copilot Instructions**: Enhanced with Render.com deployment architecture information and stricter file creation rules
- **Deployment Clarification**: Service uses Render auto-deploy via GitHub - no manual deployment scripts needed

### Enhanced
- **Deployment Architecture Documentation**: Added Render.com auto-deployment information to copilot instructions  
- **File Creation Rules**: Strengthened prohibition against unnecessary summary, status, and deployment files

## [0.1.5] - 2025-08-08
### Fixed
- **Critical: Production Dependencies**: Fixed missing `python-telegram-bot` dependency causing runtime failures
- **Enhanced Error Handling**: Added comprehensive try-catch blocks and validation for `event_data` processing
- **Type Safety**: Improved validation with enhanced logging to catch and handle malformed data structures
- **Production Deployment**: Added explicit dependency installation in Dockerfile and requirements.txt

### Technical Details
- **routes.py**: Added try-catch around NLP processing with detailed error logging
- **routes.py**: Enhanced event_data validation with intent field checking
- **Dockerfile**: Added explicit installation of `backoff` and `litellm[proxy]` dependencies
- **requirements.txt**: Created comprehensive dependency list for production deployment
- **Root Cause**: Production environment missing dependencies causing import failures and type errors
- **Impact**: Bot now handles errors gracefully and provides meaningful feedback instead of generic "trouble processing" messages

## [0.1.4] - 2025-08-08
### Fixed
- **Critical: File Organization Violation**: Removed all misplaced test files and forbidden summary files from project root
- **Development Rule Enforcement**: Strengthened copilot instructions to prevent file organization violations

### Technical Details
- **Deleted forbidden files**: Removed `FIXES_SUMMARY.md`, `MULTI_EVENT_IMPLEMENTATION_SUMMARY.md` (violate no-summary-files rule)
- **Moved utility files**: Relocated `version_check.py` to `scripts/` folder
- **Enhanced copilot instructions**: Added MANDATORY file organization enforcement with pre-task scanning
- **Root Cause**: Previous rules were not strict enough to prevent file organization violations
- **Impact**: Project structure now strictly follows approved organization rules

## [0.1.3] - 2025-08-08
### Fixed  
- **Critical: Delete/Update Confirmation Workflow**: Fixed broken confirmation workflow for delete/update operations where bot would ask for confirmation but not create any pending operations, causing "I don't have any pending operations to confirm" error
- **Multi-Event Queue Creation**: Added proper event queue creation for multi-event delete/update operations that require confirmation
- **Single-Event Pending Operations**: Added proper pending operation storage for single-event delete/update operations
- **LiteLLM Dependency**: Fixed missing 'backoff' module error by adding proper dependency specification
- **Type Safety**: Fixed "'list' object has no attribute 'get'" error in event processing

### Technical Details
- **routes.py**: Added dedicated handler for delete/update operations with `confirmation_needed: True` that properly creates event queues or stores pending operations before asking for confirmation
- **Root Cause**: Delete/update operations with confirmation were falling through to generic AI response without creating any trackable pending state
- **Impact**: Mass delete operations like "Delete all events titled 'lesson'" now work correctly through the full confirmation workflow

## [0.1.2] - 2025-08-08
### Fixed
- **Critical: Confirmation Handler Bug**: Fixed multi-event delete confirmations failing by adding proper text normalization and ensuring event queue system is checked first before legacy handler
- **Mermaid Diagram Parsing**: Fixed "No diagram type detected" error by changing flowchart syntax from `flowchart TD` to `graph TD` and removing problematic colon characters in node labels

### Technical Details
- **routes.py**: Updated confirmation intent handler to normalize confirmation text ("Yes", "yes", "confirm", "ok") and always check event_queue_handler.has_pending_queue() before multi_event_handler.has_pending_operation()
- **Root Cause**: User confirmations like "Yes" were not being properly handled for event queue operations, causing "I don't have any pending operations to confirm" error

## [0.1.1] - 2025-08-07
### Fixed
- **Critical: Mass Delete Functionality**: Fixed broken multi-event deletion where confirmation intent wasn't checking event queue system, causing "I don't have any pending operations to confirm" error
- **Mermaid Diagram Rendering**: Simplified WORKFLOW_ARCHITECTURE.md diagram by removing complex styling that was causing "No diagram type detected" errors
- **Backend Code Professionalism**: Removed all emoticons from scripts (push_to_github.sh, quick_push.sh) as they are backend files
- **File Organization**: Deleted unnecessary FIXES_SUMMARY.md and QUICK_SCRIPTS.md files to maintain clean project structure

### Technical Details
- **routes.py**: Updated confirmation intent handler to check both event_queue_handler.has_pending_queue() and multi_event_handler.has_pending_operation() systems
- **WORKFLOW_ARCHITECTURE.md**: Removed styling directives that were breaking Mermaid diagram parsing
- **Root Cause**: Event queue system (new) vs multi_event_handler (legacy) were not properly integrated in confirmation workflow

### Enhanced
- **Development Guidelines**: Updated copilot instructions to explicitly ban emoticons in all scripts and prevent creation of redundant documentation files
- **Code Style Enforcement**: Clarified that all files in scripts/ folder are backend files requiring professional style

## [0.1.0] - 2025-08-07
### Fixed
- **Event Processing Bug**: Fixed `'list' object has no attribute 'get'` error in multi-event delete operations by adding proper type validation for event objects
- **File Organization**: Moved all test files and demo scripts from project root to `tests/` folder
- **Scripts Organization**: Moved `version_check.py` to `scripts/` folder for better project structure
- **Mermaid Diagram**: Fixed WORKFLOW_ARCHITECTURE.md diagram syntax error by simplifying complex flowchart
- **Backend Code Style**: Removed all emoticons from backend Python files, log messages, and prompts for professional appearance

### Enhanced  
- **WORKFLOW_ARCHITECTURE.md**: Completely updated with comprehensive workflow diagram including all processes (create, update, delete, query, calendar management, queue handling)
- **Type Safety**: Added validation to ensure event objects are dictionaries before accessing attributes
- **Development Guidelines**: Updated copilot instructions to enforce scripts and test file organization and ban emoticons from backend files
- **Code Professionalism**: Standardized all backend messages to use clear descriptive text instead of emoticons

### Technical Details
- Added type checking in `routes.py` line 155-165 to prevent accessing attributes on non-dictionary objects
- Enhanced workflow documentation with simplified but complete Mermaid diagram
- Moved 12 test files and 2 demo files from project root to tests folder
- Updated `.github/copilot-instructions.md` to mandate proper file organization and eliminate fixes summary files
- Added `scripts/organize_files.sh` for automatic file organization enforcement
- Removed emoticons from all backend files: routes.py, google_calendar.py, multi_event_operations.py, event_queue_handler.py, intent_extraction_prompt.py
- Updated copilot instructions to ban emoticons in backend files while allowing them in README.md

### Critical Production Fixes (Previous)
- **Calendar ID Bug**: Fixed delete operations failing due to hardcoded 'primary' calendar ID
- **Multi-Event Delete Queue**: Implemented queue-based individual confirmation for delete operations  
- **Event Count Summaries**: Added event counts to all operation results ("X events deleted/created/updated")
- **Time Confirmation**: Enhanced event summaries to always show both date AND time information
- **Proper Delete Workflow**: Multi-event deletions now use queue system instead of legacy batch handler

### Discovered & Validated (Previous)
- **Event Queue System**: Found existing simplified multi-event handling that perfectly matches user requirements
- **Individual Event Confirmations**: Queue processes multi-event requests one-by-one with user confirmation
- **Version Control Workflow**: Established comprehensive version management rules across multiple files
- Centralized development rules and changelog guidelines in copilot instructions
- Streamlined project file organization and accessibility
- Comprehensive test suite validation framework

### Removed
- **Summary Files**: Deleted empty `FIXES_SUMMARY.md` and `MULTI_EVENT_IMPLEMENTATION_SUMMARY.md` (content merged into changelog)

### Technical Details
- **CRITICAL FIX**: `delete_event()` method now accepts `calendar_id` parameter to delete from correct calendar
- **Queue Integration**: Multi-event delete/update operations route through `EventQueueHandler` with individual confirmations
- **Enhanced Event Formatting**: `_format_event_summary()` handles both creation and existing event formats with proper time display
- **Routes Update**: Delete operations extract calendar_id from matched events and pass to calendar service
- **Summary Messaging**: All operation results include event counts and clear success/failure indicators
- **File Organization Rule**: ALL test files must be in `tests/` folder - NO test files in project root or backend folder
- **Docker Build Optimization**: tests/ folder excluded from Docker builds to reduce image size
- **Version Control Workflow**: Synchronized version tracking across pyproject.toml, CHANGELOG.md, and backend/app/__init__.py
- **Event Queue Handler**: `/backend/app/services/event_queue_handler.py` handles multi-event detection and confirmation
- **Testing**: Production fixes validated in `tests/test_production_fixes.py`
- **Files affected**: `google_calendar.py`, `routes.py`, `event_queue_handler.py`, `.dockerignore`, `pyproject.toml`, `backend/app/__init__.py`, all test files moved to `tests/`

## [1.2.0] - 2025-08-06

### Added
- **Multi-Event Operations System**: Comprehensive handler for batch operations affecting multiple events
  - Queue-based confirmation workflow for delete/update operations
  - Event matching algorithm for finding events by title, date, and calendar
  - Safety measures to prevent accidental bulk operations
  - Support for "delete all events called X" style requests
- **Enhanced Intent Extraction**: Added comprehensive DELETE and UPDATE operation examples
- **Robust Confirmation Workflow**: User must explicitly confirm multi-event operations
- **Pending Operations Tracking**: System tracks operations awaiting user confirmation

### Enhanced
- **Calendar Intelligence**: Improved automatic calendar selection using AI + rule-based fallbacks
- **Conversation Context**: Better conversation history formatting with numbered messages
- **Error Handling**: Graceful degradation with user-friendly error messages

### Fixed
- **Calendar Assignment Bug**: Events now correctly assigned to user-specified calendars (100% success rate)
- **Multi-Event Delete Operations**: "delete all lesson events today" now works correctly
- **Intent Classification**: Delete requests no longer misclassified as queries

### Technical Details
- Added `MultiEventOperationHandler` in `app/services/multi_event_operations.py`
- Enhanced `intent_extraction_prompt.py` with explicit DELETE/UPDATE examples
- Integrated multi-event handler into main routes workflow
- Comprehensive test suite with 100% pass rate

## [1.1.0] - 2025-08-06

### Added
- **Batch Event Creation**: Support for creating multiple events in a single request
- **Enhanced Calendar Selection**: AI-powered calendar selection with rule-based fallbacks
- **Calendar Theme Detection**: Automatic theme extraction from calendar names
- **Conversation State Management**: Persistent conversation history across interactions

### Enhanced
- **Prompt Engineering**: Structured prompts with explicit warnings and examples
- **JSON Parsing**: Custom parsing to handle multiple JSON objects from LLM responses
- **Context Memory**: LLM maintains context across conversation turns

### Fixed
- **Calendar Name Extraction**: 100% success rate for extracting calendar names from user messages
- **Batch Processing**: System correctly parses multiple JSON objects for batch creation
- **Context Handling**: LLM no longer forgets previous conversation context

### Technical Details
- Enhanced `nlp_agent.py` with multi-JSON parsing logic
- Improved `helpers.py` with better conversation history formatting
- Added comprehensive test coverage for all scenarios

## [1.0.0] - 2025-08-06

### Added
- **Core CaliBOT System**: Intelligent Telegram bot for Google Calendar management
- **Natural Language Processing**: GPT-4.1-mini integration for intent extraction
- **Google Calendar Integration**: OAuth 2.0 authentication and full Calendar API support
- **Telegram Bot Integration**: Webhook and polling modes for message handling
- **Multi-Agent Architecture**: NLP Agent → Calendar Agent → Services pipeline

### Features
- Create, update, delete, and query calendar events using conversational language
- Automatic calendar selection based on event content
- Contextual conversations with memory
- Intent recognition to separate calendar tasks from small talk
- Secure OAuth 2.0 authentication

### Technical Components
- FastAPI backend with async/await patterns
- LiteLLM for cost-efficient AI integration
- Structured prompt engineering system
- Comprehensive error handling and logging
- Production-ready webhook deployment
