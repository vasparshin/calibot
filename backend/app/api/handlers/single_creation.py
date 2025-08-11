"""Single event creation extracted from routes (phase 1)."""
from __future__ import annotations
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def create_single_event(chat_id: int, event_data: Dict[str, Any], calendar_service, send_fn, formatter_fn, conversation_state):
    try:
        res = await calendar_service.create_event(event_data)
        if res.get("success"):
            formatted = formatter_fn(event_data, res, calendar_service)
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
