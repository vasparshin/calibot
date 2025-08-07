"""
Event Queue Handler for processing multiple events one by one with user confirmation.
This approach reuses existing single-event logic while handling multi-event requests.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class EventQueueHandler:
    def __init__(self, telegram_service, conversation_state, calendar_service=None, calendar_agent=None):
        self.telegram_service = telegram_service
        self.conversation_state = conversation_state
        self.calendar_service = calendar_service
        self.calendar_agent = calendar_agent
        self.pending_queues = {}  # Store event queues by chat_id
    
    def has_pending_queue(self, chat_id: str) -> bool:
        """Check if user has pending events in queue"""
        return chat_id in self.pending_queues and len(self.pending_queues[chat_id]['events']) > 0
    
    def detect_multi_event_request(self, intent_data: Dict) -> bool:
        """Detect if the intent data represents multiple events"""
        # Check for batch_create format
        if intent_data.get('intent') == 'batch_create' and 'events' in intent_data:
            return len(intent_data['events']) > 1
        
        # Check for multiple time indicators in single event
        if isinstance(intent_data.get('start_time'), list):
            return len(intent_data['start_time']) > 1
        
        # Check for multiple events in description or title
        event_name = intent_data.get('event_name', '')
        if any(phrase in event_name.lower() for phrase in ['multiple', 'several', 'many', 'all']):
            return True
        
        return False
    
    def create_event_queue(self, chat_id: str, intent_data: Dict) -> Dict:
        """Convert multi-event intent into individual event queue"""
        events = []
        
        # Handle batch_create format
        if intent_data.get('intent') == 'batch_create' and 'events' in intent_data:
            events = intent_data['events']
        
        # Handle multiple start_times
        elif isinstance(intent_data.get('start_time'), list):
            start_times = intent_data['start_time']
            end_times = intent_data.get('end_time', [])
            
            for i, start_time in enumerate(start_times):
                event = intent_data.copy()
                event['start_time'] = start_time
                event['end_time'] = end_times[i] if i < len(end_times) else None
                event['intent'] = 'create'  # Normalize to single intent
                events.append(event)
        
        # Handle pattern-based detection (fallback)
        else:
            # For now, treat as single event but mark for queue processing
            events = [intent_data]
        
        # Store queue
        self.pending_queues[chat_id] = {
            'events': events,
            'current_index': 0,
            'created_at': datetime.now(),
            'original_request': intent_data
        }
        
        return self.get_next_event_confirmation(chat_id)
    
    def get_next_event_confirmation(self, chat_id: str) -> Dict:
        """Get the next event in queue for user confirmation"""
        if not self.has_pending_queue(chat_id):
            return {"success": False, "message": "No pending events in queue."}
        
        queue = self.pending_queues[chat_id]
        current_index = queue['current_index']
        events = queue['events']
        
        if current_index >= len(events):
            # Queue completed
            del self.pending_queues[chat_id]
            return {"success": True, "message": "All events processed!", "queue_complete": True}
        
        current_event = events[current_index]
        total_events = len(events)
        
        # Format event details for confirmation
        event_summary = self._format_event_summary(current_event)
        intent = current_event.get('intent', 'create')
        
        # Customize message based on intent
        if intent == 'delete':
            action_text = "delete this event"
            action_emoji = "🗑️"
        elif intent == 'update':
            action_text = "update this event"
            action_emoji = "✏️"
        else:
            action_text = "create this event"
            action_emoji = "📅"
        
        confirmation_message = f"""{action_emoji} Event {current_index + 1} of {total_events}:

{event_summary}

Reply with:
• 'yes' or 'y' to {action_text}
• 'no' or 'n' to skip this event  
• 'cancel' to cancel remaining events"""

        return {
            "success": True,
            "message": confirmation_message,
            "requires_user_action": True,
            "queue_position": f"{current_index + 1}/{total_events}"
        }
    
    def _format_event_summary(self, event: Dict) -> str:
        """Format a single event for user confirmation"""
        intent = event.get('intent', 'create')
        title = event.get('event_name', 'Untitled Event')
        
        # Handle different data formats
        if 'start_time' in event and 'end_time' in event:
            # Creation format
            date = event.get('date', 'Date not specified')
            start_time = event.get('start_time', 'Time not specified')
            end_time = event.get('end_time', '')
            calendar = event.get('calendar_name', 'Default calendar')
            
            time_str = f"{start_time}"
            if end_time:
                time_str += f" - {end_time}"
            
            return f"""📝 **{title}**
📅 Date: {date}
⏰ Time: {time_str}
📂 Calendar: {calendar}"""
        
        else:
            # Delete/Update format (existing events)
            start_time = event.get('start_time', 'Unknown time')
            calendar = event.get('calendar_name', 'Default calendar')
            
            # Clean up datetime format if needed
            if 'T' in str(start_time):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    start_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            return f"""📝 **{title}**
⏰ Time: {start_time}
📂 Calendar: {calendar}"""
    
    async def process_queue_response(self, chat_id: str, user_response: str) -> Dict:
        """Process user's response to queue confirmation"""
        if not self.has_pending_queue(chat_id):
            return {"success": False, "message": "No pending events to confirm."}
        
        user_response = user_response.lower().strip()
        queue = self.pending_queues[chat_id]
        current_index = queue['current_index']
        current_event = queue['events'][current_index]
        
        if user_response in ['yes', 'y', 'confirm']:
            # Process the current event
            result = await self._process_single_event(current_event)
            
            # Move to next event
            queue['current_index'] += 1
            
            # Get next confirmation or completion message
            next_result = self.get_next_event_confirmation(chat_id)
            
            if next_result.get('queue_complete'):
                return {
                    "success": True,
                    "message": f"{result['message']}\n\n{next_result['message']}",
                    "queue_complete": True
                }
            else:
                return {
                    "success": True,
                    "message": f"{result['message']}\n\n{next_result['message']}",
                    "requires_user_action": True
                }
        
        elif user_response in ['no', 'n', 'skip']:
            # Skip current event, move to next
            queue['current_index'] += 1
            
            next_result = self.get_next_event_confirmation(chat_id)
            
            if next_result.get('queue_complete'):
                return {
                    "success": True,
                    "message": f"⏭️ Event skipped.\n\n{next_result['message']}",
                    "queue_complete": True
                }
            else:
                return {
                    "success": True,
                    "message": f"⏭️ Event skipped.\n\n{next_result['message']}",
                    "requires_user_action": True
                }
        
        elif user_response in ['cancel', 'stop', 'quit']:
            # Cancel remaining events
            remaining = len(queue['events']) - current_index
            del self.pending_queues[chat_id]
            
            return {
                "success": True,
                "message": f"❌ Cancelled {remaining} remaining events.",
                "queue_complete": True
            }
        
        else:
            # Invalid response
            return {
                "success": False,
                "message": "Please reply with 'yes', 'no', or 'cancel'.",
                "requires_user_action": True
            }
    
    async def _process_single_event(self, event: Dict) -> Dict:
        """Process a single event using existing logic"""
        try:
            logger.info(f"Processing single event: {event}")
            intent = event.get('intent', 'create')
            
            # If we have calendar service integration, use it
            if self.calendar_service:
                if intent == 'create':
                    # Select appropriate calendar for creation
                    if self.calendar_agent:
                        calendar_id = await self.calendar_agent.select_calendar_for_event(event)
                    else:
                        calendar_id = 'primary'
                    
                    # Create the event
                    result = await self.calendar_service.create_event({
                        'event_name': event.get('event_name', 'Untitled Event'),
                        'start_time': event.get('start_time'),
                        'end_time': event.get('end_time'),
                        'date': event.get('date'),
                        'description': event.get('description', ''),
                        'location': event.get('location', '')
                    })
                    
                    if result.get('success'):
                        return {
                            "success": True,
                            "message": "✅ Event created successfully",
                            "event_id": result.get('event_id', 'unknown')
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"❌ Failed to create event: {result.get('message', 'Unknown error')}"
                        }
                
                elif intent == 'delete':
                    # Delete the event
                    event_id = event.get('event_id')
                    calendar_id = event.get('calendar_id', 'primary')
                    
                    result = self.calendar_service.delete_event(event_id, calendar_id)
                    
                    if result.get('success'):
                        return {
                            "success": True,
                            "message": "✅ Event deleted successfully"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"❌ Failed to delete event: {result.get('message', 'Unknown error')}"
                        }
                
                elif intent == 'update':
                    # Update the event
                    event_id = event.get('event_id')
                    calendar_id = event.get('calendar_id', 'primary')
                    
                    update_data = {
                        'event_name': event.get('event_name'),
                        'start_time': event.get('start_time'),
                        'end_time': event.get('end_time'),
                        'date': event.get('date'),
                        'description': event.get('description'),
                        'location': event.get('location')
                    }
                    
                    result = self.calendar_service.update_event(event_id, update_data, calendar_id)
                    
                    if result.get('success'):
                        return {
                            "success": True,
                            "message": "✅ Event updated successfully"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"❌ Failed to update event: {result.get('message', 'Unknown error')}"
                        }
                
            else:
                # Fallback simulation for testing
                action_map = {'create': 'created', 'delete': 'deleted', 'update': 'updated'}
                action = action_map.get(intent, 'processed')
                
                return {
                    "success": True,
                    "message": f"✅ Event {action} successfully (simulated)",
                    "event_id": f"mock_event_{datetime.now().timestamp()}"
                }
                
        except Exception as e:
            logger.error(f"Error processing single event: {e}")
            return {
                "success": False,
                "message": f"❌ Failed to process event: {str(e)}",
                "error": str(e)
            }
    
    def get_queue_status(self, chat_id: str) -> Dict:
        """Get current queue status for debugging"""
        if not self.has_pending_queue(chat_id):
            return {"has_queue": False}
        
        queue = self.pending_queues[chat_id]
        return {
            "has_queue": True,
            "total_events": len(queue['events']),
            "current_index": queue['current_index'],
            "remaining": len(queue['events']) - queue['current_index'],
            "created_at": queue['created_at'].isoformat()
        }
    
    def clear_queue(self, chat_id: str) -> bool:
        """Clear user's event queue"""
        if chat_id in self.pending_queues:
            del self.pending_queues[chat_id]
            return True
        return False
