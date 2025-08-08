"""
Event Queue Handler for processing multiple events one by one with user confirmation.
This approach reuses existi        # Build event summaries for display
        event_summaries = []
        for i, event in enumerate(events[:5], 1):  # Show first 5 events
            title = event.get('event_name', 'Untitled')
            
            # Format date and time together with more detail
            start_time = event.get('start_time', '')
            end_time = event.get('end_time', '')
            
            # Extract and format date and times
            date_time_str = "Unknown time"
            try:
                if 'T' in str(start_time):
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    date_part = start_dt.strftime('%a %b %d')
                    start_time_part = start_dt.strftime('%I:%M %p')
                    
                    if 'T' in str(end_time):
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        end_time_part = end_dt.strftime('%I:%M %p')
                        date_time_str = f"{date_part}, {start_time_part} - {end_time_part}"
                    else:
                        date_time_str = f"{date_part}, {start_time_part}"
                else:
                    date_time_str = self._format_datetime_for_display(start_time)
            except Exception as e:
                logger.warning(f"Error formatting event time: {e}")
                date_time_str = self._format_datetime_for_display(start_time)
            
            calendar = self._format_calendar_name(event.get('calendar_name', ''))
            
            event_summaries.append(f"{i}. {title} - {date_time_str} ({calendar})")
        
        if total_events > 5:
            event_summaries.append(f"... and {total_events - 5} more events")event logic while handling multi-event requests.
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
• 'cancel' or 'c' - Cancel operation"""
        
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
        
        return f"""Event: {title}
Date: {date_str}
Time: {time_str}
Calendar: {calendar}"""
    
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
    
    def _format_datetime_for_display(self, start_time: str) -> str:
        """Format datetime for event list display with date and time"""
        try:
            if 'T' in str(start_time):
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                # Format as "Sat Aug 09, 08:00 AM"
                return dt.strftime('%a %b %d, %I:%M %p')
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
            
            elif user_response in ['cancel', 'c', 'no', 'stop']:
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
        
        elif user_response in ['cancel', 'c', 'stop', 'quit']:
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
        successful_events = []
        failed_events = []
        
        for i, event in enumerate(events):
            try:
                result = await self._process_single_event(event)
                if result.get('success'):
                    successful += 1
                    # Collect successful event details for detailed summary
                    if result.get('message') and 'Updated' in result.get('message', ''):
                        successful_events.append(result.get('message'))
                    else:
                        event_name = event.get('event_name', f'Event {i+1}')
                        successful_events.append(f"• {event_name}")
                else:
                    failed += 1
                    event_name = event.get('event_name', f'Event {i+1}')
                    failed_events.append(f"• {event_name}: {result.get('message', 'Unknown error')}")
            except Exception as e:
                failed += 1
                event_name = event.get('event_name', f'Event {i+1}')
                failed_events.append(f"• {event_name}: {str(e)}")
        
        # Clear the queue
        del self.pending_queues[chat_id]
        
        # Build result message with dates
        date_info = ""
        if events and len(events) > 0:
            # Try to extract date from first event
            first_event = events[0]
            if isinstance(first_event, dict):
                start_time = first_event.get('start_time', '')
                if 'T' in str(start_time):
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        date_info = f" on {dt.strftime('%A, %B %d, %Y')}"
                    except:
                        pass
        
        # Build detailed result message
        if failed == 0:
            if intent == 'update' and successful_events:
                # For updates, show detailed changes made
                message = f"Successfully updated all {total_events} events{date_info}:\n\n" + "\n".join(successful_events)
            else:
                message = f"Successfully {action_text} all {total_events} events{date_info}!"
        elif successful == 0:
            message = f"Failed to {intent} all {total_events} events{date_info}:\n\n" + "\n".join(failed_events)
        else:
            message = f"Partially completed: {successful} events {action_text}, {failed} failed{date_info}:\n\n"
            if successful_events:
                message += "Successful:\n" + "\n".join(successful_events) + "\n\n"
            if failed_events:
                message += "Failed:\n" + "\n".join(failed_events)
        
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
                    
                    if not event_id:
                        return {
                            "success": False,
                            "message": "Error: Missing event ID for update operation"
                        }
                    
                    # Build update data - handle time shifts if specified
                    update_data = {}
                    
                    # Handle time shift (e.g., "move 1 hour later")
                    if event.get('time_shift'):
                        try:
                            from datetime import datetime, timedelta
                            import re
                            
                            # Parse current times
                            current_start = event.get('start_time')
                            current_end = event.get('end_time')
                            
                            if current_start and 'T' in str(current_start):
                                start_dt = datetime.fromisoformat(current_start.replace('Z', '+00:00'))
                                
                                # Parse time shift (e.g., "1 hour", "30 minutes")
                                time_shift = event.get('time_shift', '')
                                hours = 0
                                minutes = 0
                                
                                # Extract hours
                                hour_match = re.search(r'(\d+)\s*(?:hour|hr)', time_shift, re.IGNORECASE)
                                if hour_match:
                                    hours = int(hour_match.group(1))
                                
                                # Extract minutes  
                                minute_match = re.search(r'(\d+)\s*(?:minute|min)', time_shift, re.IGNORECASE)
                                if minute_match:
                                    minutes = int(minute_match.group(1))
                                
                                # Apply shift
                                shift_delta = timedelta(hours=hours, minutes=minutes)
                                new_start = start_dt + shift_delta
                                
                                update_data['start_time'] = new_start.isoformat()
                                
                                # Also shift end time if available
                                if current_end and 'T' in str(current_end):
                                    end_dt = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
                                    new_end = end_dt + shift_delta
                                    update_data['end_time'] = new_end.isoformat()
                                    
                        except Exception as e:
                            logger.error(f"Error processing time shift: {e}")
                            return {
                                "success": False,
                                "message": f"Error: Failed to process time shift: {str(e)}"
                            }
                    
                    # Handle direct time updates
                    if event.get('new_start_time'):
                        update_data['start_time'] = event.get('new_start_time')
                    if event.get('new_end_time'):
                        update_data['end_time'] = event.get('new_end_time')
                    if event.get('new_event_name'):
                        update_data['event_name'] = event.get('new_event_name')
                    if event.get('description'):
                        update_data['description'] = event.get('description')
                    if event.get('location'):
                        update_data['location'] = event.get('location')
                    
                    # If no specific updates provided, default to current values
                    if not update_data:
                        update_data = {
                            'event_name': event.get('event_name'),
                            'start_time': event.get('start_time'),
                            'end_time': event.get('end_time'),
                            'date': event.get('date'),
                            'description': event.get('description', ''),
                            'location': event.get('location', '')
                        }
                    
                    # Perform the update
                    result = self.calendar_service.update_event(event_id, update_data, calendar_id)
                    
                    if result.get('success'):
                        # Build detailed success message showing changes made
                        changes_made = []
                        if event.get('time_shift'):
                            changes_made.append(f"shifted by {event.get('time_shift')}")
                        if event.get('new_event_name'):
                            changes_made.append(f"renamed to '{event.get('new_event_name')}'")
                        if event.get('new_calendar'):
                            changes_made.append(f"moved to {event.get('new_calendar')}")
                        
                        change_description = ", ".join(changes_made) if changes_made else "updated"
                        
                        # Format the updated event with hyperlink if available
                        event_link = result.get('event_link', '')
                        if event_link:
                            event_title = f"[{event.get('event_name', 'Event')}]({event_link})"
                        else:
                            event_title = event.get('event_name', 'Event')
                        
                        return {
                            "success": True,
                            "message": f"Updated {event_title} - {change_description}",
                            "event_link": event_link
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Failed to update event: {result.get('message', 'Unknown error')}"
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
