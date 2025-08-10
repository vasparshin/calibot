#!/usr/bin/env python3
"""
Test for batch event creation functionality and formatting consistency.
Validates the fix for multiple event creation and consistent formatting.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent

async def test_batch_creation_intent():
    """Test that batch creation intents are properly extracted"""
    print("🔍 Testing batch creation intent extraction...")
    
    nlp_agent = NLPAgent()
    
    test_cases = [
        "tonya will have 3 lessons tomorrow, 9, 10 and 12am",
        "schedule 3 lessons for 9am, 10am, and 12pm tomorrow",
        "create lessons at 9, 10, and 11 tomorrow"
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: '{test_case}'")
        try:
            # Create mock conversation history
            history = []
            
            result = await nlp_agent.extract_intent(test_case, history)
            
            if isinstance(result, dict):
                intent = result.get('intent')
                events = result.get('events', [])
                
                print(f"  Intent: {intent}")
                print(f"  Events count: {len(events)}")
                
                if intent == "batch_create" and len(events) >= 3:
                    print(f"  ✅ Correctly detected batch creation with {len(events)} events")
                    
                    # Validate event structure
                    valid_events = 0
                    for j, event in enumerate(events):
                        if isinstance(event, dict) and 'start_time' in event and 'end_time' in event:
                            valid_events += 1
                            print(f"    Event {j+1}: {event['start_time']} - {event['end_time']}")
                    
                    if valid_events == len(events):
                        print(f"  ✅ All events have valid structure")
                    else:
                        print(f"  ❌ Only {valid_events}/{len(events)} events have valid structure")
                        all_passed = False
                else:
                    print(f"  ❌ Expected batch_create with >=3 events, got {intent} with {len(events)} events")
                    all_passed = False
            else:
                print(f"  ❌ Invalid result type: {type(result)}")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_passed = False
    
    return all_passed

async def main():
    """Run all tests"""
    print("🚀 Testing Batch Creation Intent Extraction")
    print("=" * 60)
    
    success = await test_batch_creation_intent()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All batch creation tests passed!")
        print("The intent extraction is now properly detecting multiple event scenarios.")
    else:
        print("❌ Some tests failed - batch creation needs more work")

if __name__ == "__main__":
    asyncio.run(main())
