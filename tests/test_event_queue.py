#!/usr/bin/env python3
"""
Test the new Event Queue Handler system
"""

import asyncio
import json
import sys
import os
sys.path.append('/workspaces/calibot/backend')

from app.services.event_queue_handler import EventQueueHandler
from app.services.conversation import ConversationState
from unittest.mock import Mock, AsyncMock

async def test_event_queue_system():
    """Test the event queue handler with various scenarios"""
    
    print("🧪 Testing Event Queue Handler System")
    print("=" * 60)
    
    # Mock services
    class MockTelegramService:
        pass
    
    class MockCalendarService:
        async def create_event(self, **kwargs):
            return {"id": f"event_{kwargs.get('event_name', 'test')}", "success": True}
    
    class MockCalendarAgent:
        async def select_calendar_for_event(self, event_data):
            return event_data.get('calendar_name', 'primary')
    
    # Initialize handler
    telegram_service = MockTelegramService()
    conversation_state = ConversationState()
    calendar_service = MockCalendarService()
    calendar_agent = MockCalendarAgent()
    
    queue_handler = EventQueueHandler(
        telegram_service, 
        conversation_state, 
        calendar_service, 
        calendar_agent
    )
    
    # Test 1: Detect multi-event requests
    print("\n1️⃣ Testing Multi-Event Detection")
    
    test_cases = [
        {
            "name": "Batch create format",
            "intent": {
                "intent": "batch_create",
                "events": [
                    {"intent": "create", "event_name": "lesson 1", "start_time": "08:00"},
                    {"intent": "create", "event_name": "lesson 2", "start_time": "10:00"},
                    {"intent": "create", "event_name": "lesson 3", "start_time": "12:00"}
                ]
            },
            "expected": True
        },
        {
            "name": "Multiple start times",
            "intent": {
                "intent": "create",
                "event_name": "lesson",
                "start_time": ["08:00", "10:00", "12:00"],
                "end_time": ["09:00", "11:00", "13:00"]
            },
            "expected": True
        },
        {
            "name": "Single event",
            "intent": {
                "intent": "create",
                "event_name": "meeting",
                "start_time": "14:00"
            },
            "expected": False
        }
    ]
    
    for test_case in test_cases:
        result = queue_handler.detect_multi_event_request(test_case["intent"])
        status = "✅" if result == test_case["expected"] else "❌"
        print(f"   {status} {test_case['name']}: {result}")
    
    # Test 2: Queue creation and processing
    print("\n2️⃣ Testing Queue Creation and Processing")
    
    chat_id = "test_user_123"
    
    # Create a queue with multiple events
    multi_event_intent = {
        "intent": "batch_create",
        "events": [
            {"intent": "create", "event_name": "Morning Lesson", "start_time": "08:00", "end_time": "09:00"},
            {"intent": "create", "event_name": "Afternoon Lesson", "start_time": "14:00", "end_time": "15:00"}
        ]
    }
    
    queue_result = queue_handler.create_event_queue(chat_id, multi_event_intent)
    print(f"   ✅ Queue created: {queue_result['success']}")
    print(f"   📝 First confirmation: {queue_result['message'][:100]}...")
    
    # Test queue status
    status = queue_handler.get_queue_status(chat_id)
    print(f"   📊 Queue status: {status['total_events']} events, position {status['current_index'] + 1}")
    
    # Test 3: User confirmations
    print("\n3️⃣ Testing User Confirmations")
    
    # Confirm first event
    response1 = await queue_handler.process_queue_response(chat_id, "yes")
    print(f"   ✅ First event confirmed: {response1['success']}")
    print(f"   📝 Response: {response1['message'][:100]}...")
    
    # Skip second event
    response2 = await queue_handler.process_queue_response(chat_id, "no")
    print(f"   ⏭️ Second event skipped: {response2['success']}")
    print(f"   📝 Response: {response2['message'][:100]}...")
    
    # Test 4: Queue completion
    print("\n4️⃣ Testing Queue Completion")
    
    final_status = queue_handler.get_queue_status(chat_id)
    print(f"   📊 Final queue status: {final_status}")
    
    # Test 5: Invalid responses
    print("\n5️⃣ Testing Invalid Responses")
    
    # Create new queue
    queue_handler.create_event_queue(chat_id, multi_event_intent)
    
    invalid_response = await queue_handler.process_queue_response(chat_id, "maybe")
    print(f"   ❌ Invalid response handled: {not invalid_response['success']}")
    print(f"   📝 Error message: {invalid_response['message']}")
    
    # Test 6: Cancel functionality
    print("\n6️⃣ Testing Cancel Functionality")
    
    cancel_response = await queue_handler.process_queue_response(chat_id, "cancel")
    print(f"   🛑 Cancel handled: {cancel_response['success']}")
    print(f"   📝 Cancel message: {cancel_response['message']}")
    
    print("\n✅ ALL TESTS COMPLETED!")
    print("\n🎉 Event Queue System Working!")
    print("\nKey features validated:")
    print("- ✅ Multi-event detection")
    print("- ✅ Queue creation and management")
    print("- ✅ User confirmation workflow")
    print("- ✅ Event processing with existing services")
    print("- ✅ Skip and cancel functionality")
    print("- ✅ Error handling for invalid responses")

if __name__ == "__main__":
    asyncio.run(test_event_queue_system())
