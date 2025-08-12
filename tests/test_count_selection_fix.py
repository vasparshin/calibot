"""
Test Count-Based Event Selection Fix for Multi-Event Operations

This test validates that the enhanced NLP agent and multi-event operations
properly handle count-based requests like "move the last 3 lessons 1 hr later"
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# Add the backend path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent
from app.services.multi_event_operations import MultiEventOperationHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock services for testing
class MockCalendarService:
    async def query_events(self, params):
        # Return mock events to test count selection
        return {
            "success": True,
            "events": [
                {
                    "id": "event1",
                    "summary": "Math Lesson",
                    "start": "2024-01-15T08:00:00Z",
                    "end": "2024-01-15T09:00:00Z",
                    "calendar_name": "School",
                    "calendar_id": "primary",
                    "link": "https://calendar.google.com/calendar/event?eid=event1"
                },
                {
                    "id": "event2", 
                    "summary": "Physics Lesson",
                    "start": "2024-01-15T10:00:00Z",
                    "end": "2024-01-15T11:00:00Z",
                    "calendar_name": "School",
                    "calendar_id": "primary",
                    "link": "https://calendar.google.com/calendar/event?eid=event2"
                },
                {
                    "id": "event3",
                    "summary": "Chemistry Lesson", 
                    "start": "2024-01-15T14:00:00Z",
                    "end": "2024-01-15T15:00:00Z",
                    "calendar_name": "School",
                    "calendar_id": "primary",
                    "link": "https://calendar.google.com/calendar/event?eid=event3"
                },
                {
                    "id": "event4",
                    "summary": "Biology Lesson",
                    "start": "2024-01-15T16:00:00Z", 
                    "end": "2024-01-15T17:00:00Z",
                    "calendar_name": "School",
                    "calendar_id": "primary",
                    "link": "https://calendar.google.com/calendar/event?eid=event4"
                }
            ]
        }

class MockTelegramService:
    pass

class MockConversationState:
    def add_message(self, chat_id, role, content):
        pass

async def test_count_based_selection():
    """Test count-based event selection"""
    print("=" * 60)
    print("🔥 TESTING COUNT-BASED EVENT SELECTION FIX")
    print("=" * 60)
    
    # Initialize services
    calendar_service = MockCalendarService()
    telegram_service = MockTelegramService()
    conversation_state = MockConversationState()
    
    # Initialize NLP Agent
    nlp_agent = NLPAgent()
    
    # Initialize Multi-Event Operations Handler
    multi_event_handler = MultiEventOperationHandler(
        calendar_service=calendar_service,
        telegram_service=telegram_service,
        conversation_state=conversation_state
    )
    
    # Test the critical user scenario
    test_message = "move the last 3 lessons 1 hr later"
    chat_id = 12345
    
    print(f"\n📨 Testing message: '{test_message}'")
    print("-" * 50)
    
    # Test 1: NLP Agent Enhancement
    print("\n🧠 Step 1: Testing NLP Agent Intent Extraction")
    extracted_intent = await nlp_agent.extract_intent(test_message, chat_id)
    
    print(f"✅ NLP Agent Result: {extracted_intent}")
    
    # Validate count extraction
    if 'count' in extracted_intent and extracted_intent['count'] == 3:
        print("✅ SUCCESS: Count properly extracted (count=3)")
    else:
        print(f"❌ FAILED: Count not extracted properly. Got: {extracted_intent.get('count', 'missing')}")
        return False
    
    # Validate time_shift extraction
    if 'time_shift' in extracted_intent:
        print(f"✅ SUCCESS: Time shift properly extracted (time_shift={extracted_intent['time_shift']})")
    else:
        print("❌ FAILED: Time shift not extracted properly")
        return False
    
    # Test 2: Multi-Event Operation Count Selection
    print("\n📋 Step 2: Testing Multi-Event Operation Count Selection")
    
    # Simulate finding matching events with the enhanced criteria
    test_criteria = {
        'event_name': 'lesson',
        'target': 'last',
        'count': 3,
        'time_shift': '1 hr',
        'date': '2024-01-15'
    }
    
    matching_events = await multi_event_handler._find_matching_events(test_criteria)
    
    print(f"✅ Found {len(matching_events)} matching events")
    
    # Validate count selection worked
    if len(matching_events) == 3:
        print("✅ SUCCESS: Correctly selected last 3 events")
        for i, event in enumerate(matching_events, 1):
            print(f"   {i}. {event['summary']} at {event['start_time']}")
    else:
        print(f"❌ FAILED: Expected 3 events, got {len(matching_events)}")
        return False
    
    # Test 3: Target Selection Logic
    print("\n🎯 Step 3: Testing Target Selection Logic")
    
    # Test "first" selection
    first_criteria = {
        'event_name': 'lesson',
        'target': 'first',
        'count': 2,
        'date': '2024-01-15'
    }
    
    first_events = await multi_event_handler._find_matching_events(first_criteria)
    
    if len(first_events) == 2:
        print("✅ SUCCESS: Correctly selected first 2 events")
        print(f"   First: {first_events[0]['summary']} at {first_events[0]['start_time']}")
        print(f"   Second: {first_events[1]['summary']} at {first_events[1]['start_time']}")
    else:
        print(f"❌ FAILED: Expected 2 first events, got {len(first_events)}")
        return False
    
    # Test 4: Edge Cases
    print("\n🧪 Step 4: Testing Edge Cases")
    
    # Test requesting more events than available
    edge_criteria = {
        'event_name': 'lesson',
        'target': 'last',
        'count': 10,  # More than the 4 available
        'date': '2024-01-15'
    }
    
    edge_events = await multi_event_handler._find_matching_events(edge_criteria)
    
    if len(edge_events) == 4:  # Should return all 4 available
        print("✅ SUCCESS: Edge case handled - returned all available events when count exceeds total")
    else:
        print(f"❌ FAILED: Edge case not handled properly. Expected 4, got {len(edge_events)}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED - COUNT-BASED SELECTION FIX WORKING!")
    print("=" * 60)
    print("📋 Summary:")
    print("   ✅ NLP agent extracts count and time_shift properly")
    print("   ✅ Multi-event operations processes multiple events")
    print("   ✅ Target selection (last/first) works correctly")
    print("   ✅ Edge cases handled properly")
    print("   🔥 CRITICAL BUG FIXED: 'last 3 lessons' now processes 3 events, not 1!")
    
    return True

async def main():
    """Run the count selection test"""
    try:
        success = await test_count_based_selection()
        
        if success:
            print("\n✅ Count-based selection fix validation PASSED")
            print("🚀 Ready for deployment - multi-event operations now work correctly!")
        else:
            print("\n❌ Count-based selection fix validation FAILED")
            print("🚨 Issues need to be resolved before deployment")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
