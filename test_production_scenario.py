#!/usr/bin/env python3
"""
Production scenario test - replicates the exact user request that was problematic.
Tests the full pipeline with the exact message from production logs.
"""

import asyncio
import json
import sys
import os
sys.path.append('/workspaces/calibot/backend')

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import conversation_state

async def test_production_scenario():
    """Test the exact scenario from production logs"""
    print("🧪 Testing Production Scenario")
    print("Replicating: 'create multiple 1 hr events for today for 8am, 10am, 11, 12, 13, 14 each titles 'lesson for tonyas calendar'")
    print("=" * 80)
    
    nlp_agent = NLPAgent()
    chat_id = "production_test"
    
    # Clear conversation
    if chat_id in conversation_state.conversations:
        del conversation_state.conversations[chat_id]
    
    # Set up some realistic conversation context (user mentions Tonya's calendar earlier)
    context_messages = [
        ("user", "Hi, I need to schedule some lessons today"),
        ("assistant", "I'd be happy to help you schedule lessons. What times work for you?"),
        ("user", "I need to use Tonya's calendar for these"),
        ("assistant", "Understood, I'll schedule them on Tonya's calendar. What times would you like?")
    ]
    
    print("Setting up conversation context:")
    for role, message in context_messages:
        conversation_state.add_message(chat_id, role, message)
        print(f"{role.capitalize()}: {message}")
    
    # The actual problematic message from production
    user_message = "create multiple 1 hr events for today for 8am, 10am, 11, 12, 13, 14 each titles 'lesson for tonyas calendar"
    
    print(f"\nUser message (from production): {user_message}")
    conversation_state.add_message(chat_id, "user", user_message)
    
    # Extract intent
    history = conversation_state.get_conversation_history(chat_id)
    print(f"\nConversation history being sent to LLM:")
    from app.utils.helpers import format_conversation_history
    formatted = format_conversation_history(history)
    print(formatted)
    
    print(f"\nExtracting intent...")
    result = await nlp_agent.extract_intent(user_message, history)
    
    print(f"\nFinal extracted intent:")
    print(json.dumps(result, indent=2))
    
    # Validate the result
    print(f"\n🔍 Validation:")
    
    success_count = 0
    total_checks = 0
    
    # Check 1: Should be batch_create or multiple events
    total_checks += 1
    if result.get('intent') == 'batch_create' or isinstance(result.get('start_time'), list):
        print("✅ Multiple events detected correctly")
        success_count += 1
    else:
        print("❌ Multiple events not detected")
    
    # Check 2: Should have proper event titles
    total_checks += 1
    found_lesson_title = False
    if result.get('intent') == 'batch_create' and 'events' in result:
        for event in result['events']:
            if 'lesson' in event.get('event_name', '').lower():
                found_lesson_title = True
                break
    elif 'lesson' in result.get('event_name', '').lower():
        found_lesson_title = True
    
    if found_lesson_title:
        print("✅ Event title 'lesson' detected correctly")
        success_count += 1
    else:
        print("❌ Event title 'lesson' not found")
    
    # Check 3: Should use Tonya's calendar (from context or message)
    total_checks += 1
    found_tonya_calendar = False
    if result.get('intent') == 'batch_create' and 'events' in result:
        for event in result['events']:
            calendar_name = event.get('calendar_name', '').lower()
            if 'tonya' in calendar_name:
                found_tonya_calendar = True
                break
    elif 'tonya' in result.get('calendar_name', '').lower():
        found_tonya_calendar = True
    
    if found_tonya_calendar:
        print("✅ Tonya's calendar detected correctly")
        success_count += 1
    else:
        print("❌ Tonya's calendar not detected")
    
    # Check 4: Should have correct number of events (6 times specified)
    total_checks += 1
    event_count = 0
    if result.get('intent') == 'batch_create' and 'events' in result:
        event_count = len(result['events'])
    elif isinstance(result.get('start_time'), list):
        event_count = len(result['start_time'])
    else:
        event_count = 1 if result.get('intent') == 'create' else 0
    
    if event_count == 6:
        print(f"✅ Correct number of events: {event_count}")
        success_count += 1
    else:
        print(f"❌ Wrong number of events: expected 6, got {event_count}")
    
    # Check 5: Should have correct times (8am, 10am, 11, 12, 13, 14)
    total_checks += 1
    expected_times = ["08:00", "10:00", "11:00", "12:00", "13:00", "14:00"]
    found_times = []
    
    if result.get('intent') == 'batch_create' and 'events' in result:
        found_times = [event.get('start_time') for event in result['events']]
    elif isinstance(result.get('start_time'), list):
        found_times = result['start_time']
    elif result.get('start_time'):
        found_times = [result['start_time']]
    
    if set(expected_times).issubset(set(found_times)):
        print(f"✅ All expected times found: {found_times}")
        success_count += 1
    else:
        print(f"❌ Times mismatch. Expected: {expected_times}, Found: {found_times}")
    
    # Final score
    print(f"\n🏆 FINAL SCORE: {success_count}/{total_checks} checks passed")
    
    if success_count == total_checks:
        print("🎉 ALL TESTS PASSED! Production scenario should work correctly now.")
    else:
        print("⚠️ Some issues remain. Review the failures above.")
    
    return success_count == total_checks

async def main():
    success = await test_production_scenario()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
