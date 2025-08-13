"""Single event creation extracted from routes (phase 1)."""
from __future__ import annotations
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def create_single_event(chat_id: int, event_data: Dict[str, Any], calendar_service, send_fn, conversation_state):
    try:
        res = await calendar_service.create_event(event_data)
        if res.get("success"):
            # Use MessageFormatter for consistent formatting
            try:
                from app.utils.message_formatter import MessageFormatter
                
                # Format the event data for display
                event_for_display = {
                    'summary': event_data.get('event_name', 'Event'),
                    'start': f"{event_data.get('date', '')}T{event_data.get('start_time', '')}:00",
                    'end': f"{event_data.get('date', '')}T{event_data.get('end_time', '')}:00",
                    'calendar_name': res.get('calendar_used', event_data.get('calendar_name', 'Calendar')),
                    'id': res.get('event_id', ''),
                    'htmlLink': res.get('event_link', '')
                }
                
                # Use the centralized formatter for consistency
                formatted_event = MessageFormatter.format_single_event_display(event_for_display, include_hyperlink=True)
                msg = f"Event created successfully:\n\n{formatted_event}"
                
            except ImportError:
                # Fallback formatting that matches MessageFormatter output
                event_name = event_data.get('event_name', 'Event')
                date = event_data.get('date', 'today')
                start_time = event_data.get('start_time', '')
                end_time = event_data.get('end_time', '')
                calendar_name = res.get('calendar_used', event_data.get('calendar_name', 'Calendar'))
                
                msg = f"Event created successfully:\n\n• {event_name} on {date} at {start_time} - {end_time} ({calendar_name})"
            
            await send_fn(chat_id, msg)
            conversation_state.add_message(chat_id, "assistant", msg)
        else:
            err = f"Failed to create event: {res.get('message', 'Unknown error')}"
            await send_fn(chat_id, err)
            conversation_state.add_message(chat_id, "assistant", err)
    except Exception as e:
        err = f"Error creating event: {e}"
        await send_fn(chat_id, err)
        conversation_state.add_message(chat_id, "assistant", err)
