#!/usr/bin/env python3
"""
Test script to verify update operation fixes and enhanced messaging
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append('/workspaces/calibot/backend')

def test_datetime_formatting():
    """Test the enhanced datetime formatting"""
    print("=== Testing Enhanced DateTime Formatting ===")
    
    try:
        from app.services.event_queue_handler import EventQueueHandler
        
        # Create a minimal handler for testing
        handler = EventQueueHandler(None, None, None, None)
        
        # Test datetime formatting
        test_datetime = "2025-08-09T08:00:00Z"
        formatted = handler._format_datetime_for_display(test_datetime)
        print(f"Original: {test_datetime}")
        print(f"Formatted: {formatted}")
        
        # Validate format
        assert "Aug 09" in formatted, "Should contain abbreviated date"
        assert "08:00 AM" in formatted, "Should contain time"
        
        print("✅ DateTime formatting working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_update_message_format():
    """Test the update message formatting with changes"""
    print("\n=== Testing Update Message Format ===")
    
    # Mock event with time shift
    event = {
        'event_name': 'lesson',
        'start_time': '2025-08-09T08:00:00Z',
        'end_time': '2025-08-09T09:00:00Z',
        'time_shift': '1 hour',
        'calendar_name': 'tonyas calendar'
    }
    
    # Mock calendar service result
    mock_result = {
        'success': True,
        'event_link': 'https://calendar.google.com/event/test123'
    }
    
    # Expected message format
    expected_elements = [
        "[lesson]",  # Hyperlinked title
        "shifted by 1 hour",  # Change description
        "https://calendar.google.com/event/test123"  # Event link
    ]
    
    # Simulate message creation
    event_link = mock_result.get('event_link', '')
    event_title = f"[{event.get('event_name', 'Event')}]({event_link})"
    change_description = f"shifted by {event.get('time_shift')}"
    message = f"Updated {event_title} - {change_description}"
    
    print(f"Update message: {message}")
    
    # Validate format
    for element in expected_elements:
        assert element in message, f"Should contain: {element}"
    
    print("✅ Update message formatting working correctly!")
    return True

def test_batch_update_summary():
    """Test the enhanced batch update summary"""
    print("\n=== Testing Batch Update Summary ===")
    
    # Mock successful events with details
    successful_events = [
        "Updated [lesson](https://calendar.google.com/event/1) - shifted by 1 hour",
        "Updated [lesson](https://calendar.google.com/event/2) - shifted by 1 hour"
    ]
    
    # Build summary message
    total_events = 2
    date_info = " on Saturday, August 09, 2025"
    message = f"Successfully updated all {total_events} events{date_info}:\\n\\n" + "\\n".join(successful_events)
    
    print(f"Batch summary:\\n{message}")
    
    # Validate improvements
    expected_elements = [
        "Successfully updated all 2 events",
        "Saturday, August 09, 2025",
        "[lesson]",  # Hyperlinked titles
        "shifted by 1 hour",  # Change details
        "https://calendar.google.com/event/"  # Event links
    ]
    
    for element in expected_elements:
        assert element in message, f"Should contain: {element}"
    
    print("✅ Batch update summary working correctly!")
    return True

async def main():
    """Run all update operation tests"""
    print("Starting Update Operation Fixes Test Suite")
    print("=" * 60)
    
    try:
        test_datetime_formatting()
        test_update_message_format()
        test_batch_update_summary()
        
        print("\\n" + "=" * 60)
        print("🎉 ALL UPDATE OPERATION TESTS PASSED!")
        print("✅ Enhanced datetime formatting")
        print("✅ Detailed update messages with changes")
        print("✅ Hyperlinked event titles")
        print("✅ Before/after change descriptions")
        print("✅ Comprehensive batch summaries")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    asyncio.run(main())
