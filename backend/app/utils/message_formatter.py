"""
Centralized message formatting for consistent bot responses.
Implements BOT_RULES.md specifications exactly.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

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
        
        # Skip time-only strings (e.g., "09:00", "14:30") - these are not dates
        if ':' in date_str and len(date_str) <= 8 and not 'T' in date_str and not '-' in date_str:
            logger.warning(f"Received time-only string '{date_str}' in date formatter - skipping")
            return "Unknown date"
        
        try:
            # Handle various date formats
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(date_str)
            return dt.strftime('%A, %B %d, %Y')
        except Exception as e:
            logger.warning(f"Error formatting date {date_str}: {e}")
            # NO FALLBACK PARSING - per PROJECT_RULES.md
            # LLM should provide properly formatted dates
            return "Invalid date format"
    
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
    def format_time_24hour(time_str: str) -> str:
        """Format time as 'HH:MM' in 24-hour format"""
        if not time_str:
            return "Unknown time"
        
        try:
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                return dt.strftime('%H:%M')
            elif ':' in time_str and len(time_str) <= 8:  # Handle "HH:MM" or "HH:MM:SS"
                # If already in HH:MM format, just return it
                if len(time_str) == 5 and time_str.count(':') == 1:
                    return time_str
                # Parse and reformat to ensure proper format
                dt = datetime.strptime(time_str.split('.')[0], '%H:%M:%S' if time_str.count(':') == 2 else '%H:%M')
                return dt.strftime('%H:%M')
            else:
                # NO MANUAL TIME PARSING - per PROJECT_RULES.md
                # LLM should provide properly formatted times
                return time_str
        except Exception as e:
            logger.warning(f"Error formatting 24h time {time_str}: {e}")
            # NO FALLBACK PARSING - per PROJECT_RULES.md
            # LLM should provide properly formatted times
            return "Invalid time format"
    
    @staticmethod
    def format_calendar_name(calendar_name: str) -> str:
        """Return calendar name EXACTLY as provided by API summary.
        BOT_RULES: Must not transform or strip parts (no title-casing, domain stripping).
        Fallback to 'Unknown Calendar' if empty."""
        if not calendar_name:
            return "Unknown Calendar"
        return calendar_name
    
    @staticmethod
    def create_event_hyperlink(event_name: str, event_id: str = None, calendar_link: str = None) -> str:
        """Create hyperlinked event name with consistent calendar.google.com URL format"""
        formatted_name = MessageFormatter.format_event_title(event_name)
        
        if calendar_link:
            # Convert www.google.com URLs to calendar.google.com for consistency
            if 'www.google.com' in calendar_link:
                calendar_link = calendar_link.replace('www.google.com', 'calendar.google.com')
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
                Return confirmation message listing ALL events with numbering and legacy option hint.
                Format:
                    Found N events to <action>:

                    1. <event1>
                    2. <event2>
                    ...

                    Choose an option:
                """
                count = count or len(events)
                action_verb = action.lower()
                message = f"Found {count} events to {action_verb}:\n\n"
                event_list = MessageFormatter.format_event_list_display(events, numbered=True, include_hyperlink=True)
                message += event_list
                return message

    @staticmethod
    def build_proposed_change_tokens(base_event: Dict, change_spec: Dict) -> List[str]:
        """Build token list describing proposed changes for an event.
        change_spec: dict possibly containing time_shift, new_start_time, new_end_time, new_date,
                     new_event_name, calendar / calendar_name.
        Returns list of human-readable tokens.
        """
        tokens: List[str] = []
        # Name change
        if change_spec.get('new_event_name') and change_spec.get('new_event_name') != base_event.get('summary'):
            tokens.append(f"rename → '{MessageFormatter.format_event_title(change_spec['new_event_name'])}'")
        # Calendar move
        target_cal = change_spec.get('calendar') or change_spec.get('calendar_name')
        if target_cal and target_cal != base_event.get('calendar_name'):
            tokens.append(f"calendar → {target_cal}")
        # Date change
        if change_spec.get('new_date'):
            tokens.append(f"date → {change_spec['new_date']}")
        # Explicit new times
        if change_spec.get('new_start_time') or change_spec.get('new_end_time'):
            ns = change_spec.get('new_start_time') or ''
            ne = change_spec.get('new_end_time') or ''
            if ns or ne:
                tokens.append(f"time → {ns or '?'} - {ne or '?'}")
        # Time shift textual (retain original phrase)
        if change_spec.get('time_shift') and not (change_spec.get('new_start_time') or change_spec.get('new_end_time')):
            # Try to compute resulting time window if base_event has start/end datetimes
            shift_phrase = change_spec['time_shift']
            computed = MessageFormatter._compute_shifted_time_window(base_event, shift_phrase)
            if computed:
                tokens.append(f"time → {computed}")
            else:
                tokens.append(f"shift {shift_phrase}")
        return tokens



    @staticmethod
    def format_event_with_proposed_changes(event: Dict, change_spec: Dict) -> str:
        """Return a line showing current event plus arrow and proposed tokens if any."""
        base_display = MessageFormatter.format_single_event_display(event, include_hyperlink=True)
        tokens = MessageFormatter.build_proposed_change_tokens(event, change_spec)
        if tokens:
            return f"{base_display} → " + ", ".join(tokens)
        return base_display
    
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

    @staticmethod
    def format_decision_appendix(decision: str, change_summary: str = "") -> str:
        """Append a standardized decision line for one-by-one flow history retention.
        decision: 'updated', 'deleted', 'skipped'.
        change_summary: optional concise diff e.g. (+1h), (moved to Tonya Calendar).
        """
        base = decision.lower()
        verb_map = {
            'updated': 'Updated',
            'deleted': 'Deleted',
            'skipped': 'Skipped'
        }
        label = verb_map.get(base, base.title())
        if change_summary:
            return f"Decision: {label} {change_summary}"
        return f"Decision: {label}"

    @staticmethod
    def summarize_time_change(original_start: str, original_end: str, new_start: str, new_end: str) -> str:
        """Return a concise time diff token like (+1h), (-30m), (09:00→10:00)."""
        try:
            if all('T' in t for t in [original_start, new_start]):
                from datetime import datetime
                o = datetime.fromisoformat(original_start.replace('Z','+00:00'))
                n = datetime.fromisoformat(new_start.replace('Z','+00:00'))
                delta = n - o
                minutes = int(delta.total_seconds()/60)
                if minutes == 0:
                    return ''
                sign = '+' if minutes > 0 else ''
                if minutes % 60 == 0:
                    return f"({sign}{minutes//60}h)"
                return f"({sign}{minutes}m)"
        except Exception:
            pass
        if original_start and new_start and original_start != new_start:
            return f"({original_start}→{new_start})"
        return ''
