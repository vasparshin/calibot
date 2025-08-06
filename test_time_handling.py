#!/usr/bin/env python3
"""
Test time and duration handling for events.
"""

import asyncio
import json
import sys
import os
sys.path.append('/workspaces/calibot/backend')

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import conversation_state

async def test_missing_time_scenarios():
    """Test scenarios where time or duration is missing"""
    print("🧪 Testing Missing Time/Duration Scenarios")
    print("=" * 60)
    
    nlp_agent = NLPAgent()
    
    test_cases = [
        {
            "name": "Missing start time",
            "message": "create 3 lesson events in tonyas calendar",
            "should_need_confirmation": True
        },
        {
            "name": "Missing duration", 
            "message": "create lesson at 2pm in tonyas calendar",
            "should_need_confirmation": True
        },
        {
            "name": "Complete information",
            "message": "create 1 hour lesson at 2pm in tonyas calendar", 
            "should_need_confirmation": False
        },
        {
            "name": "Moving events request",
            "message": "move lesson events to calendar Tonya",
            "should_need_confirmation": True  # This is complex operation
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Message: {test_case['message']}")
        
        chat_id = f"time_test_{i}"
        if chat_id in conversation_state.conversations:
            del conversation_state.conversations[chat_id]
        
        conversation_state.add_message(chat_id, "user", test_case['message'])
        history = conversation_state.get_conversation_history(chat_id)
        
        result = await nlp_agent.extract_intent(test_case['message'], history)
        
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Check confirmation_needed
        needs_confirmation = result.get('confirmation_needed', False)
        if result.get('intent') == 'batch_create' and 'events' in result:
            # For batch, check if any event needs confirmation
            for event in result['events']:
                if event.get('confirmation_needed', False):
                    needs_confirmation = True
                    break
        
        expected = test_case['should_need_confirmation']
        if needs_confirmation == expected:
            print(f"✅ Confirmation handling correct: {'needs' if needs_confirmation else 'no'} confirmation")
            results.append(True)
        else:
            print(f"❌ Confirmation handling wrong: expected {'needs' if expected else 'no'} confirmation, got {'needs' if needs_confirmation else 'no'}")
            results.append(False)
        
        # Check calendar name extraction
        calendar_found = False
        if result.get('intent') == 'batch_create' and 'events' in result:
            for event in result['events']:
                if 'tonya' in event.get('calendar_name', '').lower():
                    calendar_found = True
                    break
        elif 'tonya' in result.get('calendar_name', '').lower():
            calendar_found = True
        
        if calendar_found or 'tonya' not in test_case['message'].lower():
            print("✅ Calendar name handling correct")
        else:
            print("❌ Calendar name not extracted when specified")
            results[-1] = False
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed}/{total} tests passed")
    
    return passed == total

async def main():
    success = await test_missing_time_scenarios()
    
    if success:
        print("\n🎉 All time/duration handling tests passed!")
    else:
        print("\n❌ Some time/duration handling issues remain")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
