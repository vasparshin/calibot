# CaliBOT Changelog

CHANGELOG RULES - BE SPECIFIC AND TECHNICAL

## [0.1.189] - 2025-09-01

### 🚨 **CRITICAL BUG FIXES - DELETE OPERATIONS & QUERY FORMATTING**

**calibot/backend/app/operations/delete_operation.py**: Fixed delete operation failing when LLM returns `event_name: "ANY"` for "delete all events" requests
- **Root Cause**: DeleteOperation passed `event_name: "ANY"` to GoogleCalendarService, which searched for events containing "ANY" text, finding nothing
- **Fix Applied**: Added logic to exclude "ANY" from query parameters - only pass event_name filter if not "ANY" or empty
- **Impact**: ✅ Delete operations like "delete all events yesterday" now correctly find and list events for confirmation

**calibot/backend/app/api/routes.py**: Enhanced LLM query formatting prompt with mandatory event format specification
- **Root Cause**: LLM prompt was too vague ("Format appropriately for Telegram") causing inconsistent event formatting
- **Fix Applied**: Added EXACT format specification with examples:
  ```
  CRITICAL: Format ALL events using this EXACT format (MANDATORY):
  • [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
  ```
- **Impact**: ✅ Query responses now consistently match the required format with calendar links and full event details

**calibot/backend/app/services/telegram.py**: Fixed TelegramBotService missing method errors
- **Root Cause**: `send_telegram_message` and `edit_message_text` were standalone functions, but code called them as class methods
- **Fix Applied**: Added wrapper methods to TelegramBotService class:
  - `async def send_telegram_message()` - wraps standalone function
  - `async def edit_message_text()` - wraps standalone function
- **Impact**: ✅ Eliminated "'TelegramBotService' object has no attribute 'send_telegram_message'" errors

### 📝 **VERSION FILES UPDATED**
- **calibot/pyproject.toml**: Version 0.1.188 → 0.1.189
- **calibot/backend/app/__init__.py**: __version__ 0.1.188 → 0.1.189

### 📈 **TECHNICAL IMPACT**
- **Fixed delete operation search**: "delete all events yesterday" now finds events instead of returning "no events found"
- **Standardized query formatting**: All event queries now use consistent format with hyperlinks and full date/time display
- **Eliminated method attribution errors**: Fixed runtime crashes when sending messages or editing keyboards
- **Enhanced user experience**: Multi-event confirmations now display properly formatted event lists

**Testing Required**: Verify delete operations and query formatting in Telegram group chat -4627994150

## [0.1.187] - 2025-01-27

### 🚨 **CRITICAL BUG FIX - SCHEDULE RESPONSES NOT BEING SENT**

**calibot/backend/app/api/routes.py**: Fixed critical bug where schedule responses were generated but never sent to Telegram users

**Root Cause**: In `process_user_message()`, schedule requests were handled and results returned, but the function returned early without calling `send_telegram_message()`

**Fix Applied**: Modified schedule handling to actually send responses to Telegram:
- Added `await send_telegram_message(chat_id, schedule_result["message"])` for successful responses
- Added error message sending for failed schedule requests
- Changed return value from schedule result to `{"status": "ok"}` for proper webhook handling

**Impact**: 
- ✅ **Fixed**: Users now receive schedule responses in Telegram
- ✅ **Fixed**: Schedule queries like "whats the schedule tomorrow" now work correctly
- ✅ **Fixed**: Error messages are properly sent to users for failed requests

**Testing Required**: Verify schedule requests now send responses to Telegram group chat -4627994150

### 📝 **VERSION FILES UPDATED**
- **calibot/pyproject.toml**: Version 0.1.186 → 0.1.187
- **calibot/backend/app/__init__.py**: __version__ 0.1.186 → 0.1.187

## [0.1.183] - 2025-01-27

### DOCUMENTATION MODIFICATIONS

calibot/Project Docs/CHANGELOG_BACKUP_v0.1.182.md: Created backup of previous changelog (1668 lines)

.cursorrules: Consolidated PROJECT_RULES.md content into single source

calibot/tests/README.md: Updated references to .cursorrules

calibot/scripts/README.md: Updated references to .cursorrules

calibot/pyproject.toml: Version 0.1.182 → 0.1.183

calibot/backend/app/__init__.py: Version 0.1.182 → 0.1.183

### 🔧 **CRITICAL BUG FIXES**

**calibot/backend/app/services/schedule_service.py**: Added missing `detect_schedule_query()` method with pattern matching for "today", "tomorrow", "day after tomorrow", "next week" queries

**calibot/backend/app/core/base_handler.py**: Fixed `edit_message()` method to use global `edit_message_text()` function instead of non-existent `telegram_service.edit_message_text()` method

**calibot/backend/app/core/confirmation_handler.py**: Fixed `edit_message()` method to use global `edit_message_text()` function instead of non-existent `telegram_service.edit_message_text()` method

**calibot/backend/app/api/routes.py**: Added missing callback handlers for multi-event operations:
- Added support for "update_one_by_one" callback
- Added support for "confirm_update_X" callback pattern
- Added `handle_multi_event_callback()` function

**calibot/pyproject.toml**: Incremented version from '0.1.183' to '0.1.184'

**calibot/backend/app/__init__.py**: Incremented __version__ from '0.1.183' to '0.1.184'

### 📈 Impact:
- **Fixed critical AttributeError**: Eliminated "'ScheduleService' object has no attribute 'detect_schedule_query'" errors
- **Fixed critical AttributeError**: Eliminated "'TelegramBotService' object has no attribute 'edit_message_text'" errors
- **Fixed unknown callback data**: Added support for multi-event operation callbacks
- **Improved error handling**: Proper callback processing for one-by-one and confirmation operations
- **Enhanced stability**: Bot can now handle schedule queries and button interactions without crashes

## CHANGELOG STANDARDS (MANDATORY)

### AVOID Vague Statements:
- 'Fixed the issue' → INSTEAD: 'Updated GoogleCalendarService.query_events() to include q parameter for text search'
- 'Improved performance' → INSTEAD: 'Added Redis caching to reduce database queries by 40%'

### REQUIRED Format:
'[Component].[Method/Function/File]: [Specific Technical Change]'

### Impact Statements:
- Quantify changes: 'Reduced response time by 30%', 'Fixed 5 edge cases'
- Technical metrics: 'Decreased webhook processing from 2.1s to 0.8s'

### Version Format:
- Semantic versioning: X.Y.Z (Major.Minor.Patch)
- Major (X): Breaking changes, API changes
- Minor (Y): New features, enhancements
- Patch (Z): Bug fixes, documentation updates
