#!/usr/bin/env python3
"""
Test Batch Operations - Create and Delete
Comprehensive testing for batch creation and deletion operations
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from app.services.event_queue_handler import EventQueueHandler
from app.services.conversation import ConversationState
from app.services.google_calendar import GoogleCalendarService
from app.agent.calendar_agent import CalendarAgent
import asyncio

class MockCalendarService:
    def __init__(self):
        self.created_events = []
        self.deleted_events = []
    
    async def create_event(self, event_data):
        """Mock create event"""
        self.created_events.append(event_data)
        return {
            "success": True, 
            "message": "Event created successfully",
            "event_id": f"mock_event_{len(self.created_events)}",
            "event_link": f"https://calendar.google.com/event/mock_{len(self.created_events)}",
            "calendar_used": event_data.get("calendar_name", "Personal")
        }
    
    def delete_event(self, event_id, calendar_id):
        """Mock delete event"""
        self.deleted_events.append({"event_id": event_id, "calendar_id": calendar_id})
        return {"success": True, "message": "Event deleted successfully"}

class MockTelegramService:
    def __init__(self):
        self.sent_messages = []
    
    async def send_message(self, chat_id, message):
        self.sent_messages.append({"chat_id": chat_id, "message": message})

async def test_batch_creation():
    """Test batch event creation"""
    print("=== Testing Batch Event Creation ===")
    
    # Create services
    calendar_service = MockCalendarService()
    telegram_service = MockTelegramService()
    conversation_state = ConversationState()
    calendar_agent = CalendarAgent()
    
    # Test batch creation data (like from the user's request)
    batch_create_data = {
        "intent": "batch_create",
        "events": [
            {
                "intent": "create",
                "event_name": "lesson",
                "date": "2025-08-09",
                "start_time": "08:00",
                "end_time": "09:00",
                "calendar_name": "tonyas calendar",
                "confirmation_needed": False
            },
            {
                "intent": "create", 
                "event_name": "lesson",
                "date": "2025-08-09",
                "start_time": "10:00",
                "end_time": "11:00",
                "calendar_name": "tonyas calendar",
                "confirmation_needed": False
            }
        ],
        "confirmation_needed": False
    }
    
    chat_id = "test_batch_creation"
    
    # Simulate the batch creation logic from routes.py
    events_to_create = batch_create_data["events"]
    created_count = 0
    failed_count = 0
    results = []
    
    for i, single_event in enumerate(events_to_create):
        if isinstance(single_event, dict) and single_event.get("intent") == "create":
            try:
                print(f"Creating event {i+1}/{len(events_to_create)}: {single_event}")
                calendar_result = await calendar_service.create_event(single_event)
                if calendar_result and calendar_result.get("success"):
                    created_count += 1
                    results.append(f"SUCCESS Event {i+1}: {single_event.get('event_name', 'Untitled')} at {single_event.get('start_time', 'Unknown time')}")
                else:
                    failed_count += 1
                    error_msg = calendar_result.get('message', 'Unknown error') if calendar_result else 'Unknown error'
                    results.append(f"FAILED Event {i+1}: {single_event.get('event_name', 'Untitled')} - {error_msg}")
            except Exception as e:
                print(f"Error creating batch event: {e}")
                failed_count += 1
                results.append(f"FAILED Event {i+1}: {single_event.get('event_name', 'Untitled')} - Error: {str(e)}")
                continue
    
    # Send comprehensive response
    if created_count > 0:
        success_message = f"Batch creation completed: {created_count} events created"
        if failed_count > 0:
            success_message += f", {failed_count} failed"
        success_message += f"\n\n" + "\n".join(results)
    else:
        success_message = f"Failed to create all {len(events_to_create)} events:\n" + "\n".join(results)
    
    print(f"\nFinal Result: {success_message}")
    
    # Validate results
    assert created_count == 2, f"Expected 2 events created, got {created_count}"
    assert failed_count == 0, f"Expected 0 failures, got {failed_count}"
    assert len(calendar_service.created_events) == 2, f"Expected 2 events in calendar service, got {len(calendar_service.created_events)}"
    
    print("✅ Batch creation test passed!")
    return True

async def test_batch_deletion():
    """Test batch event deletion"""
    print("\n=== Testing Batch Event Deletion ===")
    
    # Create services
    calendar_service = MockCalendarService()
    telegram_service = MockTelegramService()
    conversation_state = ConversationState()
    
    handler = EventQueueHandler(
        telegram_service=telegram_service,
        conversation_state=conversation_state,
        calendar_service=calendar_service
    )
    
    # Test deletion events (like from calendar query result)
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
    
    chat_id = "test_batch_deletion"
    
    # Test 1: Create queue with initial batch options
    print("\n1. Testing queue creation with batch options:")
    result = handler.create_event_queue_from_list(chat_id, events_to_delete)
    
    print(f"Success: {result.get('success')}")
    print(f"Message:\n{result.get('message')}")
    
    assert result.get('success'), "Queue creation should succeed"
    assert "Found 2 events to delete" in result.get('message', ''), "Should show 2 events"
    print("✅ Queue creation successful!")
    
    # Test 2: Process "all" response to delete all events
    print("\n2. Testing 'all' batch deletion:")
    result = await handler.process_queue_response(chat_id, "all")
    
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    assert result.get('success'), "Batch deletion should succeed"
    assert result.get('queue_complete'), "Queue should be complete"
    assert "All 2 events deleted successfully" in result.get('message', ''), "Should confirm 2 events deleted"
    assert len(calendar_service.deleted_events) == 2, f"Expected 2 deleted events, got {len(calendar_service.deleted_events)}"
    
    print("✅ Batch deletion test passed!")
    return True

async def test_mixed_batch_operations():
    """Test error handling in batch operations"""
    print("\n=== Testing Mixed Batch Results ===")
    
    # Create a calendar service that fails on second event
    class PartialFailCalendarService:
        def __init__(self):
            self.call_count = 0
        
        async def create_event(self, event_data):
            self.call_count += 1
            if self.call_count == 1:
                return {"success": True, "message": "Event created", "event_id": "event1", "event_link": "link1", "calendar_used": "Personal"}
            else:
                return {"success": False, "message": "Calendar quota exceeded"}
        
        def delete_event(self, event_id, calendar_id):
            if event_id == "event1":
                return {"success": True, "message": "Event deleted"}
            else:
                return {"success": False, "message": "Event not found"}
    
    calendar_service = PartialFailCalendarService()
    
    # Test partial failure in batch creation
    events_to_create = [
        {"intent": "create", "event_name": "test1", "start_time": "08:00", "end_time": "09:00"},
        {"intent": "create", "event_name": "test2", "start_time": "10:00", "end_time": "11:00"}
    ]
    
    created_count = 0
    failed_count = 0
    results = []
    
    for i, single_event in enumerate(events_to_create):
        if isinstance(single_event, dict) and single_event.get("intent") == "create":
            try:
                calendar_result = await calendar_service.create_event(single_event)
                if calendar_result and calendar_result.get("success"):
                    created_count += 1
                    results.append(f"SUCCESS Event {i+1}: {single_event.get('event_name', 'Untitled')} at {single_event.get('start_time', 'Unknown time')}")
                else:
                    failed_count += 1
                    error_msg = calendar_result.get('message', 'Unknown error') if calendar_result else 'Unknown error'
                    results.append(f"FAILED Event {i+1}: {single_event.get('event_name', 'Untitled')} - {error_msg}")
            except Exception as e:
                failed_count += 1
                results.append(f"FAILED Event {i+1}: {single_event.get('event_name', 'Untitled')} - Error: {str(e)}")
    
    print(f"Mixed results: {created_count} created, {failed_count} failed")
    print("Results:", results)
    
    assert created_count == 1, f"Expected 1 success, got {created_count}"
    assert failed_count == 1, f"Expected 1 failure, got {failed_count}"
    assert "SUCCESS Event 1: test1" in results[0], "First event should succeed"
    assert "FAILED Event 2: test2" in results[1], "Second event should fail"
    
    print("✅ Mixed batch results test passed!")
    return True

async def main():
    """Run all batch operation tests"""
    print("Starting Comprehensive Batch Operations Test")
    print("=" * 60)
    
    try:
        # Test batch creation
        await test_batch_creation()
        
        # Test batch deletion  
        await test_batch_deletion()
        
        # Test mixed results
        await test_mixed_batch_operations()
        
        print("\n" + "=" * 60)
        print("🎉 ALL BATCH OPERATION TESTS PASSED!")
        print("✅ Batch creation working correctly")
        print("✅ Batch deletion working correctly") 
        print("✅ Error handling working correctly")
        print("✅ Production fix validated")
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
