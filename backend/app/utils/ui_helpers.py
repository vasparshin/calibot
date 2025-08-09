"""
CaliBOT UI Helper Functions

Centralized formatting functions to ensure consistent user-facing messages
following BOT_RULES.md specifications.
"""
from datetime import datetime
import re
from app.services.telegram import create_confirmation_keyboard, create_event_selection_keyboard

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
    
    # If we have calendar service, try to get actual name from API
    if calendar_service and hasattr(calendar_service, 'get_calendar_display_name'):
        try:
            display_name = calendar_service.get_calendar_display_name(calendar_id)
            return display_name
        except Exception:
            pass  # Fall through to manual parsing
    
    # Try calendar agent method
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
            elif 'calendar' in display_name.lower():
                # Handle "tonyas calendar" → "Tonya"
                clean_name = display_name.lower().replace(' calendar', '').replace('calendar', '').strip()
                return clean_name.title()
            return display_name
    
    # Fallback for known patterns
    if '@' in calendar_id:
        if 'group.calendar.google.com' in calendar_id:
            return 'Shared Calendar'
        else:
            return calendar_id.split('@')[0].replace('.', ' ').title()
    elif '.' in calendar_id and not calendar_id.startswith('http'):
        # Handle patterns like "some.calendar.id"
        return calendar_id.replace('.', ' ').title()
    
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
    # Handle both Google Calendar event format and our internal format
    title = ""
    if 'summary' in event_data:
        # Google Calendar format
        title = format_event_title(event_data.get('summary', 'Untitled Event'))
    else:
        # Our internal format
        title = format_event_title(event_data.get('event_name', 'Untitled Event'))
    
    # Format date - handle multiple possible sources
    date_str = "Unknown date"
    
    # Try Google Calendar format first
    if event_data.get('start', {}).get('dateTime'):
        try:
            start_dt = datetime.fromisoformat(event_data['start']['dateTime'].replace('Z', '+00:00'))
            date_str = start_dt.strftime('%A, %B %d, %Y')
        except:
            pass
    # Try our internal format
    elif event_data.get('date'):
        date_str = format_date_full(event_data['date'])
    elif event_data.get('start_time') and 'T' in str(event_data.get('start_time')):
        try:
            start_dt = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
            date_str = start_dt.strftime('%A, %B %d, %Y')
        except:
            pass
    
    # Format times - handle multiple possible sources
    time_str = "Unknown time"
    
    # Try Google Calendar format
    if event_data.get('start', {}).get('dateTime') and event_data.get('end', {}).get('dateTime'):
        try:
            start_dt = datetime.fromisoformat(event_data['start']['dateTime'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(event_data['end']['dateTime'].replace('Z', '+00:00'))
            start_formatted = start_dt.strftime('%I:%M %p')
            end_formatted = end_dt.strftime('%I:%M %p')
            time_str = f"{start_formatted} - {end_formatted}"
        except:
            pass
    # Try our internal format
    elif event_data.get('start_time') and event_data.get('end_time'):
        start_formatted = format_time_12hour(event_data['start_time'])
        end_formatted = format_time_12hour(event_data['end_time'])
        time_str = f"{start_formatted} - {end_formatted}"
    elif event_data.get('start_time'):
        time_str = format_time_12hour(event_data['start_time'])
    
    # Get proper calendar name
    calendar_id = (
        event_data.get('calendar_id') or 
        event_data.get('calendar_name') or 
        'primary'
    )
    calendar_name = get_calendar_display_name(calendar_id, calendar_service)
    
    # Create hyperlink if available
    event_link = None
    if calendar_result and calendar_result.get('event_link'):
        event_link = calendar_result['event_link']
    elif event_data.get('htmlLink'):
        event_link = event_data['htmlLink']
    
    if event_link:
        clickable_title = f"[{title}]({event_link})"
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

def format_duplicate_confirmation_with_keyboard(duplicates, action="create"):
    """Format duplicate confirmation message with inline keyboard"""
    count = len(duplicates)
    
    message = f"Found {count} potential duplicate event(s):\n\n"
    
    for duplicate_item in duplicates:
        # Handle different data structures
        if isinstance(duplicate_item, dict) and 'new_event' in duplicate_item:
            # New structure from check_for_duplicate_events
            event = duplicate_item['new_event']
            event_name = format_event_title(event.get('event_name', 'Untitled Event'))
            start_time = event.get('start_time', '')
            date = event.get('date', '')
        else:
            # Direct event structure
            event = duplicate_item
            event_name = format_event_title(event.get('summary', event.get('event_name', 'Untitled Event')))
            start_time = event.get('start', {}).get('dateTime', event.get('start_time', ''))
            date = event.get('start', {}).get('dateTime', event.get('date', ''))
        
        # Format time and date
        if start_time:
            if 'T' in start_time:
                # ISO format
                try:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%I:%M %p')
                    formatted_date = dt.strftime('%A, %B %d, %Y')
                except:
                    formatted_time = format_time_12hour(start_time)
                    formatted_date = format_date_full(date) if date else "Unknown date"
            else:
                formatted_time = format_time_12hour(start_time)
                formatted_date = format_date_full(date) if date else "Unknown date"
        else:
            formatted_time = "Unknown time"
            formatted_date = format_date_full(date) if date else "Unknown date"
        
        message += f"• {event_name} at {formatted_time} on {formatted_date}\n"
    
    message += f"\nDo you want to {action} duplicate events?"
    
    keyboard = create_confirmation_keyboard("duplicate")
    return message, keyboard

def format_multi_event_confirmation_with_keyboard(events, action="delete"):
    """Format multi-event confirmation message with inline keyboard"""
    count = len(events)
    
    message = f"Found {count} events to {action}:\n\n"
    
    for i, event in enumerate(events[:10], 1):  # Show first 10
        event_name = format_event_title(event.get('summary', 'Untitled Event'))
        
        # Handle different datetime formats
        start_time = ""
        date_short = ""
        
        if event.get('start', {}).get('dateTime'):
            # Google Calendar format
            try:
                dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                start_time = dt.strftime('%I:%M %p')
                date_short = dt.strftime('%a %b %d')
            except:
                start_time = format_time_12hour(event['start']['dateTime'])
                date_short = event['start']['dateTime'][:10] if event['start']['dateTime'] else ''
        elif event.get('start'):
            # Handle string format
            start_time = format_time_12hour(str(event['start']))
            date_short = str(event['start'])[:10] if str(event['start']) else ''
        
        calendar_name = get_calendar_display_name(event.get('calendar_id', ''))
        message += f"{i}. {event_name} - {date_short} {start_time} ({calendar_name})\n"
    
    if count > 10:
        message += f"... and {count - 10} more events\n"
    
    message += f"\nChoose an option:"
    
    keyboard = create_confirmation_keyboard("multi_event")
    return message, keyboard

def format_event_selection_with_keyboard(events, action="select"):
    """Format event selection message with inline keyboard for individual selection"""
    count = len(events)
    
    message = f"Select which events to {action} ({count} total):\n\n"
    
    keyboard = create_event_selection_keyboard(events)
    return message, keyboard
