# CaliBOT User Interface Rules

This document defines the consistent formatting and behavior rules for CaliBOT responses to ensure a professional and consistent user experience.

## Message Formatting Standards

### Event Display Format (MANDATORY)
All event displays must follow this exact format:
```
• [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
```

**Example:**
```
• [Lesson](https://calendar.google.com/event/...) on Saturday, August 09, 2025 at 08:00 AM - 09:00 AM (Tonya)
```

**Required Components:**
1. **Event Name**: ALWAYS capitalize first letter of each word
2. **Hyperlink**: Event name must be clickable link to calendar event
3. **Date**: Full format "Day, Month DD, YYYY" 
4. **Time**: 12-hour format with AM/PM, include both start and end times
5. **Calendar Name**: Display actual calendar name (e.g., "Tonya"), not technical name (e.g., "tonyas calendar")

### Calendar Name Resolution
- **ALWAYS fetch and display the actual calendar display name**
- **NEVER use technical/email-based names in user messages**
- Examples:
  - ✅ Correct: "Tonya", "Personal", "Work Calendar"
  - ❌ Wrong: "tonyas calendar", "user@gmail.com", "group.calendar.google.com"

### Success Messages

#### Event Creation
```
Successfully created {count} event(s):

• [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
• [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
```

#### Event Updates
```
Successfully updated all {count} events on Day, Month DD, YYYY:

Updated [Event Name](link) - description of change
Updated [Event Name](link) - description of change
```

#### Event Deletion
```
Successfully deleted all {count} events on Day, Month DD, YYYY!
```

### Confirmation Messages

#### Multi-Event Operations
```
Found {count} events to {action}:

1. Event Name - Day Mon DD, HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
2. Event Name - Day Mon DD, HH:MM AM/PM - HH:MM AM/PM (Calendar Name)

Choose an option:
• 'one' or '1' - Review and {action} one by one
• 'all' or 'yes' - {Action} all events now
• 'cancel' or 'c' - Cancel operation
```

#### Duplicate Detection
```
Found {count} potential duplicate event(s):

• Event Name at HH:MM AM/PM on Day, Month DD
• Event Name at HH:MM AM/PM on Day, Month DD

Do you want to create duplicate events?
• 'yes' - Create all events anyway
• 'no' or 'cancel' - Cancel creation
```

## User Input Handling

### Confirmation Responses
**Accepted "Yes" responses:**
- "yes", "y", "confirm", "ok", "proceed", "all"

**Accepted "No" responses:**
- "no", "n", "cancel", "stop", "abort", "c"

**Accepted "One-by-one" responses:**
- "one", "1", "individual", "step"

### Date Format Handling
- Support multiple date formats: "tomorrow", "10/08/25", "2025-08-10", "August 10"
- Always convert to consistent internal format
- Always display in full format: "Day, Month DD, YYYY"

## Error Handling Rules

### No Events Found
```
No events found matching your criteria for {date/description}.
```

### Authentication Required
```
To use this bot, please authenticate your Google account: [Click here](auth_url)
```

### Duplicate Confirmation Error
```
Please respond with:
• 'yes' to create duplicate events
• 'no' or 'cancel' to cancel creation
```

## Technical Implementation Rules

### Reusable Functions
All message formatting MUST use these centralized functions:

1. **`format_event_for_user()`** - Single event display
2. **`format_event_list()`** - Multiple event lists  
3. **`format_success_message()`** - Success confirmations
4. **`format_confirmation_message()`** - User confirmations
5. **`get_calendar_display_name()`** - Calendar name resolution

### Calendar Name Fetching
- ALWAYS call `calendar_service.get_calendar_display_name(calendar_id)` 
- Cache calendar names to avoid repeated API calls
- Fallback to "Unknown Calendar" if name cannot be retrieved

### Event Title Capitalization
- Apply title case to all event names before display
- Function: `format_event_title()` should handle capitalization

## User Experience Priorities

1. **Consistency**: All similar operations use identical formatting
2. **Clarity**: Always show complete information (date, time, calendar)
3. **Professionalism**: Proper capitalization and grammar
4. **Accessibility**: Clickable links and clear action options
5. **Reliability**: Robust error handling and confirmation flows

## Future Enhancements

### Inline Keyboard Buttons (Planned)
Replace text-based confirmations with inline keyboard buttons:
- ✅ Yes / ❌ No
- 🔄 All / 1️⃣ One by One / ❌ Cancel
- Implementation: Telegram inline keyboard markup

This will improve user experience by eliminating typing and potential misunderstandings in confirmation flows.
