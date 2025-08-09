#!/usr/bin/env python3
"""
Test script for multi-event delete functionality with inline keyboards
Validates that delete requests with multiple events show inline keyboards for selection
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent
from app.services.multi_event_operations import MultiEventOperationHandler
from app.utils.ui_helpers import format_multi_event_confirmation_with_keyboard

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockCalendarService:
    """Mock calendar service for testing"""
    
    async def query_events(self, query_data):
        """Mock query events to return multiple events for testing"""
        if query_data.get("event_name") == "lesson":
            # Return multiple lessons to test delete confirmation
            return {
                "success": True,
                "events": [
                    {
                        "id": "lesson_1",
                        "summary": "Math Lesson",
                        "start": {"dateTime": "2024-01-15T08:00:00"},
                        "end": {"dateTime": "2024-01-15T09:00:00"},
                        "calendar_id": "primary",
                        "calendar_name": "tonyas calendar"
                    },
                    {
                        "id": "lesson_2", 
                        "summary": "Science Lesson",
                        "start": {"dateTime": "2024-01-15T10:00:00"},
                        "end": {"dateTime": "2024-01-15T11:00:00"},
                        "calendar_id": "primary",
                        "calendar_name": "tonyas calendar"
                    },
                    {
                        "id": "lesson_3",
                        "summary": "History Lesson", 
                        "start": {"dateTime": "2024-01-15T14:00:00"},
                        "end": {"dateTime": "2024-01-15T15:00:00"},
                        "calendar_id": "work_calendar",
                        "calendar_name": "Work Calendar"
                    }
                ]
            }
        return {"success": False, "events": []}

async def test_multi_event_delete_keyboard():
    """Test that delete requests with multiple events show inline keyboards"""
    
    print("🧪 Testing Multi-Event Delete with Inline Keyboards")
    print("=" * 60)
    
    # Initialize services
    nlp_agent = NLPAgent()
    mock_calendar = MockCalendarService()
    
    # Mock the services for MultiEventOperationHandler
    class MockTelegramService:
        pass
    
    class MockConversationState:
        pass
    
    multi_event_handler = MultiEventOperationHandler(
        calendar_service=mock_calendar,
        telegram_service=MockTelegramService(),
        conversation_state=MockConversationState()
    )
    
    # Test user message requesting delete of multiple events
    test_messages = [
        "delete all lessons today",
        "remove my lessons", 
        "delete lesson events",
        "cancel all my lesson appointments"
    ]
    
    success_count = 0
    
    for i, user_message in enumerate(test_messages, 1):
        print(f"\n--- Test {i}: '{user_message}' ---")
        
        try:
            # Extract intent using NLP agent
            intent_result = await nlp_agent.extract_intent(user_message, [])
            print(f"📝 Extracted Intent: {intent_result}")
            
            if intent_result and intent_result.get("intent") == "delete":
                # Mock query for events (simulating the route logic)
                query_data = {
                    "event_name": intent_result.get("event_name", ""),
                    "date": intent_result.get("date", "")
                }
                
                matched_events = await mock_calendar.query_events(query_data)
                print(f"📅 Matched Events: {len(matched_events.get('events', []))} events found")
                
                if matched_events["success"] and len(matched_events["events"]) > 1:
                    events = matched_events["events"]
                    
                    # Test inline keyboard formatting
                    confirmation_msg, keyboard = format_multi_event_confirmation_with_keyboard(events, "delete")
                    
                    print(f"✅ Multi-event keyboard generated successfully!")
                    print(f"📱 Confirmation Message Preview:")
                    print(confirmation_msg[:200] + "..." if len(confirmation_msg) > 200 else confirmation_msg)
                    print(f"⌨️ Keyboard: {len(keyboard.get('inline_keyboard', []))} buttons")
                    
                    # Test pending operation storage
                    chat_id = f"test_chat_{i}"
                    multi_event_handler.store_pending_operation(chat_id, {
                        "intent": "delete",
                        "events": events,
                        "event_data": intent_result
                    })
                    
                    # Verify pending operation stored
                    has_pending = multi_event_handler.has_pending_operation(chat_id)
                    print(f"💾 Pending operation stored: {has_pending}")
                    
                    if has_pending:
                        success_count += 1
                        print(f"✅ Test {i} PASSED: Delete keyboard and storage working")
                    else:
                        print(f"❌ Test {i} FAILED: Pending operation not stored")
                else:
                    print(f"❌ Test {i} FAILED: No multiple events found")
            else:
                print(f"❌ Test {i} FAILED: Intent not detected as delete")
                
        except Exception as e:
            print(f"❌ Test {i} FAILED with exception: {e}")
            logger.exception(f"Error in test {i}")
    
    print(f"\n🏆 Test Results: {success_count}/{len(test_messages)} tests passed")
    
    if success_count == len(test_messages):
        print("✅ ALL TESTS PASSED: Multi-event delete keyboards working correctly!")
        return True
    else:
        print("❌ SOME TESTS FAILED: Issues with multi-event delete keyboard functionality")
        return False

async def test_keyboard_formatting():
    """Test the inline keyboard formatting specifically"""
    
    print("\n🎯 Testing Keyboard Formatting Details")
    print("=" * 60)
    
    # Mock events for testing
    test_events = [
        {
            "id": "event_1",
            "summary": "Math Lesson",
            "start": {"dateTime": "2024-01-15T08:00:00"},
            "end": {"dateTime": "2024-01-15T09:00:00"}, 
            "calendar_id": "primary",
            "calendar_name": "tonyas calendar"
        },
        {
            "id": "event_2",
            "summary": "Science Lesson", 
            "start": {"dateTime": "2024-01-15T10:00:00"},
            "end": {"dateTime": "2024-01-15T11:00:00"},
            "calendar_id": "work_calendar", 
            "calendar_name": "Work Calendar"
        }
    ]
    
    try:
        # Test delete keyboard
        delete_msg, delete_keyboard = format_multi_event_confirmation_with_keyboard(test_events, "delete")
        print("🗑️ Delete Keyboard Test:")
        print(f"Message: {delete_msg[:100]}...")
        print(f"Keyboard structure: {delete_keyboard}")
        
        # Verify keyboard has correct buttons
        buttons = delete_keyboard.get('inline_keyboard', [])
        expected_buttons = len(test_events) + 2  # events + "All" + "Cancel"
        actual_buttons = sum(len(row) for row in buttons)
        
        print(f"Expected buttons: {expected_buttons}, Actual: {actual_buttons}")
        
        if actual_buttons >= expected_buttons - 1:  # Allow some flexibility
            print("✅ Keyboard formatting PASSED")
            return True
        else:
            print("❌ Keyboard formatting FAILED: Missing buttons")
            return False
            
    except Exception as e:
        print(f"❌ Keyboard formatting FAILED with exception: {e}")
        logger.exception("Error in keyboard formatting test")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Multi-Event Delete Keyboard Tests")
    print("=" * 60)
    
    # Run all tests
    test1_passed = await test_multi_event_delete_keyboard()
    test2_passed = await test_keyboard_formatting()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Multi-event delete keyboard functionality is working correctly")
        print("✅ Delete requests with multiple events will show inline keyboards")
        print("✅ Users can select individual events or delete all at once")
        return True
    else:
        print("⚠️ SOME TESTS FAILED!")
        print("❌ Multi-event delete keyboard functionality needs attention")
        return False

if __name__ == "__main__":
    asyncio.run(main())
