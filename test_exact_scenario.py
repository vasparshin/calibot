#!/usr/bin/env python3
"""
Test the exact failing scenario from production logs.
"""

import asyncio
import json
import sys
import os
sys.path.append('/workspaces/calibot/backend')

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import conversation_state

async def test_exact_scenario():
    """Test the exact failing scenario"""
    print("🧪 Testing Exact Production Scenario")
    print("=" * 60)
    
    nlp_agent = NLPAgent()
    chat_id = "exact_test"
    
    # Clear conversation
    if chat_id in conversation_state.conversations:
        del conversation_state.conversations[chat_id]
    
    # The exact message that failed
    user_message = "cna you make 3 1 hr events for today, all titles \"lesson\" in tonyas calendar"
    
    print(f"User message: {user_message}")
    conversation_state.add_message(chat_id, "user", user_message)
    
    # Extract intent
    history = conversation_state.get_conversation_history(chat_id)
    result = await nlp_agent.extract_intent(user_message, history)
    
    print(f"\nExtracted Intent:")
    print(json.dumps(result, indent=2))
    
    # Validate
    print(f"\n🔍 Validation:")
    
    # Check if it's batch_create with events
    if result.get('intent') == 'batch_create' and 'events' in result:
        events = result['events']
        print(f"✅ Detected batch_create with {len(events)} events")
        
        # Check each event for calendar_name
        calendar_issues = []
        for i, event in enumerate(events):
            if 'calendar_name' not in event:
                calendar_issues.append(f"Event {i+1}: Missing calendar_name")
            elif 'tonya' not in event['calendar_name'].lower():
                calendar_issues.append(f"Event {i+1}: Wrong calendar '{event['calendar_name']}'")
            else:
                print(f"✅ Event {i+1}: Correct calendar '{event['calendar_name']}'")
        
        if calendar_issues:
            print("❌ Calendar Issues Found:")
            for issue in calendar_issues:
                print(f"  {issue}")
            return False
        else:
            print("✅ All events have correct calendar!")
            return True
    else:
        print("❌ Did not detect batch_create format")
        return False

async def test_simple_case():
    """Test simple single event case"""
    print("\n🧪 Testing Simple Single Event")
    print("=" * 60)
    
    nlp_agent = NLPAgent()
    chat_id = "simple_test"
    
    # Clear conversation
    if chat_id in conversation_state.conversations:
        del conversation_state.conversations[chat_id]
    
    user_message = "create 1 lesson event at 2pm in tonyas calendar"
    
    print(f"User message: {user_message}")
    conversation_state.add_message(chat_id, "user", user_message)
    
    history = conversation_state.get_conversation_history(chat_id)
    result = await nlp_agent.extract_intent(user_message, history)
    
    print(f"\nExtracted Intent:")
    print(json.dumps(result, indent=2))
    
    # Check calendar_name
    if 'calendar_name' in result and 'tonya' in result['calendar_name'].lower():
        print("✅ Calendar name extracted correctly!")
        return True
    else:
        print(f"❌ Calendar name issue: {result.get('calendar_name', 'MISSING')}")
        return False

async def main():
    test1_success = await test_exact_scenario()
    test2_success = await test_simple_case()
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"Exact Scenario: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Simple Case:    {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED - Calendar extraction is working!")
    else:
        print("\n❌ TESTS FAILED - Calendar extraction needs more work")
    
    return test1_success and test2_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
    asyncio.run(test_exact_user_scenario())
