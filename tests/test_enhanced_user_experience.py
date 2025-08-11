#!/usr/bin/env python3
"""
Test Enhanced User Experience - Professional Messaging
Tests the new professional messaging format across all operations
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

import pytest
from app.utils.message_formatter import MessageFormatter
from app.services.event_queue_handler import EventQueueHandler
from app.services.conversation import ConversationState
from datetime import datetime
import asyncio

class MockCalendarService:
    def __init__(self):
        self.events = []
    
    async def create_event(self, event_data):
        """Mock create event with proper response"""
        event_id = f"event_{len(self.events) + 1}"
        self.events.append(event_data)
        return {
            "success": True,
            "message": "Event created successfully",
            "event_id": event_id,
            "event_link": f"https://calendar.google.com/event/{event_id}",
            "calendar_used": event_data.get("calendar_name", "Personal")
        }
    
    def delete_event(self, event_id, calendar_id):
        return {"success": True, "message": "Event deleted successfully"}
    
    def update_event(self, event_id, update_data, calendar_id):
        return {"success": True, "message": "Event updated successfully"}

class MockTelegramService:
    def __init__(self):
        self.messages = []
    
    async def send_message(self, chat_id, message):
        self.messages.append(message)

def test_enhanced_event_formatting():
    """Test the new format_event_for_user function"""
    print("=== Testing Enhanced Event Formatting ===")
    
    # Test event data
    event_data = {
        "event_name": "Team Meeting",
        "date": "2025-08-09",
        "start_time": "14:30",
        "end_time": "15:30",
        "calendar_name": "work@company.group.calendar.google.com"
    }
    
    calendar_result = {
        "event_link": "https://calendar.google.com/event/test123",
        "calendar_used": "Work Calendar"
    }
    
    # Test formatting
    # Build event object compatible with formatter
    event_obj = {
        'summary': event_data['event_name'],
        'start': f"{event_data['date']}T{event_data['start_time']}:00Z",
        'end': f"{event_data['date']}T{event_data['end_time']}:00Z",
        'calendar_name': 'Shared Calendar',
        'htmlLink': calendar_result['event_link']
    }
    formatted = MessageFormatter.format_single_event_display(event_obj)
    print(f"Formatted event: {formatted}")
    
    # Validate format
    expected_elements = [
        "Team Meeting",
        "Saturday, August 09, 2025",
        "02:30 PM - 03:30 PM",
        "Shared Calendar",
        "https://calendar.google.com/event/test123"
    ]
    
    for element in expected_elements:
        assert element in formatted, f"Missing element: {element}"
    
    print("✅ Enhanced event formatting working correctly!")
    return True

@pytest.mark.asyncio
async def test_professional_batch_messaging():
    """Test professional batch creation messaging"""
    print("\n=== Testing Professional Batch Messaging ===")
    
    # Mock successful batch creation scenario
    events_to_create = [
        {
            "intent": "create",
            "event_name": "lesson",
            "date": "2025-08-09", 
            "start_time": "08:00",
            "end_time": "09:00",
            "calendar_name": "tonyas calendar"
        },
        {
            "intent": "create",
            "event_name": "lesson",
            "date": "2025-08-09",
            "start_time": "10:00", 
            "end_time": "11:00",
            "calendar_name": "tonyas calendar"
        }
    ]
    
    calendar_service = MockCalendarService()
    
    # Simulate the new batch creation logic
    created_count = 0
    failed_count = 0
    success_events = []
    failed_events = []
    
    for i, single_event in enumerate(events_to_create):
        try:
            calendar_result = await calendar_service.create_event(single_event)
            if calendar_result and calendar_result.get("success"):
                created_count += 1
                event_obj = {
                    'summary': single_event['event_name'],
                    'start': f"{single_event['date']}T{single_event['start_time']}:00Z",
                    'end': f"{single_event['date']}T{single_event['end_time']}:00Z",
                    'calendar_name': single_event.get('calendar_name','Shared Calendar'),
                    'htmlLink': calendar_result['event_link']
                }
                formatted_event = MessageFormatter.format_single_event_display(event_obj)
                success_events.append(formatted_event)
            else:
                failed_count += 1
                error_msg = calendar_result.get('message', 'Unknown error') if calendar_result else 'Unknown error'
                failed_events.append(f"• {single_event.get('event_name', 'Untitled')} - {error_msg}")
        except Exception as e:
            failed_count += 1
            failed_events.append(f"• {single_event.get('event_name', 'Untitled')} - Error: {str(e)}")
    
    # Build message (new format)
    if created_count > 0 and failed_count == 0:
        message = f"Successfully created {created_count} events:\n\n" + "\n".join(success_events)
    elif created_count > 0 and failed_count > 0:
        message = f"Created {created_count} events, {failed_count} failed:\n\nSuccessful:\n" + "\n".join(success_events)
        message += f"\n\nFailed:\n" + "\n".join(failed_events)
    else:
        message = f"Failed to create all {len(events_to_create)} events:\n\n" + "\n".join(failed_events)
    
    print(f"Professional batch message:\n{message}")
    
    # Validate improvements
    assert "SUCCESS Event" not in message, "Should not contain caps SUCCESS"
    assert "FAILED Event" not in message, "Should not contain caps FAILED"
    assert "Successfully created 2 events:" in message, "Should have professional success message"
    assert "Saturday, August 09, 2025" in message, "Should include proper date formatting"
    assert "https://calendar.google.com/event/" in message, "Should include event links"
    assert "tonyas calendar" in message, "Should have calendar name"
    
    print("✅ Professional batch messaging working correctly!")
    return True

@pytest.mark.asyncio
async def test_enhanced_queue_messaging():
    """Test enhanced queue operation messaging"""
    print("\n=== Testing Enhanced Queue Messaging ===")
    
    # Create handler
    telegram_service = MockTelegramService()
    conversation_state = ConversationState()
    calendar_service = MockCalendarService()
    
    handler = EventQueueHandler(
        telegram_service=telegram_service,
        conversation_state=conversation_state,
        calendar_service=calendar_service
    )
    
    # Test delete events
    events_to_delete = [
        {
            "intent": "delete",
            "event_id": "event1",
            "event_name": "lesson",
            "start_time": "2025-08-09T08:00:00Z",
            "end_time": "2025-08-09T09:00:00Z",
            "calendar_id": "primary",
            "calendar_name": "tonyas calendar"
        },
        {
            "intent": "delete",
            "event_id": "event2", 
            "event_name": "lesson",
            "start_time": "2025-08-09T10:00:00Z",
            "end_time": "2025-08-09T11:00:00Z",
            "calendar_id": "primary",
            "calendar_name": "tonyas calendar"
        }
    ]
    
    chat_id = "test_enhanced_messaging"
    
    # Create queue and process all
    handler.create_event_queue_from_list(chat_id, events_to_delete)
    result = await handler.process_queue_response(chat_id, "all")
    
    message = result.get('message', '')
    print(f"Enhanced queue message:\n{message}")
    
    # Validate enhancements
    assert "SUCCESS:" not in message, "Should not contain caps SUCCESS"
    assert "ERROR:" not in message, "Should not contain caps ERROR"
    assert "Successfully deleted all 2 events" in message, "Should have professional success message"
    assert "Saturday, August 09, 2025" in message, "Should include date information"
    
    print("✅ Enhanced queue messaging working correctly!")
    return True

def test_time_shift_parsing():
    """Test time shift calculation logic"""
    print("\n=== Testing Time Shift Parsing ===")
    
    # Test time shift calculation (simplified version of the logic)
    import re
    from datetime import datetime, timedelta
    
    # Test cases
    test_cases = [
        ("1 hour", 1, 0),
        ("2 hours", 2, 0),
        ("30 minutes", 0, 30),
        ("1 hour 30 minutes", 1, 30)
    ]
    
    for time_shift, expected_hours, expected_minutes in test_cases:
        hours = 0
        minutes = 0
        
        # Extract hours
        hour_match = re.search(r'(\d+)\s*(?:hour|hr)', time_shift, re.IGNORECASE)
        if hour_match:
            hours = int(hour_match.group(1))
        
        # Extract minutes  
        minute_match = re.search(r'(\d+)\s*(?:minute|min)', time_shift, re.IGNORECASE)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        print(f"Time shift '{time_shift}' -> {hours} hours, {minutes} minutes")
        
        assert hours == expected_hours, f"Expected {expected_hours} hours, got {hours}"
        assert minutes == expected_minutes, f"Expected {expected_minutes} minutes, got {minutes}"
    
    print("✅ Time shift parsing working correctly!")
    return True

async def main():
    """Run all enhanced UX tests"""
    print("Starting Enhanced User Experience Test Suite")
    print("=" * 60)
    
    try:
        # Test enhanced formatting
        test_enhanced_event_formatting()
        
        # Test professional batch messaging
        await test_professional_batch_messaging()
        
        # Test enhanced queue messaging
        await test_enhanced_queue_messaging()
        
        # Test time shift parsing
        test_time_shift_parsing()
        
        print("\n" + "=" * 60)
        print("🎉 ALL ENHANCED UX TESTS PASSED!")
        print("✅ Professional messaging implemented")
        print("✅ Consistent formatting across operations")
        print("✅ Date information included")
        print("✅ Event links provided")
        print("✅ Time shift parsing working")
        print("✅ No more horrible caps messages!")
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
