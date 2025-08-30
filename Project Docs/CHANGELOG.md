# CaliBOT Changelog

CHANGELOG RULES - BE SPECIFIC AND TECHNICAL

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

### 🔧 **SCHEDULE QUERY PATTERN FIX**

**calibot/backend/app/services/schedule_service.py: detect_schedule_query()**: Expanded pattern matching for schedule queries to handle common variations:
- Added support for "whats on today" (without apostrophe)
- Added support for "whats on tomorrow" (without apostrophe)
- Added support for "todays schedule" and "tomorrows schedule" (possessive without apostrophe)
- Added support for "what's today" and "whats today" variations
- Added support for "what's tomorrow" and "whats tomorrow" variations

**calibot/pyproject.toml**: Incremented version from '0.1.184' to '0.1.185'

**calibot/backend/app/__init__.py**: Incremented __version__ from '0.1.184' to '0.1.185'

### 📈 Impact:
- **Fixed critical AttributeError**: Eliminated "'ScheduleService' object has no attribute 'detect_schedule_query'" errors
- **Fixed critical AttributeError**: Eliminated "'TelegramBotService' object has no attribute 'edit_message_text'" errors
- **Fixed unknown callback data**: Added support for multi-event operation callbacks
- **Enhanced schedule query detection**: Now recognizes "whats on today", "whats on tomorrow", and similar natural language variations
- **Improved user experience**: Schedule queries bypass expensive LLM processing for faster response times
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
