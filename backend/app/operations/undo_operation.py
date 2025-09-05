"""
Undo operation for reversing recent calendar actions.
Uses conversation history and LLM to determine what to undo.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)

class UndoOperation(BaseOperation):
    """Handles undo operations by analyzing recent conversation history."""

    async def execute(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute undo operation based on cached operation data."""
        try:
            logger.info(f"🔧 UndoOperation: Starting undo for chat_id {chat_id}")
            
            # CRITICAL FIX: Use cached operation data instead of conversation history parsing
            cached_operation = self.conversation_state.get_data(chat_id, "last_operation")
            
            if not cached_operation:
                logger.warning(f"🔧 UndoOperation: No cached operation found for chat_id {chat_id}")
                return {
                    "success": False,
                    "message": "No recent actions found to undo. Only operations from this session can be undone."
                }

            operation_type = cached_operation.get("operation_type")
            operation_result = cached_operation.get("operation_result", {})
            intent_data = cached_operation.get("intent_data", {})
            
            logger.info(f"🔧 UndoOperation: Found cached {operation_type} operation from {cached_operation.get('timestamp')}")
            logger.info(f"🔧 UndoOperation: Processing undo for operation type: {operation_type}")
            
            if operation_type == "create":
                return await self._undo_creation(chat_id, cached_operation)
            elif operation_type == "delete":
                return await self._undo_deletion(chat_id, cached_operation)
            elif operation_type == "update":
                return await self._undo_update(chat_id, cached_operation)
            else:
                logger.warning(f"🔧 UndoOperation: Unknown operation type: {operation_type}")
                return {
                    "success": False,
                    "message": f"Cannot undo operation of type: {operation_type}"
                }

        except Exception as e:
            logger.error(f"🔧 UndoOperation: Error in undo operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process undo request."
            }

    def _extract_recent_operations(self, conversation_history: List[Dict]) -> List[Dict]:
        """Extract recent calendar operations from conversation history."""
        operations = []
        
        # Look for assistant messages that indicate successful operations
        for message in reversed(conversation_history[-10:]):  # Check last 10 messages
            if message.get("role") == "assistant":
                content = message.get("content", "")
                
                # CRITICAL FIX: More comprehensive operation detection patterns
                # Look for operation indicators - expand patterns to catch all formats
                if any(phrase in content for phrase in ["Successfully created", "created event", "event created", "Successfully created event"]):
                    operations.append({
                        "type": "create",
                        "timestamp": message.get("timestamp", datetime.now()),
                        "content": content,
                        "events": self._extract_events_from_message(content)
                    })
                elif any(phrase in content for phrase in ["Successfully deleted", "deleted event", "event deleted", "Successfully deleted event"]):
                    operations.append({
                        "type": "delete", 
                        "timestamp": message.get("timestamp", datetime.now()),
                        "content": content,
                        "events": self._extract_events_from_message(content)
                    })
                elif any(phrase in content for phrase in ["Successfully updated", "updated event", "event updated", "Successfully updated event"]):
                    operations.append({
                        "type": "update",
                        "timestamp": message.get("timestamp", datetime.now()), 
                        "content": content,
                        "events": self._extract_events_from_message(content)
                    })
        
        return operations

    def _extract_events_from_message(self, message_content: str) -> List[Dict]:
        """Extract event information from success messages."""
        events = []
        
        # Look for event links in the format [Event Name](link)
        import re
        event_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(event_pattern, message_content)
        
        for event_name, event_link in matches:
            # Extract event ID from link if possible
            event_id = None
            if 'eid=' in event_link:
                try:
                    event_id = event_link.split('eid=')[1].split('&')[0]
                except:
                    pass
            
            events.append({
                "name": event_name,
                "link": event_link, 
                "id": event_id
            })
        
        return events

    async def _undo_creation(self, chat_id: int, cached_operation: Dict) -> Dict[str, Any]:
        """Undo event creation by deleting the created events using cached operation data."""
        try:
            operation_result = cached_operation.get("operation_result", {})
            
            # Extract events from the operation result
            events = []
            
            # Handle different result structures
            if "successful_events" in operation_result:
                # Multiple events structure
                for event_data in operation_result["successful_events"]:
                    calendar_response = event_data.get("calendar_response", {})
                    event_id = calendar_response.get("event_id")
                    formatted_text = event_data.get("formatted", "")
                    
                    # Extract event name from formatted text
                    import re
                    name_match = re.search(r'\[([^\]]+)\]', formatted_text)
                    event_name = name_match.group(1) if name_match else "Event"
                    
                    if event_id:
                        events.append({
                            "id": event_id,
                            "name": event_name,
                            "calendar_id": calendar_response.get("calendar_id", "primary")
                        })
            elif "calendar_response" in operation_result:
                # Single event structure
                calendar_response = operation_result["calendar_response"]
                event_data = operation_result.get("event_data", {})
                event_id = calendar_response.get("event_id")
                event_name = event_data.get("event_name", "Event")
                
                if event_id:
                    events.append({
                        "id": event_id,
                        "name": event_name,
                        "calendar_id": calendar_response.get("calendar_id", "primary")
                    })
            
            if not events:
                logger.warning(f"🔧 UndoOperation: No events found in cached operation result: {operation_result}")
                return {
                    "success": False,
                    "message": "No events found to undo from creation operation."
                }

            logger.info(f"🔧 UndoOperation: Found {len(events)} events to undo: {[e['name'] for e in events]}")

            # Delete each created event
            successful_deletions = 0
            failed_deletions = 0
            results = []

            for event in events:
                if event.get("id"):
                    try:
                        # Try to delete the event
                        delete_result = await self.calendar_service.delete_event(event["id"], event.get("calendar_id", "primary"))
                        
                        if delete_result.get("success"):
                            successful_deletions += 1
                            results.append(f"✓ Undid creation of '{event['name']}'")
                        else:
                            failed_deletions += 1
                            results.append(f"✗ Failed to undo '{event['name']}': {delete_result.get('message', 'Unknown error')}")
                    except Exception as e:
                        failed_deletions += 1
                        results.append(f"✗ Error undoing '{event['name']}': {str(e)}")
                else:
                    failed_deletions += 1
                    results.append(f"✗ Cannot undo '{event['name']}': No event ID found")

            # Format response
            if successful_deletions > 0:
                message = f"Undid creation of {successful_deletions} event(s):\n\n" + "\n".join(results)
                return {
                    "success": True,
                    "message": message
                }
            else:
                message = f"Failed to undo creation:\n\n" + "\n".join(results)
                return {
                    "success": False,
                    "message": message
                }

        except Exception as e:
            logger.error(f"Error undoing creation: {e}")
            return {
                "success": False,
                "message": f"Error undoing creation: {str(e)}"
            }

    async def _undo_deletion(self, chat_id: int, operation: Dict) -> Dict[str, Any]:
        """Undo event deletion - not possible with Google Calendar API."""
        return {
            "success": False,
            "message": "Sorry, deleted events cannot be restored. Google Calendar doesn't support undeleting events."
        }

    async def _undo_update(self, chat_id: int, operation: Dict) -> Dict[str, Any]:
        """Undo event updates - would require storing original state."""
        return {
            "success": False,
            "message": "Sorry, event updates cannot be undone automatically. You'll need to manually revert the changes."
        }
