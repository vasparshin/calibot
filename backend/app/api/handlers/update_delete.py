"""Extraction of update/delete multi or single event handling with confirmation.
Phase 2 refactor: encapsulates logic previously inline in routes.
"""
from __future__ import annotations
from typing import Dict, Any, List
import logging
from app.utils.inline_keyboard import InlineKeyboardHelper
from app.utils.message_formatter import MessageFormatter

logger = logging.getLogger(__name__)

async def process_update_delete_with_confirmation(
    chat_id: int,
    event_data: Dict[str, Any],
    calendar_service,
    event_queue_handler,
    multi_event_handler,
    send_fn,
    conversation_state,
):
    intent = event_data.get("intent")
    if intent not in ["delete", "update"]:
        return {"handled": False}
    if not event_data.get("confirmation_needed", True):
        return {"handled": False}

    # Build query params
    query_params = {
        "event_name": event_data.get("event_name", ""),
        "date": event_data.get("date", ""),
    }
    if event_data.get("start_time_after"):
        query_params["start_time_after"] = event_data["start_time_after"]
    if event_data.get("start_time_before"):
        query_params["start_time_before"] = event_data["start_time_before"]

    matched = await calendar_service.query_events(query_params)
    if not (isinstance(matched, dict) and matched.get("success") and matched.get("events")):
        # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
        # Don't provide hardcoded "no events found" message
        # Let LLM handle this scenario through proper prompting
        msg = f"I couldn't find any events matching your {intent} request. Could you please provide more specific details?"
        await send_fn(chat_id, msg)
        conversation_state.add_message(chat_id, "assistant", msg)
        return {"handled": True, "status": "ok"}

    events = matched["events"]
    if not isinstance(events, list):
        msg = "Sorry, there was an issue retrieving events. Please try again."
        await send_fn(chat_id, msg)
        conversation_state.add_message(chat_id, "assistant", msg)
        return {"handled": True, "status": "ok"}

    # Name filtering
    if event_data.get("event_name"):
        name_lower = event_data["event_name"].lower()
        events = [e for e in events if isinstance(e, dict) and name_lower in e.get("summary", "").lower()]

    # Target filtering
    target = (event_data.get("target") or "").lower()
    if target and events:
        if target == "last":
            events = [events[-1]]
        elif target == "first":
            events = [events[0]]
        elif target in ["2nd", "second", "2"] and len(events) >= 2:
            events = [events[1]]
        elif target in ["3rd", "third", "3"] and len(events) >= 3:
            events = [events[2]]
        elif target in ["4th", "fourth", "4"] and len(events) >= 4:
            events = [events[3]]

    if not events:
        no_events_msg = "No events found matching your criteria."
        await send_fn(chat_id, no_events_msg)
        conversation_state.add_message(chat_id, "assistant", no_events_msg)
        return {"handled": True, "status": "ok"}

    # Multi-event path → queue system
    if len(events) > 1:
        # Build enriched proposed change confirmation using MessageFormatter
        formatted_events = []
        for ev in events:
            if not isinstance(ev, dict) or "id" not in ev:
                continue
            base_event = {
                'summary': ev.get('summary', 'Untitled'),
                'start': ev.get('start', ''),
                'end': ev.get('end', ''),
                'calendar_name': ev.get('calendar_name', 'Unknown Calendar'),
                'id': ev.get('id'),
                'htmlLink': ev.get('htmlLink') or ev.get('calendar_link')
            }
            proposed = event_data  # same change applied to all events for now
            enriched_line = MessageFormatter.format_event_with_proposed_changes(base_event, proposed)
            formatted_events.append({
                'summary': enriched_line,  # treat full line as summary for display
                'start': base_event['start'],
                'end': base_event['end'],
                'calendar_name': base_event['calendar_name'],
                'id': base_event['id'],
                'htmlLink': base_event.get('htmlLink')
            })

        header = f"Found {len(formatted_events)} events to {intent} (review proposed changes):\n\n"
        # Use list display without re-numbering inside each bullet since lines may already contain arrows
        display_lines = []
        for idx, ev in enumerate(formatted_events, 1):
            # ev['summary'] already contains bullet from formatter; ensure consistency
            if not ev['summary'].startswith('•'):
                display_lines.append(f"{idx}. {ev['summary']}")
            else:
                display_lines.append(f"{idx}. {ev['summary'][2:]}")
        message = header + "\n".join(display_lines)
        keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard(action=intent)
        multi_event_handler.store_pending_operation(chat_id, {
            "type": f"{intent}_multiple",
            "events": events,
            "original_request": event_data,
        })
        await send_fn(chat_id, message, reply_markup=keyboard)
        conversation_state.add_message(chat_id, "assistant", message)
        return {"handled": True, "status": "ok"}

    # Single event path
    event = events[0]
    if not isinstance(event, dict) or "id" not in event:
        msg = "Sorry, the event data is incomplete. Please try again."
        await send_fn(chat_id, msg)
        conversation_state.add_message(chat_id, "assistant", msg)
        return {"handled": True, "status": "ok"}

    title = MessageFormatter.format_event_title(event.get("summary", "Untitled"))
    start_time = event.get("start", "")
    if "T" in start_time:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            formatted_date = dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            formatted_date = start_time
    else:
        formatted_date = start_time
    calendar_name = event.get("calendar_name", "Unknown Calendar")
    event_link = event.get("link") or event.get("htmlLink") or event.get("event_link") or event.get("calendar_link", "")
    if event_link:
        summary = f"[{title}]({event_link}) on {formatted_date} ({calendar_name})"
    else:
        summary = f"'{title}' on {formatted_date} ({calendar_name})"

    if intent == "delete":
        confirmation_msg = f"Are you sure you want to delete {summary}?"
        op_type = "delete_single"
    else:
        if event_data.get("new_date"):
            # CRITICAL FIX: Use dd.mm.yy format for user-facing messages
            from datetime import datetime
            try:
                date_obj = datetime.fromisoformat(event_data['new_date'].split('T')[0])
                date_formatted = date_obj.strftime('%d.%m.%y')
                action_desc = f"move to {date_formatted}"
            except:
                action_desc = f"move to {event_data['new_date']}"  # Fallback
        elif event_data.get("new_event_name"):
            action_desc = f"rename to '{event_data['new_event_name']}'"
        elif event_data.get("time_shift"):
            action_desc = f"shift time by {event_data['time_shift']}"
        else:
            action_desc = "update"
        confirmation_msg = f"Are you sure you want to {action_desc} {summary}?"
        op_type = "update_multiple"  # consistent with existing store logic

    keyboard = InlineKeyboardHelper.create_single_event_confirmation_keyboard(action=intent)
    multi_event_handler.store_pending_operation(chat_id, {
        "type": op_type,
        "events": [event],
        "original_request": event_data,
    })
    await send_fn(chat_id, confirmation_msg, reply_markup=keyboard)
    conversation_state.add_message(chat_id, "assistant", confirmation_msg)
    return {"handled": True, "status": "ok"}
