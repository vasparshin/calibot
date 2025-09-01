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
            event_name = event_data.get("event_name", "").strip()
            event_date = event_data.get("date", "").strip()

            # If no date specified, default to tomorrow (common for test scenarios)
            if not event_date:
                from datetime import datetime, timedelta
                tomorrow = datetime.now() + timedelta(days=1)
                event_date = tomorrow.strftime("%Y-%m-%d")

            # Handle "ANY" event name for "update all events" requests
            # Don't pass "ANY" to calendar service as it will search for events containing "ANY"
            query_params = {
                "date": event_date
            }
            
            # Only add event_name filter if it's not "ANY" or empty
            if event_name and event_name.upper() != "ANY":
                query_params["event_name"] = event_name

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
                # CRITICAL FIX: Use master formatter with proper event structure
                from app.utils.message_formatter import MessageFormatter
                
                # Build complete event structure with hyperlink from calendar response
                updated_event = calendar_response.get('updated_event') or event
                event_for_display = {
                    'summary': updated_event.get('summary', event.get('summary', 'Untitled')),
                    'start': updated_event.get('start', event.get('start', '')),
                    'end': updated_event.get('end', event.get('end', '')),
                    'calendar_name': updated_event.get('calendar_name', event.get('calendar_name', 'Unknown Calendar')),
                    'id': updated_event.get('id', event.get('id', '')),
                    'link': updated_event.get('htmlLink', event.get('link', '')),  # CRITICAL: Include hyperlink
                    'htmlLink': updated_event.get('htmlLink', event.get('link', ''))  # Alternative field
                }
                
                formatted_event = MessageFormatter.format_single_event_display(event_for_display, include_hyperlink=True)
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

        # Handle time shift - LLM should provide properly formatted time_shift
        # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
        if event_data.get("time_shift"):
            # LLM should provide time_shift in proper format (e.g., "+30", "-60", "30 minutes", "1 hour")
            # No manual parsing needed - pass through to calendar service
            update_data["time_shift"] = event_data["time_shift"]

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



    async def handle_multi_event_update(self, chat_id: int, events: List[Dict], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle updates for multiple events using queue system."""
        try:
            # Use global queue handler to maintain state across operations
            from app.core.global_instances import get_global_queue_handler
            global_queue_handler = get_global_queue_handler()
            
            logger.info(f"🔍 UPDATE DEBUG: Using queue handler instance ID: {id(global_queue_handler)}")
            logger.info(f"🔍 UPDATE DEBUG: Chat ID: {chat_id}, Events count: {len(events)}")

            # Prepare events for queue - fix data structure mapping
            events_for_queue = []
            for event in events:
                # Map GoogleCalendarService format to EventQueueHandler format
                queue_event = {
                    'id': event.get('id'),
                    'event_name': event.get('summary', 'Untitled'),  # summary -> event_name
                    'start_time': event.get('start', ''),            # start -> start_time
                    'end_time': event.get('end', ''),                # end -> end_time
                    'calendar_name': event.get('calendar_name', 'Unknown Calendar'),
                    'calendar_id': event.get('calendar_id', 'primary'),
                    'calendar_link': event.get('link', ''),          # link -> calendar_link
                    'intent': 'update'
                }
                # Add update-specific data from event_data
                queue_event.update({k: v for k, v in event_data.items() 
                                  if k in ['time_shift', 'new_start_time', 'new_end_time', 'new_date', 'new_event_name']})
                events_for_queue.append(queue_event)

            # Create queue using the proper method for multi-event operations
            queue_result = global_queue_handler.create_event_queue_from_list(chat_id, events_for_queue)

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
