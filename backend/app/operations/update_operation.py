"""
Update operation for handling event updates.
Supports time shifts, calendar moves, and property modifications.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)

class UpdateOperation(BaseOperation):
    """Handles event update operations including time shifts and calendar moves."""

    async def execute(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute update operation."""
        try:
            # Find events to update
            query_params = {
                "event_name": event_data.get("event_name", ""),
                "date": event_data.get("date", "")
            }

            matched_events = await self.calendar_service.query_events(query_params)

            if not matched_events.get("success") or not matched_events.get("events"):
                return {
                    "success": False,
                    "message": "No events found matching your criteria."
                }

            events = matched_events["events"]

            # Handle single vs multiple events
            if len(events) == 1:
                return await self.update_single_event(chat_id, events[0], event_data)
            else:
                return await self.handle_multi_event_update(chat_id, events, event_data)

        except Exception as e:
            logger.error(f"Error in update operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update event(s)."
            }

    async def update_single_event(self, chat_id: int, event: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a single event."""
        try:
            source_calendar_id = event.get('calendar_id', 'primary')
            update_data = self.prepare_update_data(event_data)

            calendar_response = self.calendar_service.update_event(
                event["id"],
                update_data,
                source_calendar_id
            )

            if calendar_response.get("success"):
                updated_event = calendar_response.get('updated_event') or event
                formatted_event = self.response_manager.format_single_event_display(updated_event, include_hyperlink=True)
                message = f"Successfully updated event:\n\n{formatted_event}"

                return {
                    "success": True,
                    "message": message,
                    "calendar_response": calendar_response,
                    "updated_event": updated_event
                }
            else:
                return {
                    "success": False,
                    "message": calendar_response.get("message", "Failed to update event"),
                    "error": calendar_response.get("message", "Unknown error")
                }

        except Exception as e:
            logger.error(f"Error updating single event: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update event."
            }

    def prepare_update_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare update data from event data."""
        update_data = {}

        # Handle time shift
        if event_data.get("time_shift"):
            update_data["time_shift"] = self.parse_time_shift(event_data["time_shift"])

        # Handle specific time updates
        if event_data.get("new_start_time"):
            update_data["start_time"] = event_data["new_start_time"]
        if event_data.get("new_end_time"):
            update_data["end_time"] = event_data["new_end_time"]
        if event_data.get("new_date"):
            update_data["date"] = event_data["new_date"]

        # Handle calendar move
        if event_data.get("new_calendar") or event_data.get("calendar_name"):
            target_calendar = event_data.get("new_calendar") or event_data.get("calendar_name")
            update_data["calendar_name"] = target_calendar

        return update_data

    def parse_time_shift(self, time_shift: str) -> int:
        """Parse time shift string into minutes."""
        import re

        # Patterns: "1 hour", "30 minutes", "2 hours later", "1h", "45m"
        hour_pattern = re.search(r'(\d+)\s*(hour|h)', time_shift.lower())
        minute_pattern = re.search(r'(\d+)\s*(minute|min|m)', time_shift.lower())

        minutes = 0

        if hour_pattern:
            hours = int(hour_pattern.group(1))
            minutes += hours * 60

        if minute_pattern:
            minutes += int(minute_pattern.group(1))

        # Handle direction
        if "later" in time_shift.lower() or "forward" in time_shift.lower():
            return minutes
        elif "earlier" in time_shift.lower() or "back" in time_shift.lower():
            return -minutes

        return minutes

    async def handle_multi_event_update(self, chat_id: int, events: List[Dict], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle updates for multiple events using queue system."""
        try:
            from app.services.event_queue_handler import EventQueueHandler

            queue_handler = EventQueueHandler(
                self.telegram_service,
                self.conversation_state,
                self.calendar_service,
                self.calendar_agent
            )

            # Prepare events for queue
            events_for_queue = []
            for event in events:
                event_copy = event.copy()
                event_copy.update(event_data)
                event_copy['intent'] = 'update'
                events_for_queue.append(event_copy)

            # Create queue
            queue_result = queue_handler.create_event_queue(chat_id, {
                "intent": "update",
                "events": events_for_queue,
                "original_request": event_data
            })

            if queue_result.get("keyboard"):
                await self.send_message(chat_id, queue_result["message"], queue_result["keyboard"])
                return {
                    "success": True,
                    "requires_user_action": True,
                    "message": queue_result["message"],
                    "keyboard": queue_result["keyboard"]
                }
            else:
                await self.send_message(chat_id, queue_result["message"])
                return {
                    "success": True,
                    "message": queue_result["message"]
                }

        except Exception as e:
            logger.error(f"Error in multi-event update: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process multi-event update."
            }

    def format_success_message(self, result: Dict[str, Any], event_data: Dict[str, Any]) -> str:
        """Format success message for update operation."""
        if result.get("calendar_response"):
            return self.response_manager.format_success_message("update", event_data, result["calendar_response"])
        elif result.get("updated_event"):
            return self.response_manager.format_success_message("update", event_data, {"event_link": "", "calendar_used": ""})
        else:
            return result.get("message", "Event updated successfully")
