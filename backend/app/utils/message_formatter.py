"""
Centralized message formatting for consistent bot responses.
Implements BOT_RULES.md specifications exactly.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageFormatter:
    """Centralized message formatting following BOT_RULES.md specifications"""
    
    @staticmethod
    def format_event_title(title: str) -> str:
        """Format event title with proper capitalization"""
        if not title:
            return "Untitled"
        return title.title()
    
    @staticmethod
    def format_date_full(date_str: str) -> str:
        """Format date as 'Day, Month DD, YYYY'"""
        if not date_str:
            return "Unknown date"
        
        # If already formatted, return as-is
        if ',' in date_str and any(month in date_str for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                                                                    'July', 'August', 'September', 'October', 'November', 'December']):
            return date_str
        
        try:
            # Handle various date formats
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(date_str)
            return dt.strftime('%A, %B %d, %Y')
        except Exception as e:
            logger.warning(f"Error formatting date {date_str}: {e}")
            return date_str  # Return original if can't parse
    
    @staticmethod
    def format_time_12hour(time_str: str) -> str:
        """Format time as 'HH:MM AM/PM'"""
        if not time_str:
            return "Unknown time"
        
        try:
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                return dt.strftime('%I:%M %p')
            else:
                # Try parsing as time-only
                dt = datetime.strptime(time_str, '%H:%M')
                return dt.strftime('%I:%M %p')
        except Exception as e:
            logger.warning(f"Error formatting time {time_str}: {e}")
            return "Unknown time"
    
    @staticmethod
    def format_calendar_name(calendar_name: str) -> str:
        """Format calendar name, removing technical details"""
        if not calendar_name:
            return "Unknown Calendar"
        
        # Remove common technical suffixes
        clean_name = calendar_name
        if '@' in clean_name:
            clean_name = clean_name.split('@')[0]
        if '.calendar.google.com' in clean_name:
            clean_name = clean_name.replace('.calendar.google.com', '')
        
        return clean_name.title()
    
    @staticmethod
    def create_event_hyperlink(event_name: str, event_id: str = None, calendar_link: str = None) -> str:
        """Create hyperlinked event name"""
        formatted_name = MessageFormatter.format_event_title(event_name)
        
        if calendar_link:
            return f"[{formatted_name}]({calendar_link})"
        elif event_id:
            # Generate calendar link from event ID
            link = f"https://calendar.google.com/calendar/event?eid={event_id}"
            return f"[{formatted_name}]({link})"
        else:
            return formatted_name
    
    @staticmethod
    def format_single_event_display(event: Dict, include_hyperlink: bool = True) -> str:
        """
        Format single event for display following BOT_RULES.md specification.
        Format: • [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
        """
        try:
            # Extract event details
            event_name = event.get('summary', event.get('event_name', 'Untitled'))
            start_time = event.get('start', event.get('start_time', ''))
            end_time = event.get('end', event.get('end_time', ''))
            calendar_name = event.get('calendar_name', 'Unknown Calendar')
            event_id = event.get('id', event.get('event_id', ''))
            calendar_link = event.get('htmlLink', event.get('calendar_link', ''))
            
            # Format components
            if include_hyperlink:
                formatted_name = MessageFormatter.create_event_hyperlink(event_name, event_id, calendar_link)
            else:
                formatted_name = MessageFormatter.format_event_title(event_name)
            
            # Extract date from start_time
            date_str = MessageFormatter.format_date_full(start_time)
            start_time_str = MessageFormatter.format_time_12hour(start_time)
            end_time_str = MessageFormatter.format_time_12hour(end_time)
            calendar_formatted = MessageFormatter.format_calendar_name(calendar_name)
            
            # Build the formatted string
            return f"• {formatted_name} on {date_str} at {start_time_str} - {end_time_str} ({calendar_formatted})"
            
        except Exception as e:
            logger.error(f"Error formatting event display: {e}")
            return f"• {event.get('summary', 'Untitled')} - Error formatting event"
    
    @staticmethod
    def format_event_list_display(events: List[Dict], numbered: bool = True, include_hyperlink: bool = True) -> str:
        """
        Format multiple events for display. NEVER truncates list.
        """
        if not events:
            return ""
        
        formatted_events = []
        for i, event in enumerate(events, 1):
            event_display = MessageFormatter.format_single_event_display(event, include_hyperlink)
            
            if numbered:
                # Replace bullet with number
                if event_display.startswith('• '):
                    event_display = f"{i}. {event_display[2:]}"
                else:
                    event_display = f"{i}. {event_display}"
            
            formatted_events.append(event_display)
        
        return "\n".join(formatted_events)
    
    @staticmethod
    def format_success_message_create(events: List[Dict], count: int = None) -> str:
        """Format success message for event creation"""
        count = count or len(events)
        
        if count == 1:
            header = "Successfully created 1 event:\n\n"
        else:
            header = f"Successfully created {count} events:\n\n"
        
        event_list = MessageFormatter.format_event_list_display(events, numbered=False, include_hyperlink=True)
        return header + event_list
    
    @staticmethod
    def format_success_message_update(events: List[Dict], count: int = None, date: str = None) -> str:
        """Format success message for event updates"""
        count = count or len(events)
        
        if date:
            date_formatted = MessageFormatter.format_date_full(date)
            header = f"Successfully updated all {count} events on {date_formatted}:\n\n"
        else:
            header = f"Successfully updated {count} event(s):\n\n"
        
        # For updates, prefix each event with "Updated"
        formatted_events = []
        for event in events:
            event_display = MessageFormatter.format_single_event_display(event, include_hyperlink=True)
            if event_display.startswith('• '):
                event_display = f"• Updated {event_display[2:]}"
            else:
                event_display = f"• Updated {event_display}"
            formatted_events.append(event_display)
        
        return header + "\n".join(formatted_events)
    
    @staticmethod
    def format_success_message_delete(count: int, date: str = None) -> str:
        """Format success message for event deletion"""
        if date:
            date_formatted = MessageFormatter.format_date_full(date)
            return f"Successfully deleted all {count} events on {date_formatted}!"
        else:
            return f"Successfully deleted {count} event(s)!"
    
    @staticmethod
    def format_confirmation_message(action: str, events: List[Dict], count: int = None) -> str:
        """
        Format confirmation message for multi-event operations.
        NEVER truncates event list - shows ALL events.
        NOTE: Does NOT include text options since we use inline keyboards.
        """
        count = count or len(events)
        action_verb = action.lower()
        
        # Header
        message = f"Found {count} events to {action_verb}:\n\n"
        
        # Event list - ALWAYS show ALL events (never truncate)
        event_list = MessageFormatter.format_event_list_display(events, numbered=True, include_hyperlink=True)
        message += event_list
        
        # No text options - inline keyboard handles this
        return message
    
    @staticmethod
    def format_duplicate_message(duplicates: List[Dict]) -> str:
        """Format duplicate detection message"""
        count = len(duplicates)
        message = f"Found {count} potential duplicate event(s):\n\n"
        
        # Show ALL duplicates (never truncate)
        for dup in duplicates:
            if 'new_event' in dup:
                event = dup['new_event']
                event_display = MessageFormatter.format_single_event_display(event, include_hyperlink=True)
                message += event_display + "\n"
        
        message += f"\nDo you want to create these events anyway?\n"
        message += f"• 'yes' - Create all events anyway\n"
        message += f"• 'no' or 'cancel' - Cancel creation"
        
        return message
    
    @staticmethod
    def format_single_event_confirmation(action: str, event: Dict) -> str:
        """Format confirmation for single event operations"""
        event_display = MessageFormatter.format_single_event_display(event, include_hyperlink=True)
        
        # Remove bullet point for this format
        if event_display.startswith('• '):
            event_display = event_display[2:]
        
        action_verb = action.lower()
        return (f"Are you sure you want to {action_verb} {event_display}?\n"
                f"• 'yes' - Confirm {action_verb}\n"
                f"• 'no' or 'cancel' - Cancel operation")
    
    @staticmethod
    def format_no_events_message(criteria: str = "") -> str:
        """Format message when no events are found"""
        if criteria:
            return f"No events found matching your criteria: {criteria}"
        else:
            return "No events found matching your criteria."
