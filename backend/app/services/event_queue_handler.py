"""
Event Queue Handler for processing multiple events one by one with user confirmation.
This approach reuses existing event logic while handling multi-event requests.
"""

import logging
from typing import Dict, List, Optional, Any
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

    def clear_queue(self, chat_id: str):
        """Clear any existing queue for the chat_id"""
        if chat_id in self.pending_queues:
            del self.pending_queues[chat_id]
            logger.info(f"Cleared pending event queue for chat {chat_id}")

    def skip_event_and_get_next(self, chat_id: str) -> Dict[str, Any]:
        """Skip current event and return next confirmation structure.
        Returns dict with either next confirmation or completion message."""
        if not self.has_pending_queue(chat_id):
            return {"success": False, "message": "No pending events."}
        queue = self.pending_queues[chat_id]
        queue['current_index'] += 1  # Skip current
        if queue['current_index'] >= len(queue['events']):
            # All done
            del self.pending_queues[chat_id]
            return {"success": True, "queue_complete": True, "message": "All events processed!"}
        return self.get_next_event_confirmation(chat_id)
    
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
            'original_request': {"intent": "multi_operation", "event_count": len(validated_events)},
            'one_by_one_mode': True  # CRITICAL FIX: Mark as one-by-one mode when created from external handler
        }

        # Return initial message with options
        return self._get_initial_batch_message(chat_id)
    
    def _get_initial_batch_message(self, chat_id: str) -> Dict:
        """
        Get initial message showing found events and batch options.
        CRITICAL: Updated to follow BOT_RULES.md - shows ALL events with hyperlinks.
        """
        if not self.has_pending_queue(chat_id):
            return {"success": False, "message": "No pending events found."}
        
        queue = self.pending_queues[chat_id]
        events = queue['events']
        total_events = len(events)
        
        # Get the intent from first event
        intent = events[0].get('intent', 'process') if events else 'process'
        action_text = {'delete': 'delete', 'update': 'update', 'create': 'create'}.get(intent, 'process')
        
        # Use centralized formatter if available
        if MessageFormatter:
            # Determine what changes will be made for the header
            first_event = events[0] if events else {}
            proposed_changes = []
            if first_event.get('time_shift'):
                time_shift = first_event.get('time_shift')
                # Check for negative shifts (earlier) or keywords
                is_earlier = time_shift.startswith('-') or any(keyword in time_shift.lower() for keyword in ['earlier', 'back'])
                is_extend = any(keyword in time_shift.lower() for keyword in ['extend', 'make it', 'long', 'after start'])
                
                if is_earlier:
                    # Remove the minus sign for display
                    display_shift = time_shift.replace('-', '').strip()
                    proposed_changes.append(f"move {display_shift} earlier")
                elif is_extend:
                    proposed_changes.append(f"extend duration to {time_shift}")
                else:
                    proposed_changes.append(f"shift by {time_shift}")
            if first_event.get('new_event_name'):
                proposed_changes.append(f"rename to '{first_event.get('new_event_name')}'")
            if first_event.get('new_date'):
                proposed_changes.append(f"move to {first_event.get('new_date')}")
            
            # Convert events to proper format for the formatter
            formatted_events = []
            for event in events:
                formatted_event = {
                    'summary': event.get('event_name', 'Untitled'),
                    'start': event.get('start_time', ''),
                    'end': event.get('end_time', ''),
                    'calendar_name': event.get('calendar_name', 'Unknown Calendar'),
                    'id': event.get('event_id', ''),
                    'htmlLink': event.get('calendar_link', '')
                }
                formatted_events.append(formatted_event)
            
            # Get base message from formatter
            base_message = MessageFormatter.format_confirmation_message(action_text, formatted_events, total_events)
            
            # Add proposed changes to the message
            if proposed_changes:
                change_description = ", ".join(proposed_changes)
                # Insert the proposed changes into the first line
                lines = base_message.split('\n')
                if lines:
                    first_line = lines[0]
                    # Replace "Found X events to update:" with "Found X events to update (proposed changes):"
                    if f"Found {total_events} events to {action_text}:" in first_line:
                        lines[0] = f"Found {total_events} events to {action_text} ({change_description}):"
                        base_message = '\n'.join(lines)
            
            keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard(action_text) if InlineKeyboardHelper else None
            
            return {
                "success": True,
                "message": base_message,
                "requires_user_action": True,
                "batch_options": True,
                "keyboard": keyboard
            }
        
        # Legacy fallback implementation (FIXED to show ALL events with proposed changes)
        # Determine what changes will be made
        first_event = events[0] if events else {}
        proposed_changes = []
        if first_event.get('time_shift'):
            time_shift = first_event.get('time_shift')
            # Check for negative shifts (earlier) or keywords
            is_earlier = time_shift.startswith('-') or any(keyword in time_shift.lower() for keyword in ['earlier', 'back'])
            is_extend = any(keyword in time_shift.lower() for keyword in ['extend', 'make it', 'long', 'after start'])
            
            if is_earlier:
                # Remove the minus sign for display
                display_shift = time_shift.replace('-', '').strip()
                proposed_changes.append(f"move {display_shift} earlier")
            elif is_extend:
                proposed_changes.append(f"extend duration to {time_shift}")
            else:
                proposed_changes.append(f"shift by {time_shift}")
        if first_event.get('new_event_name'):
            proposed_changes.append(f"rename to '{first_event.get('new_event_name')}'")
        if first_event.get('new_date'):
            proposed_changes.append(f"move to {first_event.get('new_date')}")
        
        change_description = ", ".join(proposed_changes) if proposed_changes else action_text
        
        message = f"Found {total_events} events to {action_text}"
        if proposed_changes:
            message += f" ({change_description})"
        message += ":\n\n"
        
        # CRITICAL CHANGE: Show ALL events, never truncate
        for i, event in enumerate(events, 1):
            title = event.get('event_name', 'Untitled')
            start_time = event.get('start_time', '')
            end_time = event.get('end_time', '')
            calendar_name = self._format_calendar_name(event.get('calendar_name', ''))
            
            # Format with hyperlink if available
            event_id = event.get('event_id', '')
            calendar_link = event.get('calendar_link', '')
            
            if calendar_link:
                formatted_title = f"[{title}]({calendar_link})"
            elif event_id:
                formatted_title = f"[{title}](https://calendar.google.com/calendar/event?eid={event_id})"
            else:
                formatted_title = title
            
            # Format date and time
            try:
                if 'T' in str(start_time):
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    date_str = start_dt.strftime('%A, %B %d, %Y')
                    start_time_str = start_dt.strftime('%I:%M %p')
                    
                    if 'T' in str(end_time):
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        end_time_str = end_dt.strftime('%I:%M %p')
                        time_display = f"{start_time_str} - {end_time_str}"
                    else:
                        time_display = start_time_str
                else:
                    date_str = "Unknown date"
                    time_display = "Unknown time"
            except Exception as e:
                logger.warning(f"Error formatting event time: {e}")
                date_str = "Unknown date"
                time_display = "Unknown time"
            
            message += f"{i}. {formatted_title} on {date_str} at {time_display} ({calendar_name})\n"
        
        # REMOVED: Truncation logic that violated BOT_RULES.md
        
        message += f"\nChoose an option:\n"
        message += f"• 'one' or '1' - Review and {action_text} one by one\n"
        message += f"• 'all' or 'yes' - {action_text.title()} all events now\n"
        message += f"• 'cancel' or 'c' - Cancel operation"
        
        # Create inline keyboard for better UX
        keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard(action_text) if InlineKeyboardHelper else None
        
        return {
            "success": True,
            "message": message,
            "requires_user_action": True,
            "batch_options": True,
            "keyboard": keyboard
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

        # Create navigation keyboard (Yes / Skip / Stop All)
        keyboard = InlineKeyboardHelper.create_queue_navigation_keyboard(current_index=current_index, total_count=total_events, action=intent) if InlineKeyboardHelper else None

        confirmation_message = f"""{action_prefix} Event {current_index + 1} of {total_events}:

{event_summary}

Choose your action:"""

        return {
            "success": True,
            "message": confirmation_message,
            "keyboard": keyboard,
            "requires_user_action": True,
            "queue_position": f"{current_index + 1}/{total_events}"
        }
    
    def _format_event_summary(self, event: Dict) -> str:
        """Format a single event for user confirmation using centralized formatter"""
        try:
            # Use centralized formatter for consistency with multi-event displays
            if MessageFormatter:
                event_display = MessageFormatter.format_single_event_display(event, include_hyperlink=True)
                # Remove the bullet point since we'll have our own header
                if event_display.startswith('• '):
                    event_display = event_display[2:]
                
                intent = event.get('intent', 'create')
                
                if intent == 'update':
                    # For updates, show what changes will be made
                    summary = f"""Current Event: {event_display}

📋 Proposed Changes:"""
                    
                    # Add proposed changes
                    changes = []
                    if event.get('new_date'):
                        changes.append(f"📅 Move to: {event.get('new_date')}")
                    if event.get('time_shift'):
                        changes.append(f"⏰ Time change: {event.get('time_shift')}")
                    if event.get('new_start_time') and event.get('new_end_time'):
                        new_start = event.get('new_start_time')
                        new_end = event.get('new_end_time')
                        # Format new times
                        try:
                            if ':' in new_start:
                                new_time_str = f"{new_start} - {new_end}"
                            else:
                                new_time_str = f"{new_start} - {new_end}"
                            changes.append(f"🕐 New time: {new_time_str}")
                        except:
                            if new_start:
                                changes.append(f"🕐 New start time: {new_start}")
                            if new_end:
                                changes.append(f"🕐 New end time: {new_end}")
                    if event.get('new_event_name'):
                        changes.append(f"📝 Rename to: {event.get('new_event_name')}")
                    
                    if changes:
                        summary += "\n" + "\n".join(changes)
                    
                    return summary
                else:
                    # For delete/create, show basic details with consistent formatting
                    return f"Event: {event_display}"
            else:
                # Fallback to original formatting if MessageFormatter not available
                return self._format_event_summary_fallback(event)
                
        except Exception as e:
            logger.error(f"Error formatting event summary: {e}")
            return self._format_event_summary_fallback(event)
    
    def _format_event_summary_fallback(self, event: Dict) -> str:
        """Fallback formatting if MessageFormatter is not available"""
        title = event.get('event_name', 'Untitled Event')
        
        # Extract and format the time properly
        start_time = event.get('start_time', 'Unknown time')
        end_time = event.get('end_time', '')
        
        # Parse the datetime and format it nicely
        date_str, time_str = self._format_datetime_nice(start_time, end_time)
        
        # Get proper calendar name
        calendar = self._format_calendar_name(event.get('calendar_name', 'Default calendar'))
        
        intent = event.get('intent', 'create')
        
        if intent == 'update':
            # For updates, show what changes will be made
            summary = f"""Current Event: {title}
Current Date: {date_str}
Current Time: {time_str}
Calendar: {calendar}"""
            
            # Add proposed changes
            changes = []
            if event.get('new_date'):
                changes.append(f"📅 Move to: {event.get('new_date')}")
            if event.get('time_shift'):
                changes.append(f"⏰ Time change: {event.get('time_shift')}")
            if event.get('new_start_time') and event.get('new_end_time'):
                new_start = event.get('new_start_time')
                new_end = event.get('new_end_time')
                # Format new times
                try:
                    if ':' in new_start:
                        new_time_str = f"{new_start} - {new_end}"
                    else:
                        new_time_str = f"{new_start} - {new_end}"
                    changes.append(f"🕐 New time: {new_time_str}")
                except:
                    if new_start:
                        changes.append(f"🕐 New start time: {new_start}")
                    if new_end:
                        changes.append(f"🕐 New end time: {new_end}")
            if event.get('new_event_name'):
                changes.append(f"📝 Rename to: {event.get('new_event_name')}")
            
            if changes:
                summary += f"\n\n📋 Proposed Changes:\n" + "\n".join(changes)
            
            return summary
        else:
            # For delete/create, show basic details
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
        
        # Handle initial batch options (when current_index is 0 AND not yet in one-by-one mode)
        # Check if we're in one-by-one mode by looking at the queue state
        is_one_by_one_mode = queue.get('one_by_one_mode', False)
        
        # CRITICAL FIX: Only handle batch options if NOT in one-by-one mode
        # Once one-by-one mode is active, "yes" means confirm current event, not all events
        if current_index == 0 and not is_one_by_one_mode:
            if user_response in ['one', '1', 'review']:
                # Start one-by-one confirmation - mark the queue as in one-by-one mode
                queue['one_by_one_mode'] = True
                return self.get_next_event_confirmation(chat_id)
            
            elif user_response in ['all', 'delete all', 'confirm all']:
                # Process all events at once - REMOVED 'yes' from here
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
        
        # Handle individual event confirmations (both text and callback data)
        current_event = queue['events'][current_index]
        
        # Handle callback data patterns (e.g., "confirm_update", "cancel_delete")
        is_confirm = (user_response in ['yes', 'y', 'confirm'] or 
                     user_response.startswith('confirm_'))
        is_cancel = (user_response in ['no', 'n'] or 
                     user_response.startswith('cancel_'))

        if user_response == 'skip':
            # Skip current event without processing
            queue['current_index'] += 1
            next_result = self.get_next_event_confirmation(chat_id)
            if next_result.get('queue_complete'):
                return {
                    "success": True,
                    "message": "All events processed!",
                    "queue_complete": True
                }
            return {
                "success": True,
                "message": f"Skipped.\n{next_result['message']}",
                "queue_continues": True,
                "next_confirmation": next_result
            }
        if is_confirm:
            # Process current event
            result = await self._process_single_event(current_event)
            queue['current_index'] += 1
            next_result = self.get_next_event_confirmation(chat_id)

            if next_result.get('queue_complete'):
                return {
                    "success": True,
                    "message": f"{result['message']}\n\n✅ All events processed!",
                    "queue_complete": True
                }
            return {
                "success": True,
                "message": result['message'],
                "next_confirmation": {
                    "message": next_result['message'],
                    "keyboard": next_result.get('keyboard'),
                    "requires_user_action": True
                },
                "queue_continues": True
            }

        elif is_cancel:
            queue['current_index'] += 1
            next_result = self.get_next_event_confirmation(chat_id)
            if next_result.get('queue_complete'):
                return {
                    "success": True,
                    "message": f"Skipped: Event skipped.\n\n{next_result['message']}",
                    "queue_complete": True
                }
            return {
                "success": True,
                "message": f"Skipped: Event skipped.\n\n{next_result['message']}",
                "keyboard": next_result.get('keyboard'),
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
        
        # Build result message with proper formatting following BOT_RULES.md
        date_info = ""
        if events and len(events) > 0:
            # Try to extract date from first event
            first_event = events[0]
            if isinstance(first_event, dict):
                start_time = first_event.get('start_time', '')
                if 'T' in str(start_time):
                    try:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        date_info = dt.strftime('%A, %B %d, %Y')
                    except:
                        pass
        
        # Use centralized formatters if available
        if MessageFormatter and failed == 0:
            # Convert events to proper format for success messages
            formatted_events = []
            for event in events:
                formatted_event = {
                    'summary': event.get('event_name', 'Untitled'),
                    'start': event.get('start_time', ''),
                    'end': event.get('end_time', ''),
                    'calendar_name': event.get('calendar_name', 'Unknown Calendar'),
                    'id': event.get('event_id', ''),
                    'htmlLink': event.get('calendar_link', '')
                }
                formatted_events.append(formatted_event)
            
            if intent == 'create':
                message = MessageFormatter.format_success_message_create(formatted_events, total_events)
            elif intent == 'update':
                message = MessageFormatter.format_success_message_update(formatted_events, total_events, date_info)
            elif intent == 'delete':
                message = MessageFormatter.format_success_message_delete(total_events, date_info)
            else:
                message = f"Successfully {action_text} all {total_events} events!"
        else:
            # Legacy implementation for mixed results or when formatter unavailable
            if failed == 0:
                if intent == 'update' and successful_events:
                    # For updates, show detailed changes made
                    date_suffix = f" on {date_info}" if date_info else ""
                    message = f"Successfully updated all {total_events} events{date_suffix}:\n\n" + "\n".join(successful_events)
                elif intent == 'delete':
                    date_suffix = f" on {date_info}" if date_info else ""
                    message = f"Successfully deleted all {total_events} events{date_suffix}!"
                else:
                    date_suffix = f" on {date_info}" if date_info else ""
                    message = f"Successfully {action_text} all {total_events} events{date_suffix}!"
            elif successful == 0:
                date_suffix = f" on {date_info}" if date_info else ""
                message = f"Failed to {intent} all {total_events} events{date_suffix}:\n\n" + "\n".join(failed_events)
            else:
                date_suffix = f" on {date_info}" if date_info else ""
                message = f"Partially completed: {successful} events {action_text}, {failed} failed{date_suffix}:\n\n"
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
                    
                    # Handle time shift (supports both "move earlier/later" and "extend duration")
                    if event.get('time_shift'):
                        try:
                            from datetime import datetime, timedelta
                            import re
                            
                            # Parse current times
                            current_start = event.get('start_time')
                            current_end = event.get('end_time')
                            
                            if current_start and 'T' in str(current_start):
                                start_dt = datetime.fromisoformat(current_start.replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(current_end.replace('Z', '+00:00')) if current_end and 'T' in str(current_end) else None
                                
                                # Parse time shift (e.g., "1 hour", "30 minutes", "-3 hours")
                                time_shift = event.get('time_shift', '')
                                
                                logger.info(f"EventQueue: Time shift request: {time_shift} for event")
                                logger.info(f"EventQueue: BEFORE UPDATE: Event start={current_start}, end={current_end}")
                                
                                # Determine if this is a duration change or a time shift
                                is_duration_change = any(keyword in time_shift.lower() for keyword in [
                                    'extend', 'make it', 'long', 'duration', 'end time to', 'after start'
                                ])
                                is_time_shift = any(keyword in time_shift.lower() for keyword in [
                                    'move', 'shift', 'earlier', 'later', 'forward', 'back'
                                ])
                                
                                # Extract amount and direction
                                negative_shift = '-' in time_shift or any(word in time_shift.lower() for word in ['earlier', 'back'])
                                shift_match = re.search(r'(\d+)\s*(hour|minute|hr|min)', time_shift.lower())
                                
                                if shift_match:
                                    amount = int(shift_match.group(1))
                                    unit = shift_match.group(2)
                                    
                                    if negative_shift:
                                        amount = -amount
                                    
                                    if is_duration_change:
                                        # Duration change: keep start time, modify end time to be X hours/minutes after start
                                        if unit in ['hour', 'hr']:
                                            new_end_dt = start_dt + timedelta(hours=abs(amount))  # Duration is always positive
                                        elif unit in ['minute', 'min']:
                                            new_end_dt = start_dt + timedelta(minutes=abs(amount))
                                        
                                        update_data['start_time'] = start_dt.isoformat()
                                        update_data['end_time'] = new_end_dt.isoformat()
                                        
                                        logger.info(f"EventQueue: DURATION CHANGE: {time_shift} -> duration = {abs(amount)} {unit}")
                                        logger.info(f"EventQueue: RESULT: start unchanged, end = start + {abs(amount)} {unit}")
                                        
                                    else:
                                        # Time shift: move both start and end times by the same amount
                                        if unit in ['hour', 'hr']:
                                            time_delta = timedelta(hours=amount)
                                        elif unit in ['minute', 'min']:
                                            time_delta = timedelta(minutes=amount)
                                        
                                        new_start_dt = start_dt + time_delta
                                        new_end_dt = end_dt + time_delta if end_dt else new_start_dt + timedelta(hours=1)  # Default 1hr if no end
                                        
                                        update_data['start_time'] = new_start_dt.isoformat()
                                        update_data['end_time'] = new_end_dt.isoformat()
                                        
                                        logger.info(f"EventQueue: TIME SHIFT: {time_shift} -> shift = {amount} {unit}")
                                        logger.info(f"EventQueue: RESULT: both start and end moved by {amount} {unit}")
                                    
                                    logger.info(f"EventQueue: AFTER CALCULATION: start={update_data['start_time']}, end={update_data['end_time']}")
                                else:
                                    logger.warning(f"EventQueue: Could not parse time shift: {time_shift}")
                                    
                            else:
                                logger.warning(f"EventQueue: Invalid datetime format for time shift: start={current_start}, end={current_end}")
                                    
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
                        # CRITICAL FIX: Build success message with ACTUAL updated times, not just operation description
                        updated_event = result.get('updated_event', {})
                        
                        # Get the actual new times from update_data (what was sent to calendar)
                        new_start = update_data.get('start_time')
                        new_end = update_data.get('end_time')
                        original_start = event.get('start_time')
                        original_end = event.get('end_time')
                        
                        # Format actual new times for display
                        actual_changes = []
                        date_info = ""
                        time_info = ""
                        
                        if new_start and 'T' in str(new_start):
                            try:
                                new_start_dt = datetime.fromisoformat(new_start.replace('Z', '+00:00'))
                                date_info = new_start_dt.strftime('%A, %B %d, %Y')
                                start_time_display = new_start_dt.strftime('%I:%M %p')
                                
                                if new_end and 'T' in str(new_end):
                                    new_end_dt = datetime.fromisoformat(new_end.replace('Z', '+00:00'))
                                    end_time_display = new_end_dt.strftime('%I:%M %p')
                                    time_info = f"at {start_time_display} - {end_time_display}"
                                else:
                                    time_info = f"at {start_time_display}"
                                
                                # Compare with original to show what changed
                                if original_start and original_start != new_start:
                                    try:
                                        orig_start_dt = datetime.fromisoformat(original_start.replace('Z', '+00:00'))
                                        orig_time = orig_start_dt.strftime('%I:%M %p')
                                        actual_changes.append(f"time changed from {orig_time} to {start_time_display}")
                                    except:
                                        actual_changes.append(f"time updated to {start_time_display}")
                                
                            except Exception as e:
                                logger.warning(f"Error formatting updated times: {e}")
                                if event.get('time_shift'):
                                    actual_changes.append(f"time shifted by {event.get('time_shift')}")
                        
                        # Add other change descriptions
                        if event.get('new_event_name'):
                            actual_changes.append(f"renamed to '{event.get('new_event_name')}'")
                        if event.get('new_calendar'):
                            actual_changes.append(f"moved to {event.get('new_calendar')}")
                        
                        # Format the event with hyperlink and show NEW info
                        event_link = result.get('event_link', '') or updated_event.get('htmlLink', '')
                        event_title = event.get('event_name', 'Event')
                        calendar_name = event.get('calendar_name', 'Unknown Calendar')
                        
                        if event_link:
                            formatted_title = f"[{event_title}]({event_link})"
                        else:
                            formatted_title = f"'{event_title}'"
                        
                        # Build comprehensive message showing UPDATED info, not original
                        if date_info and time_info:
                            success_message = f"• Updated {formatted_title} on {date_info} {time_info} ({calendar_name})"
                        else:
                            change_desc = ", ".join(actual_changes) if actual_changes else "updated"
                            success_message = f"• Updated {formatted_title} - {change_desc} ({calendar_name})"
                        
                        return {
                            "success": True,
                            "message": success_message,
                            "event_link": event_link,
                            "updated_info": {
                                "start": new_start,
                                "end": new_end,
                                "date": date_info
                            }
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
