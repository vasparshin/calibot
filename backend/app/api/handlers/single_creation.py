"""Single event creation extracted from routes (phase 1)."""
from __future__ import annotations
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def create_single_event(chat_id: int, event_data: Dict[str, Any], calendar_service, send_fn, conversation_state):
    try:
        res = await calendar_service.create_event(event_data)
        if res.get("success"):
            # Use simple formatting instead of the removed formatter function
            event_details = []
            if event_data.get("event_name"):
                event_details.append(f"📅 {event_data['event_name']}")
            if event_data.get("start_time") and event_data.get("end_time"):
                event_details.append(f"🕐 {event_data['start_time']} - {event_data['end_time']}")
            if event_data.get("date"):
                event_details.append(f"📆 {event_data['date']}")
            if event_data.get("calendar_name"):
                event_details.append(f"📚 Calendar: {event_data['calendar_name']}")
            
            formatted = "\n".join(event_details)
            msg = f"Event created successfully:\n\n{formatted}"
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
