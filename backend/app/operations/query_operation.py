"""
Query operation for handling event queries and schedule requests.
Consolidates all schedule and calendar query functionality.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)

class QueryOperation(BaseOperation):
    """Handles event query operations including schedule requests."""

    async def execute(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query operation."""
        try:
            # Handle schedule requests
            if self.is_schedule_request(event_data):
                return await self.handle_schedule_request(chat_id, event_data)

            # Handle general event queries
            return await self.handle_event_query(chat_id, event_data)

        except Exception as e:
            logger.error(f"Error in query operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process query."
            }

    def is_schedule_request(self, event_data: Dict[str, Any]) -> bool:
        """Check if this is a schedule request."""
        user_message = event_data.get("original_message", "")
        query_type = event_data.get("query_type", "")

        schedule_keywords = [
            "schedule", "today", "tomorrow", "week", "month",
            "what's", "whats", "when", "where", "calendar"
        ]

        return (
            any(keyword in user_message.lower() for keyword in schedule_keywords) or
            query_type in ["schedule", "today", "tomorrow", "week"]
        )

    async def handle_schedule_request(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle schedule-specific requests."""
        try:
            # Use schedule service if available
            from app.services.schedule_service import ScheduleService

            schedule_service = ScheduleService(self.calendar_service)
            user_message = event_data.get("original_message", "")

            # Detect schedule type from message
            schedule_type = self.detect_schedule_type(user_message)

            result = None
            if schedule_type == "today":
                result = await schedule_service.get_today_schedule(chat_id)
            elif schedule_type == "tomorrow":
                result = await schedule_service.get_tomorrow_schedule(chat_id)
            elif schedule_type == "week":
                result = await schedule_service.get_week_schedule(chat_id)
            elif schedule_type == "month":
                result = await schedule_service.get_month_schedule(chat_id)
            else:
                # General query
                result = await self.handle_general_query(chat_id, event_data)

            if result and result.get("success"):
                return {
                    "success": True,
                    "message": result["message"],
                    "data": result
                }
            else:
                error_msg = result.get("message", "Failed to get schedule") if result else "Schedule service unavailable"
                if result and result.get("auth_required"):
                    error_msg = "Please authenticate with Google Calendar first: /start"
                return {
                    "success": False,
                    "message": error_msg
                }

        except ImportError:
            # Fallback to general query if schedule service not available
            return await self.handle_general_query(chat_id, event_data)
        except Exception as e:
            logger.error(f"Error in schedule request: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Sorry, there was an error loading your schedule."
            }

    def detect_schedule_type(self, message: str) -> str:
        """Detect the type of schedule request."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["today", "todays", "today's"]):
            return "today"
        elif any(word in message_lower for word in ["tomorrow", "tomorrows", "tomorrow's"]):
            return "tomorrow"
        elif any(word in message_lower for word in ["week", "weekly", "this week"]):
            return "week"
        elif any(word in message_lower for word in ["month", "monthly", "this month"]):
            return "month"
        else:
            return "general"

    async def handle_general_query(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general event queries."""
        try:
            # Extract query parameters
            query_params = {
                "event_name": event_data.get("event_name", ""),
                "date": event_data.get("date", ""),
                "calendar_name": event_data.get("calendar_name", "")
            }

            # Query events
            matched_events = await self.calendar_service.query_events(query_params)

            if not matched_events.get("success") or not matched_events.get("events"):
                return {
                    "success": False,
                    "message": "No matching events found."
                }

            events = matched_events["events"]
            logger.info(f"Found {len(events)} events matching query")

            # Format response based on event count
            if len(events) == 1:
                formatted_event = self.response_manager.format_single_event_display(events[0], include_hyperlink=True)
                message = f"Found 1 event:\n\n{formatted_event}"
            else:
                title = f"Found {len(events)} events"
                if query_params.get("event_name"):
                    title += f" matching '{query_params['event_name']}'"
                if query_params.get("date"):
                    title += f" on {query_params['date']}"

                formatted_events = self.response_manager.format_event_list_display(events, numbered=True, include_hyperlink=True)
                message = f"{title}:\n\n{formatted_events}"

            return {
                "success": True,
                "message": message,
                "events": events,
                "count": len(events)
            }

        except Exception as e:
            logger.error(f"Error in general query: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to query events."
            }

    async def handle_event_query(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific event queries."""
        return await self.handle_general_query(chat_id, event_data)

    def format_success_message(self, result: Dict[str, Any], event_data: Dict[str, Any]) -> str:
        """Format success message for query operation."""
        if result.get("events"):
            count = len(result["events"])
            return f"Found {count} event{'s' if count != 1 else ''} matching your query."
        return result.get("message", "Query completed successfully")
