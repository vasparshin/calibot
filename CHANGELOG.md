# CaliBOT Changelog

All notable changes to the CaliBOT project are documented here in reverse chronological order.

## [Unreleased]

## [0.1.47] - 2025-08-11

### Added
- **Immediate Update/Delete Handler**: New `immediate_update_delete.py` to execute single update/delete operations instantly when `confirmation_needed` is False.

### Changed
- **routes.py**: Integrated immediate handler before existing create/batch logic in no-confirmation path to unify execution flow.
- **handlers/__init__.py**: Exported new handler for centralized imports.

### Technical Details
- Prevents duplicate inline logic growth by routing all no-confirmation update/delete operations through dedicated handler.
- Maintains user-facing message consistency via existing formatting utilities.

## [0.1.46] - 2025-08-11

### Added
- **Update/Delete Handler Extraction**: Introduced `update_delete.py` handler consolidating multi-event and single-event update/delete confirmation logic previously embedded in `routes.py`.

### Changed
- **routes.py**: Replaced large inline block for update/delete confirmation and execution with call to `process_update_delete_with_confirmation` to reduce duplication and undefined variable errors.

### Technical Details
- **Handler Integration**: Centralizes queue creation, target filtering, and single-event confirmation generation; preserves existing UX (buttons, messages) per BOT rules.
- **Legacy Removal**: Removed obsolete inline single-event update/delete processing to eliminate risk of stale code paths and undefined `events` references after refactor.

## [0.1.45] - 2025-08-11

### Added
- **Handler Scaffolding**: Introduced `backend/app/api/handlers/` package with `batch_creation`, `duplicate_detection`, `event_query`, `single_creation`, and `intent_dispatcher` modules.
- **Batch Creation Refactor (Phase 1)**: Extracted batch creation and duplicate detection logic from `routes.py` into `process_batch_creation` and `find_duplicates` without changing behavior.
- **Single Event Creation Extraction**: Moved single event creation path into `create_single_event` helper to reduce repetition.

### Technical Details
- **routes.py**: Integrated new handlers with minimal invasive edits; existing logic preserved for all other intents.
- **Duplicate Logic**: Centralized in `duplicate_detection.py` for future enhancement (fuzzy matching/time overlap).
- **Future Dispatcher**: Added `IntentDispatcher` scaffold for upcoming phased decomposition.

### Impact
- Reduces monolith size and paves way for subsequent refactors (multi-event operations, confirmation flow unification) while keeping all tests expected to pass unchanged.

## [0.1.44] - 2025-08-11

### Added
- **Refactor Plan Initiated**: Established phased refactor strategy to decompose `routes.py` (≈1200 lines) into modular handlers (batch creation, duplicate detection, event querying, multi-event operations, confirmations, intent dispatcher). No functional changes yet; groundwork for complexity reduction and future feature expansion.

### Technical Details
- **Version Bump**: Incremented version across `pyproject.toml` and `backend/app/__init__.py` per mandatory versioning rules.
- **Planning Only**: This release documents architecture planning before code extraction to ensure traceability; implementation to follow in subsequent versions.
- **No Structural Cleanup Needed**: Scan confirmed no forbidden summary/status/fixes files or misplaced root test files requiring relocation at this stage.

## [0.1.43] - 2025-01-04

### Fixed - Critical Batch Creation Issues
- **CRITICAL: Batch Event Creation Failure**: Fixed the root cause where batch events were missing required fields (event_name, date, intent) preventing calendar service from creating events
- **Enhanced Event Processing**: Added event enhancement logic to inherit missing fields from parent event_data before processing
- **Robust Error Handling**: Improved error reporting for batch creation scenarios with detailed failure messages

### Enhanced - Button Behavior Rules
- **Updated BOT_RULES.md**: Added absolute rule requiring ALL buttons to be temporary and removed immediately after interaction
- **Critical UI Rule**: Established that buttons must disappear with status updates ("Processing...", "Cancelled") after every click
- **Developer Guidance**: Clear implementation requirements for button removal using edit_message_text() with reply_markup={}

### Technical Improvements
- **routes.py**: Fixed batch creation logic to enhance events with missing fields from parent event_data
- **routes.py**: Added intent="create" field to all batch events before sending to calendar service
- **BOT_RULES.md**: Added comprehensive button behavior section with implementation requirements

## [0.1.42] - 2025-01-04

### Fixed - Multiple Event Creation
- **CRITICAL: Batch Event Creation**: Fixed multiple event creation failing for requests like "3 lessons at 9, 10 and 12am" - now properly creates multiple events instead of single event
- **CRITICAL: Single Event Formatting**: Fixed inconsistent formatting between single and multi-event success messages - now uses consistent hyperlinked format with calendar names

### Enhanced - Intent Extraction
- **Enhanced NLP Prompt**: Added `batch_create` intent type with comprehensive examples for multiple event scenarios
- **Improved Event Detection**: Intent extraction now recognizes patterns like "3 lessons at 9, 10, 12" and generates proper JSON structure with events array
- **Robust Event Handling**: Enhanced routes.py to properly process batch_create intents and create individual events from event arrays

### Technical Improvements
- **intent_extraction_prompt.py**: Added batch_create intent with JSON format examples and multiple event patterns
- **routes.py**: Fixed batch creation handling to use consistent success message formatting without calling undefined format_success_message function
- **routes.py**: Updated single event creation to use format_event_for_display for consistency with multi-event summaries

## [0.1.41] - 2025-01-04

### Fixed - Critical UX Issues
- **CRITICAL: Button Removal**: Buttons now properly disappear after selection with status updates ("Processing...", "Cancelled", etc.)
- **CRITICAL: Success Messages**: Now show actual updated times/info instead of original event data (e.g., shows new 2:00 PM time, not old 5:00 PM)
- **CRITICAL: One-by-One Logic**: Fixed queue progression to properly advance through individual event confirmations without skipping to "all" processing
- **CRITICAL: Queue State Management**: Added `one_by_one_mode` flag to distinguish between initial batch selection and individual event confirmations

### Enhanced - User Experience
- **Dual Message Flow**: One-by-one processing now sends result and next confirmation as separate messages for better UX
- **Proper Keyboard Management**: All multi-event confirmation buttons removed with meaningful status text
- **Enhanced Route Handling**: Updated both callback and text message handling to support proper queue progression
- **Detailed Success Formatting**: Success messages include full date, updated times, calendar names, and hyperlinks

### Technical Improvements
- **event_queue_handler.py**: Fixed `process_queue_response` logic to handle one-by-one mode properly
- **event_queue_handler.py**: Enhanced `_process_single_event` to show actual updated times in success messages
- **routes.py**: Updated `handle_confirmation_callback` to remove keyboards with status updates for all confirmation types
- **routes.py**: Added proper handling for `queue_continues` response type with dual message sending

## [0.1.40] - 2025-01-04

### Fixed
- **Critical: Time Shift Logic**: Fixed distinction between "move earlier/later" (shifts both start/end times) vs "extend duration" (only changes end time)
- **Critical: Button Persistence**: Buttons now properly disappear after selection with empty reply_markup to remove keyboard
- **Critical: Callback Handling**: Enhanced routes to handle single event confirmation callback patterns (confirm_action, cancel_action)
- **Enhanced: Success Messages**: Updated messages now show specific changes made (e.g., "shifted by -3 hours", "renamed to X")
- **Enhanced: Proposed Changes**: "Found X events to update" messages now show what changes will be made (e.g., "move 3 hours earlier")
- **Enhanced: Intent Extraction**: Updated prompt examples to distinguish between move operations and duration changes

### Technical Details
- **event_queue_handler.py**: Enhanced time shift logic to detect move vs extend operations using keywords and negative values
- **routes.py**: Fixed `handle_confirmation_callback` to remove keyboards using `reply_markup={}` parameter
- **routes.py**: Added specific handling for single event confirmation callbacks (`confirm_` patterns)
- **intent_extraction_prompt.py**: Updated examples to clarify "move X earlier" vs "extend X duration" patterns
- **Comprehensive testing**: All fixes validated with test suite covering time shift logic, button persistence, and message improvements

## [0.1.39] - 2025-01-04

### Fixed
- **Critical: EventQueueHandler Time Shift Bug**: Fixed incorrect time shift logic that was moving both start AND end times instead of keeping start time unchanged and extending end time
- **Critical: Message Persistence in EventQueueHandler**: Fixed missing keyboard in `get_next_event_confirmation` responses causing buttons to disappear after selection
- **Enhanced: Callback Data Handling**: Updated `process_queue_response` to properly handle inline keyboard callback data patterns (confirm_action, cancel_action)
- **Enhanced: User Experience**: Replaced text-based confirmations in EventQueueHandler with inline buttons matching MultiEventOperationHandler

### Technical Details
- **event_queue_handler.py**: Fixed time shift calculation to match MultiEventOperationHandler (keep start unchanged, set end = start + duration)
- **event_queue_handler.py**: Added keyboard parameter to `get_next_event_confirmation` responses
- **event_queue_handler.py**: Enhanced `process_queue_response` to handle callback data patterns and maintain keyboard persistence
- **Added comprehensive logging**: EventQueueHandler now includes detailed time shift calculation logging to match MultiEventOperationHandler

## [0.1.38] - 2025-01-04

### Fixed
- **Critical: Callback Processing**: Fixed `handle_confirmation_callback` to process pending multi-event operations directly instead of triggering new intent extraction
- **Critical: Button Response Flow**: Resolved issue where "One by One" button presses were not properly initiating queue-based processing
- **Enhanced: Intent Extraction**: Added specific examples in prompt for "move end time to X hour after start" patterns
- **Enhanced: Time Shift Recognition**: Updated intent extraction patterns to better recognize duration change requests

### Technical Details
- **routes.py**: Modified `handle_confirmation_callback` to check for pending operations (multi_event_handler and event_queue_handler) before falling back to `process_user_message`
- **intent_extraction_prompt.py**: Added examples for time shift patterns like "move the end time to one hour after the start times" → `time_shift: "1 hour"`
- **Flow Fix**: Prevents double intent extraction when inline keyboard buttons are pressed, ensuring smooth transition from confirmation to execution

### Issues Resolved
- Inline keyboard buttons disappearing after selection without executing operations
- "One by one" processing not working due to callback handling issues
- Time shift parameters not being extracted from natural language requests
- New intent extraction being triggered instead of processing pending operations