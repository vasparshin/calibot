"""Batch creation handling extracted from routes (phase 1).
Keeps behavior identical; future phases will unify with single creation.
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

async def process_batch_creation(chat_id: int, event_data: Dict[str, Any], calendar_service, send_fn, formatter_fn, duplicate_formatter_fn, conversation_state, duplicate_checker):
    events_to_create = event_data.get("events", [])
    enhanced = []
    for ev in events_to_create:
        if not isinstance(ev, dict):
            continue
        merged = ev.copy()
        for key in ["event_name", "date", "calendar_name", "description"]:
            if key in event_data and key not in merged:
                merged[key] = event_data[key]
        enhanced.append(merged)

    duplicates = await duplicate_checker(enhanced)
    if duplicates:
        duplicate_indices = [d["index"] for d in duplicates]
        non_dupes = [e for i, e in enumerate(enhanced) if i not in duplicate_indices]
        if non_dupes:
            created_count = 0
            success_events: List[str] = []
            for single in non_dupes:
                try:
                    single["intent"] = "create"
                    res = await calendar_service.create_event(single)
                    if res and res.get("success"):
                        created_count += 1
                        success_events.append(formatter_fn(single, res, calendar_service))
                except Exception as e:
                    logger.error("Error creating non-duplicate event: %s", e)
            if success_events:
                if created_count == 1:
                    msg = "Event created successfully:\n\n" + "\n".join(success_events)
                else:
                    msg = f"Successfully created {created_count} events:\n\n" + "\n".join(success_events)
                await send_fn(chat_id, msg)
                conversation_state.add_message(chat_id, "assistant", msg)
        dup_msg, keyboard = duplicate_formatter_fn(duplicates, "create")
        await send_fn(chat_id, dup_msg, reply_markup=keyboard)
        conversation_state.add_message(chat_id, "assistant", dup_msg)
        conversation_state.add_message(chat_id, "system", f"PENDING_DUPLICATE_CREATION:{len(duplicates)} events")
        return {"status": "ok", "handled": True}

    # No duplicates path
    created_count = 0
    failed_count = 0
    success_events: List[str] = []
    failed_events: List[str] = []
    for idx, single in enumerate(enhanced):
        single["intent"] = "create"
        try:
            res = await calendar_service.create_event(single)
            if res and res.get("success"):
                created_count += 1
                success_events.append(formatter_fn(single, res, calendar_service))
            else:
                failed_count += 1
                err = res.get('message', 'Unknown error') if res else 'Unknown error'
                failed_events.append(f"• {single.get('event_name', 'Untitled')} - {err}")
        except Exception as e:
            failed_count += 1
            failed_events.append(f"• {single.get('event_name', 'Untitled')} - Error: {e}")
    if created_count > 0 and failed_count == 0:
        if created_count == 1:
            message = "Event created successfully:\n\n" + "\n".join(success_events)
        else:
            message = f"Successfully created {created_count} events:\n\n" + "\n".join(success_events)
    elif created_count > 0 and failed_count > 0:
        message = f"Created {created_count} events, {failed_count} failed:\n\nSuccessful:\n" + "\n".join(success_events)
        message += "\n\nFailed:\n" + "\n".join(failed_events)
    else:
        message = f"Failed to create all {len(enhanced)} events:\n\n" + "\n".join(failed_events)
    await send_fn(chat_id, message)
    conversation_state.add_message(chat_id, "assistant", message)
    return {"status": "ok", "handled": True}
