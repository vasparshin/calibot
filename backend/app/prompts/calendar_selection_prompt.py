"""
Calendar selection prompt for AI-powered calendar suggestion.
"""

def get_calendar_selection_prompt(calendar_options, event_data):
    """Generate AI prompt for calendar selection based on event content and available calendars"""
    
    return f"""You are a calendar organization expert. Based on the event details and available calendars, select the most appropriate calendar.

Available Calendars:
{calendar_options}

Rules:
1. Match event content with calendar themes/names
2. Consider calendar purpose (work, personal, sports, etc.)
3. If no clear match, prefer primary calendar
4. Return only the calendar ID, nothing else

Event to analyze: {event_data}

Respond with only the calendar ID (e.g., "primary" or the specific calendar ID)."""
