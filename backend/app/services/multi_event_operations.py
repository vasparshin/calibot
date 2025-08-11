"""
Multi-event operation handler for batch operations like delete, update, move.
Handles operations that affect multiple events with user confirmation.

UPDATED: Now uses centralized message formatting from BOT_RULES.md specifications.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

# Import centralized formatters for consistent messaging
try:
    from ..utils.message_formatter import MessageFormatter
    from ..utils.inline_keyboard import InlineKeyboardHelper
except ImportError:
    # Fallback for development/testing
    MessageFormatter = None
    InlineKeyboardHelper = None

logger = logging.getLogger(__name__)

class MultiEventOperationHandler:
    def __init__(self, calendar_service, telegram_service, conversation_state):
        self.calendar_service = calendar_service
        self.telegram_service = telegram_service
        self.conversation_state = conversation_state
        self.pending_operations = {}  # Store pending operations by chat_id
        # Clear any stale operations on startup
        self.clear_all_pending_operations()
    
    async def handle_delete_operation(self, chat_id: int, event_data: Dict) -> Dict:
        """Handle delete operations - find matching events and confirm with user"""
        try:
            # Find matching events
            matching_events = await self._find_matching_events(event_data)
            
            if not matching_events:
                return {
                    "success": False,
                    "message": "No events found matching your criteria.",
                    "requires_user_action": False
                }
            
            # If only one event, proceed with simple confirmation
            if len(matching_events) == 1:
                event = matching_events[0]
                operation_id = f"delete_{chat_id}_{datetime.now().timestamp()}"
                
                self.pending_operations[operation_id] = {
                    "type": "delete_single",
                    "chat_id": chat_id,
                    "events": matching_events,
                    "original_request": event_data
                }
                
                return {
                    "success": True,
                    "message": f"Found 1 event to delete:\n• {event['summary']} on {event['date']} at {event['start_time']}\n\nType 'yes' to confirm deletion.",
                    "requires_user_action": True,
                    "operation_id": operation_id
                }
            
            # Multiple events - show list and ask for confirmation
            else:
                operation_id = f"delete_{chat_id}_{datetime.now().timestamp()}"
                
                self.pending_operations[operation_id] = {
                    "type": "delete_multiple",
                    "chat_id": chat_id,
                    "events": matching_events,
                    "original_request": event_data
                }
                
                # Use centralized formatter if available
                if MessageFormatter:
                    # Convert events to proper format
                    formatted_events = []
                    for event in matching_events:
                        formatted_event = {
                            'summary': event.get('summary', 'Untitled'),
                            'start': event.get('date', '') + 'T' + event.get('start_time', ''),
                            'end': event.get('date', '') + 'T' + event.get('end_time', ''),
                            'calendar_name': event.get('calendar_name', 'Unknown Calendar'),
                            'id': event.get('event_id', ''),
                            'htmlLink': event.get('calendar_link', '')
                        }
                        formatted_events.append(formatted_event)
                    
                    message = MessageFormatter.format_confirmation_message("delete", formatted_events, len(matching_events))
                    keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("delete") if InlineKeyboardHelper else None
                else:
                    # Legacy fallback - FIXED to follow BOT_RULES.md
                    message = f"Found {len(matching_events)} events to delete:\n\n"
                    
                    # Show ALL events with proper formatting
                    for i, event in enumerate(matching_events, 1):
                        event_name = event.get('summary', 'Untitled')
                        date = event.get('date', 'Unknown date')
                        start_time = event.get('start_time', 'Unknown time')
                        calendar_name = event.get('calendar_name', 'Unknown')
                        
                        # Add hyperlink if available
                        event_id = event.get('event_id', '')
                        calendar_link = event.get('calendar_link', '')
                        
                        if calendar_link:
                            formatted_name = f"[{event_name}]({calendar_link})"
                        elif event_id:
                            formatted_name = f"[{event_name}](https://calendar.google.com/calendar/event?eid={event_id})"
                        else:
                            formatted_name = event_name
                        
                        message += f"{i}. {formatted_name} on {date} at {start_time} ({calendar_name})\n"
                    
                    message += f"\nChoose an option:\n"
                    message += f"• 'one' or '1' - Review and delete one by one\n"
                    message += f"• 'all' or 'yes' - Delete all events now\n"
                    message += f"• 'cancel' or 'c' - Cancel operation"
                    
                    keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("delete") if InlineKeyboardHelper else None
                
                return {
                    "success": True,
                    "message": message,
                    "requires_user_action": True,
                    "operation_id": operation_id,
                    "keyboard": keyboard
                }
                
        except Exception as e:
            logger.error(f"Error in delete operation: {e}")
            return {
                "success": False,
                "message": f"Error processing delete request: {str(e)}",
                "requires_user_action": False
            }
    
    async def handle_update_operation(self, chat_id: int, event_data: Dict) -> Dict:
        """Handle update operations"""
        try:
            matching_events = await self._find_matching_events(event_data)
            
            if not matching_events:
                return {
                    "success": False,
                    "message": "No events found matching your criteria.",
                    "requires_user_action": False
                }
            
            operation_id = f"update_{chat_id}_{datetime.now().timestamp()}"
            
            self.pending_operations[operation_id] = {
                "type": "update_multiple",
                "chat_id": chat_id,
                "events": matching_events,
                "original_request": event_data
            }
            
            # Check if we have specific changes to describe
            has_specific_changes = any(key in event_data for key in ['calendar_name', 'new_event_name', 'new_date', 'time_shift'])
            
            if has_specific_changes:
                # Show detailed change description when we have specific changes
                event_list = ""
                for i, event in enumerate(matching_events, 1):
                    event_name = event.get('summary', 'Untitled')
                    date = event.get('date', 'Unknown date')
                    start_time = event.get('start_time', 'Unknown time')
                    calendar_name = event.get('calendar_name', 'Unknown')
                    
                    # Add hyperlink if available
                    event_id = event.get('event_id', '')
                    calendar_link = event.get('calendar_link', '')
                    
                    if calendar_link:
                        formatted_name = f"[{event_name}]({calendar_link})"
                    elif event_id:
                        formatted_name = f"[{event_name}](https://calendar.google.com/calendar/event?eid={event_id})"
                    else:
                        formatted_name = event_name
                    
                    event_list += f"{i}. {formatted_name} on {date} at {start_time} ({calendar_name})\n"
                
                # Describe what will be updated
                update_desc = []
                if 'new_event_name' in event_data:
                    update_desc.append(f"rename to '{event_data['new_event_name']}'")
                if 'new_date' in event_data:
                    update_desc.append(f"move to {event_data['new_date']}")
                if 'time_shift' in event_data:
                    update_desc.append(f"shift time by {event_data['time_shift']}")
                if 'calendar_name' in event_data:
                    update_desc.append(f"move to '{event_data['calendar_name']}' calendar")
                
                update_description = " and ".join(update_desc) if update_desc else "update"
                
                message = f"Found {len(matching_events)} events to update (review proposed changes):\n\n{event_list}\nWill {update_description}"
                keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("update") if InlineKeyboardHelper else None
            elif MessageFormatter:
                # Use centralized formatter when no specific changes to describe  
                formatted_events = []
                for event in matching_events:
                    formatted_event = {
                        'summary': event.get('summary', 'Untitled'),
                        'start': event.get('date', '') + 'T' + event.get('start_time', ''),
                        'end': event.get('date', '') + 'T' + event.get('end_time', ''),
                        'calendar_name': event.get('calendar_name', 'Unknown Calendar'),
                        'id': event.get('event_id', ''),
                        'htmlLink': event.get('calendar_link', '')
                    }
                    formatted_events.append(formatted_event)
                
                message = MessageFormatter.format_confirmation_message("update", formatted_events, len(matching_events))
                keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("update") if InlineKeyboardHelper else None
            else:
                # Fallback when no MessageFormatter available
                event_list = "\n".join([
                    f"• {event['summary']} on {event['date']} at {event['start_time']}"
                    for event in matching_events
                ])
                
                message = f"Found {len(matching_events)} events to update:\n{event_list}"
                keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("update") if InlineKeyboardHelper else None
            
            return {
                "success": True,
                "message": message,
                "requires_user_action": True,
                "operation_id": operation_id,
                "keyboard": keyboard
            }
            
        except Exception as e:
            logger.error(f"Error in update operation: {e}")
            return {
                "success": False,
                "message": f"Error processing update request: {str(e)}",
                "requires_user_action": False
            }
    
    async def confirm_operation(self, chat_id: int, user_confirmation: str) -> Dict:
        """Process user confirmation for pending operations"""
        try:
            # Find pending operation for this chat
            pending_op = None
            operation_id = None
            
            for op_id, op_data in self.pending_operations.items():
                if op_data["chat_id"] == chat_id:
                    pending_op = op_data
                    operation_id = op_id
                    break
            
            if not pending_op:
                return {
                    "success": False,
                    "message": "No pending operation found. Please start a new request.",
                    "requires_user_action": False
                }
            
            user_response = user_confirmation.lower().strip()
            
            if user_response in ['yes', 'y', 'confirm', 'proceed', 'all']:
                # Execute all operations immediately
                result = await self._execute_operation(pending_op)
                
                # Clean up pending operation
                del self.pending_operations[operation_id]
                
                return result
            
            elif user_response in ['one', '1', 'individual', 'step']:
                # Switch to one-by-one processing using event queue handler
                events = pending_op["events"]
                original_request = pending_op["original_request"]
                op_type = pending_op["type"]
                
                # Convert to queue format
                queue_events = []
                for event in events:
                    queue_event = {
                        "intent": "update" if "update" in op_type else "delete",
                        "event_id": event.get("id", event.get("event_id")),
                        "event_name": event.get("summary", ""),
                        "start_time": event.get("start", event.get("start_time", "")),
                        "end_time": event.get("end", event.get("end_time", "")),
                        "calendar_id": event.get("calendar_id", "primary"),
                        "calendar_name": event.get("calendar_name", "Unknown"),
                        **original_request  # Include the update parameters
                    }
                    queue_events.append(queue_event)
                
                # Create event queue (need to import EventQueueHandler)
                try:
                    from .event_queue_handler import EventQueueHandler
                    # Pass required dependencies
                    queue_handler = EventQueueHandler(
                        self.telegram_service,
                        self.conversation_state,
                        self.calendar_service,
                        getattr(self.calendar_service, 'calendar_agent', None)
                    )
                    queue_result = queue_handler.create_event_queue_from_list(chat_id, queue_events)
                    
                    # Clean up pending operation
                    del self.pending_operations[operation_id]
                    
                    return queue_result
                except ImportError:
                    # Fallback if queue handler not available
                    result = await self._execute_operation(pending_op)
                    del self.pending_operations[operation_id]
                    return result
            
            elif user_response in ['no', 'n', 'cancel', 'abort']:
                # Cancel operation
                del self.pending_operations[operation_id]
                
                return {
                    "success": True,
                    "message": "Operation cancelled.",
                    "requires_user_action": False
                }
            
            else:
                # Invalid response, keep operation pending
                return {
                    "success": False,
                    "message": "Please respond with 'yes' to confirm or 'cancel' to abort the operation.",
                    "requires_user_action": True
                }
                
        except Exception as e:
            logger.error(f"Error confirming operation: {e}")
            return {
                "success": False,
                "message": f"Error processing confirmation: {str(e)}",
                "requires_user_action": False
            }
    
    async def _find_matching_events(self, criteria: Dict) -> List[Dict]:
        """Find events matching the given criteria"""
        try:
            # Build query parameters
            query_params = {}
            
            if 'event_name' in criteria:
                query_params['q'] = criteria['event_name']
            
            if 'date' in criteria:
                query_params['timeMin'] = f"{criteria['date']}T00:00:00Z"
                query_params['timeMax'] = f"{criteria['date']}T23:59:59Z"
            else:
                # Default to today if no date specified
                today = datetime.now().strftime("%Y-%m-%d")
                query_params['timeMin'] = f"{today}T00:00:00Z"
                query_params['timeMax'] = f"{today}T23:59:59Z"
            
            # Get events from calendar service
            events_response = await self.calendar_service.get_events(query_params)
            
            if not events_response.get('success'):
                return []
            
            events = events_response.get('events', [])
            
            # Filter events more precisely if needed
            if 'event_name' in criteria:
                event_name = criteria['event_name'].lower()
                events = [
                    event for event in events 
                    if event_name in event.get('summary', '').lower()
                ]
            
            logger.info(f"Found {len(events)} matching events for criteria: {criteria}")
            return events
            
        except Exception as e:
            logger.error(f"Error finding matching events: {e}")
            return []
    
    async def _execute_operation(self, operation: Dict) -> Dict:
        """Execute the confirmed operation"""
        try:
            op_type = operation["type"]
            events = operation["events"]
            
            if op_type == "delete_single":
                # Delete single event
                event = events[0]
                result = await self.calendar_service.delete_event(event["id"])
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"Deleted event: {event.get('summary', 'Untitled')}",
                        "requires_user_action": False
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to delete event: {result.get('message', 'Unknown error')}",
                        "requires_user_action": False
                    }
            
            elif op_type == "delete_multiple":
                # Delete multiple events
                successful_deletes = []
                failed_deletes = []
                
                for event in events:
                    try:
                        result = await self.calendar_service.delete_event(event["id"])
                        if result.get("success"):
                            successful_deletes.append(event.get('summary', 'Untitled'))
                        else:
                            failed_deletes.append(f"{event.get('summary', 'Untitled')}: {result.get('message', 'Unknown error')}")
                    except Exception as e:
                        failed_deletes.append(f"{event.get('summary', 'Untitled')}: {str(e)}")
                        logger.error(f"Error deleting event {event.get('id', 'unknown')}: {e}")
                
                # Build response message
                message_parts = []
                if successful_deletes:
                    message_parts.append(f"Successfully deleted {len(successful_deletes)} events:")
                    for event_name in successful_deletes:
                        message_parts.append(f"  • {event_name}")
                
                if failed_deletes:
                    message_parts.append(f"\nFailed to delete {len(failed_deletes)} events:")
                    for failure in failed_deletes:
                        message_parts.append(f"  • {failure}")
                
                return {
                    "success": len(successful_deletes) > 0,
                    "message": "\n".join(message_parts),
                    "requires_user_action": False
                }
            
            elif op_type == "update_multiple":
                # Update multiple events
                original_request = operation["original_request"]
                
                successful_updates = []
                failed_updates = []
                
                for event in events:
                    try:
                        # Prepare update data based on what fields are provided
                        update_data = {
                            "event_id": event["id"]
                        }
                        
                        # Handle different types of updates
                        if 'new_event_name' in original_request:
                            update_data['event_name'] = original_request['new_event_name']
                        
                        if 'new_date' in original_request:
                            # Parse the original event start and end times
                            original_start = event.get('start', '')
                            original_end = event.get('end', '')
                            
                            # Extract time portion if datetime format
                            if 'T' in original_start:
                                start_time = original_start.split('T')[1].split('+')[0]  # Get time part
                                end_time = original_end.split('T')[1].split('+')[0] if 'T' in original_end else start_time
                            else:
                                start_time = "14:00:00"  # Default time
                                end_time = "14:30:00"
                            
                            # Create new datetime strings
                            new_date = original_request['new_date']
                            update_data['start_time'] = f"{new_date}T{start_time}"
                            update_data['end_time'] = f"{new_date}T{end_time}"
                        
                        if 'time_shift' in original_request:
                            # Handle time shifting logic - calculate new times based on shift
                            time_shift = original_request['time_shift']
                            
                            # Parse current start and end times
                            original_start = event.get('start', '')
                            original_end = event.get('end', '')
                            
                            # Handle different event data formats
                            if not original_start and 'start_time' in event:
                                original_start = event['start_time']
                            if not original_end and 'end_time' in event:
                                original_end = event['end_time']
                            
                            logger.info(f"Time shift request: {time_shift} for event {event.get('summary', 'Unknown')}")
                            logger.info(f"Original times: start={original_start}, end={original_end}")
                            
                            if original_start and original_end and 'T' in original_start and 'T' in original_end:
                                from datetime import datetime, timedelta
                                import re
                                
                                try:
                                    # Parse original datetime strings
                                    start_dt = datetime.fromisoformat(original_start.replace('Z', '+00:00'))
                                    end_dt = datetime.fromisoformat(original_end.replace('Z', '+00:00'))
                                    
                                    logger.info(f"Parsed times: start={start_dt}, end={end_dt}")
                                    
                                    # Parse time shift (e.g., "1 hour", "30 minutes", "2 hours")
                                    shift_match = re.search(r'(\d+)\s*(hour|minute|hr|min)', time_shift.lower())
                                    if shift_match:
                                        amount = int(shift_match.group(1))
                                        unit = shift_match.group(2)
                                        
                                        if unit in ['hour', 'hr']:
                                            # Set end time to be exactly X hours after start
                                            new_end_dt = start_dt + timedelta(hours=amount)
                                        elif unit in ['minute', 'min']:
                                            # Set end time to be exactly X minutes after start  
                                            new_end_dt = start_dt + timedelta(minutes=amount)
                                        
                                        # CRITICAL: Keep start time unchanged, only modify end time
                                        update_data['start_time'] = start_dt.isoformat()
                                        update_data['end_time'] = new_end_dt.isoformat()
                                        
                                        logger.info(f"BEFORE UPDATE: Event start={original_start}, end={original_end}")
                                        logger.info(f"TIME SHIFT: {time_shift} parsed as {amount} {unit}")
                                        logger.info(f"AFTER CALCULATION: start={update_data['start_time']}, end={update_data['end_time']}")
                                        logger.info(f"EXPECTED RESULT: Start time unchanged, end time = start + {amount} {unit}")
                                        logger.info(f"Sending to calendar service: start={update_data['start_time']}, end={update_data['end_time']}")
                                    else:
                                        logger.warning(f"Could not parse time shift: {time_shift}")
                                except Exception as parse_error:
                                    logger.error(f"Error parsing datetime for time shift: {parse_error}")
                            else:
                                logger.warning(f"Invalid datetime format for time shift: start={original_start}, end={original_end}")
                        
                        if 'description' in original_request:
                            update_data['description'] = original_request['description']
                        
                        if 'location' in original_request:
                            update_data['location'] = original_request['location']
                        
                        # Handle calendar moves (NEW FUNCTIONALITY)
                        target_calendar_id = None
                        if 'calendar_name' in original_request or 'new_calendar' in original_request:
                            target_calendar_name = original_request.get('calendar_name') or original_request.get('new_calendar')
                            
                            # Pass calendar name to calendar service (it will handle the resolution)
                            update_data['calendar_name'] = target_calendar_name
                            logger.info(f"Setting target calendar for move: {target_calendar_name}")
                        
                        # Get the calendar ID for the update
                        calendar_id = event.get('calendar_id', 'primary')
                        
                        result = self.calendar_service.update_event(
                            event["id"], 
                            update_data, 
                            source_calendar_id=calendar_id
                        )
                        
                        if result.get("success"):
                            # Create descriptive update message with hyperlink using centralized formatter
                            event_name = event.get('summary', 'Untitled')
                            
                            # Use MessageFormatter for consistent URL formatting
                            if MessageFormatter:
                                # Get the event link from result or event
                                existing_link = result.get('event_link', '') or event.get('htmlLink', '') or event.get('calendar_link', '')
                                # Use centralized hyperlink creation
                                formatted_name = MessageFormatter.create_event_hyperlink(
                                    event_name, 
                                    event["id"], 
                                    existing_link if existing_link else None
                                )
                            else:
                                # Fallback for testing/development
                                event_id = event["id"]
                                formatted_name = f"[{event_name}](https://calendar.google.com/calendar/event?eid={event_id})"
                                
                            # Extract date from the original event for display
                            event_date = event.get('date', '')
                            if not event_date and 'start' in event:
                                # Extract date from start datetime
                                start_dt = event['start']
                                if 'T' in start_dt:
                                    event_date = start_dt.split('T')[0]
                                    
                            # Format date for display
                            if event_date:
                                try:
                                    from datetime import datetime
                                    date_obj = datetime.fromisoformat(event_date)
                                    formatted_date = date_obj.strftime('%A, %B %d, %Y')
                                except:
                                    formatted_date = event_date
                            else:
                                formatted_date = "today"
                            
                            update_desc = f"• Updated {formatted_name}"
                            if 'new_date' in original_request:
                                update_desc += f" - moved to {original_request['new_date']}"
                            if 'new_event_name' in original_request:
                                update_desc += f" - renamed to {original_request['new_event_name']}"
                            if 'time_shift' in original_request:
                                update_desc += f" - extended by {original_request['time_shift']}"
                            if 'calendar_name' in original_request:
                                update_desc += f" - moved to {original_request['calendar_name']} calendar"
                                
                            successful_updates.append(update_desc)
                        else:
                            failed_updates.append(f"{event.get('summary', 'Untitled')}: {result.get('message', 'Unknown error')}")
                    except Exception as e:
                        failed_updates.append(f"{event.get('summary', 'Untitled')}: {str(e)}")
                        logger.error(f"Error updating event {event.get('id', 'unknown')}: {e}")
                
                # Build response message
                message_parts = []
                if successful_updates:
                    # Extract date from original request or first event for header
                    header_date = original_request.get('new_date') or original_request.get('date')
                    if not header_date and events:
                        # Get date from first event
                        first_event = events[0]
                        if 'start' in first_event and 'T' in first_event['start']:
                            header_date = first_event['start'].split('T')[0]
                        elif 'date' in first_event:
                            header_date = first_event['date']
                    
                    # Format the header date
                    if header_date:
                        try:
                            from datetime import datetime
                            date_obj = datetime.fromisoformat(header_date)
                            formatted_date = date_obj.strftime('%A, %B %d, %Y')
                        except:
                            formatted_date = header_date
                    else:
                        formatted_date = "today"
                    
                    message_parts.append(f"Successfully updated all {len(successful_updates)} events on {formatted_date}:")
                    message_parts.append("")  # Empty line
                    for update_desc in successful_updates:
                        message_parts.append(update_desc)
                
                if failed_updates:
                    if successful_updates:
                        message_parts.append("")  # Empty line before failures
                    message_parts.append(f"Failed to update {len(failed_updates)} events:")
                    for failure in failed_updates:
                        message_parts.append(f"  • {failure}")
                
                return {
                    "success": len(successful_updates) > 0,
                    "message": "\n".join(message_parts),
                    "requires_user_action": False
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown operation type: {op_type}",
                    "requires_user_action": False
                }
                
        except Exception as e:
            logger.error(f"Error executing operation: {e}")
            return {
                "success": False,
                "message": f"Error executing operation: {str(e)}",
                "requires_user_action": False
            }
    
    def has_pending_operation(self, chat_id: int) -> bool:
        """Check if there's a pending operation for this chat"""
        return any(op["chat_id"] == chat_id for op in self.pending_operations.values())
    
    def store_pending_operation(self, chat_id: int, operation_data: Dict):
        """Store a pending operation for later processing"""
        operation_id = f"{chat_id}_{len(self.pending_operations)}"
        self.pending_operations[operation_id] = {
            "chat_id": chat_id,
            "operation_id": operation_id,
            **operation_data
        }
        logger.info(f"Stored pending operation {operation_id} for chat {chat_id}")
    
    def clear_pending_operations(self, chat_id: int):
        """Clear all pending operations for a chat (useful for cleanup)"""
        to_remove = [
            op_id for op_id, op_data in self.pending_operations.items()
            if op_data["chat_id"] == chat_id
        ]
        for op_id in to_remove:
            del self.pending_operations[op_id]
    
    def clear_all_pending_operations(self):
        """Clear all pending operations (useful for startup cleanup)"""
        self.pending_operations.clear()
        logger.info("Cleared all pending operations on startup")
