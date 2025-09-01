"""
Create operation for handling event creation (single and batch).
Consolidates creation logic from routes.py and handlers.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)

class CreateOperation(BaseOperation):
    """Handles event creation operations (single and batch)."""

    async def execute(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create operation."""
        try:
            # Determine if this is a batch creation
            events_to_create = self.extract_events_to_create(event_data)

            if not events_to_create:
                return {
                    "success": False,
                    "message": "No valid events to create.",
                    "error": "No events extracted from request"
                }

            # Check for duplicates if creating multiple events
            if len(events_to_create) > 1:
                duplicate_check = await self.check_duplicates(chat_id, events_to_create)
                if duplicate_check and duplicate_check.get("requires_confirmation"):
                    # Store pending operation and return confirmation request
                    await self.store_pending_duplicate_operation(chat_id, duplicate_check, events_to_create, event_data)
                    return {
                        "success": True,
                        "requires_user_action": True,
                        "message": duplicate_check["message"],
                        "keyboard": duplicate_check["keyboard"]
                    }

            # Process creation
            if len(events_to_create) == 1:
                return await self.create_single_event(chat_id, events_to_create[0])
            else:
                return await self.create_batch_events(chat_id, events_to_create)

        except Exception as e:
            logger.error(f"Error in create operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create event(s)."
            }

    def extract_events_to_create(self, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract events to create from various input formats."""
        events = []

        # Format 1: Direct batch_create with events array
        if event_data.get("intent") == "batch_create" and "events" in event_data:
            events = event_data["events"]

        # Format 2: Create intent with events array
        elif event_data.get("intent") == "create" and "events" in event_data:
            events = []
            for event_item in event_data["events"]:
                merged_event = event_data.copy()
                merged_event.update(event_item)
                # Remove events array to avoid recursion
                if "events" in merged_event:
                    del merged_event["events"]
                merged_event["intent"] = "create"
                events.append(merged_event)

        # Format 3: Single event
        elif event_data.get("intent") == "create":
            events = [event_data]

        return events

    async def create_single_event(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single event."""
        try:
            # Select calendar
            calendar_info = await self.select_calendar(event_data)
            if not calendar_info.get("success"):
                return calendar_info

            # Prepare event for creation
            prepared_event = self.prepare_event_for_creation(event_data, calendar_info)

            # Create event
            calendar_response = await self.calendar_service.create_event(prepared_event)

            if calendar_response.get("success"):
                # Format event summary like other operations
                created_event = calendar_response.get('created_event') or prepared_event
                from app.utils.message_formatter import MessageFormatter
                formatted_event = MessageFormatter.format_single_event_display(created_event, include_hyperlink=True)
                message = f"Successfully created event:\n\n{formatted_event}"
                
                return {
                    "success": True,
                    "message": message,
                    "calendar_response": calendar_response,
                    "event_data": prepared_event
                }
            else:
                return {
                    "success": False,
                    "message": calendar_response.get("message", "Failed to create event"),
                    "error": calendar_response.get("message", "Unknown error")
                }

        except Exception as e:
            logger.error(f"Error creating single event: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create event."
            }

    async def create_batch_events(self, chat_id: int, events_to_create: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple events."""
        try:
            successful_events = []
            failed_events = []

            for i, event_data in enumerate(events_to_create):
                try:
                    single_result = await self.create_single_event(chat_id, event_data)

                    if single_result.get("success"):
                        successful_events.append({
                            "event_data": event_data,
                            "calendar_response": single_result["calendar_response"],
                            "formatted": self.format_single_event_success(event_data, single_result["calendar_response"])
                        })
                    else:
                        failed_events.append({
                            "event_data": event_data,
                            "error": single_result.get("message", "Unknown error")
                        })

                except Exception as e:
                    logger.error(f"Failed to create event {i+1}: {e}")
                    failed_events.append({
                        "event_data": event_data,
                        "error": str(e)
                    })

            # Format response
            if successful_events:
                message = self.format_batch_success_message(successful_events, failed_events)
                return {
                    "success": True,
                    "message": message,
                    "successful_count": len(successful_events),
                    "failed_count": len(failed_events),
                    "successful_events": successful_events,
                    "failed_events": failed_events
                }
            else:
                message = self.format_batch_failure_message(failed_events)
                return {
                    "success": False,
                    "message": message,
                    "failed_count": len(failed_events),
                    "failed_events": failed_events
                }

        except Exception as e:
            logger.error(f"Error in batch creation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create events."
            }

    def format_single_event_success(self, event_data: Dict[str, Any], calendar_response: Dict[str, Any]) -> str:
        """Format success message for single event creation."""
        return self.response_manager.format_success_message("create", event_data, calendar_response)

    def format_batch_success_message(self, successful_events: List[Dict], failed_events: List[Dict]) -> str:
        """Format success message for batch creation."""
        return self.response_manager.format_batch_success_message("create", successful_events, failed_events)

    def format_batch_failure_message(self, failed_events: List[Dict]) -> str:
        """Format failure message for batch creation."""
        if not failed_events:
            return "No events were created."

        message = f"Failed to create {len(failed_events)} events:\n\n"
        for event in failed_events:
            event_data = event.get("event_data", {})
            event_name = event_data.get("event_name", "Event")
            start_time = event_data.get("start_time", "Unknown time")
            error = event.get("error", "Unknown error")
            message += f"• {event_name} at {start_time}: {error}\n"

        return message

    async def store_pending_duplicate_operation(self, chat_id: int, duplicate_check: Dict,
                                             events_to_create: List[Dict], original_request: Dict) -> None:
        """Store pending operation for duplicate confirmation."""
        # This would integrate with the multi-event operation handler
        # For now, store in conversation state
        self.set_conversation_data(chat_id, "pending_duplicates", {
            "duplicates": duplicate_check["duplicates"],
            "events_to_create": events_to_create,
            "original_request": original_request,
            "timestamp": datetime.now().isoformat()
        })

    def format_success_message(self, result: Dict[str, Any], event_data: Dict[str, Any]) -> str:
        """Format success message for create operation."""
        if result.get("calendar_response"):
            return self.response_manager.format_success_message("create", event_data, result["calendar_response"])
        else:
            return result.get("message", "Operation completed successfully")
