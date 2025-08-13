#!/usr/bin/env python3
"""
Test script to debug the event editing issue.
Identifies specific problems with update intent processing.
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import required modules
from app.agent.nlp_agent import NLPAgent
from app.services.multi_event_operations import MultiEventOperationHandler

def setup_mock_services():
    """Setup mock services for testing"""
    # Mock calendar service
    calendar_service = MagicMock()
    calendar_service.get_events = AsyncMock(return_value=[
        {
            "id": "test_event_123",
            "summary": "Test Lesson",
            "start": "2025-08-13T10:00:00",
            "end": "2025-08-13T11:00:00",
            "calendar_id": "primary",
            "calendar_name": "Main Calendar",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test123"
        }
    ])
    
    calendar_service.update_event = MagicMock(return_value={
        "success": True,
        "event_id": "test_event_123",
        "event_link": "https://calendar.google.com/calendar/event?eid=test123",
        "updated_event": {
            "summary": "Test Lesson",
            "start": "2025-08-13T15:00:00",
            "end": "2025-08-13T16:00:00",
            "calendar_name": "Main Calendar",
            "id": "test_event_123",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test123"
        }
    })
    
    # Mock other services
    telegram_service = MagicMock()
    conversation_state = MagicMock()
    
    return calendar_service, telegram_service, conversation_state

async def test_nlp_update_intent_extraction():
    """Test if NLP agent correctly extracts update intents"""
    print("=== Testing NLP Update Intent Extraction ===")
    
    nlp_agent = NLPAgent()
    
    # Test cases for different update scenarios
    test_cases = [
        "change the lesson to 3pm",
        "move the last lesson 1 hour later", 
        "update my lesson today to start at 7pm",
        "move lesson to 5pm"
    ]
    
    for i, message in enumerate(test_cases):
        print(f"\n{i+1}. Testing: '{message}'")
        try:
            # Mock conversation history
            conversation_history = []
            
            result = await nlp_agent.extract_intent_from_message(message, conversation_history)
            print(f"   Result: {json.dumps(result, indent=2)}")
            
            # Check if intent is correctly identified as update
            if result.get("intent") != "update":
                print(f"   ❌ ISSUE: Intent should be 'update' but got '{result.get('intent')}'")
            else:
                print(f"   ✅ Intent correctly identified as 'update'")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

async def test_multi_event_update_operation():
    """Test multi-event update operation handler"""
    print("\n=== Testing Multi-Event Update Operation ===")
    
    # Setup mocks
    calendar_service, telegram_service, conversation_state = setup_mock_services()
    
    # Create handler
    handler = MultiEventOperationHandler(
        calendar_service=calendar_service,
        telegram_service=telegram_service,
        conversation_state=conversation_state
    )
    
    # Test update operation
    chat_id = 12345
    event_data = {
        "intent": "update",
        "event_name": "lesson",
        "new_start_time": "15:00",
        "confirmation_needed": True
    }
    
    print(f"Testing update operation with data: {json.dumps(event_data, indent=2)}")
    
    try:
        result = await handler.handle_update_operation(chat_id, event_data)
        print(f"Update operation result: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Update operation handled successfully")
        else:
            print(f"❌ Update operation failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ ERROR in update operation: {e}")
        import traceback
        traceback.print_exc()

async def test_update_execution():
    """Test the actual update execution"""
    print("\n=== Testing Update Execution ===")
    
    # Setup mocks
    calendar_service, telegram_service, conversation_state = setup_mock_services()
    
    handler = MultiEventOperationHandler(
        calendar_service=calendar_service,
        telegram_service=telegram_service,
        conversation_state=conversation_state
    )
    
    # Create a pending operation
    operation = {
        "type": "update_multiple",
        "chat_id": 12345,
        "events": [
            {
                "id": "test_event_123",
                "summary": "Test Lesson",
                "start": "2025-08-13T10:00:00",
                "end": "2025-08-13T11:00:00",
                "calendar_id": "primary",
                "date": "2025-08-13",
                "start_time": "10:00",
                "end_time": "11:00"
            }
        ],
        "original_request": {
            "intent": "update",
            "new_start_time": "15:00",
            "new_end_time": "16:00"
        }
    }
    
    print(f"Testing execution with operation: {json.dumps(operation, indent=2)}")
    
    try:
        result = await handler._execute_operation(operation)
        print(f"Execution result: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print("✅ Update execution successful")
        else:
            print(f"❌ Update execution failed: {result.get('message')}")
            
        # Check if calendar service was called correctly
        if calendar_service.update_event.called:
            call_args = calendar_service.update_event.call_args
            print(f"Calendar service called with: {call_args}")
        else:
            print("❌ Calendar service update_event was not called")
            
    except Exception as e:
        print(f"❌ ERROR in update execution: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests to identify the update issue"""
    print("🔍 Debugging Event Update Issue")
    print("=" * 50)
    
    try:
        await test_nlp_update_intent_extraction()
        await test_multi_event_update_operation()
        await test_update_execution()
        
        print("\n" + "=" * 50)
        print("🏁 Debug tests completed")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
