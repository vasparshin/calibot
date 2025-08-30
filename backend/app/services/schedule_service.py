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
        """Get schedule for relative dates - LLM should provide proper date format"""
        # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
        # LLM should provide date in proper format, no manual parsing
        # If LLM provides relative date strings, they should be converted to ISO format by LLM
        raise ValueError(f"LLM should provide dates in ISO format, not relative strings like '{date_str}'")
    
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
    


