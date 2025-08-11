"""Event query & filtering utilities extracted from routes.
Phase 1: direct lift of existing logic with light normalization.
"""
from __future__ import annotations
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

async def query_and_filter_events(event_data: Dict[str, Any], calendar_service) -> Dict[str, Any]:
    query_params = {
        "event_name": event_data.get("event_name", ""),
        "date": event_data.get("date", "")
    }
    if event_data.get("start_time_after"):
        query_params["start_time_after"] = event_data["start_time_after"]
    if event_data.get("start_time_before"):
        query_params["start_time_before"] = event_data["start_time_before"]

    matched = await calendar_service.query_events(query_params)
    if not isinstance(matched, dict) or not matched.get("success") or not matched.get("events"):
        return {"success": False, "reason": "no_matches", "events": []}

    events = matched["events"]
    if not isinstance(events, list):
        return {"success": False, "reason": "invalid_type", "events": []}

    # Name filter
    if event_data.get("event_name"):
        name_lower = event_data["event_name"].lower()
        filtered = []
        for ev in events:
            if isinstance(ev, dict) and name_lower in ev.get("summary", "").lower():
                filtered.append(ev)
        events = filtered

    # Target filtering (first, last, nth)
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
        return {"success": False, "reason": "filtered_empty", "events": []}

    return {"success": True, "events": events}
