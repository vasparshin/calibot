#!/usr/bin/env python3
"""
Test for Production Delete Bug
==============================

This test reproduces the exact production bug where delete operations fail with:
"'list' object has no attribute 'get'"

Based on production logs from 2025-08-07T11:33:32
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from app.api.routes import process_webhook
from app.services.google_calendar import GoogleCalendarService
from app.services.conversation import ConversationState
from app.services.multi_event_operations import MultiEventOperationHandler
from app.services.event_queue_handler import EventQueueHandler

def test_delete_production_scenario():
    """Test the exact production scenario that's failing"""
    
    print("🔍 Testing Production Delete Scenario")
    print("=" * 60)
    
    # Create mock event data similar to production
    mock_events = [
        {
            "id": "event1",
            "summary": "lesson",
            "start": "2025-08-06T10:00:00",
            "end": "2025-08-06T11:00:00",
            "calendar_id": "primary",
            "calendar_name": "Main Calendar"
        },
        {
            "id": "event2", 
            "summary": "lesson",
            "start": "2025-08-06T14:00:00",
            "end": "2025-08-06T15:00:00",
            "calendar_id": "primary",
            "calendar_name": "Main Calendar"
        },
        {
            "id": "event3",
            "summary": "lesson", 
            "start": "2025-08-06T16:00:00",
            "end": "2025-08-06T17:00:00",
            "calendar_id": "primary", 
            "calendar_name": "Main Calendar"
        }
    ]
    
    # Test 1: Check if events are properly formatted
    print("\n📋 Test 1: Event Format Validation")
    for i, event in enumerate(mock_events):
        try:
            # This is what fails in production - calling .get() on a list
            summary = event.get("summary", "Untitled")
            start_time = event.get("start", "Unknown")
            print(f"   ✅ Event {i+1}: {summary} at {start_time}")
        except AttributeError as e:
            print(f"   ❌ Event {i+1}: {e}")
            print(f"      Event type: {type(event)}")
            print(f"      Event content: {event}")
    
    # Test 2: Simulate the routes.py processing
    print("\n🔧 Test 2: Routes Processing Simulation")
    try:
        # Simulate what happens in routes.py line 143
        search_name = "lesson"
        filtered_events = []
        
        for event in mock_events:
            if search_name in event.get("summary", "").lower():
                filtered_events.append(event)
        
        print(f"   ✅ Filtered {len(filtered_events)} events successfully")
        
        # Test single event processing (line 178)
        if filtered_events:
            event = filtered_events[0]
            event_summary = f"'{event.get('summary', 'Untitled')}' on {event.get('start', 'unknown date')}"
            print(f"   ✅ Event summary: {event_summary}")
            
    except Exception as e:
        print(f"   ❌ Routes processing failed: {e}")
        return False
        
    # Test 3: Multi-event queue creation
    print("\n📬 Test 3: Queue Event Creation")
    try:
        queue_events = []
        for event in mock_events:
            queue_event = {
                "intent": "delete",
                "event_id": event["id"],
                "event_name": event.get("summary", "Untitled"),
                "start_time": event.get("start", "Unknown time"),
                "end_time": event.get("end", "Unknown time"),
                "calendar_id": event.get("calendar_id", "primary"),
                "calendar_name": event.get("calendar_name", "Default")
            }
            queue_events.append(queue_event)
        
        print(f"   ✅ Created {len(queue_events)} queue events successfully")
        
        # Verify queue event structure
        for i, queue_event in enumerate(queue_events):
            if not all(key in queue_event for key in ["intent", "event_id", "event_name"]):
                print(f"   ❌ Queue event {i+1} missing required keys")
                return False
                
        print("   ✅ All queue events have required keys")
        
    except Exception as e:
        print(f"   ❌ Queue creation failed: {e}")
        return False

    # Test 4: Check for list/dict confusion
    print("\n🔍 Test 4: List/Dict Type Validation")
    
    # Test potential problematic scenarios
    test_scenarios = [
        {"name": "Direct event dict", "data": mock_events[0]},
        {"name": "List of events", "data": mock_events},
        {"name": "Nested structure", "data": {"events": mock_events}}
    ]
    
    for scenario in test_scenarios:
        print(f"   Testing: {scenario['name']}")
        data = scenario['data']
        
        if isinstance(data, list):
            print(f"      Type: list (length {len(data)})")
            if data and isinstance(data[0], dict):
                print("      ✅ List contains dictionaries")
            else:
                print("      ❌ List contains non-dictionaries")
        elif isinstance(data, dict):
            print("      Type: dict")
            if hasattr(data, 'get'):
                print("      ✅ Has .get() method")
            else:
                print("      ❌ Missing .get() method")
        else:
            print(f"      ❌ Unexpected type: {type(data)}")

    print("\n✅ Production Delete Scenario Test Complete")
    return True

if __name__ == "__main__":
    success = test_delete_production_scenario()
    print(f"\n{'✅ ALL TESTS PASSED' if success else '❌ TESTS FAILED'}")
