#!/usr/bin/env python3
"""
Test Enhanced Batch Operations - User Experience Improvements
Tests the new batch operation interface with improved formatting and options
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from app.services.event_queue_handler import EventQueueHandler
from app.services.conversation import ConversationState
from datetime import datetime, timezone
import asyncio

class MockCalendarService:
    def delete_event(self, event_id, calendar_id):
        return {"success": True, "message": "Event deleted"}

class MockTelegramService:
    pass

def test_enhanced_batch_interface():
    """Test the enhanced batch operation interface"""
    print("=== Testing Enhanced Batch Operations Interface ===")
    
    # Create handler
    telegram_service = MockTelegramService()
    conversation_state = ConversationState()
    calendar_service = MockCalendarService()
    
    handler = EventQueueHandler(
        telegram_service=telegram_service,
        conversation_state=conversation_state,
        calendar_service=calendar_service
    )
    
    # Test sample events with realistic data
    test_events = [
        {
            "intent": "delete",
            "event_name": "Morning Workout",
            "start_time": "2025-08-06T08:00:00Z",
            "end_time": "2025-08-06T09:00:00Z",
            "calendar_name": "zoutna@gmail.com",
            "event_id": "event1",
            "calendar_id": "primary"
        },
        {
            "intent": "delete", 
            "event_name": "Team Meeting",
            "start_time": "2025-08-06T14:30:00Z",
            "end_time": "2025-08-06T15:30:00Z",
            "calendar_name": "work@company.group.calendar.google.com",
            "event_id": "event2",
            "calendar_id": "work_cal"
        },
        {
            "intent": "delete",
            "event_name": "Dinner with Friends", 
            "start_time": "2025-08-06T19:00:00Z",
            "end_time": "2025-08-06T21:00:00Z",
            "calendar_name": "Personal Calendar",
            "event_id": "event3",
            "calendar_id": "personal"
        }
    ]
    
    chat_id = "test_user_123"
    
    # Test 1: Initial batch message with enhanced formatting
    print("\n1. Testing Enhanced Initial Batch Message:")
    result = handler.create_event_queue_from_list(chat_id, test_events)
    
    print(f"Success: {result.get('success')}")
    print(f"Message:\n{result.get('message')}")
    print(f"Requires user action: {result.get('requires_user_action')}")
    print(f"Batch options: {result.get('batch_options')}")
    
    # Validate enhanced formatting features
    message = result.get('message', '')
    
    # Check for proper event formatting
    assert "Morning Workout - 08:00 AM (Personal)" in message, "Event formatting incorrect"
    assert "Team Meeting - 02:30 PM (Shared Calendar)" in message, "Calendar name formatting incorrect"
    assert "Dinner with Friends - 07:00 PM (Personal Calendar)" in message, "Time formatting incorrect"
    
    # Check for batch options
    assert "'one' or '1' - Review and delete one by one" in message, "Missing one-by-one option"
    assert "'all' or 'yes' - Delete all events now" in message, "Missing delete all option"
    assert "'cancel' - Cancel operation" in message, "Missing cancel option"
    
    print("✅ Enhanced formatting validation passed!")
    
    return True

async def test_batch_response_handling():
    """Test batch response handling"""
    print("\n=== Testing Batch Response Handling ===")
    
    # Create handler
    telegram_service = MockTelegramService()
    conversation_state = ConversationState()
    calendar_service = MockCalendarService()
    
    handler = EventQueueHandler(
        telegram_service=telegram_service,
        conversation_state=conversation_state,
        calendar_service=calendar_service
    )
    
    # Create test events
    test_events = [
        {
            "intent": "delete",
            "event_name": "Test Event 1",
            "start_time": "2025-08-06T10:00:00Z",
            "calendar_name": "zoutna@gmail.com",
            "event_id": "event1"
        },
        {
            "intent": "delete",
            "event_name": "Test Event 2", 
            "start_time": "2025-08-06T11:00:00Z",
            "calendar_name": "Personal Calendar",
            "event_id": "event2"
        }
    ]
    
    chat_id = "test_batch_123"
    
    # Initialize queue
    handler.create_event_queue_from_list(chat_id, test_events)
    
    # Test 2: Process "all" response
    print("\n2. Testing 'all' batch response:")
    result = await handler.process_queue_response(chat_id, "all")
    
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    print(f"Queue complete: {result.get('queue_complete')}")
    
    # Validate all events processed
    assert result.get('success'), "Batch processing failed"
    assert result.get('queue_complete'), "Queue should be complete"
    assert "All 2 events deleted successfully" in result.get('message', ''), "Success message incorrect"
    
    print("✅ Batch 'all' processing validation passed!")
    
    # Test 3: Test "one" response workflow
    print("\n3. Testing 'one by one' response:")
    
    # Recreate queue for new test
    handler.create_event_queue_from_list(chat_id, test_events)
    
    # Start one-by-one workflow
    result = await handler.process_queue_response(chat_id, "one")
    
    print(f"Success: {result.get('success')}")
    print(f"Message:\n{result.get('message')}")
    print(f"Requires user action: {result.get('requires_user_action')}")
    
    # Validate one-by-one started
    assert result.get('success'), "One-by-one workflow failed to start"
    assert result.get('requires_user_action'), "Should require user action"
    assert "DELETE Event 1 of 2" in result.get('message', ''), "Event confirmation format incorrect"
    
    print("✅ One-by-one workflow validation passed!")
    
    # Test 4: Test cancel response
    print("\n4. Testing cancel response:")
    
    # Recreate queue for cancel test
    handler.create_event_queue_from_list(chat_id, test_events)
    
    # Cancel operation
    result = await handler.process_queue_response(chat_id, "cancel")
    
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    print(f"Queue complete: {result.get('queue_complete')}")
    
    # Validate cancellation
    assert result.get('success'), "Cancel operation failed"
    assert result.get('queue_complete'), "Queue should be complete after cancel"
    assert "Operation cancelled" in result.get('message', ''), "Cancel message incorrect"
    
    print("✅ Cancel operation validation passed!")
    
    return True

def test_datetime_formatting():
    """Test enhanced datetime formatting"""
    print("\n=== Testing Enhanced DateTime Formatting ===")
    
    # Create handler
    handler = EventQueueHandler(None, None)
    
    # Test ISO datetime formatting
    test_cases = [
        ("2025-08-06T08:00:00Z", "2025-08-06T09:00:00Z", "Wednesday, August 06, 2025", "08:00 AM - 09:00 AM"),
        ("2025-12-25T14:30:00Z", "", "Thursday, December 25, 2025", "02:30 PM"),
        ("2025-01-01T00:00:00Z", "2025-01-01T23:59:00Z", "Wednesday, January 01, 2025", "12:00 AM - 11:59 PM")
    ]
    
    for start_time, end_time, expected_date, expected_time in test_cases:
        date_str, time_str = handler._format_datetime_nice(start_time, end_time)
        
        print(f"Input: {start_time} -> {end_time}")
        print(f"Output: {date_str} | {time_str}")
        print(f"Expected: {expected_date} | {expected_time}")
        
        assert date_str == expected_date, f"Date formatting failed for {start_time}"
        assert time_str == expected_time, f"Time formatting failed for {start_time}"
        print("✅ Formatting correct!")
        print()
    
    return True

def test_calendar_name_formatting():
    """Test calendar name formatting"""
    print("\n=== Testing Calendar Name Formatting ===")
    
    # Create handler
    handler = EventQueueHandler(None, None)
    
    # Test cases for calendar name formatting
    test_cases = [
        ("zoutna@gmail.com", "Personal"),
        ("work@company.group.calendar.google.com", "Shared Calendar"),
        ("john.doe@company.com", "John.Doe"),
        ("Personal Calendar", "Personal Calendar"),
        ("", "Personal Calendar"),
        ("Default calendar", "Personal Calendar")
    ]
    
    for input_name, expected_output in test_cases:
        result = handler._format_calendar_name(input_name)
        
        print(f"Input: '{input_name}' -> Output: '{result}' (Expected: '{expected_output}')")
        
        assert result == expected_output, f"Calendar name formatting failed for '{input_name}'"
        print("✅ Calendar name formatting correct!")
        print()
    
    return True

async def main():
    """Run all enhanced batch operation tests"""
    print("Starting Enhanced Batch Operations Validation")
    print("=" * 60)
    
    try:
        # Test enhanced batch interface
        test_enhanced_batch_interface()
        
        # Test batch response handling
        await test_batch_response_handling()
        
        # Test datetime formatting
        test_datetime_formatting()
        
        # Test calendar name formatting
        test_calendar_name_formatting()
        
        print("\n" + "=" * 60)
        print("🎉 ALL ENHANCED BATCH OPERATION TESTS PASSED!")
        print("✅ User experience improvements validated")
        print("✅ Datetime formatting working correctly")
        print("✅ Calendar name formatting improved")
        print("✅ Batch options interface working properly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
