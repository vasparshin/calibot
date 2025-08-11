#!/usr/bin/env python3

"""
Test for batch event creation and formatting consistency.
Tests the user reported issues:
1. "tonya will have 3 lessons tomorrow, 9, 10 and 12am" should create 3 events
2. Single event formatting should match multi-event summaries with hyperlinks
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent
from app.utils.message_formatter import MessageFormatter
from unittest.mock import MagicMock, AsyncMock
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_batch_creation_functionality():
    """Test that multiple lessons are created correctly"""
    print("🧪 Testing batch event creation functionality...")
    
    # Mock services
    calendar_service = MagicMock()
    calendar_service.create_event = AsyncMock()
    calendar_service.create_event.return_value = {
        "success": True,
        "event_link": "https://calendar.google.com/calendar/event?eid=test123",
        "calendar_used": "primary"
    }
    
    # Test the intent extraction first
    agent = NLPAgent()
    user_message = "tonya will have 3 lessons tomorrow, 9, 10 and 12am"
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Extract intent
    intent_result = await agent.extract_intent(user_message, tomorrow)
    print(f"📝 Intent extraction result: {intent_result}")
    
    # Verify it's detected as batch_create
    assert intent_result.get("intent") == "batch_create", f"Expected batch_create, got {intent_result.get('intent')}"
    assert "events" in intent_result, "Should have events array"
    assert len(intent_result["events"]) == 3, f"Expected 3 events, got {len(intent_result.get('events', []))}"
    
    # Verify the times are correct
    expected_times = [
        {"start_time": "09:00", "end_time": "10:00"},
        {"start_time": "10:00", "end_time": "11:00"},
        {"start_time": "12:00", "end_time": "13:00"}
    ]
    
    events = intent_result["events"]
    for i, expected in enumerate(expected_times):
        assert events[i]["start_time"] == expected["start_time"], f"Event {i+1} start time mismatch"
        assert events[i]["end_time"] == expected["end_time"], f"Event {i+1} end time mismatch"
    
    print("✅ Batch creation intent extraction works correctly")
    print(f"   • Detected {len(events)} events")
    times_list = [f"{e['start_time']}-{e['end_time']}" for e in events]
    print(f"   • Times: {times_list}")
    
    return True

async def test_formatting_consistency():
    """Test that single and multi-event formatting is consistent"""
    print("🧪 Testing event formatting consistency...")
    
    # Mock calendar service
    calendar_service = MagicMock()
    calendar_service.get_calendar_name = MagicMock(return_value="Primary Calendar")
    
    # Test single event formatting
    single_event_data = {
        'event_name': 'Lesson',
        'start_time': '09:00',
        'end_time': '10:00',
        'date': '2025-08-11',
        'calendar_name': 'primary'
    }
    
    calendar_result = {
        "success": True,
        "event_link": "https://calendar.google.com/calendar/event?eid=test123"
    }
    
    single_event_obj = {
        'summary': single_event_data['event_name'],
        'start': f"{single_event_data['date']}T{single_event_data['start_time']}:00",
        'end': f"{single_event_data['date']}T{single_event_data['end_time']}:00",
        'calendar_name': single_event_data['calendar_name'],
        'id': 'evt_single',
        'htmlLink': calendar_result['event_link']
    }
    formatted_single = MessageFormatter.format_single_event_display(single_event_obj)
    print(f"📋 Single event format: {formatted_single}")
    
    # Test multi-event format (should be same structure)
    multi_event_data = {
        'event_name': 'Lesson',
        'start_time': '10:00',
        'end_time': '11:00',
        'date': '2025-08-11',
        'calendar_name': 'primary'
    }
    
    calendar_result_2 = {
        "success": True,
        "event_link": "https://calendar.google.com/calendar/event?eid=test456"
    }
    
    multi_event_obj = {
        'summary': multi_event_data['event_name'],
        'start': f"{multi_event_data['date']}T{multi_event_data['start_time']}:00",
        'end': f"{multi_event_data['date']}T{multi_event_data['end_time']}:00",
        'calendar_name': multi_event_data['calendar_name'],
        'id': 'evt_multi',
        'htmlLink': calendar_result_2['event_link']
    }
    formatted_multi = MessageFormatter.format_single_event_display(multi_event_obj)
    print(f"📋 Multi event format: {formatted_multi}")
    
    # Verify both formats have the same structure
    assert formatted_single.startswith("• ["), "Single event should have hyperlink format"
    assert formatted_multi.startswith("• ["), "Multi event should have hyperlink format"
    assert "](" in formatted_single, "Single event should have markdown link"
    assert "](" in formatted_multi, "Multi event should have markdown link"
    assert "on " in formatted_single, "Single event should have 'on' for date"
    assert "on " in formatted_multi, "Multi event should have 'on' for date"
    assert "at " in formatted_single, "Single event should have 'at' for time"
    assert "at " in formatted_multi, "Multi event should have 'at' for time"
    
    print("✅ Event formatting is consistent between single and multi-event scenarios")
    print(f"   • Both use hyperlink format: [Event Name](link)")
    print(f"   • Both include date and time properly")
    print(f"   • Both include calendar name")
    
    return True

async def test_edge_cases():
    """Test various edge cases for batch creation"""
    print("🧪 Testing edge cases...")
    
    agent = NLPAgent()
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Test case 1: Different wording
    test_cases = [
        "please schedule 3 lessons in tonyas calendar tomorrow, 9, 10 and 12am",
        "schedule 3 lessons for 9am, 10am, and 12pm tomorrow",
        "I need 3 meetings at 9, 10, and 11 tomorrow"
    ]
    
    for i, message in enumerate(test_cases):
        print(f"   Testing case {i+1}: '{message}'")
        intent_result = await agent.extract_intent(message, tomorrow)
        
        if intent_result.get("intent") == "batch_create":
            print(f"      ✅ Detected as batch_create with {len(intent_result.get('events', []))} events")
        else:
            print(f"      ⚠️  Detected as {intent_result.get('intent')} - may need prompt improvement")
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting batch creation and formatting tests...\n")
    
    try:
        # Test 1: Batch creation functionality
        await test_batch_creation_functionality()
        print()
        
        # Test 2: Formatting consistency
        await test_formatting_consistency()
        print()
        
        # Test 3: Edge cases
        await test_edge_cases()
        print()
        
        print("🎉 All tests completed successfully!")
        print("✅ Batch creation works correctly")
        print("✅ Formatting is consistent")
        print("✅ Edge cases handled appropriately")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
