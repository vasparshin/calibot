# CaliBOT Changelog

All notable changes to the CaliBOT project are documented here in reverse chronological order.

## [Unreleased]

## [0.1.107] - 2025-01-13

### Fixed
- **CRITICAL: Route Bypass Bug**: Fixed fallback confirmation logic that was preventing multi-event handlers from being called
- **Handler Execution Flow**: Moved proper handler call to correct location in routes.py logic flow
- **Target Selection Integration**: Now update/delete operations with confirmation properly flow through multi-event handlers with fixed "last 3" parsing

### Technical Details
- **routes.py**: Fixed duplicate handler calls and moved `process_update_delete_with_confirmation` to proper location in confirmation logic
- **Root Cause**: Simple confirmation fallback was running before multi-event handlers, bypassing all target selection logic
- **Impact**: Now "last 3" operations will properly call `_find_matching_events` with fixed boolean logic and target parsing

## [0.1.106] - 2025-01-13

### Enhanced
- **Critical Debugging: Handlers.py Call Chain**: Added comprehensive debug logging to verify if handlers.py is being called for update operations
- **Handler Execution Tracking**: Enhanced logging shows if `process_update_delete_with_confirmation` is invoked and what it returns

### Technical Details
- **handlers.py**: Added detailed debug output to track handler execution and results
- **Investigation Support**: Logs will show if handler chain is working or if there's a bypass in the routes.py logic
- **Debug Output**: Confirms handler invocation, operation processing, and return values

## [0.1.105] - 2025-01-13

### Fixed
- **CRITICAL: Missing Handlers Module**: Created missing `backend/app/api/handlers.py` file that was causing import errors
- **Update Operation Flow**: Fixed broken import chain that was preventing multi-event update operations from using proper target selection logic

### Technical Details
- **handlers.py**: Created `process_update_delete_with_confirmation` function that properly calls `multi_event_handler.handle_update_operation`
- **Import Chain**: Fixed broken import in routes.py that was causing multi-event operations to bypass the fixed target parsing logic
- **Integration**: Now update operations properly flow through `_find_matching_events` with fixed "last 3" parsing

## [0.1.104] - 2025-01-13

### Fixed
- **CRITICAL: Last N Events Selection Logic Bug**: Fixed operator precedence bug in target parsing condition that prevented "last 3" from being parsed correctly
- **Target Parsing Condition**: Fixed `if target and not isinstance(count, int) or count == 1:` to `if target and (not isinstance(count, int) or count == 1):`

### Technical Details
- **multi_event_operations.py**: Fixed boolean logic that was causing "last 3" to select 4 events instead of 3
- **Root Cause**: Operator precedence made condition evaluate incorrectly, bypassing numeric target parsing
- **Impact**: Now "last 3 lessons" will correctly select exactly 3 events instead of 4

## [0.1.103] - 2025-01-13

### Enhanced
- **Critical Debugging: Multi-Event Target Selection**: Added comprehensive debug logging for "last 3" target parsing and event selection
- **Event Filtering Debug**: Enhanced logging to track target parsing, count extraction, and final selection results

### Technical Details
- **multi_event_operations.py**: Added detailed debug output for target parsing ("last 3" -> target: "last", count: 3)
- **Selection Process**: Enhanced logging shows total events found, target applied, and final count selected
- **Investigation Support**: Logs now clearly show if target filtering is working correctly for user confirmation process

## [0.1.102] - 2025-01-13

### Enhanced  
- **Critical Debugging: Enhanced LLM Intent Extraction Logging**: Added comprehensive debug logging to track "last 3" target extraction issues
- **Debugging Infrastructure**: Added critical debug logging to verify if LLM correctly extracts numeric targets like "last 3"

### Technical Details
- **nlp_agent.py**: Added enhanced target field debugging with specific "last 3" detection logging
- **Investigation Focus**: Determine if issue is in LLM extraction vs backend processing by monitoring production logs for actual extracted JSON
- **Debug Output**: Logs now show full JSON, target value, and numeric presence for "last" operations

## [0.1.101] - 2025-01-13

### Fixed
- **CRITICAL: Last N Events Selection Bug**: Fixed "last 3 lessons" selecting 4 events instead of 3 by changing event filtering order
- **Event Query Logic**: Removed premature Google Calendar API filtering to ensure proper chronological target selection
- **Multi-Event Target Processing**: Now gets ALL events first, then filters by name, then applies target selection correctly

### Technical Details
- **multi_event_operations.py**: Removed `query_params['q'] = criteria['event_name']` to prevent Google Calendar from pre-filtering events
- **Selection Algorithm**: Changed to: 1) Get all events for date, 2) Filter by event name locally, 3) Apply target selection (last/first N)
- **Chronological Accuracy**: "last 3 lessons" now correctly selects the 3 most recent lesson events, not all lesson events
- **Validation**: Added comprehensive test demonstrating correct selection from 5 total events (4 lessons) -> exactly 3 selected

## [0.1.100] - 2025-01-11

### Fixed
- **CRITICAL: Target Count Parsing Bug**: Fixed "last 3" being interpreted as 4 events by adding numeric extraction from target strings
- **CRITICAL: Missing Hyperlinks in Success Messages**: Fixed success messages not showing clickable links by checking multiple link field names
- **Target Selection Logic**: Added regex parsing to extract count from target expressions like "last 3", "first 2", "next 4"
- **Event Link Resolution**: Enhanced link field checking to support htmlLink, link, and calendar_link field variations

### Technical Details
- **multi_event_operations.py**: Added regex-based target parsing to extract numeric counts from target strings
- **multi_event_operations.py**: Enhanced event link resolution to check multiple field names for hyperlinks
- **Validation**: Added comprehensive test suite for target parsing logic covering edge cases
- **Intent Processing**: Now correctly processes "move the last 3 lessons" to select exactly 3 events, not 4

## [0.1.99] - 2025-01-11

### Enhanced
- **CRITICAL: Multi-Event Success Message Formatting**: Fixed poor formatting in batch operation success messages to follow BOT_RULES.md standards
- **Button Removal Fix**: Ensured all inline keyboard buttons disappear properly after user selection
- **Event Display Consistency**: Multi-event results now use same format as daily summaries with hyperlinks and full event details

### Technical Details  
- **multi_event_operations.py**: Replaced "Updated [Event]" format with proper BOT_RULES.md compliance: "• [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)"
- **routes.py**: Added missing reply_markup={} to all edit_message_text calls to ensure buttons are removed after selection
- **UX Consistency**: Success messages now include clickable hyperlinks, full calendar names, and proper date/time formatting
- **Validation**: Created comprehensive test suite confirming format compliance and button removal functionality

## [0.1.98] - 2025-08-12

### Optimized
- **CRITICAL: Deployment Size Reduction**: Eliminated ~16MB of unnecessary files from Docker builds
- **Enhanced .dockerignore**: Added comprehensive exclusions for tests/, info/, scripts/, documentation
- **Cleaned Project Root**: Removed misplaced test files that violated project organization rules
- **Binary File Exclusion**: Blocked .mp4 (6MB), .tgz (9MB), .png files from deployments

### Technical Details
- **info/ directory**: 16MB of development assets now excluded from deployments
- **tests/ directory**: 65+ test files no longer deployed to production
- **Documentation**: Only README.md and CHANGELOG.md included in production builds
- **File Organization**: Enforced project rules - no test files in root, all development assets ignored

### Performance Impact
- **Deployment Speed**: Significantly reduced build and transfer times on Render
- **Image Size**: Substantially smaller Docker images
- **Build Efficiency**: Fewer files to process during CI/CD

## [0.1.97] - 2025-08-12

### Fixed
- **CRITICAL: Multi-Event Time Shift Logic**: Fixed "move X events Y hours later" to properly shift both start and end times instead of just extending duration
- **Enhanced Intent Extraction for Time Shifts**: Added explicit rules to distinguish between time shifts vs specific time changes
- **Malformed Time Response Prevention**: Added critical rules to prevent LLM from returning invalid time formats like "6:00 PM, 7:00 PM, 8:00 PM"

### Technical Details
- **intent_extraction_prompt.py**: Added specific examples and rules for time shifts vs specific time changes
- **multi_event_operations.py**: Fixed time shift logic to move both start/end times by delta instead of extending duration
- **Root Cause**: LLM was confused between shifting multiple events vs setting multiple specific times

## [0.1.96] - 2025-08-12

### Fixed
- **CRITICAL: Simplified Intent Extraction Prompt**: Reduced overly complex prompt that was causing LLM to return partial responses
- **Enhanced Response Cleaning**: Added aggressive cleaning for markdown, JSON tags, and extra quotes
- **Token Optimization**: Reduced max_tokens from 800 to 200 for focused JSON responses
- **Temperature Adjustment**: Changed from 0.0 to 0.1 to prevent model getting stuck on malformed outputs

### Confirmed Working
- ✅ **"today schedule" Query Intent**: Now correctly detected as query instead of create intent - DO NOT MODIFY query keywords in fallback logic

### Technical Details
- **intent_extraction_prompt.py**: Simplified from 88 lines to 20 lines, removed excessive examples and warnings
- **nlp_agent.py**: Enhanced response cleaning, better malformed response detection, optimized LLM parameters
- **Root Cause**: Overly complex prompt was causing model to return truncated responses like '"intent"'

## [0.1.95] - 2025-08-12

### Fixed
- **CRITICAL: Schedule Keyword Conflict**: Removed 'schedule' from create intent keywords to prevent "today schedule" being misclassified as create
- **Fallback Logic Priority**: Reordered keyword checks to prioritize query detection over create detection
- **Malformed Response Handling**: Fixed both early detection and exception handler fallback logic

### Technical Details
- **nlp_agent.py**: Removed 'schedule' from create intent patterns in both malformed response handler and exception fallback
- **Keyword Priority**: Query keywords ('today', 'schedule', 'agenda', 'list', 'show') now checked before create keywords
- **Consistent Logic**: All three fallback locations now use same prioritized keyword matching

## [0.1.94] - 2025-08-12

### Fixed
- **CRITICAL: Intent Detection for Queries**: Fixed "today schedule" being incorrectly detected as 'create' instead of 'query'
- **Missing Function Parameter**: Fixed `create_single_event() missing 1 required positional argument: 'conversation_state'`
- **LLM Malformed Response Handling**: Added immediate handling for partial LLM responses like '"intent"' before JSON parsing
- **Fallback Intent Detection**: Enhanced fallback logic to properly detect query intents with keywords like 'schedule', 'agenda', 'list', 'show'

### Enhanced  
- **Robust Error Handling**: Added early detection of malformed LLM responses to prevent JSON parsing failures
- **Intent Classification**: Improved keyword-based fallback for both main and exception handlers
- **Event Display**: Simplified event formatting in single_creation.py to remove dependency on removed formatter function

### Technical Details
- **nlp_agent.py**: Added malformed response detection before JSON parsing, enhanced query keyword detection
- **single_creation.py**: Removed formatter_fn parameter and implemented inline event formatting
- **routes.py**: Function call now matches updated signature

## [0.1.93] - 2025-08-12

### Fixed
- **CRITICAL: Count Extraction Logic Position**: Moved count and time shift extraction to final processing stage to prevent override
- **Multi-Event NLP Fallback Flow**: Fixed count extraction being overridden by later target extraction logic
- **Time Shift Pattern Enhancement**: Added "late" pattern support for "1 hr late" variations
- **Debug Logging Enhancement**: Added comprehensive debug logging with fire markers for count extraction troubleshooting

### Enhanced
- **Final Stage Processing**: Count extraction now happens at the very end of fallback processing
- **Pattern Recognition**: Enhanced time shift patterns to include "late", "later", "forward", "ahead"
- **Comprehensive Debugging**: Added step-by-step logging for count and time shift extraction
- **Override Prevention**: Restructured fallback logic to prevent count field from being lost

### Technical Details
- **backend/app/agent/nlp_agent.py**: Moved count extraction to final processing stage after all other extractions
- Removed duplicate count extraction code that was being overridden
- Enhanced debug logging with fire emoji markers for troubleshooting

## [0.1.92] - 2025-08-12

### Fixed
- **CRITICAL: Multi-Event Count Extraction Bug**: Fixed "move the last 3 lessons 1 hr later" only processing 1 event instead of 3
- **Count Detection in NLP Fallback**: Added enhanced debugging and improved count extraction patterns in update intent fallback
- **Multi-Event Operations Selection**: Enhanced _find_matching_events with count-based chronological selection logic
- **Success Message Hyperlink Preservation**: Restructured multi-event success messages to prevent markdown link breaking
- **Target-Based Event Selection**: Implemented last/first/next selection with proper chronological sorting

### Enhanced
- **Count Pattern Recognition**: Robust extraction of "last 3", "first 2", "next 5" with comprehensive regex patterns
- **Written Number Support**: Detection of "last three", "first two" using written number mapping
- **Time Shift Extraction**: Enhanced patterns for "1 hr later", "30 minutes earlier" with direction handling
- **Multi-Event Debugging**: Added extensive logging with fire markers for count extraction troubleshooting
- **Edge Case Handling**: Proper handling when requesting more events than available

### Technical Details
- **backend/app/agent/nlp_agent.py**: Enhanced update intent fallback with comprehensive count and time shift extraction
- **backend/app/services/multi_event_operations.py**: Added count-based event selection and chronological sorting
- **Success Message Format**: Changed to multi-line format preserving hyperlinks and improving readability

## [0.1.91] - 2025-08-12

### Fixed
- **🔧 CRITICAL: Time Extraction in Updates**: Fixed "change the last lesson to 7pm" not extracting the new time properly
- **LLM Fallback Time Parsing**: Added comprehensive time extraction patterns to NLP agent fallback system
- **Update Operation Time Changes**: Multi-event operations now properly process new_start_time and new_end_time fields
- **Confirmation Message Details**: Update confirmations now show proposed time changes (e.g., "change time to 7:00 PM - 8:00 PM")
- **Summary Message Accuracy**: Update summaries now display actual time changes made (e.g., "changed time to 7:00 PM - 8:00 PM")

### Enhanced
- **Time Format Support**: Robust parsing of "7pm", "19:00", "7:30pm", etc. in update requests
- **12-Hour Display Format**: User-friendly time display in confirmations and summaries
- **Fallback Intelligence**: Enhanced NLP agent fallback with regex patterns for time extraction
- **Update Descriptions**: Detailed change descriptions in both confirmation and summary messages

### Technical Details
- **backend/app/agent/nlp_agent.py**: Added time extraction patterns to update intent fallback
- **backend/app/services/multi_event_operations.py**: Added support for new_start_time/new_end_time fields in update processing and message generation

## [0.1.90] - 2025-08-12

### Fixed
- **🔧 CRITICAL FIXES**: Resolved LLM parsing, calendar API, and confirmation message issues
- **LLM Parsing Error**: Fixed 'Error extracting intent: AND END WITH' by removing problematic instruction
- **Calendar API 404 Errors**: Fixed HttpError 404 when requesting calendars by using proper query_events() method
- **Summary Messages Disappearing**: Fixed confirmation callback indentation issue in routes.py

### Technical Details
- **backend/app/prompts/intent_extraction_prompt.py**: Removed 'START YOUR RESPONSE WITH { AND END WITH }' instruction
- **backend/app/services/multi_event_operations.py**: Fixed _find_matching_events() to use query_events() method and added helper methods
- **backend/app/api/routes.py**: Fixed confirmation callback indentation for proper cancellation handling

## [0.1.89] - 2025-08-12

### Added
- **📅 Today's Schedule Button**: New inline keyboard with "Today's Schedule" and "Tomorrow's Schedule" buttons
- **Direct Schedule Service**: New ScheduleService that bypasses LLM for fast, reliable schedule queries
- **Enhanced /today Command**: Shows schedule with interactive menu keyboard for quick access
- **Optimized Date Formatting**: Clean dd/mm/yy format and time-only display for same-day events
- **Relative Date Support**: Handle "day after tomorrow", "next week", and other relative date expressions

### Enhanced 
- **Performance Optimization**: Schedule queries now skip LLM processing for instant responses
- **User Experience**: Chronologically sorted events with proper time formatting (no date needed for same-day)
- **Response Consistency**: Standardized "Today (12/08/25) you have X events:" format across all date-specific queries
- **Smart Detection**: Automatic recognition of schedule queries in natural language

### Technical Details
- **schedule_service.py**: New service for direct calendar queries with optimized formatting
- **inline_keyboard.py**: Added schedule menu keyboard and callback parsing
- **routes.py**: Integrated schedule detection early in message processing pipeline
- **UI Consistency**: All schedule responses follow BOT_RULES.md formatting with hyperlinks and calendar names

## [0.1.88] - 2025-08-12

### Enhanced
- **Configuration Externalization**: Completed removal of all hardcoded model references from codebase
- **Environment-Driven Architecture**: System now purely environment-configured with no model names in code

### Technical Details
- **ai_service.py**: Updated to use LITELLM_MODEL instead of deprecated OPENAI_MODEL configuration
- **Import Cleanup**: Replaced legacy OPENAI_MODEL imports with environment-driven LITELLM_MODEL
- **Function Updates**: Updated both get_ai_response and get_small_talk_response to use external model configuration
- **Consistency Achievement**: All LLM services now use unified environment-based model configuration approach

## [0.1.87] - 2025-08-12

### Fixed
- **CRITICAL: LLM Reliability Focus**: Completely refactored to prioritize LLM accuracy over fallback dependency
- **Model Correction**: Fixed model name from "gpt-4.1-mini" to correct "gpt-4o-mini" 
- **Clean LLM Call**: Removed problematic parameters that were causing malformed responses
- **Simplified JSON Parsing**: Streamlined parsing to expect proper JSON responses from LLM
- **Temperature Optimization**: Set temperature to 0.0 for maximum response consistency

### Enhanced
- **Primary LLM Focus**: System now relies on LLM returning proper JSON instead of fallback logic
- **Better Error Detection**: Enhanced logging to identify when LLM returns malformed responses
- **Response Validation**: Added proper structure validation for parsed JSON responses
- **Secondary Extraction**: Backup JSON extraction for edge cases without complex fallback chains

### Technical Details
- **config.py**: Corrected LITELLM_MODEL to "gpt-4o-mini" (was "gpt-4.1-mini")
- **nlp_agent.py**: Simplified JSON parsing, removed response_format parameter, optimized temperature
- **Architecture**: Prioritizes LLM accuracy with minimal fallback dependency as requested

## [0.1.86] - 2025-08-12

### Fixed
- **CRITICAL: Create/Batch-Create Intent Detection**: Added comprehensive fallback logic for event creation requests
- **Time Parsing for Batch Events**: Enhanced regex patterns to detect multiple times in natural language (e.g., "at 2, 4, 5 and 6pm")
- **Tomorrow Date Handling**: Fixed date extraction for "tomorrow" requests in create intents
- **Calendar Name Extraction**: Added calendar name detection for create requests (Tonya, Personal, etc.)

### Enhanced
- **Batch Creation Fallback**: Intelligent detection of multiple time slots with proper parsing to 24-hour format
- **Natural Language Time**: Support for "at 2, 4, 5 and 6pm" format with proper PM/AM conversion
- **Single Event Creation**: Fallback support for single event creation with time and calendar extraction
- **Debug Logging**: Added comprehensive time parsing debug logs for troubleshooting

### Technical Details
- **nlp_agent.py**: Added create/batch_create detection in exception handler fallback
- **Time Parsing**: Advanced regex patterns for bare numbers + PM/AM suffix detection
- **Event Structure**: Proper start_time/end_time generation for batch events

## [0.1.85] - 2025-08-11

### Fixed
- **CRITICAL: Exception Handler Order Bug**: Fixed duplicate exception handlers where first handler was preventing intelligent fallback
- **Calendar Move Detection**: Moved enhanced fallback logic to the primary exception handler to ensure it executes
- **Update Intent Recognition**: Fixed "move lessons to calendar" requests being misclassified as query intent
- **Target Detection**: Added "all" target detection for batch operations (e.g., "move the lessons")

### Enhanced
- **Calendar Extraction in Fallback**: Complete calendar name extraction with regex patterns in exception handler
- **Comprehensive Fallback**: Enhanced fallback with move, delete, and query intent detection
- **Error Flow**: Streamlined exception handling to ensure intelligent fallbacks always execute

### Technical Details
- **nlp_agent.py**: Moved intelligent fallback logic from unreachable second exception handler to primary handler
- **Bug Root Cause**: Two exception handlers existed, first one caught errors and returned generic query fallback
- **Fix**: Consolidated exception handling with intelligent keyword-based fallback in primary handler

## [0.1.84] - 2025-08-11

### Fixed
- **CRITICAL: LLM Prompt Formatting Issue**: Enhanced intent extraction prompt with specific calendar move examples
- **Response Format Compatibility**: Added graceful fallback for LLM models that don't support response_format parameter
- **Calendar Move Examples**: Added detailed examples for calendar moves in prompt (move lessons to calendar "Tonya")
- **JSON Format Enforcement**: Strengthened prompt with mandatory JSON format requirements

### Enhanced
- **Prompt Robustness**: Added multiple warnings against partial responses like '"intent"' or '"query"'
- **LLM Call Resilience**: Implemented try-catch for response_format parameter with automatic fallback
- **Calendar Move Detection**: Added calendar_name field to required JSON patterns

### Technical Details
- **intent_extraction_prompt.py**: Added specific calendar move examples and stronger JSON format enforcement
- **nlp_agent.py**: Enhanced LLM call with graceful response_format fallback for model compatibility

## [0.1.83] - 2025-08-11

### Fixed
- **CRITICAL: Complete LLM Architecture Refactor**: Fixed malformed LLM responses returning '"intent"' instead of proper JSON
- **LLM Response Quality**: Added temperature=0.1 and response_format parameters to improve JSON consistency
- **JSON Parsing Resilience**: Implemented try_parse_json function with multiple parsing strategies and error recovery
- **Code Cleanup**: Removed all duplicate fallback sections that caused maintenance issues and execution path confusion

### Enhanced
- **LLM Error Detection**: Enhanced detection for invalid responses with specific checks for '"intent"' and 'query' strings
- **Fallback Architecture**: Simplified and consolidated fallback logic to single execution path
- **Error Logging**: Improved error messages with specific detection of malformed LLM responses

### Technical Details
- **nlp_agent.py**: Complete refactor of extract_intent method with new try_parse_json function
- **LLM Call Enhancement**: Added temperature=0.1 and response_format="json_object" for better consistency
- **Architecture Cleanup**: Removed duplicate code sections and streamlined exception handling

## [0.1.82] - 2025-08-11

### Fixed
- **CRITICAL: Root Cause Found and Fixed**: Discovered duplicate fallback sections causing calendar extraction to never execute
- **Calendar Move Functionality**: Added calendar extraction logic to the ACTIVE fallback section (first one)
- **Execution Path Issue**: Fixed code structure where first fallback section was returning early, preventing calendar extraction

### Technical Details
- **nlp_agent.py**: Moved calendar extraction logic from second (unreachable) fallback section to first (active) section
- **Bug Analysis**: Two identical `elif any(word in user_lower for word in ['move', 'update', 'change'])` sections existed
- **Fix**: Added complete calendar extraction logic to the fallback section that actually executes

### Root Cause
- First fallback section (line ~211) was executing and returning immediately
- Second fallback section (line ~469) with calendar extraction was never reached
- Calendar moves failed because `calendar_name` was never extracted into the intent

## [0.1.81] - 2025-08-11

### Debug
- **CRITICAL DEBUG: Intent Extraction Path Investigation**: Added ERROR-level logging to trace calendar extraction execution
- **Root Cause Investigation**: Determine why enhanced calendar extraction logging isn't appearing in production logs
- **Execution Path Tracing**: Identify which fallback path is actually being executed for calendar moves

### Technical Details
- **nlp_agent.py**: Upgraded calendar extraction logging to ERROR level with 🔥 prefixes for visibility
- **Purpose**: Determine if calendar extraction code is being executed at all or if logs are being filtered

## [0.1.80] - 2025-08-11

### Fixed
- **Critical: Success Message URL Consistency**: Fixed MessageFormatter to convert www.google.com URLs to calendar.google.com format
- **Enhanced Intent Extraction Debugging**: Added comprehensive logging to track calendar name extraction in fallback logic
- **Calendar Name Capitalization**: Properly capitalize extracted calendar names (tonya -> Tonya)

### Technical Details
- **message_formatter.py**: Added URL format conversion in create_event_hyperlink method
- **nlp_agent.py**: Enhanced calendar extraction logging with step-by-step pattern testing
- **Root Cause Investigation**: Added detailed logging to identify why calendar_name isn't reaching update_event method

## [0.1.79] - 2025-08-11

### Fixed
- **Critical: Calendar Move Functionality**: Fixed calendar moves failing by adding proper calendar agent initialization and debugging
- **Critical: Intent Extraction Errors**: Enhanced fallback logic to handle malformed LLM responses that return just '"intent"'
- **Critical: Success Message URL Consistency**: Fixed success messages to use same calendar.google.com URL format as "found" messages
- **Enhanced Calendar Lookup**: Added multiple regex patterns for calendar name extraction from user messages
- **Better Error Logging**: Added detailed logging for calendar move operations and intent extraction failures

### Enhanced
- **Calendar Agent Integration**: Improved calendar cache loading and calendar ID resolution for moves
- **Message Formatting**: Centralized URL formatting using MessageFormatter utility for consistency
- **Fallback Logic**: Enhanced regex patterns to catch calendar names like "Tonya" in various formats

### Technical Details
- **nlp_agent.py**: Added better malformed response detection and multiple calendar extraction patterns
- **google_calendar.py**: Enhanced calendar move debugging with detailed logging and cache updating
- **multi_event_operations.py**: Switched to centralized MessageFormatter for consistent URL formatting

## [0.1.78] - 2025-08-11

### Fixed
- **REVERTED: OAuth Over-Engineering**: Removed complex OAuth validation that was breaking working authentication
- **Restored Simple OAuth Flow**: Reverted to the simple, working OAuth implementation that worked fine before recent changes
- **Production Authentication**: Authentication should now work as it did before without requiring reauthentication on every restart

### Reverted
- **OAuth Client Validation**: Removed excessive validation that was incorrectly reading Google credentials file
- **State Parameter Strictness**: Made state validation more forgiving for production deployment environments  
- **Complex Error Handling**: Simplified OAuth callback to the working version

### Technical Details
- **google_calendar.py**: Reverted get_auth_url() to simple working version without extra validation
- **OAuth Callback**: Simplified callback handling while maintaining server restart resilience
- **Authentication Flow**: Restored the authentication flow that was working fine on Render before recent commits

### Fixed
- **Critical: OAuth State Management**: Fixed "Invalid state parameter" error caused by server restarts on Render.com
- **Robust OAuth Callback**: OAuth authentication now works despite server restarts between auth URL generation and callback
- **Production-Ready Authentication**: Removed strict state validation dependency for cloud deployment environments

### Enhanced
- **OAuth Resilience**: Authentication continues even when temporary state files are lost due to server restarts
- **Better Error Handling**: More informative error messages during OAuth token exchange process
- **Cleanup Process**: Automatic cleanup of temporary OAuth files after successful authentication

### Technical Details
- **google_calendar.py**: Redesigned OAuth callback to handle missing state files gracefully
- **State Validation**: Made state parameter validation optional for production stability
- **Token Exchange**: Improved error handling and logging during credential exchange process

### Known Issue Resolution
- **Server Restart Impact**: OAuth flow now resilient to Render.com server restarts between auth steps

### Fixed
- **Enhanced OAuth Diagnostics**: Improved OAuth error handling for "flowName=GeneralOAuthFlow" authentication issues
- **OAuth Client Validation**: Added validation to ensure OAuth client is configured as "Web application" type
- **Robust Error Messages**: Better user-facing error messages when OAuth configuration issues occur

### Added
- **OAuth Configuration Validation**: Check if redirect URI matches Google Cloud Console configuration
- **Enhanced Auth Status Endpoint**: Added OAuth client type and redirect URI validation details
- **Fallback Authentication URLs**: Provide alternative authentication paths when OAuth generation fails

### Technical Details
- **google_calendar.py**: Added OAuth client configuration validation and enhanced logging
- **routes.py**: Improved error handling for OAuth URL generation failures
- **OAuth Flow**: Better diagnostics for Google Cloud Console configuration mismatches

### Fixed
- **Critical: OAuth Authentication Error**: Fixed "Required parameter is missing: response_type" error in Google OAuth 2.0 flow
- **Enhanced OAuth Diagnostics**: Added comprehensive OAuth status endpoint and improved error handling
- **Robust Authentication Flow**: Added fallback logic to ensure response_type parameter is included in OAuth URLs

### Added
- **OAuth Status Endpoint**: New `/auth/status` endpoint to diagnose authentication issues and configuration problems
- **OAuth Login Endpoint**: New `/auth/login` endpoint for manual authentication initiation
- **Enhanced OAuth Logging**: Comprehensive logging for OAuth URL generation and callback handling

### Technical Details
- **google_calendar.py**: Enhanced OAuth URL generation with explicit response_type parameter handling
- **routes.py**: Added authentication diagnostic endpoints with proper error handling
- **OAuth Flow**: Improved state management and credential validation with better error messages

### Fixed
- **Critical: Calendar Move Intent Detection**: Enhanced fallback logic in NLP agent to properly extract calendar names from user messages like "move to calendar 'Tonya'"
- **Critical: Confirmation Message Logic**: Fixed multi-event operations confirmation to show proposed changes when calendar moves are detected
- **Enhanced Logging**: Added comprehensive logging to track intent extraction failures and calendar extraction process

### Technical Details
- **nlp_agent.py**: Improved fallback detection with detailed logging for calendar extraction regex patterns
- **multi_event_operations.py**: Fixed confirmation message logic to prioritize showing proposed changes over generic formatting
- **Intent Processing**: Calendar move detection now properly extracts target calendar names and includes them in confirmation messages

### Fixed
- **Critical: Calendar Move Extraction**: Fixed regex pattern to properly extract target calendar from "move to calendar X" commands
- **Critical: Confirmation Messages**: Fixed confirmation messages to show what changes will be made (e.g., "Will move to Tonya calendar")
- **Critical: Success Message Links**: Fixed malformed markdown links in success messages showing proper clickable event names
### Technical Details
- **nlp_agent.py**: Simplified calendar extraction regex to `r'to calendar ["\']([^"\']+)["\']'` for better matching
- **multi_event_operations.py**: Force legacy confirmation path when calendar moves detected to show proposed changes
- **multi_event_operations.py**: Fixed success message link format to use event name and proper URL

## [0.1.72] - 2025-08-11

### Fixed
- **Critical: Intent Detection and Calendar Moves**: Fixed multiple issues causing create/update intents to be misclassified as query and calendar moves to fail
### Added
- **Create Intent Fallback**: Added missing fallback logic for create intents (add, make, create, schedule) with time and calendar extraction
- **Calendar Move Support**: Enhanced update intent fallback to extract target calendar from "move to calendar X" requests  
- **Calendar Move Execution**: Added calendar move functionality to multi-event operations with proper success messages
### Technical Details
- **nlp_agent.py**: Added create intent fallback with regex-based time and calendar extraction
- **nlp_agent.py**: Enhanced update intent fallback to extract calendar_name from "to calendar X" patterns
- **multi_event_operations.py**: Added calendar_name handling in update operations for cross-calendar moves
- **multi_event_operations.py**: Updated success messages to indicate calendar moves ("moved to X calendar")

## [0.1.71] - 2025-08-11

### Fixed
- **Critical: Batch Creation Function Arguments**: Fixed incorrect argument order in process_batch_creation call causing TypeError with missing duplicate_checker parameter
### Technical Details
- **routes.py**: Added missing import for format_event_for_display function
- **routes.py**: Corrected process_batch_creation call to include all 8 required parameters in correct order: formatter_fn, duplicate_formatter_fn, conversation_state, duplicate_checker

## [0.1.70] - 2025-08-11

### Fixed
- **Critical: Import Error in Batch Creation**: Fixed missing import of `format_duplicate_confirmation_with_keyboard` in routes.py causing 500 errors during batch event creation when duplicates are detected
### Technical Details
- **routes.py**: Added missing import `from app.utils.ui_helpers import format_duplicate_confirmation_with_keyboard` to resolve `NameError` in batch creation workflow
- **Issue Resolution**: Batch creation requests were failing with 500 Internal Server Error when duplicate detection was triggered

## [0.1.69] - 2025-08-11

### Fixed
- **Critical: Syntax Error in Event Queue Handler**: Fixed IndentationError and unterminated f-string literal in event_queue_handler.py that was preventing application startup
### Technical Details
- **event_queue_handler.py**: Corrected indentation on lines 509-510 for is_cancel variable assignment
- **event_queue_handler.py**: Fixed unterminated f-string literal on line 524 by properly escaping newline character

## [0.1.68] - 2025-08-11

### Fixed
- Batch multi-time creation fallback not triggering when LLM returned pathological `"intent"` token; parser was never invoked in exception path due to early exception handling. Added invocation of `_parse_simple_batch_create` inside exception fallback block and corrected gating indentation.

### Added
- Unit test `tests/test_simple_batch_parser.py` verifying phrases like "add two lessons today at 5 and 7 pm" produce `batch_create` with correct event count (2–3+).

### Changed
- Improved meridiem inference (unspecified hours 1–11 default to AM, 12/13+ to PM) and broadened initial keyword gate to include 'lesson', 'meet', 'call'. Removed unused count enforcement to stay permissive.

### Technical Details
- `nlp_agent.py`: Fixed indentation of gating logic inside `_parse_simple_batch_create`; added batch parser call in exception handler; adjusted meridiem logic; broadened quick gate keywords.
- `test_simple_batch_parser.py`: New focused test ensuring deterministic batch parsing independent of LLM quality.
- Version bump to 0.1.68 (`pyproject.toml`, `backend/app/__init__.py`).

### Impact
- Restores reliable multi-event creation for common user phrasings even when LLM degrades; prevents silent downgrade to single `query` intent, reducing user friction and re-prompt loops.

## [0.1.65] - 2025-08-11
## [0.1.66] - 2025-08-11
## [0.1.67] - 2025-08-11

### Changed
- Updated legacy UX test (`test_ux_fixes_v041.py`) to reflect new queue navigation keyboard layout (Yes / Skip / Stop All) replacing single-button confirmation.

### Technical Details
- Tests: Adjusted expected inline keyboard JSON to new callback data patterns (`queue_confirm_X`, `queue_skip_X`, `queue_stop_all`).
- Version bump to 0.1.67.

### Impact
- Ensures test suite aligns with refactored callback and navigation system prior to external validation.

### Added
- Rule-based batch create fallback parser in `NLPAgent` to recover from malformed minimal LLM outputs ("intent") for phrases like "add two lessons today at 5 and 7 pm". Automatically produces `batch_create` intent with inferred 1‑hour slots and shared meridiem propagation.

### Fixed
- Multi-event creation prompts incorrectly downgraded to `query` or bare `create` missing times when LLM returned pathological minimal token; now robustly parsed locally before generic keyword fallback.

### Technical Details
- `nlp_agent.py`: Added `_parse_simple_batch_create` with plural normalization, time extraction (infers meridiem, default 1h duration), calendar name capture (Tonya's calendar), invoked at three fallback decision points (initial malformed detection, post-regeneration invalid, multi-JSON failure path).
- Version bump to 0.1.66.

### Impact
- Restores correct batch creation UX without asking for missing start/end times for common multi-time user phrasings; reduces unnecessary clarification loops and improves reliability under degraded LLM responses.

### Changed
- Refactored callback query handling to use `InlineKeyboardHelper.parse_callback_data` enabling unified action mapping (multi_all, multi_one, single, duplicates, queue navigation) while keeping backward compatibility for legacy `confirm_yes/no` patterns.
- Introduced queue navigation keyboard (Yes / Skip / Stop All) replacing legacy single-button confirmation during one-by-one processing.

### Added
- Support for skip action in one-by-one queue mode with proper status messaging and transition to next event.

### Fixed
- Removed brittle if/elif callback chain; reduces risk of inconsistent future button additions. Ensured keyboard removal and status line updates cover new skip path.

### Technical Details
- `routes.py`: Replaced manual callback branching with parsed result; added legacy fallback; extended confirmation handler to handle `skip`.
- `event_queue_handler.py`: Implemented navigation keyboard usage, skip logic, and consistent message returns.
- Version bump to 0.1.65.

### Impact
- More maintainable and extensible callback processing; prepares for further UX refinements (Issue 6 ephemerality audit) with standardized callback schema.

## [0.1.64] - 2025-08-11

### Changed
- Consolidated all confirmation inline keyboards to centralized `InlineKeyboardHelper`; removed legacy `create_confirmation_keyboard` to prevent drift and enforce single-row button layouts per BOT_RULES.

### Fixed
- Residual imports and usages of deprecated keyboard helper in `routes.py`, `update_delete.py`, `ui_helpers.py`, and related tests now migrated to standardized helper methods (multi-event, single-event, duplicate). Resolved indentation issues introduced during refactor.

### Technical Details
- `routes.py`, `handlers/update_delete.py`: Replaced helper calls with `InlineKeyboardHelper` methods (`create_multi_event_confirmation_keyboard`, `create_single_event_confirmation_keyboard`).
- `services/telegram.py`: Removed obsolete `create_confirmation_keyboard` function definition.
- `utils/ui_helpers.py`: Swapped legacy calls for helper-based keyboards while preserving backward compatibility for other legacy helpers.
- Tests (`test_inline_keyboards_and_ui.py`, `test_message_consistency.py`, `test_final_delete_validation.py`): Updated to import and use `InlineKeyboardHelper`; cleaned indentation errors.
- Version bump to 0.1.64 across version files.

### Impact
- Ensures consistent button text, callback data schema, and single-row layouts; reduces maintenance overhead and future inconsistency regressions (Issue 5 completion milestone).

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