#!/usr/bin/env python3
"""
Test script to verify update operation fixes and enhanced messaging
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/workspaces/calibot/backend')

from app.api.routes import format_event_for_user

def test_enhanced_event_formatting():
    """Test the enhanced event formatting with hyperlinks"""
    print("=== Testing Enhanced Event Formatting ===")
    
    # Test event with link
    event_data = {
        'event_name': 'Team Meeting',
        'date': '2025-08-09',
        'start_time': '2025-08-09T14:30:00Z',
        'end_time': '2025-08-09T15:30:00Z',
        'calendar_name': 'tonyas calendar'
    }
    
    calendar_result = {
        'event_link': 'https://calendar.google.com/event/test123'
    }
    
    formatted_event = format_event_for_user(event_data, calendar_result)
    print(f"Formatted event with hyperlink: {formatted_event}")
    
    # Validate hyperlink format
    assert "[Team Meeting]" in formatted_event, "Should contain hyperlink format"
    assert "https://calendar.google.com/event/test123" in formatted_event, "Should contain event link"
    assert "Saturday, August 09, 2025" in formatted_event, "Should have correct date"
    assert "14:30 - 15:30" in formatted_event, "Should have correct time format"
    
    print("✅ Enhanced event formatting working correctly!")
    
    # Test event without link
    formatted_no_link = format_event_for_user(event_data, None)
    print(f"Formatted event without link: {formatted_no_link}")
    
    assert "Team Meeting" in formatted_no_link, "Should contain plain title"
    assert "[" not in formatted_no_link, "Should not contain hyperlink brackets"
    
    print("✅ Event formatting without links working correctly!")
    return True

def test_batch_message_format():
    """Test that batch messages use hyperlinks consistently"""
    print("\n=== Testing Batch Message Format ===")
    
    # Simulate batch creation message
    events = [
        {
            'event_name': 'lesson',
            'date': '2025-08-09',
            'start_time': '2025-08-09T08:00:00Z',
            'end_time': '2025-08-09T09:00:00Z',
            'calendar_name': 'tonyas calendar'
        },
        {
            'event_name': 'lesson',
            'date': '2025-08-09', 
            'start_time': '2025-08-09T10:00:00Z',
            'end_time': '2025-08-09T11:00:00Z',
            'calendar_name': 'tonyas calendar'
        }
    ]
    
    calendar_results = [
        {'event_link': 'https://www.google.com/calendar/event?eid=event_1'},
        {'event_link': 'https://www.google.com/calendar/event?eid=event_2'}
    ]
    
    # Format events
    success_events = []
    for i, event in enumerate(events):
        formatted_event = format_event_for_user(event, calendar_results[i], "created")
        success_events.append(formatted_event)
    
    # Build message like routes.py does
    message = f"Successfully created {len(events)} events:\\n\\n" + "\\n".join(success_events)
    
    print(f"Batch message with hyperlinks:\\n{message}")
    
    # Validate improvements
    assert "[lesson]" in message, "Should contain hyperlinked event titles"
    assert "Saturday, August 09, 2025" in message, "Should include proper date formatting"
    assert "https://www.google.com/calendar/event" in message, "Should include event links"
    assert "tonyas calendar" in message, "Should have calendar name"
    
    print("✅ Batch messaging with hyperlinks working correctly!")
    return True

async def main():
    """Run all enhanced formatting tests"""
    print("Starting Enhanced Formatting Test Suite")
    print("=" * 60)
    
    try:
        test_enhanced_event_formatting()
        test_batch_message_format()
        
        print("\\n" + "=" * 60)
        print("🎉 ALL ENHANCED FORMATTING TESTS PASSED!")
        print("✅ Hyperlinked event titles implemented")
        print("✅ Consistent date formatting")
        print("✅ Professional messaging maintained")
        print("✅ Space-saving hyperlinks working")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False
        
    return True

if __name__ == "__main__":
    asyncio.run(main())
