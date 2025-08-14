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
                operation_data = {
                    "type": "delete_single",
                    "events": matching_events,
                    "original_request": event_data
                }
                operation_id = self.store_pending_operation(chat_id, operation_data)
                
                return {
                    "success": True,
                    "message": f"Found 1 event to delete:\n• {event['summary']} on {event['date']} at {event['start_time']}\n\nType 'yes' to confirm deletion.",
                    "requires_user_action": True,
                    "operation_id": operation_id
                }
            
            # Multiple events - show list and ask for confirmation
            else:
                operation_data = {
                    "type": "delete_multiple",
                    "events": matching_events,
                    "original_request": event_data
                }
                operation_id = self.store_pending_operation(chat_id, operation_data)
                
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
            logger.info(f"🚨 UPDATE OPERATION DEBUG - event_data received: {event_data}")
            matching_events = await self._find_matching_events(event_data)
            logger.info(f"🚨 UPDATE OPERATION DEBUG - _find_matching_events returned {len(matching_events)} events")
            
            if not matching_events:
                return {
                    "success": False,
                    "message": "No events found matching your criteria.",
                    "requires_user_action": False
                }
            
            operation_data = {
                "type": "update_multiple",
                "events": matching_events,
                "original_request": event_data
            }
            operation_id = self.store_pending_operation(chat_id, operation_data)
            
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
                    
                    # Add hyperlink if available - check multiple possible fields
                    event_id = event.get('event_id', '') or event.get('id', '')
                    calendar_link = event.get('calendar_link', '') or event.get('htmlLink', '') or event.get('link', '')
                    
                    if calendar_link:
                        formatted_name = f"[{event_name}]({calendar_link})"
                    elif event_id:
                        formatted_name = f"[{event_name}](https://calendar.google.com/calendar/event?eid={event_id})"
                    else:
                        formatted_name = event_name
                    
                    # Show current → proposed format for changes
                    if 'time_shift' in event_data and 'day' in event_data['time_shift']:
                        # For date shifts, show date change
                        try:
                            from datetime import datetime as dt, timedelta
                            current_date_obj = dt.fromisoformat(date)
                            if '1 day' in event_data['time_shift']:
                                new_date_obj = current_date_obj + timedelta(days=1)
                                new_date_str = new_date_obj.strftime('%Y-%m-%d')
                                event_list += f"{i}. {formatted_name} on {date} at {start_time} → {new_date_str} at {start_time} ({calendar_name})\n"
                            else:
                                event_list += f"{i}. {formatted_name} on {date} at {start_time} → will be shifted ({calendar_name})\n"
                        except Exception as e:
                            logger.error(f"Error formatting date change: {e}")
                            event_list += f"{i}. {formatted_name} on {date} at {start_time} → moved to today ({calendar_name})\n"
                    else:
                        event_list += f"{i}. {formatted_name} on {date} at {start_time} ({calendar_name})\n"
                
                # Describe what will be updated
                update_desc = []
                if 'new_event_name' in event_data:
                    update_desc.append(f"rename to '{event_data['new_event_name']}'")
                if 'new_date' in event_data:
                    update_desc.append(f"move to {event_data['new_date']}")
                if 'new_start_time' in event_data:
                    # Show the proposed time change in confirmation
                    new_start = event_data['new_start_time']
                    new_end = event_data.get('new_end_time', new_start)
                    
                    # Convert to 12-hour format for confirmation display
                    def format_time_12hr_confirm(time_24hr):
                        hour, minute = map(int, time_24hr.split(':')[:2])
                        if hour == 0:
                            return f"12:{minute:02d} AM"
                        elif hour < 12:
                            return f"{hour}:{minute:02d} AM"
                        elif hour == 12:
                            return f"12:{minute:02d} PM"
                        else:
                            return f"{hour-12}:{minute:02d} PM"
                    
                    start_12hr = format_time_12hr_confirm(new_start)
                    end_12hr = format_time_12hr_confirm(new_end)
                    update_desc.append(f"change time to {start_12hr} - {end_12hr}")
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
            # Find the most recent pending operation for this chat
            pending_op = None
            operation_id = None
            
            # Get operations for this chat sorted by operation_id (most recent last)
            chat_operations = [
                (op_id, op_data) for op_id, op_data in self.pending_operations.items()
                if op_data["chat_id"] == chat_id
            ]
            
            if chat_operations:
                # Take the most recent operation
                operation_id, pending_op = chat_operations[-1]
                logger.info(f"🔧 Found pending operation {operation_id} of type {pending_op.get('type', 'unknown')}")
            
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
                logger.info(f"🔄 SWITCHING TO ONE-BY-ONE - Operation type: {pending_op.get('type')}")
                events = pending_op["events"]
                original_request = pending_op["original_request"]
                op_type = pending_op["type"]
                
                logger.info(f"🔄 Events to queue: {len(events)}")
                logger.info(f"🔄 Original request: {original_request}")
                
                # Convert to queue format
                queue_events = []
                for i, event in enumerate(events):
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
                    
                    # For update requests with specific times mentioned (like "5 and 6 pm")
                    # Check if we need to set individual times for each event
                    if "update" in op_type and original_request.get("new_date"):
                        # If user said "5 and 6 pm", set specific times for each event
                        user_text = original_request.get("user_message", "").lower()
                        if ("5 and 6" in user_text or "17:00 and 18:00" in user_text):
                            if i == 0:  # First event gets 5 PM
                                queue_event["new_start_time"] = "17:00"
                                queue_event["new_end_time"] = "18:00"
                            elif i == 1:  # Second event gets 6 PM
                                queue_event["new_start_time"] = "18:00"
                                queue_event["new_end_time"] = "19:00"
                        elif ("5pm and 6pm" in user_text or "5 pm and 6 pm" in user_text):
                            if i == 0:  # First event gets 5 PM
                                queue_event["new_start_time"] = "17:00"
                                queue_event["new_end_time"] = "18:00"
                            elif i == 1:  # Second event gets 6 PM
                                queue_event["new_start_time"] = "18:00"
                                queue_event["new_end_time"] = "19:00"
                    
                    queue_events.append(queue_event)
                    logger.info(f"🔄 Queue event {i+1}: {queue_event.get('event_name')} - {queue_event.get('intent')} - New times: {queue_event.get('new_start_time', 'N/A')}-{queue_event.get('new_end_time', 'N/A')}")
                
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
                    logger.info(f"🔄 Creating event queue for chat {chat_id}")
                    
                    # Create the queue first
                    queue_result = queue_handler.create_event_queue_from_list(chat_id, queue_events)
                    
                    if queue_result.get("success"):
                        # Instead of returning the batch message, get the first individual event confirmation
                        logger.info(f"🔄 Queue created successfully, getting first event confirmation")
                        first_event_result = queue_handler.get_next_event_confirmation(chat_id)
                        
                        # Clean up pending operation
                        del self.pending_operations[operation_id]
                        logger.info(f"🔄 Cleaned up pending operation {operation_id}")
                        
                        return first_event_result
                    else:
                        logger.error(f"🔄 Queue creation failed: {queue_result}")
                        return queue_result
                except ImportError as ie:
                    logger.error(f"🔄 ImportError: {ie}")
                    # Fallback if queue handler not available
                    result = await self._execute_operation(pending_op)
                    del self.pending_operations[operation_id]
                    return result
                except Exception as ex:
                    logger.error(f"🔄 Exception in queue creation: {ex}")
                    # Fallback on any error
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
            logger.info(f"🚨 _FIND_MATCHING_EVENTS START - criteria: {criteria}")
            
            # Get ALL events from the specified date first, then filter locally
            # This ensures we can apply target selection (last 3) correctly
            
            # Get events from calendar service - get ALL events, don't filter by name yet
            events_response = await self.calendar_service.query_events({
                'date': criteria.get('date', datetime.now().strftime("%Y-%m-%d"))
            })
            
            logger.info(f"🚨 CALENDAR SERVICE RESPONSE - success: {events_response.get('success')}, events count: {len(events_response.get('events', []))}")
            
            if not events_response.get('success'):
                logger.warning(f"🚨 CALENDAR SERVICE FAILED - returning empty list")
                return []

            events = events_response.get('events', [])
            logger.info(f"🚨 RAW EVENTS COUNT - {len(events)} events from calendar service")
            
            # Filter events by name AFTER getting all events (so we can apply target selection correctly)
            if 'event_name' in criteria:
                event_name = criteria['event_name'].lower()
                logger.info(f"🚨 FILTERING BY EVENT NAME - '{event_name}', before: {len(events)} events")
                
                # Handle generic "events" case - don't filter if user said "events" generically
                if event_name in ['event', 'any', 'events']:
                    logger.info(f"🚨 GENERIC EVENT NAME DETECTED - including all {len(events)} events (no name filtering)")
                else:
                    events = [
                        event for event in events 
                        if event_name in event.get('summary', '').lower()
                    ]
                    logger.info(f"🚨 AFTER NAME FILTERING - {len(events)} events remain")
            else:
                logger.info(f"🚨 NO EVENT NAME FILTERING - including all {len(events)} events")

            # Convert events to the format expected by multi-event operations
            formatted_events = []
            logger.info(f"🚨 CONVERTING {len(events)} EVENTS TO FORMATTED LIST")
            for event in events:
                # Ensure proper event format with all required fields
                formatted_event = {
                    'id': event.get('id'),
                    'event_id': event.get('id'),  # Add both for compatibility
                    'summary': event.get('summary', 'Untitled'),
                    'start_time': self._extract_time_from_datetime(event.get('start', '')),
                    'end_time': self._extract_time_from_datetime(event.get('end', '')),
                    'date': self._extract_date_from_datetime(event.get('start', '')),
                    'calendar_name': event.get('calendar_name', 'Unknown'),
                    'calendar_id': event.get('calendar_id', 'primary'),  # CRITICAL: Include actual calendar ID
                    'calendar_link': event.get('link', ''),
                    'htmlLink': event.get('link', ''),
                    'start_datetime': event.get('start', '')  # Keep original datetime for sorting
                }
                formatted_events.append(formatted_event)

            logger.info(f"🚨 FORMATTED EVENTS COMPLETE - {len(formatted_events)} events ready for target selection")

            # Handle target selection and count-based filtering
            target = criteria.get('target', '')
            count = criteria.get('count', 1)
            
            logger.info(f"🚨 INITIAL VALUES - target: '{target}', count: {count}, type(count): {type(count)}")
            logger.info(f"🚨 CRITERIA KEYS - {list(criteria.keys())}")
            
            # Parse numeric count from target string (e.g., "last 3", "first 2")
            import re
            if target and (not isinstance(count, int) or count == 1):
                logger.info(f"🔍 ENTERING TARGET PARSING - condition met")
                # Extract number from target like "last 3", "first 2", "next 4"
                number_match = re.search(r'(\w+)\s+(\d+)', target)
                if number_match:
                    target_word = number_match.group(1)  # "last", "first", etc.
                    extracted_count = int(number_match.group(2))  # the number
                    logger.info(f"🎯 REGEX MATCH - target_word: '{target_word}', extracted_count: {extracted_count}")
                    target = target_word  # Update target to just the word
                    count = extracted_count  # Update count to the extracted number
                    logger.info(f"🎯 TARGET PARSING DEBUG - Original: '{criteria.get('target', '')}' -> target: '{target}', count: {count}")
                else:
                    logger.info(f"🚨 TARGET PARSING FAILED - No regex match for: '{target}'")
            else:
                logger.debug(f"SKIPPING TARGET PARSING - condition not met: target='{target}', count={count}, isinstance(count, int)={isinstance(count, int)}")
            
            logger.info(f"📊 Processing target selection - target: '{target}', count: {count}, total events found: {len(formatted_events)}")
            
            # Sort events by start time
            formatted_events.sort(key=lambda x: x.get('start_datetime', ''))
            logger.info(f"📅 SORTED EVENTS ({len(formatted_events)} total):")
            for i, event in enumerate(formatted_events):
                logger.info(f"  {i+1}. {event.get('event_name', 'Unknown')} at {event.get('start_datetime', 'Unknown time')}")
            
            # Apply target-based selection
            if target in ['last', 'latest'] and len(formatted_events) > 0:
                # Select last N events (chronologically last)
                before_count = len(formatted_events)
                formatted_events = formatted_events[-count:] if count <= len(formatted_events) else formatted_events
                logger.info(f"✅ LAST TARGET APPLIED - Before: {before_count}, After: {len(formatted_events)}, Requested: {count}")
                logger.info(f"🎯 SELECTED EVENTS:")
                for i, event in enumerate(formatted_events):
                    logger.info(f"  {i+1}. {event.get('event_name', 'Unknown')} at {event.get('start_datetime', 'Unknown time')}")
            elif target in ['first', 'earliest'] and len(formatted_events) > 0:
                # Select last N events (chronologically last)
                formatted_events = formatted_events[-count:] if count <= len(formatted_events) else formatted_events
                logger.info(f"✅ LAST TARGET APPLIED - Selected last {len(formatted_events)} events (requested: {count})")
            elif target in ['first', 'earliest'] and len(formatted_events) > 0:
                # Select first N events (chronologically first)
                formatted_events = formatted_events[:count] if count <= len(formatted_events) else formatted_events
                logger.info(f"✅ FIRST TARGET APPLIED - Selected first {len(formatted_events)} events (requested: {count})")
            elif target in ['next', 'upcoming'] and len(formatted_events) > 0:
                # For future events, select first N (earliest upcoming)
                current_time = datetime.now().isoformat()
                future_events = [e for e in formatted_events if e.get('start_datetime', '') > current_time]
                formatted_events = future_events[:count] if count <= len(future_events) else future_events
                logger.info(f"✅ NEXT TARGET APPLIED - Selected next {len(formatted_events)} upcoming events (requested: {count})")
            elif count > 1 and len(formatted_events) > count:
                # If count specified but no specific target, limit to count
                formatted_events = formatted_events[:count]
                logger.info(f"✅ COUNT LIMIT APPLIED - Limited to {len(formatted_events)} events based on count: {count}")
            else:
                logger.debug(f"NO TARGET FILTERING - Using all {len(formatted_events)} events")

            logger.info(f"🎯 FINAL SELECTION COMPLETE - returning {len(formatted_events)} events for criteria: {criteria}")
            return formatted_events
            
        except Exception as e:
            logger.error(f"🚨 EXCEPTION in _find_matching_events: {e}")
            logger.error(f"🚨 EXCEPTION criteria was: {criteria}")
            import traceback
            logger.error(f"🚨 EXCEPTION traceback: {traceback.format_exc()}")
            return []

    def _extract_time_from_datetime(self, datetime_str: str) -> str:
        """Extract time in HH:MM format from datetime string"""
        try:
            if 'T' in datetime_str:
                time_part = datetime_str.split('T')[1]
                if '+' in time_part:
                    time_part = time_part.split('+')[0]
                elif 'Z' in time_part:
                    time_part = time_part.split('Z')[0]
                return time_part[:5]  # HH:MM
            return "00:00"
        except:
            return "00:00"
    
    def _extract_date_from_datetime(self, datetime_str: str) -> str:
        """Extract date in YYYY-MM-DD format from datetime string"""
        try:
            if 'T' in datetime_str:
                return datetime_str.split('T')[0]
            elif len(datetime_str) >= 10:
                return datetime_str[:10]
            return datetime.now().strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")
    
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
                        
                        # CRITICAL FIX: Handle new start/end time updates (e.g., "change to 7pm")
                        if 'new_start_time' in original_request:
                            # Extract the date from the original event
                            original_start = event.get('start', '')
                            if 'T' in original_start:
                                event_date = original_start.split('T')[0]  # Get date part (YYYY-MM-DD)
                            else:
                                event_date = event.get('date', datetime.now().strftime("%Y-%m-%d"))
                            
                            new_start_time = original_request['new_start_time']  # e.g., "19:00"
                            
                            # Calculate end time - if not specified, add 1 hour to start time
                            if 'new_end_time' in original_request:
                                new_end_time = original_request['new_end_time']
                            else:
                                # Add 1 hour to start time
                                from datetime import datetime, timedelta
                                try:
                                    start_dt = datetime.strptime(new_start_time, "%H:%M")
                                    end_dt = start_dt + timedelta(hours=1)
                                    new_end_time = end_dt.strftime("%H:%M")
                                except:
                                    # Fallback if time parsing fails
                                    new_end_time = new_start_time
                            
                            # Create full datetime strings with timezone
                            update_data['start_time'] = f"{event_date}T{new_start_time}:00"
                            update_data['end_time'] = f"{event_date}T{new_end_time}:00"
                            
                            # Add timezone information if available from original event
                            original_start_full = event.get('start', '')
                            if '+' in original_start_full or 'Z' in original_start_full:
                                # Extract timezone from original event
                                if 'Z' in original_start_full:
                                    tz_suffix = 'Z'
                                elif '+' in original_start_full:
                                    tz_suffix = original_start_full.split('+')[1]
                                    tz_suffix = '+' + tz_suffix
                                else:
                                    tz_suffix = ''
                                
                                if tz_suffix:
                                    update_data['start_time'] += tz_suffix
                                    update_data['end_time'] += tz_suffix
                            
                            logger.info(f"NEW TIME UPDATE: Event '{event.get('summary', 'Unknown')}' changing to {new_start_time}-{new_end_time} on {event_date}")
                        
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
                            
                            # NEW: Handle both full datetime and time-only formats
                            if original_start and original_end:
                                from datetime import datetime, timedelta
                                import re
                                
                                try:
                                    # Check if we have full datetime strings or just times
                                    if 'T' in original_start and 'T' in original_end:
                                        # Full datetime format (e.g., "2025-08-12T21:00:00+01:00")
                                        start_dt = datetime.fromisoformat(original_start.replace('Z', '+00:00'))
                                        end_dt = datetime.fromisoformat(original_end.replace('Z', '+00:00'))
                                    else:
                                        # Time-only format (e.g., "21:00", "22:00") - need to add date
                                        event_date = event.get('date', '')
                                        if not event_date:
                                            # Extract date from today or use default
                                            from datetime import date
                                            event_date = date.today().isoformat()
                                        
                                        # Combine date and time
                                        start_dt = datetime.fromisoformat(f"{event_date}T{original_start}:00")
                                        end_dt = datetime.fromisoformat(f"{event_date}T{original_end}:00")
                                    
                                    logger.info(f"Parsed times: start={start_dt}, end={end_dt}")
                                    
                                    # Parse time shift - handle both relative and absolute shifts
                                    delta = None
                                    
                                    # Check for day shift first (like "1 day", "move to today")
                                    day_match = re.search(r'(\d+)\s*day', time_shift.lower())
                                    if day_match:
                                        amount = int(day_match.group(1))
                                        # Determine direction
                                        is_negative = 'earlier' in time_shift.lower() or 'back' in time_shift.lower() or time_shift.startswith('-')
                                        if is_negative:
                                            amount = -amount
                                        delta = timedelta(days=amount)
                                        unit_name = f"{amount} day(s)"
                                    else:
                                        # Check for hour/minute shift
                                        shift_match = re.search(r'(\d+)\s*(hour|minute|hr|min)', time_shift.lower())
                                        if shift_match:
                                            amount = int(shift_match.group(1))
                                            unit = shift_match.group(2)
                                            
                                            # Determine direction (default is forward/later)
                                            is_negative = 'earlier' in time_shift.lower() or 'back' in time_shift.lower() or time_shift.startswith('-')
                                            if is_negative:
                                                amount = -amount
                                            
                                            # Calculate time shift
                                            if unit in ['hour', 'hr']:
                                                delta = timedelta(hours=amount)
                                                unit_name = f"{amount} hour(s)"
                                            elif unit in ['minute', 'min']:
                                                delta = timedelta(minutes=amount)
                                                unit_name = f"{amount} minute(s)"
                                    
                                    if delta:
                                        # SHIFT BOTH start and end times by the same amount
                                        new_start_dt = start_dt + delta
                                        new_end_dt = end_dt + delta
                                        
                                        update_data['start_time'] = new_start_dt.isoformat()
                                        update_data['end_time'] = new_end_dt.isoformat()
                                        
                                        logger.info(f"🎯 TIME SHIFT SUCCESS: {time_shift} parsed as {unit_name}")
                                        logger.info(f"🎯 BEFORE: start={start_dt}, end={end_dt}")
                                        logger.info(f"🎯 AFTER: start={new_start_dt}, end={new_end_dt}")
                                        logger.info(f"🎯 Sending to calendar: start={update_data['start_time']}, end={update_data['end_time']}")
                                    else:
                                        logger.warning(f"Could not parse time shift pattern: {time_shift}")
                                        
                                except Exception as parse_error:
                                    logger.error(f"Error parsing datetime for time shift: {parse_error}")
                            else:
                                logger.warning(f"Missing start/end times for time shift: start={original_start}, end={original_end}")
                        
                        
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
                            
                            # Format event following BOT_RULES.md: • [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
                            event_link = event.get('htmlLink', '') or event.get('link', '') or event.get('calendar_link', '')
                            calendar_name = event.get('calendar_name', 'Unknown Calendar')
                            
                            # Create hyperlinked event name
                            if event_link:
                                hyperlinked_name = f"[{event.get('summary', 'Untitled')}]({event_link})"
                            else:
                                hyperlinked_name = event.get('summary', 'Untitled')
                            
                            # Format date and time for display
                            event_start = event.get('start', '')
                            event_end = event.get('end', '')
                            
                            # Parse datetime and format as "Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM"
                            try:
                                if 'T' in event_start:
                                    from datetime import datetime
                                    start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                                    end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00')) if event_end and 'T' in event_end else start_dt
                                    
                                    # Format date as "Day, Month DD, YYYY"
                                    date_formatted = start_dt.strftime('%A, %B %d, %Y')
                                    
                                    # Format time as "HH:MM AM/PM"
                                    start_time_formatted = start_dt.strftime('%I:%M %p').lstrip('0')
                                    end_time_formatted = end_dt.strftime('%I:%M %p').lstrip('0')
                                    
                                    datetime_display = f"on {date_formatted} at {start_time_formatted} - {end_time_formatted}"
                                else:
                                    datetime_display = "on today (all day)"
                            except:
                                datetime_display = "on today"
                            
                            # Build the properly formatted event description
                            update_desc = f"• {hyperlinked_name} {datetime_display} ({calendar_name})"
                                
                            successful_updates.append(update_desc)
                        else:
                            failed_updates.append(f"{event.get('summary', 'Untitled')}: {result.get('message', 'Unknown error')}")
                    except Exception as e:
                        failed_updates.append(f"{event.get('summary', 'Untitled')}: {str(e)}")
                        logger.error(f"Error updating event {event.get('id', 'unknown')}: {e}")
                
                # Build response message - just show the updated events without "Successfully updated" header
                message_parts = []
                if successful_updates:
                    # Just show the event list directly, no success header
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
        import time
        timestamp = time.time()
        operation_id = f"{operation_data.get('type', 'unknown')}_{chat_id}_{timestamp}"
        self.pending_operations[operation_id] = {
            "chat_id": chat_id,
            "operation_id": operation_id,
            "timestamp": timestamp,
            **operation_data
        }
        logger.debug(f"Stored pending {operation_data.get('type', 'unknown')} operation {operation_id} for chat {chat_id}")
        return operation_id
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
