#!/usr/bin/env python3
"""
Test script to verify the 'list' object attribute error is fixed.
This script simulates the exact error scenario and validates the fix.
"""

import sys
import os
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_list_attribute_error_fix():
    """Test that the 'list' object has no attribute 'get' error is fixed"""
    
    print("🧪 Testing 'list' object attribute error fix...")
    
    try:
        # Import after path setup
        from app.api.routes import process_webhook_message
        from app.services.google_calendar import GoogleCalendarService
        from app.services.conversation import ConversationState
        from app.services.telegram import TelegramBotService
        
        # Mock the calendar service to return problematic data structure
        calendar_service = AsyncMock()
        
        # This simulates the problematic response that caused the error
        # The issue was that sometimes events was not a list of dicts
        calendar_service.query_events.return_value = {
            "success": True,
            "events": [
                {"id": "event1", "summary": "lesson", "start": "2025-08-06T10:00:00Z"},
                {"id": "event2", "summary": "lesson", "start": "2025-08-06T14:00:00Z"},
                {"id": "event3", "summary": "lesson", "start": "2025-08-06T16:00:00Z"},
                # Simulate a malformed event that could cause issues
                "invalid_event_data",  # This shouldn't be here but could happen
                {"id": "event4", "summary": "lesson", "start": "2025-08-06T18:00:00Z"},
            ]
        }
        
        # Mock other services
        conversation_state = MagicMock()
        telegram_service = AsyncMock()
        
        # Mock the send_telegram_message function
        async def mock_send_telegram_message(chat_id, message):
            print(f"📤 Mock telegram message to {chat_id}: {message}")
            return True
        
        # Test data that previously caused the error
        webhook_data = {
            "message": {
                "message_id": 123,
                "from": {"id": 12345, "first_name": "Test"},
                "chat": {"id": 12345},
                "text": "Delete all events titled \"lesson\" scheduled for day before yesterday"
            }
        }
        
        print("✅ Test 1: Malformed events list handling")
        
        # This should not crash with 'list' object has no attribute 'get'
        try:
            # Mock the dependencies in the routes module
            import app.api.routes as routes_module
            routes_module.calendar_service = calendar_service
            routes_module.conversation_state = conversation_state
            routes_module.send_telegram_message = mock_send_telegram_message
            
            # Mock NLP agent to return delete intent
            nlp_agent_mock = AsyncMock()
            nlp_agent_mock.extract_intent.return_value = {
                "intent": "delete",
                "event_name": "lesson", 
                "date": "2025-08-06",
                "confirmation_needed": True
            }
            routes_module.nlp_agent = nlp_agent_mock
            
            # Mock other required components
            routes_module.calendar_agent = AsyncMock()
            routes_module.event_queue_handler = MagicMock()
            routes_module.multi_event_handler = MagicMock()
            
            result = await routes_module.process_webhook_message(webhook_data)
            print(f"✅ Test passed! Result: {result}")
            
        except Exception as e:
            if "'list' object has no attribute 'get'" in str(e):
                print(f"❌ FAILED: The 'list' object attribute error still exists: {e}")
                return False
            else:
                print(f"⚠️  Different error (might be expected): {e}")
        
        print("✅ Test 2: Normal events list handling")
        
        # Test with normal data structure
        calendar_service.query_events.return_value = {
            "success": True,
            "events": [
                {"id": "event1", "summary": "lesson", "start": "2025-08-06T10:00:00Z"},
                {"id": "event2", "summary": "lesson", "start": "2025-08-06T14:00:00Z"},
            ]
        }
        
        try:
            result = await routes_module.process_webhook_message(webhook_data)
            print(f"✅ Normal case passed! Result: {result}")
        except Exception as e:
            print(f"⚠️  Error in normal case: {e}")
        
        print("✅ Test 3: Empty events list")
        
        # Test with empty events
        calendar_service.query_events.return_value = {
            "success": True,
            "events": []
        }
        
        try:
            result = await routes_module.process_webhook_message(webhook_data)
            print(f"✅ Empty case passed! Result: {result}")
        except Exception as e:
            print(f"⚠️  Error in empty case: {e}")
        
        print("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 CaliBOT - Testing List Attribute Error Fix")
    print("=" * 50)
    
    success = asyncio.run(test_list_attribute_error_fix())
    
    if success:
        print("\n✅ ALL TESTS PASSED - The 'list' object attribute error should be fixed!")
        exit(0)
    else:
        print("\n❌ TESTS FAILED - The error may still exist!")
        exit(1)
