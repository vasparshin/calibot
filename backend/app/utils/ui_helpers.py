"""
CaliBOT UI Helper Functions

Centralized formatting functions to ensure consistent user-facing messages
following BOT_RULES.md specifications.

IMPORTANT: New implementations should use message_formatter.py and inline_keyboard.py
for consistent formatting. This file contains legacy functions for backward compatibility.
"""
from datetime import datetime
import re
from app.services.telegram import create_event_selection_keyboard

# Import new centralized formatters
# NO FALLBACK IMPORTS - per PROJECT_RULES.md
from .message_formatter import MessageFormatter
from .inline_keyboard import InlineKeyboardHelper

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
    
    # Handle calendar names (not IDs) directly
    if isinstance(calendar_id, str) and 'calendar' in calendar_id.lower():
        # Handle "tonyas calendar" → "Tonya"
        clean_name = calendar_id.lower().replace(' calendar', '').replace('calendar', '').strip()
        if clean_name == 'tonyas':
            return 'Tonya'
        elif clean_name == 'work':
            return 'Work'
        elif clean_name == 'personal':
            return 'Personal'
        elif clean_name:
            return clean_name.title()
        else:
            return 'Personal'
    
    # If we have calendar service, try to get actual name from API
    if calendar_service and hasattr(calendar_service, 'get_calendar_display_name'):
        try:
            display_name = calendar_service.get_calendar_display_name(calendar_id)
            return display_name
        except Exception:
            # NO MANUAL PARSING - per PROJECT_RULES.md
            # Return calendar ID if name lookup fails
            pass
    
    # Try calendar agent method
    if calendar_service and hasattr(calendar_service, 'calendar_agent'):
        calendar_info = calendar_service.calendar_agent.get_calendar_info(calendar_id)
        if calendar_info and calendar_info.get('name'):
            display_name = calendar_info['name']
            
            # Clean up technical names
            if '@' in display_name:
                if 'group.calendar.google.com' in display_name:
                    return 'Shared Calendar'
                else:
                    # Return actual email address as requested
                    return display_name
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
            # Return actual email address as requested
            return calendar_id
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
            return time_obj.strftime('%H:%M')
        else:
            # NO MANUAL TIME PARSING - per PROJECT_RULES.md
            # LLM should provide properly formatted time data
            return time_str  # Return as-is if LLM provides proper format
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
            start_formatted = start_dt.strftime('%H:%M')
            end_formatted = end_dt.strftime('%H:%M')
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
    """
    Format confirmation messages consistently - UPDATED TO FOLLOW BOT_RULES.md
    CRITICAL: Shows ALL events, never truncates with "... and X more"
    """
    # Use new centralized formatter
    # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
    return MessageFormatter.format_confirmation_message(operation, events, count)

def format_duplicate_message(duplicates):
    """
    Format duplicate detection message - UPDATED TO FOLLOW BOT_RULES.md
    CRITICAL: Shows ALL duplicates, never truncates with "... and X more"
    """
    # Use new centralized formatter
    # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
    return MessageFormatter.format_duplicate_message(duplicates)

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
    import logging
    logger = logging.getLogger(__name__)
    
    count = len(duplicates)
    
    message = f"Found {count} potential duplicate event(s):\n\n"
    
    for duplicate_item in duplicates:
        # CRITICAL FIX: Validate duplicate_item structure before processing
        if not isinstance(duplicate_item, dict):
            logger.warning(f"format_duplicate_confirmation_with_keyboard: Invalid duplicate_item type: {type(duplicate_item)}")
            continue
            
        # Handle different data structures
        if 'existing_event' in duplicate_item:
            # CRITICAL FIX: Use existing_event (from calendar) instead of new_event (from user input)
            # The existing_event has proper hyperlinks and calendar information
            event = duplicate_item['existing_event']
            
            # CRITICAL FIX: Validate event is a dictionary
            if not isinstance(event, dict):
                logger.warning(f"format_duplicate_confirmation_with_keyboard: existing_event is not a dict, type: {type(event)}")
                continue
                
            event_name = format_event_title(event.get('summary', event.get('event_name', 'Untitled Event')))
            
            # CRITICAL FIX: Handle start/end time extraction with proper validation
            start_data = event.get('start', {})
            end_data = event.get('end', {})
            
            # Handle both string and dict formats for start/end times
            if isinstance(start_data, dict) and start_data.get('dateTime'):
                start_time = start_data['dateTime']
                date = start_time
            elif isinstance(start_data, str):
                start_time = start_data
                date = start_time
            else:
                start_time = event.get('start_time', '')
                date = event.get('date', '')
                
            if isinstance(end_data, dict) and end_data.get('dateTime'):
                end_time = end_data['dateTime']
            elif isinstance(end_data, str):
                end_time = end_data
            else:
                end_time = event.get('end_time', '')
            
            # CRITICAL FIX: Get proper calendar name - use same logic as multi-event summaries
            # Problem: Calendar IDs were being confused with calendar names, showing hash IDs
            # Solution: Use MessageFormatter logic for consistent calendar naming
            calendar_id = event.get('calendar_id', event.get('calendar_name', 'primary'))
            calendar_name = get_calendar_display_name(calendar_id)
            
            # Additional fallback: if calendar_name is still a hash-like ID, clean it up
            if calendar_name and len(calendar_name) > 20 and '@' in calendar_name:
                # This is likely a calendar ID, not a display name - extract meaningful part
                if 'group' in calendar_name.lower():
                    calendar_name = 'Group Calendar'
                elif 'primary' in calendar_name.lower():
                    calendar_name = 'Primary Calendar'
                else:
                    calendar_name = 'Shared Calendar'
        else:
            # Direct event structure (fallback)
            event = duplicate_item
            
            # CRITICAL FIX: Validate event is a dictionary
            if not isinstance(event, dict):
                logger.warning(f"format_duplicate_confirmation_with_keyboard: event is not a dict, type: {type(event)}")
                continue
                
            event_name = format_event_title(event.get('summary', event.get('event_name', 'Untitled Event')))
            
            # CRITICAL FIX: Handle start/end time extraction with proper validation
            start_data = event.get('start', {})
            end_data = event.get('end', {})
            
            # Handle both string and dict formats for start/end times
            if isinstance(start_data, dict) and start_data.get('dateTime'):
                start_time = start_data['dateTime']
                date = start_time
            elif isinstance(start_data, str):
                start_time = start_data
                date = start_time
            else:
                start_time = event.get('start_time', '')
                date = event.get('date', '')
                
            if isinstance(end_data, dict) and end_data.get('dateTime'):
                end_time = end_data['dateTime']
            elif isinstance(end_data, str):
                end_time = end_data
            else:
                end_time = event.get('end_time', '')
            
            # CRITICAL FIX: Get proper calendar name - use same logic as multi-event summaries
            calendar_id = event.get('calendar_id', event.get('calendar_name', 'primary'))
            calendar_name = get_calendar_display_name(calendar_id)
            
            # Additional fallback: if calendar_name is still a hash-like ID, clean it up
            if calendar_name and len(calendar_name) > 20 and '@' in calendar_name:
                # This is likely a calendar ID, not a display name - extract meaningful part
                if 'group' in calendar_name.lower():
                    calendar_name = 'Group Calendar'
                elif 'primary' in calendar_name.lower():
                    calendar_name = 'Primary Calendar'
                else:
                    calendar_name = 'Shared Calendar'
        
        # Format time and date
        if start_time:
            if 'T' in start_time:
                # ISO format
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    formatted_start = start_dt.strftime('%H:%M')
                    formatted_date = start_dt.strftime('%A, %B %d, %Y')
                    
                    # Handle end time
                    if end_time and 'T' in end_time:
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        formatted_end = end_dt.strftime('%H:%M')
                        time_display = f"at {formatted_start} - {formatted_end}"
                    else:
                        time_display = f"at {formatted_start}"
                        
                except:
                    formatted_time = format_time_12hour(start_time)
                    formatted_date = format_date_full(date) if date else "Unknown date"
                    time_display = f"at {formatted_time}"
            else:
                formatted_time = format_time_12hour(start_time)
                formatted_date = format_date_full(date) if date else "Unknown date"
                time_display = f"at {formatted_time}"
        else:
            time_display = "at Unknown time"
            formatted_date = format_date_full(date) if date else "Unknown date"
        
        # CRITICAL FIX: Use master formatter for consistent hyperlink formatting
        from app.utils.message_formatter import MessageFormatter
        
        # Build event structure for master formatter
        display_event = {
            'summary': event_name,
            'start': start_time,
            'end': end_time,
            'id': event.get('id', event.get('event_id', '')),
            'htmlLink': event.get('htmlLink', event.get('event_link', event.get('link', ''))),
            'calendar_name': calendar_name
        }
        
        # Use master formatter for consistent hyperlink formatting
        formatted_event = MessageFormatter.format_event_with_hyperlink(display_event, include_hyperlink=True)
        
        # Add to message
        message += f"• {formatted_event}\n"
    
    message += f"\nDo you want to {action} these events anyway?"
    
    # CRITICAL FIX: Use multi-event buttons for multiple duplicates
    if count > 1:
        # Multiple duplicates should use same buttons as multi-event operations
        keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("create")
    else:
        # Single duplicate uses create anyway/cancel buttons
        keyboard = InlineKeyboardHelper.create_duplicate_confirmation_keyboard()
    
    return message, keyboard

def format_multi_event_confirmation_with_keyboard(events, action="delete"):
    """Format multi-event confirmation message with inline keyboard"""
    count = len(events)
    
    message = f"Found {count} events to {action}:\n\n"
    
    for i, event in enumerate(events[:10], 1):  # Show first 10
        # Get event name and create hyperlink if event has link
        event_name = format_event_title(event.get('summary', 'Untitled Event'))
        
        # Create hyperlink if event has a link
        event_link = event.get('htmlLink') or event.get('event_link')
        if event_link:
            event_display = f"[{event_name}]({event_link})"
        else:
            event_display = event_name
        
        # Handle different datetime formats for start time
        start_time = ""
        end_time = ""
        date_display = ""
        
        # Try to get start time - handle both dict and string formats
        start_data = event.get('start')
        if isinstance(start_data, dict) and start_data.get('dateTime'):
            # Google Calendar format with dict
            try:
                start_dt = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                start_time = start_dt.strftime('%H:%M')
                date_display = start_dt.strftime('%A, %B %d, %Y')
                
                # Get end time if available
                end_data = event.get('end')
                if isinstance(end_data, dict) and end_data.get('dateTime'):
                    end_dt = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
                    end_time = end_dt.strftime('%H:%M')
            except:
                start_time = "Unknown time"
                date_display = "Unknown date"
        elif isinstance(start_data, str):
            # Handle string format
            try:
                if 'T' in start_data:
                    start_dt = datetime.fromisoformat(start_data.replace('Z', '+00:00'))
                    start_time = start_dt.strftime('%H:%M')
                    date_display = start_dt.strftime('%A, %B %d, %Y')
                else:
                    start_time = format_time_12hour(start_data)
                    date_display = start_data
            except:
                start_time = "Unknown time"
                date_display = "Unknown date"
        else:
            start_time = "Unknown time"
            date_display = "Unknown date"
        
        # Get proper calendar name
        calendar_name = get_calendar_display_name(event.get('calendar_id', 'primary'))
        
        # Format time range
        time_range = f"at {start_time}"
        if end_time and end_time != start_time:
            time_range = f"at {start_time} - {end_time}"
        
        # Create consistent format: Event (link) on Date at Time (Calendar)
        message += f"• {event_display} on {date_display} {time_range} ({calendar_name})\n"
    
    if count > 10:
        message += f"... and {count - 10} more events\n"
    
    # Use buttons only - no text instructions per user request
    message += f"\nUse the buttons below to proceed:"
    
    # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
    keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard(action=action)
    return message, keyboard

def format_event_selection_with_keyboard(events, action="select"):
    """Format event selection message with inline keyboard for individual selection"""
    count = len(events)
    
    message = f"Select which events to {action} ({count} total):\n\n"
    
    keyboard = create_event_selection_keyboard(events)
    return message, keyboard
