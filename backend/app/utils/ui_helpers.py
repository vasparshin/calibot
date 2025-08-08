"""
CaliBOT UI Helper Functions

Centralized formatting functions to ensure consistent user-facing messages
following BOT_RULES.md specifications.
"""
from datetime import datetime
import re

def format_event_title(title):
    """Format event title with proper capitalization"""
    if not title:
        return "Untitled Event"
    
    # Capitalize first letter of each word
    return title.title()

def get_calendar_display_name(calendar_id, calendar_service=None):
    """Get proper calendar display name, not technical name"""
    if not calendar_id:
        return "Unknown Calendar"
    
    # Handle common calendar IDs
    if calendar_id == 'primary':
        return "Personal"
    
    # If we have calendar service, try to get actual name
    if calendar_service and hasattr(calendar_service, 'calendar_agent'):
        calendar_info = calendar_service.calendar_agent.get_calendar_info(calendar_id)
        if calendar_info and calendar_info.get('name'):
            display_name = calendar_info['name']
            
            # Clean up technical names
            if '@' in display_name:
                if 'group.calendar.google.com' in display_name:
                    return 'Shared Calendar'
                elif display_name == 'zoutna@gmail.com':
                    return 'Personal'
                else:
                    # Extract name before @ and clean it up
                    name = display_name.split('@')[0].replace('.', ' ').title()
                    return name
            return display_name
    
    # Fallback for known patterns
    if '@' in calendar_id:
        if 'group.calendar.google.com' in calendar_id:
            return 'Shared Calendar'
        else:
            return calendar_id.split('@')[0].replace('.', ' ').title()
    
    return calendar_id

def format_date_full(date_str):
    """Format date in full format: 'Day, Month DD, YYYY'"""
    if not date_str:
        return "Unknown date"
    
    try:
        # Handle different date formats
        if 'T' in date_str:
            # ISO datetime format
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%y', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return date_str  # Return as-is if parsing fails
        
        return date_obj.strftime('%A, %B %d, %Y')
    except:
        return date_str

def format_time_12hour(time_str):
    """Format time in 12-hour format with AM/PM"""
    if not time_str:
        return "Unknown time"
    
    try:
        if 'T' in time_str:
            # ISO datetime format
            time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return time_obj.strftime('%I:%M %p')
        else:
            # Try to parse as time only
            time_obj = datetime.strptime(time_str, '%H:%M')
            return time_obj.strftime('%I:%M %p')
    except:
        return time_str

def format_event_for_display(event_data, calendar_result=None, calendar_service=None):
    """
    Format event information consistently for user messages
    Following BOT_RULES.md format:
    • [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
    """
    # Format title with proper capitalization
    title = format_event_title(event_data.get('event_name', 'Untitled Event'))
    
    # Format date
    date_str = "Unknown date"
    date_value = event_data.get('date')
    if not date_value and event_data.get('start_time') and 'T' in str(event_data.get('start_time')):
        # Extract date from start_time ISO string
        try:
            start_dt = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
            date_value = start_dt.strftime('%Y-%m-%d')
        except:
            pass
    
    if date_value:
        date_str = format_date_full(date_value)
    elif event_data.get('start_time') and 'T' in str(event_data.get('start_time')):
        # Fallback: extract date from start_time
        try:
            start_dt = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
            date_str = start_dt.strftime('%A, %B %d, %Y')
        except:
            pass
    
    # Format times
    start_time = event_data.get('start_time', '')
    end_time = event_data.get('end_time', '')
    
    time_str = "Unknown time"
    if start_time and end_time:
        start_formatted = format_time_12hour(start_time)
        end_formatted = format_time_12hour(end_time)
        time_str = f"{start_formatted} - {end_formatted}"
    elif start_time:
        time_str = format_time_12hour(start_time)
    
    # Get proper calendar name
    calendar_name = get_calendar_display_name(
        event_data.get('calendar_name') or event_data.get('calendar_id', 'primary'),
        calendar_service
    )
    
    # Create hyperlink if available
    if calendar_result and calendar_result.get('event_link'):
        clickable_title = f"[{title}]({calendar_result['event_link']})"
        return f"• {clickable_title} on {date_str} at {time_str} ({calendar_name})"
    else:
        return f"• {title} on {date_str} at {time_str} ({calendar_name})"

def format_event_list_item(event, index, include_calendar=True):
    """
    Format event for list display
    Format: 1. Event Name - Day Mon DD, HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
    """
    title = format_event_title(event.get('summary', 'Untitled'))
    
    # Extract date and time from event
    start_time = event.get('start', '')
    end_time = event.get('end', '')
    
    # Format date (shorter format for lists)
    date_str = ""
    if start_time:
        try:
            if 'T' in start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date_str = start_dt.strftime('%a %b %d')
            else:
                date_obj = datetime.fromisoformat(start_time)
                date_str = date_obj.strftime('%a %b %d')
        except:
            date_str = "Unknown date"
    
    # Format times
    time_str = ""
    if start_time and end_time:
        start_formatted = format_time_12hour(start_time)
        end_formatted = format_time_12hour(end_time)
        time_str = f"{start_formatted} - {end_formatted}"
    elif start_time:
        time_str = format_time_12hour(start_time)
    
    # Build the formatted string
    result = f"{index}. {title}"
    if date_str and time_str:
        result += f" - {date_str}, {time_str}"
    elif time_str:
        result += f" - {time_str}"
    
    # Add calendar name if requested
    if include_calendar:
        calendar_name = event.get('calendar_name', 'Unknown')
        result += f" ({calendar_name})"
    
    return result

def format_success_message(operation, count, events=None, date=None):
    """Format success messages consistently"""
    if operation == "create":
        if count == 1:
            return f"Successfully created 1 event:\n\n"
        else:
            return f"Successfully created {count} events:\n\n"
    elif operation == "update":
        if date:
            return f"Successfully updated all {count} events on {format_date_full(date)}:\n\n"
        else:
            return f"Successfully updated {count} event(s):\n\n"
    elif operation == "delete":
        if date:
            return f"Successfully deleted all {count} events on {format_date_full(date)}!"
        else:
            return f"Successfully deleted {count} event(s)!"
    
    return f"Successfully {operation}d {count} event(s)!"

def format_confirmation_message(operation, count, events):
    """Format confirmation messages consistently"""
    action_verb = operation
    if operation == "delete":
        action_verb = "delete"
    elif operation == "update":
        action_verb = "update"
    
    message = f"Found {count} events to {action_verb}:\n\n"
    
    # Add event list
    for i, event in enumerate(events[:10], 1):  # Limit to 10 events for readability
        message += format_event_list_item(event, i) + "\n"
    
    if len(events) > 10:
        message += f"... and {len(events) - 10} more events\n"
    
    message += f"\nChoose an option:\n"
    message += f"• 'one' or '1' - Review and {action_verb} one by one\n"
    message += f"• 'all' or 'yes' - {action_verb.title()} all events now\n"
    message += f"• 'cancel' or 'c' - Cancel operation"
    
    return message

def format_duplicate_message(duplicates):
    """Format duplicate detection message"""
    count = len(duplicates)
    message = f"Found {count} potential duplicate event(s):\n\n"
    
    for dup in duplicates[:5]:  # Show first 5 duplicates
        event = dup["new_event"]
        event_name = format_event_title(event.get("event_name", "Event"))
        start_time = format_time_12hour(event.get("start_time", ""))
        date = format_date_full(event.get("date", ""))
        message += f"• {event_name} at {start_time} on {date}\n"
    
    if count > 5:
        message += f"... and {count - 5} more duplicates\n"
    
    message += f"\nDo you want to create duplicate events?\n"
    message += f"• 'yes' - Create all events anyway\n"
    message += f"• 'no' or 'cancel' - Cancel creation"
    
    return message

def is_confirmation_yes(text):
    """Check if user input is a positive confirmation"""
    if not text:
        return False
    
    text = text.strip().lower()
    return text in ["yes", "y", "confirm", "ok", "proceed", "all"]

def is_confirmation_no(text):
    """Check if user input is a negative confirmation"""
    if not text:
        return False
    
    text = text.strip().lower()
    return text in ["no", "n", "cancel", "stop", "abort", "c"]

def format_no_events_message(event_data):
    """Format message when no events are found"""
    search_criteria = []
    if event_data.get("event_name"):
        search_criteria.append(f"name '{event_data['event_name']}'")
    if event_data.get("date"):
        date_str = format_date_full(event_data["date"]) if event_data["date"] else event_data["date"]
        search_criteria.append(f"date {date_str}")
    
    criteria_text = " and ".join(search_criteria) if search_criteria else "your criteria"
    return f"No events found matching {criteria_text}."

def is_confirmation_one(text):
    """Check if user input requests one-by-one processing"""
    if not text:
        return False
    
    text = text.strip().lower()
    return text in ["one", "1", "individual", "step"]
