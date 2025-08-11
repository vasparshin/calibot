"""Unified update/delete handling (confirmation + immediate paths).
Replaces separate confirmation and immediate handlers.
"""
from __future__ import annotations
from typing import Dict, Any, List
import logging
from app.services.telegram import create_confirmation_keyboard
from app.utils.ui_helpers import (
    format_no_events_message,
    format_event_title,
    format_multi_event_confirmation_with_keyboard,
    format_event_for_display,
)

logger = logging.getLogger(__name__)

async def process_update_delete(
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

    confirmation_needed = event_data.get("confirmation_needed", True)

    # Query events first (shared for both paths)
    matched = await calendar_service.query_events({
        "event_name": event_data.get("event_name", ""),
        "date": event_data.get("date", ""),
    })
    if not (isinstance(matched, dict) and matched.get("success") and matched.get("events")):
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

    # Name filtering (confirmation + immediate)
    if event_data.get("event_name"):
        name_lower = event_data["event_name"].lower()
        events = [e for e in events if isinstance(e, dict) and name_lower in e.get("summary", "").lower()]
        if not events:
            msg = format_no_events_message(event_data)
            await send_fn(chat_id, msg)
            conversation_state.add_message(chat_id, "assistant", msg)
            return {"handled": True, "status": "ok"}

    # Target filtering (shared)
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
        elif target == "all":
            pass  # keep all
        if not events:
            msg = format_no_events_message(event_data)
            await send_fn(chat_id, msg)
            conversation_state.add_message(chat_id, "assistant", msg)
            return {"handled": True, "status": "ok"}

    # Immediate path
    if confirmation_needed is False:
        # If target == all and multiple events, process all directly
        if len(events) > 1 and (target == "all"):
            results = []
            failures = []
            for ev in events:
                if intent == "update":
                    source_calendar_id = ev.get('calendar_id', 'primary')
                    resp = calendar_service.update_event(ev.get('id'), event_data, source_calendar_id)
                    if resp.get("success"):
                        formatted = format_event_for_display(ev, resp, calendar_service)
                        results.append(formatted)
                    else:
                        failures.append(f"• {ev.get('summary','Event')}: {resp.get('message','Unknown error')}")
                else:
                    source_calendar_id = ev.get('calendar_id', 'primary')
                    resp = calendar_service.delete_event(ev.get('id'), source_calendar_id)
                    if resp.get("success"):
                        from app.utils.message_formatter import MessageFormatter
                        name = MessageFormatter.format_event_title(ev.get('summary','Event'))
                        results.append(f"Deleted: {name}")
                    else:
                        failures.append(f"• {ev.get('summary','Event')}: {resp.get('message','Unknown error')}")
            if intent == "update":
                base_msg = f"Updated {len(results)} events" if results else "No events updated"
            else:
                base_msg = f"Deleted {len(results)} events" if results else "No events deleted"
            msg = base_msg
            if results:
                msg += "\n\n" + "\n".join(results)
            if failures:
                msg += f"\n\nFailed ({len(failures)}):\n" + "\n".join(failures)
            await send_fn(chat_id, msg)
            conversation_state.add_message(chat_id, "assistant", msg)
            return {"handled": True, "status": "ok"}
        # Single (or first) event immediate
        ev = events[0]
        if intent == "update":
            source_calendar_id = ev.get('calendar_id', 'primary')
            resp = calendar_service.update_event(ev.get('id'), event_data, source_calendar_id)
            if resp.get("success"):
                formatted = format_event_for_display(ev, resp, calendar_service)
                msg = f"Event updated successfully:\n\n{formatted}" if not resp.get("moved") else f"Event moved successfully:\n\n{formatted}"
            else:
                msg = f"Failed to update event: {resp.get('message','Unknown error')}"
        else:
            source_calendar_id = ev.get('calendar_id', 'primary')
            resp = calendar_service.delete_event(ev.get('id'), source_calendar_id)
            if resp.get("success"):
                from app.utils.message_formatter import MessageFormatter
                name = MessageFormatter.format_event_title(ev.get('summary','Event'))
                msg = f"Successfully deleted: {name}"
            else:
                msg = f"Failed to delete event: {resp.get('message','Unknown error')}"
        await send_fn(chat_id, msg)
        conversation_state.add_message(chat_id, "assistant", msg)
        return {"handled": True, "status": "ok"}

    # Confirmation path (existing logic migrated from previous handler)
    if len(events) > 1:
        queue_events = []
        for ev in events:
            if not isinstance(ev, dict) or "id" not in ev:
                continue
            q_ev = {
                "intent": intent,
                "event_id": ev["id"],
                "event_name": ev.get("summary", "Untitled"),
                "start_time": ev.get("start", "Unknown time"),
                "end_time": ev.get("end", "Unknown time"),
                "calendar_id": ev.get("calendar_id", "primary"),
                "calendar_name": ev.get("calendar_name", "Default"),
            }
            if intent == "update":
                for key in [
                    "new_start_time","new_end_time","new_date","new_event_name","time_shift","date_shift","description","location"
                ]:
                    if key in event_data:
                        q_ev[key] = event_data[key]
            queue_events.append(q_ev)
        if not queue_events:
            msg = "Sorry, no valid events found that match your criteria."
            await send_fn(chat_id, msg)
            conversation_state.add_message(chat_id, "assistant", msg)
            return {"handled": True, "status": "ok"}
        queue_result = event_queue_handler.create_event_queue_from_list(chat_id, queue_events)
        keyboard = queue_result.get("keyboard")
        if keyboard:
            await send_fn(chat_id, queue_result["message"], reply_markup=keyboard)
        else:
            await send_fn(chat_id, queue_result["message"])
        conversation_state.add_message(chat_id, "assistant", queue_result["message"])
        return {"handled": True, "status": "ok"}

    # Single event confirmation
    ev = events[0]
    if not isinstance(ev, dict) or "id" not in ev:
        msg = "Sorry, the event data is incomplete. Please try again."
        await send_fn(chat_id, msg)
        conversation_state.add_message(chat_id, "assistant", msg)
        return {"handled": True, "status": "ok"}

    title = format_event_title(ev.get("summary", "Untitled"))
    start_time = ev.get("start", "")
    if "T" in start_time:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            formatted_date = dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            formatted_date = start_time
    else:
        formatted_date = start_time
    calendar_name = ev.get("calendar_name", "Unknown Calendar")
    event_link = ev.get("link") or ev.get("htmlLink") or ev.get("event_link") or ev.get("calendar_link", "")
    if event_link:
        summary = f"[{title}]({event_link}) on {formatted_date} ({calendar_name})"
    else:
        summary = f"'{title}' on {formatted_date} ({calendar_name})"

    if intent == "delete":
        confirmation_msg = f"Are you sure you want to delete {summary}?"
        op_type = "delete_single"
    else:
        if event_data.get("new_date"):
            action_desc = f"move to {event_data['new_date']}"
        elif event_data.get("new_event_name"):
            action_desc = f"rename to '{event_data['new_event_name']}'"
        elif event_data.get("time_shift"):
            action_desc = f"shift time by {event_data['time_shift']}"
        else:
            action_desc = "update"
        confirmation_msg = f"Are you sure you want to {action_desc} {summary}?"
        op_type = "update_multiple"

    keyboard = create_confirmation_keyboard("single_event")
    multi_event_handler.store_pending_operation(chat_id, {
        "type": op_type,
        "events": [ev],
        "original_request": event_data,
    })
    await send_fn(chat_id, confirmation_msg, reply_markup=keyboard)
    conversation_state.add_message(chat_id, "assistant", confirmation_msg)
    return {"handled": True, "status": "ok"}
