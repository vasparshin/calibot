"""
Schedule Service for Direct Calendar Queries

Handles today/tomorrow/date-specific schedule requests without LLM processing
for better performance and reliability. Implements BOT_RULES.md formatting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ScheduleService:
    """Service for handling direct schedule queries and formatting responses"""
    
    def __init__(self, calendar_service):
        self.calendar_service = calendar_service
    
    async def get_today_schedule(self, chat_id: int) -> Dict:
        """Get today's schedule with optimized formatting"""
        today = datetime.now().strftime("%Y-%m-%d")
        return await self._get_schedule_for_date(today, "today", chat_id)
    
    async def get_tomorrow_schedule(self, chat_id: int) -> Dict:
        """Get tomorrow's schedule with optimized formatting"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return await self._get_schedule_for_date(tomorrow, "tomorrow", chat_id)
    
    async def get_schedule_for_relative_date(self, date_str: str, chat_id: int) -> Dict:
        """Get schedule for relative dates like 'day after tomorrow', 'next Monday'"""
        parsed_date = self._parse_relative_date(date_str)
        if not parsed_date:
            return {
                "success": False,
                "message": f"Could not understand date: {date_str}"
            }
        
        return await self._get_schedule_for_date(parsed_date, date_str, chat_id)
    
    async def _get_schedule_for_date(self, date: str, date_description: str, chat_id: int) -> Dict:
        """Internal method to get and format schedule for a specific date"""
        try:
            # Query events for the specified date
            query_params = {
                "date": date
            }
            
            result = await self.calendar_service.query_events(query_params)
            
            if not result.get("success"):
                if result.get("auth_required"):
                    return {
                        "success": False,
                        "message": "Authentication required",
                        "auth_required": True
                    }
                return {
                    "success": False,
                    "message": result.get("message", "Failed to fetch events")
                }
            
            events = result.get("events", [])
            
            if not events:
                formatted_date = self._format_date_for_display(date)
                if date_description.lower() == "today":
                    return {
                        "success": True,
                        "message": f"Today ({formatted_date}) you have no events scheduled.",
                        "event_count": 0
                    }
                elif date_description.lower() == "tomorrow":
                    return {
                        "success": True,
                        "message": f"Tomorrow ({formatted_date}) you have no events scheduled.",
                        "event_count": 0
                    }
                else:
                    return {
                        "success": True,
                        "message": f"{date_description.title()} ({formatted_date}) you have no events scheduled.",
                        "event_count": 0
                    }
            
            # Sort events chronologically
            events.sort(key=lambda x: x.get('start', ''))
            
            # Format the response
            formatted_date = self._format_date_for_display(date)
            event_count = len(events)
            
            if date_description.lower() == "today":
                title = f"Today ({formatted_date}) you have {event_count} event{'s' if event_count != 1 else ''}:"
            elif date_description.lower() == "tomorrow":
                title = f"Tomorrow ({formatted_date}) you have {event_count} event{'s' if event_count != 1 else ''}:"
            else:
                title = f"{date_description.title()} ({formatted_date}) you have {event_count} event{'s' if event_count != 1 else ''}:"
            
            # Format event list with time-only display (no date needed for same-day events)
            event_list = []
            for event in events:
                formatted_event = self._format_event_for_same_day_display(event)
                event_list.append(formatted_event)
            
            message = title + "\n\n" + "\n".join(event_list)
            
            return {
                "success": True,
                "message": message,
                "event_count": event_count,
                "events": events
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule for {date_description}: {e}")
            return {
                "success": False,
                "message": f"Error retrieving schedule: {str(e)}"
            }
    
    def _format_event_for_same_day_display(self, event: Dict) -> str:
        """Format event for same-day display with time only"""
        # Get event details
        title = event.get('summary', 'Untitled Event')
        event_link = event.get('link') or event.get('htmlLink', '')
        calendar_name = event.get('calendar_name', 'Unknown Calendar')
        
        # Create hyperlinked title
        if event_link:
            hyperlinked_title = f"[{title}]({event_link})"
        else:
            hyperlinked_title = title
        
        # Extract and format time
        start_time = event.get('start', '')
        end_time = event.get('end', '')
        
        time_display = self._format_time_range(start_time, end_time)
        
        # Format: • [Event Name](link) at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
        return f"• {hyperlinked_title} at {time_display} ({calendar_name})"
    
    def _format_time_range(self, start_time: str, end_time: str) -> str:
        """Format time range for display"""
        try:
            if not start_time:
                return "All day"
            
            # Parse start time
            if 'T' in start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_formatted = start_dt.strftime('%I:%M %p').lstrip('0')
            else:
                return "All day"
            
            # Parse end time
            if end_time and 'T' in end_time:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_formatted = end_dt.strftime('%I:%M %p').lstrip('0')
                return f"{start_formatted} - {end_formatted}"
            else:
                return start_formatted
                
        except Exception as e:
            logger.warning(f"Error formatting time range: {e}")
            return "Time unavailable"
    
    def _format_date_for_display(self, date_str: str) -> str:
        """Format date for display (dd/mm/yy format)"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%y")
        except Exception:
            return date_str
    
    def _parse_relative_date(self, date_str: str) -> Optional[str]:
        """Parse relative date expressions like 'day after tomorrow', 'next Monday'"""
        date_str_lower = date_str.lower().strip()
        
        # Handle common relative dates
        if date_str_lower in ["day after tomorrow", "day after", "2 days"]:
            return (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        if date_str_lower in ["3 days", "in 3 days"]:
            return (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        
        if date_str_lower in ["next week", "1 week"]:
            return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Handle weekdays
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        for day_name, day_num in weekdays.items():
            if day_name in date_str_lower:
                today = datetime.now()
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:  # Today is the target day
                    days_ahead = 7  # Next week
                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime("%Y-%m-%d")
        
        return None
    
    def detect_schedule_query(self, message: str) -> Optional[str]:
        """Detect if message is a schedule query and return the date type"""
        message_lower = message.lower().strip()
        
        # Only match EXPLICIT schedule query patterns, not calendar modification requests
        # This prevents "move events to tomorrow" from being treated as "show tomorrow's schedule"
        
        # Handle /today command
        if message_lower in ["/today", "today", "today's schedule", "what's today", "whats today"]:
            return "today"
        
        # Handle explicit tomorrow schedule queries (NOT event modifications)
        if any(phrase in message_lower for phrase in [
            "tomorrow's schedule", "tomorrows schedule", 
            "what's tomorrow", "whats tomorrow",
            "show me tomorrow", "show tomorrow",
            "what do i have tomorrow", "what's on tomorrow", "whats on tomorrow",
            "schedule for tomorrow", "tomorrow schedule"
        ]):
            return "tomorrow"
        
        # Handle general today queries (more specific patterns)
        if any(phrase in message_lower for phrase in [
            "today's schedule", "todays schedule", "what's scheduled today", 
            "whats scheduled today", "what do i have today", "schedule today",
            "what's on today", "whats on today", "what's my schedule today",
            "whats my schedule today", "show me today", "show today"
        ]):
            return "today"
        
        # Handle day after tomorrow (explicit schedule queries only)
        if any(phrase in message_lower for phrase in [
            "day after tomorrow schedule", "schedule day after tomorrow",
            "what do i have day after tomorrow", "show me day after tomorrow"
        ]):
            return "day after tomorrow"
        
        # Handle next week references (explicit schedule queries only)
        if any(phrase in message_lower for phrase in [
            "next week schedule", "schedule next week", 
            "what do i have next week", "show me next week"
        ]):
            return "next week"
        
        return None
