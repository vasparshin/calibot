#!/usr/bin/env python3
"""
Comprehensive final test - validates all fixes together.
Tests the complete pipeline including calendar selection.
"""

import asyncio
import json
import sys
import os
sys.path.append('/workspaces/calibot/backend')

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import conversation_state

def print_test_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_test_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status:<10} {test_name}")
    if details:
        print(f"           {details}")

async def test_production_scenarios():
    """Test all the key production scenarios"""
    print_test_header("PRODUCTION SCENARIO VALIDATION")
    
    nlp_agent = NLPAgent()
    test_results = []
    
    scenarios = [
        {
            "name": "Original failing case",
            "message": "cna you make 3 1 hr events for today, all titles \"lesson\" in tonyas calendar",
            "expected_events": 3,
            "expected_calendar": "tonyas calendar"
        },
        {
            "name": "Moving events case", 
            "message": "Move lesson events to calendar Tonya",
            "expected_intent": "query",  # Moving is complex, should ask for confirmation
            "expected_calendar": "Tonya"
        },
        {
            "name": "Explicit batch creation",
            "message": "create multiple 1 hr events for today for 8am, 10am, 11am, 12pm each titled 'lesson' for Tonya's calendar",
            "expected_events": 4,
            "expected_calendar": "Tonya's calendar"
        },
        {
            "name": "Single event with calendar",
            "message": "add 1 hour meeting at 3pm to work calendar",
            "expected_events": 1,
            "expected_calendar": "work calendar"
        },
        {
            "name": "Missing time info",
            "message": "create lesson in tonyas calendar",
            "expected_confirmation": True,
            "expected_calendar": "tonyas calendar"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nTest {i}: {scenario['name']}")
        print(f"Message: {scenario['message']}")
        
        chat_id = f"prod_test_{i}"
        if chat_id in conversation_state.conversations:
            del conversation_state.conversations[chat_id]
        
        conversation_state.add_message(chat_id, "user", scenario['message'])
        history = conversation_state.get_conversation_history(chat_id)
        
        try:
            result = await nlp_agent.extract_intent(scenario['message'], history)
            print(f"Result: {json.dumps(result, indent=2)}")
            
            success = True
            issues = []
            
            # Check expected events count
            if 'expected_events' in scenario:
                actual_events = 0
                if result.get('intent') == 'batch_create' and 'events' in result:
                    actual_events = len(result['events'])
                elif result.get('intent') == 'create':
                    actual_events = 1
                
                if actual_events != scenario['expected_events']:
                    success = False
                    issues.append(f"Expected {scenario['expected_events']} events, got {actual_events}")
            
            # Check expected intent
            if 'expected_intent' in scenario:
                if result.get('intent') != scenario['expected_intent']:
                    success = False
                    issues.append(f"Expected intent '{scenario['expected_intent']}', got '{result.get('intent')}'")
            
            # Check calendar name
            if 'expected_calendar' in scenario:
                calendar_found = False
                actual_calendar = "NOT_FOUND"
                
                if result.get('intent') == 'batch_create' and 'events' in result:
                    for event in result['events']:
                        if event.get('calendar_name'):
                            actual_calendar = event['calendar_name']
                            if scenario['expected_calendar'].lower() in event['calendar_name'].lower():
                                calendar_found = True
                                break
                elif result.get('calendar_name'):
                    actual_calendar = result['calendar_name']
                    if scenario['expected_calendar'].lower() in result['calendar_name'].lower():
                        calendar_found = True
                
                if not calendar_found:
                    success = False
                    issues.append(f"Expected calendar '{scenario['expected_calendar']}', got '{actual_calendar}'")
            
            # Check confirmation needed
            if 'expected_confirmation' in scenario:
                needs_confirmation = result.get('confirmation_needed', False)
                if result.get('intent') == 'batch_create' and 'events' in result:
                    for event in result['events']:
                        if event.get('confirmation_needed', False):
                            needs_confirmation = True
                            break
                
                if needs_confirmation != scenario['expected_confirmation']:
                    success = False
                    issues.append(f"Expected confirmation_needed={scenario['expected_confirmation']}, got {needs_confirmation}")
            
            details = "; ".join(issues) if issues else ""
            print_test_result(scenario['name'], success, details)
            test_results.append(success)
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print_test_result(scenario['name'], False, f"Exception: {e}")
            test_results.append(False)
    
    return test_results

async def test_conversation_context():
    """Test conversation context handling"""
    print_test_header("CONVERSATION CONTEXT VALIDATION")
    
    nlp_agent = NLPAgent()
    chat_id = "context_test"
    
    if chat_id in conversation_state.conversations:
        del conversation_state.conversations[chat_id]
    
    # Simulate conversation with calendar context
    steps = [
        ("user", "Hi, I want to work with Sarah's calendar today"),
        ("assistant", "Great! I'll help you with Sarah's calendar."),
        ("user", "Add a meeting at 2pm")  # Should remember Sarah's calendar
    ]
    
    for role, message in steps[:-1]:
        conversation_state.add_message(chat_id, role, message)
    
    # Test the final message
    final_message = steps[-1][1]
    conversation_state.add_message(chat_id, "user", final_message)
    
    history = conversation_state.get_conversation_history(chat_id)
    result = await nlp_agent.extract_intent(final_message, history)
    
    print(f"Conversation context test:")
    print(f"Final message: {final_message}")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Should remember Sarah's calendar from context
    success = 'sarah' in result.get('calendar_name', '').lower()
    print_test_result("Context memory", success, 
                     f"Calendar: {result.get('calendar_name', 'NOT_FOUND')}")
    
    return success

async def main():
    """Run comprehensive validation"""
    print("🧪 CALIBOT COMPREHENSIVE VALIDATION")
    print("Testing all fixes: batch events, calendar selection, context handling")
    
    # Run all test suites
    production_results = await test_production_scenarios()
    context_result = await test_conversation_context()
    
    # Calculate overall results
    total_tests = len(production_results) + 1
    passed_tests = sum(production_results) + (1 if context_result else 0)
    
    print_test_header("FINAL RESULTS")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ CaliBOT is ready for production")
        print("✅ Calendar selection works correctly")
        print("✅ Batch event creation works")
        print("✅ Context memory is functional")
        print("✅ Time/duration validation works")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed")
        print("❌ Issues remain that need attention")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
