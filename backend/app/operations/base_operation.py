"""
Base operation class providing common functionality for all calendar operations.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from app.core.base_handler import BaseHandler
from app.core.response_manager import ResponseManager
from app.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class BaseOperation(BaseHandler):
    """Base class for all calendar operations providing common functionality."""

    def __init__(self, telegram_service, conversation_state, calendar_service, calendar_agent=None):
        super().__init__(telegram_service, conversation_state, calendar_service, calendar_agent)
        self.response_manager = ResponseManager()
        self.error_handler = ErrorHandler()

    async def execute(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the operation. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement execute method")

    async def validate_input(self, event_data: Dict[str, Any]) -> bool:
        """Validate input data. Can be overridden by subclasses."""
        return self.validate_event_data(event_data)

    async def pre_execute(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-execution hook. Can be overridden by subclasses."""
        return {"success": True}

    async def post_execute(self, chat_id: int, result: Dict[str, Any]) -> None:
        """Post-execution hook. Can be overridden by subclasses."""
        pass

    async def handle_success(self, chat_id: int, result: Dict[str, Any], event_data: Dict[str, Any]) -> None:
        """Handle successful operation completion."""
        try:
            success_message = self.format_success_message(result, event_data)
            await self.send_message(chat_id, success_message)
        except Exception as e:
            logger.error(f"Error handling success: {e}")
            await self.error_handler.handle_and_respond(
                e, "success formatting", chat_id, self.telegram_service, self.conversation_state
            )

    async def handle_error(self, chat_id: int, error: Exception, operation: str) -> None:
        """Handle operation errors."""
        await self.error_handler.handle_and_respond(
            error, operation, chat_id, self.telegram_service, self.conversation_state
        )

    def format_success_message(self, result: Dict[str, Any], event_data: Dict[str, Any]) -> str:
        """Format success message. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement format_success_message method")

    async def check_duplicates(self, chat_id: int, events_to_create: List[Dict]) -> Optional[Dict[str, Any]]:
        """Check for duplicate events and return confirmation if needed."""
        try:
            duplicates_found = []

            for i, event in enumerate(events_to_create):
                # CRITICAL FIX: Validate event is a dictionary before processing
                if not isinstance(event, dict):
                    logger.warning(f"check_duplicates: Event {i} is not a dict, type: {type(event)}")
                    continue

                # CRITICAL FIX: Ensure all required fields exist and are strings
                event_name = event.get("event_name", "")
                date = event.get("date", "")
                
                # Validate that both fields are strings, not None or other types
                if not isinstance(event_name, str) or not isinstance(date, str):
                    logger.warning(f"check_duplicates: Event {i} has invalid field types - event_name type: {type(event_name)}, date type: {type(date)}")
                    continue

                if not event_name or not date:
                    logger.warning(f"check_duplicates: Event {i} missing required fields, event_name='{event_name}', date='{date}'")
                    continue

                query_params = {"event_name": event_name, "date": date}

                try:
                    existing_events = await self.calendar_service.query_events(query_params)

                    if existing_events.get("success") and existing_events.get("events"):
                        event_start = event.get("start_time", "")
                        event_end = event.get("end_time", "")

                        for existing in existing_events["events"]:
                            # CRITICAL FIX: Validate existing event is a dictionary
                            if not isinstance(existing, dict):
                                logger.warning(f"check_duplicates: Existing event is not a dict, type: {type(existing)}")
                                continue
                                
                            # CRITICAL FIX: Ensure start field exists and is properly formatted
                            existing_start_data = existing.get("start", {})
                            existing_end_data = existing.get("end", {})
                            
                            # Handle both string and dict formats for start/end times
                            if isinstance(existing_start_data, dict):
                                existing_start = existing_start_data.get("dateTime", "")
                            elif isinstance(existing_start_data, str):
                                existing_start = existing_start_data
                            else:
                                existing_start = ""
                                
                            if isinstance(existing_end_data, dict):
                                existing_end = existing_end_data.get("dateTime", "")
                            elif isinstance(existing_end_data, str):
                                existing_end = existing_end_data
                            else:
                                existing_end = ""

                            # Check for time overlap (simplified)
                            if event_start and existing_start:
                                if event_start in existing_start or existing_start in event_start:
                                    duplicates_found.append({
                                        "new_event": event,
                                        "existing_event": existing,
                                        "index": i
                                    })
                                    break
                except Exception as e:
                    logger.warning(f"check_duplicates: Error checking duplicates for event {i}: {e}")

            if duplicates_found:
                logger.info(f"check_duplicates: Found {len(duplicates_found)} potential duplicates")
                
                # CRITICAL FIX: Validate duplicates_found structure before passing to formatter
                valid_duplicates = []
                for duplicate in duplicates_found:
                    if isinstance(duplicate, dict) and all(key in duplicate for key in ["new_event", "existing_event", "index"]):
                        # Additional validation: ensure both new_event and existing_event are dicts
                        if isinstance(duplicate["new_event"], dict) and isinstance(duplicate["existing_event"], dict):
                            valid_duplicates.append(duplicate)
                        else:
                            logger.warning(f"check_duplicates: Invalid duplicate structure - new_event type: {type(duplicate['new_event'])}, existing_event type: {type(duplicate['existing_event'])}")
                    else:
                        logger.warning(f"check_duplicates: Invalid duplicate structure: {duplicate}, type: {type(duplicate)}")
                
                if valid_duplicates:
                    try:
                        message, keyboard = self.response_manager.format_duplicate_confirmation(valid_duplicates)
                        return {
                            "requires_confirmation": True,
                            "message": message,
                            "keyboard": keyboard,
                            "duplicates": valid_duplicates
                        }
                    except Exception as e:
                        logger.error(f"check_duplicates: Error formatting duplicate confirmation: {e}")
                        # Fall through to create events anyway
                else:
                    logger.warning("check_duplicates: No valid duplicates found after validation")
                    # Fall through to create events anyway

            return None

        except Exception as e:
            logger.error(f"check_duplicates: Error in duplicate checking: {e}")
            return None

    async def select_calendar(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select appropriate calendar for event. Can be overridden."""
        if self.calendar_agent and hasattr(self.calendar_agent, 'select_calendar') and callable(self.calendar_agent.select_calendar):
            try:
                calendar_result = await self.calendar_agent.select_calendar(event_data)
                if calendar_result.get("success"):
                    return calendar_result
            except Exception as e:
                logger.warning(f"Calendar agent selection failed: {e}")

        # Fallback to default calendar
        calendar_name = event_data.get('calendar_name', 'Primary Calendar')
        return {
            "success": True,
            "calendar_id": "primary",
            "calendar_name": calendar_name
        }

    def prepare_event_for_creation(self, event_data: Dict[str, Any], calendar_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare event data for calendar API."""
        prepared_event = event_data.copy()
        prepared_event["calendar_id"] = calendar_info.get("calendar_id", "primary")
        prepared_event["calendar_name"] = calendar_info.get("calendar_name", "Primary Calendar")
        return prepared_event

    def log_operation_start(self, operation: str, chat_id: int, event_data: Dict[str, Any]) -> None:
        """Log operation start with consistent format."""
        event_count = 1
        if "events" in event_data and isinstance(event_data["events"], list):
            event_count = len(event_data["events"])

        self.log_operation(operation, chat_id, {
            "event_count": event_count,
            "has_multiple_events": event_count > 1,
            "intent": event_data.get("intent", "unknown")
        })

    async def run_with_hooks(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run operation with pre and post execution hooks."""
        try:
            # Validate input
            if not await self.validate_input(event_data):
                return {
                    "success": False,
                    "error": "Invalid input data",
                    "message": "Sorry, I had trouble understanding your request. Could you please try again?"
                }

            # Pre-execution hook
            pre_result = await self.pre_execute(chat_id, event_data)
            if not pre_result.get("success", True):
                return pre_result

            # Log operation start
            self.log_operation_start(self.__class__.__name__.lower(), chat_id, event_data)

            # Execute main operation
            result = await self.execute(chat_id, event_data)

            # Post-execution hook
            await self.post_execute(chat_id, result)

            return result

        except Exception as e:
            logger.error(f"Error in operation {self.__class__.__name__}: {e}")
            await self.handle_error(chat_id, e, self.__class__.__name__.lower())
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred during the operation."
            }
