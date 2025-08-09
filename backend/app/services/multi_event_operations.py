"""
Multi-event operation handler for batch operations like delete, update, move.
Handles operations that affect multiple events with user confirmation.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

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
                
                event_list = "\n".join([
                    f"• {event['summary']} on {event['date']} at {event['start_time']} (Calendar: {event.get('calendar_name', 'Unknown')})"
                    for event in matching_events
                ])
                
                return {
                    "success": True,
                    "message": f"Found {len(matching_events)} events to delete:\n{event_list}\n\nType 'yes' to delete ALL these events, or 'cancel' to abort.",
                    "requires_user_action": True,
                    "operation_id": operation_id
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
            
            event_list = "\n".join([
                f"• {event['summary']} on {event['date']} at {event['start_time']}"
                for event in matching_events
            ])
            
            new_name = event_data.get('new_event_name', 'Updated Event')
            
            return {
                "success": True,
                "message": f"Found {len(matching_events)} events to update:\n{event_list}\n\nWill change title to: '{new_name}'\n\nType 'yes' to confirm updates.",
                "requires_user_action": True,
                "operation_id": operation_id
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
            
            if user_response in ['yes', 'y', 'confirm', 'proceed']:
                # Execute the operation
                result = await self._execute_operation(pending_op)
                
                # Clean up pending operation
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
                        "message": f"Deleted event: {event['summary']}",
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
                            successful_deletes.append(event['summary'])
                        else:
                            failed_deletes.append(f"{event['summary']}: {result.get('message', 'Unknown error')}")
                    except Exception as e:
                        failed_deletes.append(f"{event['summary']}: {str(e)}")
                
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
                new_title = original_request.get('new_event_name', 'Updated Event')
                
                successful_updates = []
                failed_updates = []
                
                for event in events:
                    try:
                        # Prepare update data
                        update_data = {
                            "event_id": event["id"],
                            "new_event_name": new_title
                        }
                        
                        result = await self.calendar_service.update_event(update_data)
                        if result.get("success"):
                            successful_updates.append(f"{event['summary']} → {new_title}")
                        else:
                            failed_updates.append(f"{event['summary']}: {result.get('message', 'Unknown error')}")
                    except Exception as e:
                        failed_updates.append(f"{event['summary']}: {str(e)}")
                
                # Build response message
                message_parts = []
                if successful_updates:
                    message_parts.append(f"Successfully updated {len(successful_updates)} events:")
                    for update_desc in successful_updates:
                        message_parts.append(f"  • {update_desc}")
                
                if failed_updates:
                    message_parts.append(f"\nFailed to update {len(failed_updates)} events:")
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
