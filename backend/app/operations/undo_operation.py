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
        """Execute undo operation based on recent conversation context."""
        try:
            # Get recent conversation history to determine what to undo
            conversation_history = self.conversation_state.get_conversation_history(chat_id)
            
            if not conversation_history:
                return {
                    "success": False,
                    "message": "No recent actions found to undo."
                }

            # Analyze recent messages to find the last operation
            recent_operations = self._extract_recent_operations(conversation_history)
            
            if not recent_operations:
                return {
                    "success": False,
                    "message": "No recent calendar operations found to undo."
                }

            # Get the most recent operation
            last_operation = recent_operations[0]
            operation_type = last_operation.get("type")
            
            if operation_type == "create":
                return await self._undo_creation(chat_id, last_operation)
            elif operation_type == "delete":
                return await self._undo_deletion(chat_id, last_operation)
            elif operation_type == "update":
                return await self._undo_update(chat_id, last_operation)
            else:
                return {
                    "success": False,
                    "message": f"Cannot undo operation of type: {operation_type}"
                }

        except Exception as e:
            logger.error(f"Error in undo operation: {e}")
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
                
                # Look for operation indicators
                if "Successfully created" in content:
                    operations.append({
                        "type": "create",
                        "timestamp": message.get("timestamp", datetime.now()),
                        "content": content,
                        "events": self._extract_events_from_message(content)
                    })
                elif "Successfully deleted" in content:
                    operations.append({
                        "type": "delete", 
                        "timestamp": message.get("timestamp", datetime.now()),
                        "content": content,
                        "events": self._extract_events_from_message(content)
                    })
                elif "Successfully updated" in content:
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

    async def _undo_creation(self, chat_id: int, operation: Dict) -> Dict[str, Any]:
        """Undo event creation by deleting the created events."""
        try:
            events = operation.get("events", [])
            
            if not events:
                return {
                    "success": False,
                    "message": "No events found to undo from creation operation."
                }

            # Delete each created event
            successful_deletions = 0
            failed_deletions = 0
            results = []

            for event in events:
                if event.get("id"):
                    try:
                        # Try to delete the event
                        delete_result = self.calendar_service.delete_event(event["id"])
                        
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
