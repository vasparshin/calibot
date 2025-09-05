"""
Response manager for consistent message formatting and response handling.
Consolidates all message formatting logic into a single, reusable component.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseManager:
    """Centralized response formatting and message management."""

    @staticmethod
    def format_single_event_display(event_data: Dict[str, Any], include_hyperlink: bool = True) -> str:
        """Format single event for display following BOT_RULES.md specifications."""
        try:
            # Import here to avoid circular imports
            from app.utils.message_formatter import MessageFormatter

            return MessageFormatter.format_single_event_display(event_data, include_hyperlink)
        except ImportError:
            # Fallback formatting
            event_name = event_data.get('summary', event_data.get('event_name', 'Event'))
            date = event_data.get('date', 'today')
            start_time = event_data.get('start_time', 'Unknown time')
            end_time = event_data.get('end_time', 'Unknown time')
            calendar_name = event_data.get('calendar_name', 'Unknown Calendar')

            if include_hyperlink and event_data.get('htmlLink'):
                return f"• [{event_name}]({event_data['htmlLink']}) on {date} at {start_time} - {end_time} ({calendar_name})"
            else:
                return f"• {event_name} on {date} at {start_time} - {end_time} ({calendar_name})"

    @staticmethod
    def format_event_list_display(events: List[Dict], numbered: bool = False, include_hyperlink: bool = True) -> str:
        """Format list of events for display."""
        try:
            from app.utils.message_formatter import MessageFormatter
            return MessageFormatter.format_event_list_display(events, numbered, include_hyperlink)
        except ImportError:
            # Fallback formatting
            if not events:
                return "No events found."

            formatted_events = []
            for i, event in enumerate(events, 1):
                event_name = event.get('summary', event.get('event_name', 'Event'))
                date = event.get('date', 'Unknown date')
                start_time = event.get('start_time', 'Unknown time')
                end_time = event.get('end_time', 'Unknown time')
                calendar_name = event.get('calendar_name', 'Unknown Calendar')

                if numbered:
                    prefix = f"{i}."
                else:
                    prefix = "•"

                if include_hyperlink and event.get('htmlLink'):
                    formatted_events.append(f"{prefix} [{event_name}]({event['htmlLink']}) on {date} at {start_time} - {end_time} ({calendar_name})")
                else:
                    formatted_events.append(f"{prefix} {event_name} on {date} at {start_time} - {end_time} ({calendar_name})")

            return "\n".join(formatted_events)

    @staticmethod
    def format_confirmation_message(action: str, events: List[Dict], total_count: Optional[int] = None) -> str:
        """Format confirmation message for multi-event operations."""
        try:
            from app.utils.message_formatter import MessageFormatter
            return MessageFormatter.format_confirmation_message(action, events, total_count)
        except ImportError:
            # Fallback formatting
            if total_count is None:
                total_count = len(events)

            action_title = action.title()
            message = f"Found {total_count} events to {action}:\n\n"

            for i, event in enumerate(events, 1):
                event_name = event.get('summary', event.get('event_name', 'Event'))
                date = event.get('date', 'Unknown date')
                start_time = event.get('start_time', 'Unknown time')
                calendar_name = event.get('calendar_name', 'Unknown Calendar')
                message += f"{i}. {event_name} on {date} at {start_time} ({calendar_name})\n"

            return message

    @staticmethod
    def format_success_message(action: str, event_data: Dict[str, Any], calendar_result: Dict[str, Any]) -> str:
        """Format success message for completed operations."""
        try:
            from app.utils.message_formatter import MessageFormatter

            # Create event data structure for formatting
            formatted_event = {
                'summary': event_data.get('event_name', 'Event'),
                'start': f"{event_data.get('date', '')}T{event_data.get('start_time', '')}:00",
                'end': f"{event_data.get('date', '')}T{event_data.get('end_time', '')}:00",
                'calendar_name': calendar_result.get('calendar_used', event_data.get('calendar_name', 'Calendar')),
                'id': calendar_result.get('event_id', ''),
                'htmlLink': calendar_result.get('event_link', '')
            }

            formatted_display = MessageFormatter.format_single_event_display(formatted_event, include_hyperlink=True)

            if action == "create":
                return f"Event created successfully:\n\n{formatted_display}"
            elif action == "update":
                change_note = "(moved)" if calendar_result.get("moved") else ""
                return f"Successfully updated event {change_note}:\n\n{formatted_display}"
            elif action == "delete":
                return f"Successfully deleted: {formatted_display}"
            else:
                return f"Operation completed successfully:\n\n{formatted_display}"

        except ImportError:
            # Fallback formatting
            event_name = event_data.get('event_name', 'Event')
            date = event_data.get('date', 'today')
            start_time = event_data.get('start_time', 'Unknown time')
            end_time = event_data.get('end_time', 'Unknown time')
            calendar_name = calendar_result.get('calendar_used', event_data.get('calendar_name', 'Calendar'))

            action_past = {
                'create': 'created',
                'update': 'updated',
                'delete': 'deleted'
            }.get(action, 'processed')

            return f"Successfully {action_past} event:\n\n• {event_name} on {date} at {start_time} - {end_time} ({calendar_name})"

    @staticmethod
    def format_batch_success_message(action: str, successful_events: List[Dict], failed_events: List[Dict] = None) -> str:
        """Format success message for batch operations."""
        failed_events = failed_events or []

        if not successful_events and not failed_events:
            return f"No events were {action}d."

        message = ""
        if successful_events:
            if len(successful_events) == 1:
                message += f"Event {action}d successfully:\n\n"
            else:
                message += f"Successfully {action}d {len(successful_events)} events:\n\n"

            for event in successful_events:
                if isinstance(event, dict) and 'formatted' in event:
                    message += f"{event['formatted']}\n"
                else:
                    message += f"• {event}\n"

        if failed_events:
            if successful_events:
                message += f"\nFailed to {action} {len(failed_events)} events:\n"
            else:
                message += f"Failed to {action} all {len(failed_events)} events:\n"

            for event in failed_events:
                if isinstance(event, dict) and 'error' in event:
                    message += f"• {event.get('time', 'Unknown time')}: {event['error']}\n"
                else:
                    message += f"• {event}\n"

        return message

    @staticmethod
    def format_error_message(error_type: str, details: str = None) -> str:
        """Format error messages consistently."""
        base_messages = {
            'authentication': "❌ Authentication system is not properly configured. Please contact the administrator.",
            'auth_expired': "❌ Your Google authentication has expired. Please re-authenticate.",
            'auth_unavailable': "❌ Authentication system is temporarily unavailable. Please try again later.",
            'processing': "I'm experiencing technical difficulties. Please try again in a moment.",
            'validation': "Sorry, I had trouble understanding your request. Could you please try again?",
            'network': "Network error occurred. Please check your connection and try again.",
            'calendar_api': "Calendar service is temporarily unavailable. Please try again later.",
            'generic': "An unexpected error occurred. Please try again."
        }

        message = base_messages.get(error_type, base_messages['generic'])
        if details:
            message += f"\n\nError details: {details}"

        return message

    @staticmethod
    def format_duplicate_confirmation(duplicates: List[Dict]) -> tuple[str, Dict]:
        """Format duplicate confirmation message and keyboard."""
        try:
            from app.utils.ui_helpers import format_duplicate_confirmation_with_keyboard
            return format_duplicate_confirmation_with_keyboard(duplicates, "create")
        except ImportError:
            # Fallback formatting
            message = f"Found {len(duplicates)} potential duplicate events:\n\n"

            for i, dup in enumerate(duplicates, 1):
                new_event = dup['new_event']
                existing_event = dup['existing_event']
                message += f"{i}. New: {new_event.get('event_name', 'Event')} at {new_event.get('start_time', 'Unknown time')}\n"
                message += f"   Existing: {existing_event.get('summary', 'Event')} at {existing_event.get('start', 'Unknown time')}\n\n"

            message += "Create duplicates anyway?"

            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Create Anyway", "callback_data": "confirm_duplicates"},
                        {"text": "❌ Cancel", "callback_data": "cancel_duplicates"}
                    ]
                ]
            }

            return message, keyboard

    @staticmethod
    def create_confirmation_keyboard(action: str, event_count: int = 1) -> Dict:
        """Create appropriate confirmation keyboard based on event count."""
        try:
            from app.utils.inline_keyboard import InlineKeyboardHelper

            if event_count > 1:
                return InlineKeyboardHelper.create_multi_event_confirmation_keyboard(action)
            else:
                return InlineKeyboardHelper.create_single_event_confirmation_keyboard(action)
        except ImportError:
            # Fallback keyboard creation
            if event_count > 1:
                return {
                    "inline_keyboard": [
                        [
                            {"text": "🔄 All", "callback_data": f"confirm_all_{action}"},
                            {"text": "1️⃣ One by One", "callback_data": f"confirm_one_{action}"},
                            {"text": "❌ Cancel", "callback_data": f"cancel_{action}"}
                        ]
                    ]
                }
            else:
                return {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Yes", "callback_data": f"confirm_{action}"},
                            {"text": "❌ No", "callback_data": f"cancel_{action}"}
                        ]
                    ]
                }
