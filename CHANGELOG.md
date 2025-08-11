# CaliBOT Changelog

All notable changes to the CaliBOT project are documented here in reverse chronological order.

## [Unreleased]

## [0.1.63] - 2025-08-11

### Fixed
- Query intents matched by fast-path produced no user message: early non-confirmation branch consumed flow before dedicated query handler, causing silent responses despite logs. Added exclusion of `intent == 'query'` from early non-confirmation block.

### Technical Details
- `routes.py`: Conditional updated to `if confirmation_needed is False and intent != 'query'`; refined confirmation logging.
- Version bump to 0.1.63.

### Impact
- Restores immediate visible responses for common schedule queries ("what's on today", "today's schedule") eliminating silent success logs with no Telegram reply.

## [0.1.62] - 2025-08-11

### Fixed
- Production 500 errors for simple schedule queries ("what's on today") caused by nested `_simple_schedule_query` using `datetime.now()` without module-scope `datetime` import bound in closure, triggering `cannot access free variable 'datetime'` NameError in deployed environment. Added top-level `from datetime import datetime` and removed redundant inner import instance.

### Technical Details
- `routes.py`: Ensured `datetime` available to `_simple_schedule_query`; cleaned redundant local import.
- Version bump to 0.1.62 (`pyproject.toml`, `backend/app/__init__.py`).

### Impact
- Restores fast-path schedule query functionality preventing repeated 500 responses; reduces error log noise and user-facing failures for common queries.

## [0.1.61] - 2025-08-11

### Changed
- Standardized duplicate confirmation inline keyboard labels to BOT_RULES wording: replaced "✅ Yes - Create duplicates" / "❌ No - Cancel" with "✅ Create Anyway" / "❌ Cancel" for consistency and brevity.

### Fixed
- Removed obsolete label expectations in `test_message_consistency.py` preventing mismatch after prior inline keyboard helper introduction.

### Technical Details
- `telegram.py`: Updated `create_confirmation_keyboard` duplicate branch button texts.
- `tests/test_message_consistency.py`: Adjusted expected duplicate keyboard buttons.
- Version bump to 0.1.61 (`pyproject.toml`, `backend/app/__init__.py`).

### Impact
- Aligns all duplicate confirmation flows with documented BOT_RULES.md button names and unifies cancellation wording across confirmation types; prepares for remaining Issue 5 single-row enforcement audit (now partially complete).

## [0.1.60] - 2025-08-11

### Changed
- Renamed internal helper `_heuristic_schedule_query` to `_simple_schedule_query` and log line to use plain language ("Simple schedule query shortcut"). No behavioral change.

### Added
- Second-attempt LLM regeneration in `NLPAgent.extract_intent` when primary response is too short / malformed (single token, missing braces, <20 chars) before falling back to keyword inference.
- Schema normalization: ensures `confirmation_needed` added automatically when missing for create/update/delete intents; defaults false for query.

### Fixed
- Reduced false fallbacks by accepting a successful regenerated JSON response if it passes minimal length + JSON parse + has `intent` key.

### Technical Details
- `routes.py`: Helper rename + updated info log message.
- `nlp_agent.py`: Refactored intent extraction to wrap LLM call in `_call_llm`, add regeneration, stricter invalid detection path, schema normalization, and structured logging.
- `pyproject.toml` / `backend/app/__init__.py`: Version bump to 0.1.60.

### Impact
- Improves robustness against intermittent minimal model outputs without over-reliance on broad keyword fallbacks; maintains clean user-facing formatting and clarifies internal terminology per user preference.

## [0.1.59] - 2025-08-11

### Added
- Heuristic fast-path for simple schedule queries ("today", "tomorrow", "what's on", "what do I have tomorrow", direct weekday references) that bypasses LLM intent extraction, directly producing `{intent: query}` with resolved date. Reduces latency and eliminates exposure to intermittent malformed LLM output returning just a dangling '"intent"' token.

### Fixed
- Suppressed recurring error-path caused by pathological LLM response for trivial schedule lookups by short‑circuiting with deterministic parser before AI call.

### Technical Details
- `routes.py`: Inserted `_heuristic_schedule_query` (renamed to `_simple_schedule_query` in 0.1.60) inner helper inside `process_user_message`; when matched sets `event_data` without invoking `check_relevancy` or `extract_intent`. Retains existing defensive guards for non‑heuristic paths. No changes to downstream formatting logic (still uses unified MessageFormatter query branch).
- `pyproject.toml` / `backend/app/__init__.py`: Version bump to 0.1.59.

### Impact
- Improves reliability and responsiveness for high-frequency user requests (daily schedule checks). Lowers LLM usage, cuts error log noise, and provides stable foundation for further dispatcher refactor tasks (Immediate Issue backlog) without altering user-visible formatting.

## [0.1.58] - 2025-08-11

### Fixed
- Removed redundant second AI completion for query intents that produced placeholder filler messages ("[Fetching your events...]") after formatted event list already sent, restoring clean single-response behavior per BOT_RULES.

### Technical Details
- `routes.py`: Guard added so fallback AI response path skips when intent == 'query'.
- Version bump to 0.1.58.

### Impact
- Eliminates confusing intermediate chat noise and double responses for simple schedule queries; improves clarity and latency.

## [0.1.57] - 2025-08-11

### Fixed
- Hotfix for intermittent malformed LLM intent extraction responses returning only a dangling '"intent"' token causing error log: Error extracting intent: '"intent"'. Added defensive guards in `routes.py` to detect missing/empty intent and apply a safe query fallback instead of emitting user-facing error.

### Technical Details
- `routes.py`: Added pathological single-key empty intent detection and missing 'intent' fallback branch converting failure into `{intent: query}` with current date; prevents regression while upstream prompt tuning pending.
- Version bump to 0.1.57.

### Impact
- Eliminates user-visible failure path for sporadic malformed model outputs, restoring prior stable behavior for casual schedule queries.


## [0.1.56] - 2025-08-11

### Added
- Enhanced proposed change token system: `MessageFormatter` now computes shifted time windows when a `time_shift` phrase is provided (e.g., displays resulting time range instead of only textual shift) supporting forthcoming detailed arrow formatting (Immediate Issue 10).
- Progress tracking section inserted into `immediate_changes.md` (Completed vs Pending with status icons) to replace ad-hoc list and prevent accidental deletion of still-open items.

### Changed
- `immediate_changes.md`: Archived completed items 1–4 under a Completed section; reindexed remaining open issues (5–11) and split architectural refactor tasks into a separate track.

### Technical Details
- `message_formatter.py`: Added `_compute_shifted_time_window` and `_parse_time_shift_minutes` helpers; updated `build_proposed_change_tokens` to include computed new time window when possible.
- `pyproject.toml` / `backend/app/__init__.py`: Version bump to 0.1.56 per mandatory versioning policy.

### Impact
- Establishes clearer roadmap visibility; reduces risk of prematurely removing pending tasks. Lays foundation for integrating full per-event arrow style proposed changes and accurate multi-event success state rendering (Issues 10 & 11).


## [0.1.55] - 2025-08-11

### Fixed
- Prevent duplicate confirmation or cancellation status lines when users press confirmation buttons multiple times rapidly; `routes.py` now detects existing status tokens ("✅ **Confirmed**", "❌ **Cancelled**") before appending.

### Technical Details
- `routes.py`: Added idempotent edit logic in `handle_confirmation_callback` to avoid message text growth due to repeated callbacks; maintains keyboard removal behavior.

### Impact
- Improves UX by eliminating confusing repeated status blocks and preserves clean confirmation history. Foundation for broader button persistence audit (Immediate Issue 6).


## [0.1.48] - 2025-08-11

## [Unreleased]


## [0.1.48] - 2025-08-11

### Added
- **Immediate Issues Logged (6–11)**: Documented critical UX and formatting regressions for remediation (button persistence, calendar name accuracy, calendar migration clarity, one-by-one message retention, detailed proposed change arrows, success message updated-state enforcement).

### Technical Details
- **immediate_changes.md**: Appended sections 6–11 outlining problems, required fixes, target files, acceptance criteria, and related new test placeholders. Provides structured plan for upcoming refactor tasks aligned with BOT_RULES consistency mandate.

### Impact
- Establishes clear remediation backlog to restore compliance with existing BOT rules (ephemeral buttons, accurate calendar names, detailed summaries) and improve auditability of one-by-one flows before further handler/dispatcher refactors.

## [0.1.49] - 2025-08-11

### Changed
- **Calendar Name Preservation**: Updated `MessageFormatter.format_calendar_name` to preserve exact API-provided calendar summary (removed title-casing and domain stripping) per accuracy requirement.
- **Proposed Change Display (Multi-Event Update/Delete)**: Enhanced `update_delete.py` multi-event confirmation to show per-event current state plus arrow (→) tokens describing proposed modifications (rename, calendar move, date/time shift) using new formatter helpers.

### Added
- **Formatter Enhancements**: Introduced `build_proposed_change_tokens` and `format_event_with_proposed_changes` utilities to standardize pre-execution change summaries for future reuse (issues #8–#11 in immediate_changes backlog).

### Technical Details
- **message_formatter.py**: Added proposed change token builder; calendar name function now returns raw name; added arrow composition logic.
- **update_delete.py**: Replaced queue creation path for multi-event updates with enriched confirmation message and stored operation for subsequent confirmation; still uses existing pending operation storage pattern (transitional step before dispatcher refactor).

### Impact
- Improves user clarity by explicitly surfacing intended modifications before execution; prepares codebase for upcoming success message updated-state enforcement and unified queue formatting.

## [0.1.50] - 2025-08-11

### Added
- **Event Queue Skip Support (Issue 2)**: Implemented `skip_event_and_get_next` plus `clear_queue` in `event_queue_handler.py` to properly skip current event and continue one-by-one confirmation without looping or stalling.

### Changed
- **New Command Queue Cancellation (Issue 3)**: `process_user_message` now detects non-confirmation new commands while a queue is active and auto-clears the queue with a cancellation notice.
- **Confirmation Callback Skip Logic (Issue 2)**: 'no' button in one-by-one flow now edits prior message to show skip status and immediately presents next event.

### Fixed
- **Broken One-by-One Flow (Issues 2 & partial 6)**: Prevents duplicate persistent keyboards by always removing reply_markup on confirmation/skip actions; resolves regression where 'no' would cancel entire operation or repeat same event.

### Technical Details
- **routes.py**: Added fresh-command detection; integrated skip handling branch; ensured reply_markup cleared on 'no'.
- **event_queue_handler.py**: Added queue management helpers (`clear_queue`, `skip_event_and_get_next`).

### Impact
- Stabilizes core interactive multi-event UX ahead of deeper dispatcher refactor; reduces user friction and accidental cancellation; groundwork for full Issue 6 button persistence audit.

## [0.1.51] - 2025-08-11

### Changed
- **Query Intent Formatting Unification (Issue 4)**: Replaced legacy conditional titles and any AI-dependent formatting with strict MessageFormatter usage for single and multi-event query responses in `routes.py`.

### Technical Details
- **routes.py**: Query branch now always uses `format_single_event_display` / `format_event_list_display`; consistent header `Found X events:` (singular and plural variants) ensuring BOT_RULES compliance (hyperlinks, full dates, calendar names).

### Impact
- Eliminates formatting inconsistency between query responses and other intents; sets foundation for removing deprecated formatting in `ui_helpers.py` later in refactor plan.

## [0.1.52] - 2025-08-11

### Added
- **Limit/Order Query Support (Issue 1)**: Added `limit` & `order` extraction examples to `intent_extraction_prompt.py` and applied post-fetch ordering/limiting in `google_calendar.query_events` (supports phrases like "last 3", "next 5").

### Changed
- **Query Event Processing**: `google_calendar.query_events` now applies optional descending ordering and truncation after aggregation across calendars to preserve correctness.

### Consolidated Progress (Issues 1–4)**
- Issue 1: Limit/order implemented.
- Issue 2 & 3: (Previously in 0.1.50) Skip & queue clear already active.
- Issue 4: (Previously in 0.1.51) Unified formatter usage for query intent.

### Technical Details
- **google_calendar.py**: Added limit/order post-sort logic.
- **intent_extraction_prompt.py**: Extended prompt patterns & examples for LLM to emit `limit` & `order` fields.

### Impact
- Users can now request relative subsets ("last 2", "next 5") with deterministic ordering; groundwork for adding tests (`test_intent_limit_order.py`).

## [0.1.53] - 2025-08-11

### Changed
- Deprecated and removed `ui_helpers.py`; all formatting centralized in `MessageFormatter`.
- Updated success message construction for updates to use `updated_event` returned from calendar service ensuring displayed times, names, and calendar reflect final state.

### Updated Tests
- Refactored legacy tests importing `ui_helpers` to use `MessageFormatter` (message consistency, inline keyboards, delete scenarios, batch formatting, critical UX fixes).
- Simplified/removed calendar name cleaning expectations; names now preserved exactly as provided by API.

### Impact
- Eliminates drift between different formatting utilities and reduces risk of stale success messages.
- Establishes single source of truth for event/list/confirmation/success formatting ahead of future dispatcher refactor.

## [0.1.54] - 2025-08-11

### Fixed
- Corrected indentation logic regression in `event_queue_handler.process_queue_response` introduced during one-by-one flow enhancement.

### Added
- Introduced `format_decision_appendix` and time change summarization helpers in `MessageFormatter` to support upcoming Issues 9, 10, 11 (decision history, before→after diffs, concise change tokens).

### Impact
- Restores functional queue progression and prepares standardized diff/decision annotations for remaining immediate changes.


## [0.1.47] - 2025-08-11

### Fixed
- **Critical: Undefined Variable Crash**: Removed erroneous reference to `ai_response` after update/delete execution path without confirmation causing 500 errors in query operations.

### Technical Details
- **routes.py**: Eliminated dangling `ai_response` add_message call in non-AI branch; logic now returns early after completing update/delete action.

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