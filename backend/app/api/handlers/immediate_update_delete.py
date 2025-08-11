"""Handles update/delete when confirmation_needed is False (immediate execution).
Phase 2 companion to process_update_delete_with_confirmation.
"""
from __future__ import annotations
from typing import Dict, Any
import logging
from app.utils.ui_helpers import format_no_events_message, format_event_for_display

logger = logging.getLogger(__name__)

async def process_immediate_update_delete(
    chat_id: int,
    event_data: Dict[str, Any],
    calendar_service,
    send_fn,
    conversation_state,
):
    intent = event_data.get("intent")
    if intent not in ["update", "delete"]:
        return {"handled": False}
    if event_data.get("confirmation_needed") is not False:
        return {"handled": False}

    matched = await calendar_service.query_events({
        "event_name": event_data.get("event_name", ""),
        "date": event_data.get("date", ""),
    })
    if not matched.get("success") or not matched.get("events"):
        msg = format_no_events_message(event_data)
        await send_fn(chat_id, msg)
        conversation_state.add_message(chat_id, "assistant", msg)
        return {"handled": True, "status": "ok"}

    events = matched["events"]
    if not isinstance(events, list) or not events:
        msg = format_no_events_message(event_data)
        await send_fn(chat_id, msg)
        conversation_state.add_message(chat_id, "assistant", msg)
        return {"handled": True, "status": "ok"}

    # For immediate path, only act on first (or targeted) event for simplicity
    target_idx = 0
    target = (event_data.get("target") or "").lower()
    if target in ["last"]:
        target_idx = len(events) - 1
    elif target in ["2nd", "second", "2"] and len(events) >= 2:
        target_idx = 1
    elif target in ["3rd", "third", "3"] and len(events) >= 3:
        target_idx = 2
    elif target in ["4th", "fourth", "4"] and len(events) >= 4:
        target_idx = 3

    event = events[target_idx]
    if intent == "update":
        source_calendar_id = event.get('calendar_id', 'primary')
        response = calendar_service.update_event(event.get('id'), event_data, source_calendar_id)
        if response.get("success"):
            formatted = format_event_for_display(event, response, calendar_service)
            if response.get("moved"):
                msg = f"Event moved successfully:\n\n{formatted}"
            else:
                msg = f"Event updated successfully:\n\n{formatted}"
        else:
            msg = f"Failed to update event: {response.get('message', 'Unknown error')}"
    else:  # delete
        source_calendar_id = event.get('calendar_id', 'primary')
        response = calendar_service.delete_event(event.get('id'), source_calendar_id)
        if response.get("success"):
            from app.utils.message_formatter import MessageFormatter
            event_name = MessageFormatter.format_event_title(event.get('summary', 'Event'))
            msg = f"Successfully deleted: {event_name}"
        else:
            msg = f"Failed to delete event: {response.get('message', 'Unknown error')}"

    await send_fn(chat_id, msg)
    conversation_state.add_message(chat_id, "assistant", msg)
    return {"handled": True, "status": "ok"}
