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
    
    def create_event_queue_from_list(self, chat_id: str, events_list: List[Dict]) -> Dict:
        """Create event queue directly from a list of events (for delete/update operations)"""
        if not isinstance(events_list, list):
            logger.error(f"CRITICAL: events_list is not a list! Type: {type(events_list)}")
            return {"success": False, "message": "Invalid events data provided."}
        
        # Validate each event in the list
        validated_events = []
        for i, event in enumerate(events_list):
            if not isinstance(event, dict):
                logger.warning(f"Skipping non-dictionary event at index {i}: {type(event)}")
                continue
            validated_events.append(event)
        
        if not validated_events:
            return {"success": False, "message": "No valid events to process."}
        
        # Store queue
        self.pending_queues[chat_id] = {
            'events': validated_events,
            'current_index': 0,
            'created_at': datetime.now(),
            'original_request': {"intent": "multi_operation", "event_count": len(validated_events)}
        }

        # Return initial message with options
        return self._get_initial_batch_message(chat_id)
    
    def _get_initial_batch_message(self, chat_id: str) -> Dict:
        """Get initial message showing found events and batch options"""
        if not self.has_pending_queue(chat_id):
            return {"success": False, "message": "No pending events found."}
        
        queue = self.pending_queues[chat_id]
        events = queue['events']
        total_events = len(events)
        
        # Get the intent from first event
        intent = events[0].get('intent', 'process') if events else 'process'
        action_text = {'delete': 'delete', 'update': 'update', 'create': 'create'}.get(intent, 'process')
        
        # Build event summary list
        event_summaries = []
        for i, event in enumerate(events[:5], 1):  # Show first 5 events
            title = event.get('event_name', 'Untitled')
            start_time = self._format_time_simple(event.get('start_time', ''))
            calendar = self._format_calendar_name(event.get('calendar_name', ''))
            event_summaries.append(f"{i}. {title} - {start_time} ({calendar})")
        
        if total_events > 5:
            event_summaries.append(f"... and {total_events - 5} more events")
        
        events_list = '\n'.join(event_summaries)
        
        initial_message = f"""Found {total_events} events to {action_text}:

{events_list}

Choose an option:
• 'one' or '1' - Review and {action_text} one by one
• 'all' or 'yes' - {action_text.title()} all events now
• 'cancel' - Cancel operation"""
        
        return {
            "success": True,
            "message": initial_message,
            "requires_user_action": True,
            "batch_options": True
        }

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
            action_prefix = "DELETE"
        elif intent == 'update':
            action_text = "update this event"
            action_prefix = "UPDATE"
        else:
            action_text = "create this event"
            action_prefix = "CREATE"
        
        confirmation_message = f"""{action_prefix} Event {current_index + 1} of {total_events}:

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
        title = event.get('event_name', 'Untitled Event')
        
        # Extract and format the time properly
        start_time = event.get('start_time', 'Unknown time')
        end_time = event.get('end_time', '')
        
        # Parse the datetime and format it nicely
        date_str, time_str = self._format_datetime_nice(start_time, end_time)
        
        # Get proper calendar name
        calendar = self._format_calendar_name(event.get('calendar_name', 'Default calendar'))
        
        return f"""📅 {title}
📆 Date: {date_str}
🕒 Time: {time_str}
📋 Calendar: {calendar}"""
    
    def _format_datetime_nice(self, start_time: str, end_time: str = '') -> tuple:
        """Format datetime strings into readable date and time"""
        try:
            if 'T' in str(start_time):
                # Parse ISO format datetime
                dt_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date_str = dt_start.strftime('%A, %B %d, %Y')  # "Monday, August 06, 2025"
                start_str = dt_start.strftime('%I:%M %p')  # "08:00 AM"
                
                if end_time and 'T' in str(end_time):
                    dt_end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    end_str = dt_end.strftime('%I:%M %p')
                    time_str = f"{start_str} - {end_str}"
                else:
                    time_str = start_str
                
                return date_str, time_str
            else:
                # Fallback for other formats
                return "Date not available", str(start_time)
        except Exception as e:
            logger.warning(f"Error formatting datetime {start_time}: {e}")
            return "Date not available", str(start_time)
    
    def _format_time_simple(self, start_time: str) -> str:
        """Format time for list display"""
        try:
            if 'T' in str(start_time):
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                return dt.strftime('%I:%M %p')  # "08:00 AM"
            else:
                return str(start_time)
        except:
            return str(start_time)
    
    def _format_calendar_name(self, calendar_name: str) -> str:
        """Format calendar name to be more user-friendly"""
        if not calendar_name or calendar_name == 'Default calendar':
            return 'Personal Calendar'
        
        # If it's an email address, extract the name part
        if '@' in calendar_name:
            if calendar_name == 'zoutna@gmail.com':
                return 'Personal'
            elif 'group.calendar.google.com' in calendar_name:
                return 'Shared Calendar'
            else:
                # Extract name before @ symbol
                name = calendar_name.split('@')[0]
                return name.title()
        
        return calendar_name
    
    async def process_queue_response(self, chat_id: str, user_response: str) -> Dict:
        """Process user's response to queue confirmation"""
        if not self.has_pending_queue(chat_id):
            return {"success": False, "message": "No pending events to confirm."}
        
        user_response = user_response.lower().strip()
        queue = self.pending_queues[chat_id]
        current_index = queue['current_index']
        
        # Handle initial batch options (when current_index is 0)
        if current_index == 0:
            if user_response in ['one', '1', 'review']:
                # Start one-by-one confirmation
                return self.get_next_event_confirmation(chat_id)
            
            elif user_response in ['all', 'yes', 'delete all', 'confirm all']:
                # Process all events at once
                return await self._process_all_events(chat_id)
            
            elif user_response in ['cancel', 'no', 'stop']:
                # Cancel operation
                total_events = len(queue['events'])
                del self.pending_queues[chat_id]
                return {
                    "success": True,
                    "message": f"Operation cancelled. No events were processed.",
                    "queue_complete": True
                }
            else:
                # Invalid response for initial options
                return self._get_initial_batch_message(chat_id)
        
        # Handle individual event confirmations
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
                    "message": f"Skipped: Event skipped.\n\n{next_result['message']}",
                    "queue_complete": True
                }
            else:
                return {
                    "success": True,
                    "message": f"Skipped: Event skipped.\n\n{next_result['message']}",
                    "requires_user_action": True
                }
        
        elif user_response in ['cancel', 'stop', 'quit']:
            # Cancel remaining events
            remaining = len(queue['events']) - current_index
            del self.pending_queues[chat_id]
            
            return {
                "success": True,
                "message": f"Error: Cancelled {remaining} remaining events.",
                "queue_complete": True
            }
        
        else:
            # Invalid response
            return {
                "success": False,
                "message": "Please reply with 'yes', 'no', or 'cancel'.",
                "requires_user_action": True
            }
    
    async def _process_all_events(self, chat_id: str) -> Dict:
        """Process all events in the queue at once"""
        if not self.has_pending_queue(chat_id):
            return {"success": False, "message": "No pending events found."}
        
        queue = self.pending_queues[chat_id]
        events = queue['events']
        total_events = len(events)
        
        # Get intent for messaging
        intent = events[0].get('intent', 'process') if events else 'process'
        action_text = {'delete': 'deleted', 'update': 'updated', 'create': 'created'}.get(intent, 'processed')
        
        successful = 0
        failed = 0
        failures = []
        
        # Process each event
        for i, event in enumerate(events):
            try:
                result = await self._process_single_event(event)
                if result.get('success'):
                    successful += 1
                else:
                    failed += 1
                    event_name = event.get('event_name', f'Event {i+1}')
                    failures.append(f"• {event_name}: {result.get('message', 'Unknown error')}")
            except Exception as e:
                failed += 1
                event_name = event.get('event_name', f'Event {i+1}')
                failures.append(f"• {event_name}: {str(e)}")
        
        # Clear the queue
        del self.pending_queues[chat_id]
        
        # Build result message
        if failed == 0:
            message = f"✅ All {total_events} events {action_text} successfully!"
        elif successful == 0:
            message = f"❌ Failed to {intent} all {total_events} events:\n" + "\n".join(failures)
        else:
            message = f"⚠️ {successful} events {action_text}, {failed} failed:\n" + "\n".join(failures)
        
        return {
            "success": True,
            "message": message,
            "queue_complete": True,
            "stats": {"successful": successful, "failed": failed, "total": total_events}
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
                            "message": "Success: Event created successfully",
                            "event_id": result.get('event_id', 'unknown')
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Error: Failed to create event: {result.get('message', 'Unknown error')}"
                        }
                
                elif intent == 'delete':
                    # Delete the event
                    event_id = event.get('event_id')
                    calendar_id = event.get('calendar_id', 'primary')
                    
                    result = self.calendar_service.delete_event(event_id, calendar_id)
                    
                    if result.get('success'):
                        return {
                            "success": True,
                            "message": "Success: Event deleted successfully"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Error: Failed to delete event: {result.get('message', 'Unknown error')}"
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
                            "message": "Success: Event updated successfully"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Error: Failed to update event: {result.get('message', 'Unknown error')}"
                        }
                
            else:
                # Fallback simulation for testing
                action_map = {'create': 'created', 'delete': 'deleted', 'update': 'updated'}
                action = action_map.get(intent, 'processed')
                
                return {
                    "success": True,
                    "message": f"Success: Event {action} successfully (simulated)",
                    "event_id": f"mock_event_{datetime.now().timestamp()}"
                }
                
        except Exception as e:
            logger.error(f"Error processing single event: {e}")
            return {
                "success": False,
                "message": f"Error: Failed to process event: {str(e)}",
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
