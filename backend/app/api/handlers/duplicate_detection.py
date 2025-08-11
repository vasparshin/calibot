"""Duplicate detection logic extracted from routes (phase 1).
Currently mirrors existing behavior; future enhancement may add fuzzy time overlap checks.
"""
from __future__ import annotations
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def find_duplicates(events: List[Dict[str, Any]], calendar_service) -> List[Dict[str, Any]]:
    duplicates_found = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        event_name = event.get("event_name")
        date = event.get("date")
        if not event_name or not date:
            logger.debug("Skipping incomplete event for duplicate check: %s", event)
            continue
        try:
            existing = await calendar_service.query_events({"event_name": event_name, "date": date})
            if existing.get("success") and existing.get("events"):
                event_start = event.get("start_time", "")
                for existing_event in existing["events"]:
                    existing_summary = existing_event.get("summary", "").lower()
                    name_lower = event_name.lower()
                    if (existing_summary == name_lower or name_lower in existing_summary or existing_summary in name_lower):
                        existing_start = existing_event.get("start", "")
                        if not event_start or event_start in existing_start:
                            duplicates_found.append({
                                "new_event": event,
                                "existing_event": existing_event,
                                "index": index,
                            })
                            break
        except Exception as e:
            logger.warning("Duplicate check error: %s", e)
    logger.info("Found %d potential duplicates", len(duplicates_found))
    return duplicates_found
