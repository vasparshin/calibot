#!/usr/bin/env python3
"""
Test script for context handling and calendar selection improvements.
Tests the enhanced prompt and conversation history formatting.
"""

import asyncio
import json
import sys
import os
sys.path.append('/workspaces/calibot/backend')

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import conversation_state
from app.utils.helpers import format_conversation_history
from datetime import datetime

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

async def test_context_handling():
    """Test conversation context and memory"""
    print_section("TESTING CONTEXT HANDLING AND CALENDAR SELECTION")
    
    nlp_agent = NLPAgent()
    
    # Test scenarios with context
    test_scenarios = [
        {
            "name": "Calendar Name in Current Message",
            "history": [
                {"role": "user", "content": "Hi, I need help with my schedule", "timestamp": "2025-08-06 09:00"},
                {"role": "assistant", "content": "I'd be happy to help you with your schedule. What would you like to do?", "timestamp": "2025-08-06 09:01"}
            ],
            "current_message": "Create a 1 hour lesson event for today at 2pm for Tonya's calendar",
            "expected_calendar": "Tonya's calendar",
            "expected_intent": "create"
        },
        {
            "name": "Multiple Events with Calendar Reference",
            "history": [
                {"role": "user", "content": "I want to schedule some lessons", "timestamp": "2025-08-06 09:00"},
                {"role": "assistant", "content": "Great! I can help you schedule lessons. What times work for you?", "timestamp": "2025-08-06 09:01"},
                {"role": "user", "content": "I need them on Tonya's calendar", "timestamp": "2025-08-06 09:02"},
                {"role": "assistant", "content": "Understood, I'll schedule them on Tonya's calendar. What times?", "timestamp": "2025-08-06 09:03"}
            ],
            "current_message": "Create multiple 1 hr events for today for 8am, 10am, 11am, 12pm each titled 'lesson'",
            "expected_calendar": "Tonya's calendar",
            "expected_intent": "create",
            "expected_multiple": True
        },
        {
            "name": "Reference to Previous Context",
            "history": [
                {"role": "user", "content": "I'm working with my personal calendar today", "timestamp": "2025-08-06 08:00"},
                {"role": "assistant", "content": "Got it, I'll help you with your personal calendar. What do you need?", "timestamp": "2025-08-06 08:01"},
                {"role": "user", "content": "Actually, let me switch to work calendar", "timestamp": "2025-08-06 08:30"},
                {"role": "assistant", "content": "Switching to your work calendar. How can I help?", "timestamp": "2025-08-06 08:31"}
            ],
            "current_message": "Add a meeting at 3pm today for 2 hours",
            "expected_calendar": "work calendar",
            "expected_intent": "create"
        },
        {
            "name": "Mixed Instructions Test",
            "history": [
                {"role": "user", "content": "I have two calendars - my personal one and Sarah's calendar", "timestamp": "2025-08-06 07:00"},
                {"role": "assistant", "content": "I understand you work with both your personal calendar and Sarah's calendar. Which one should I use?", "timestamp": "2025-08-06 07:01"}
            ],
            "current_message": "Create 3 events: gym at 7am on my personal calendar, meeting at 9am on Sarah's calendar, and lunch at 12pm on Sarah's calendar",
            "expected_intent": "create",
            "expected_multiple": True
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Test {i}: {scenario['name']} ---")
        
        # Set up conversation history
        chat_id = f"test_chat_{i}"
        # Clear any existing conversation for this test
        if chat_id in conversation_state.conversations:
            del conversation_state.conversations[chat_id]
        
        # Add messages to conversation state
        for msg in scenario['history']:
            conversation_state.add_message(chat_id, msg['role'], msg['content'])
        
        # Get history in the correct format
        history = conversation_state.get_conversation_history(chat_id)
        formatted_history = format_conversation_history(history)
        print(f"Formatted History:\n{formatted_history}")
        print(f"\nCurrent Message: {scenario['current_message']}")
        
        # Extract intent
        try:
            result = await nlp_agent.extract_intent(scenario['current_message'], history)
            print(f"\nExtracted Intent:")
            print(json.dumps(result, indent=2))
            
            # Check expectations
            success_flags = []
            
            # Check intent
            if result.get('intent') == scenario.get('expected_intent'):
                success_flags.append("✅ Intent correct")
            else:
                success_flags.append(f"❌ Intent wrong: expected {scenario.get('expected_intent')}, got {result.get('intent')}")
            
            # Check calendar name if expected
            if 'expected_calendar' in scenario:
                found_calendar = False
                if result.get('intent') == 'batch_create' and 'events' in result:
                    # Check if any event has the expected calendar
                    for event in result['events']:
                        if event.get('calendar_name') == scenario['expected_calendar']:
                            found_calendar = True
                            break
                elif result.get('calendar_name') == scenario['expected_calendar']:
                    found_calendar = True
                
                if found_calendar:
                    success_flags.append("✅ Calendar name extracted correctly")
                else:
                    success_flags.append(f"❌ Calendar name wrong: expected '{scenario['expected_calendar']}', not found in result")
            
            # Check multiple events if expected
            if scenario.get('expected_multiple'):
                if result.get('intent') == 'batch_create' and len(result.get('events', [])) > 1:
                    success_flags.append(f"✅ Multiple events detected ({len(result['events'])} events)")
                elif isinstance(result.get('start_time'), list) and len(result['start_time']) > 1:
                    success_flags.append(f"✅ Multiple events detected (array format)")
                else:
                    success_flags.append("❌ Multiple events expected but not detected")
            
            print(f"\nValidation:")
            for flag in success_flags:
                print(f"  {flag}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 40)

async def test_conversation_formatting():
    """Test the improved conversation history formatting"""
    print_section("TESTING CONVERSATION HISTORY FORMATTING")
    
    # Test with various history lengths
    test_histories = [
        {
            "name": "Empty History",
            "history": []
        },
        {
            "name": "Short History",
            "history": [
                {"role": "user", "content": "Hello", "timestamp": "2025-08-06 09:00"},
                {"role": "assistant", "content": "Hi! How can I help?", "timestamp": "2025-08-06 09:01"}
            ]
        },
        {
            "name": "Long History (>10 messages)",
            "history": [
                {"role": "user", "content": f"Message {i}", "timestamp": f"2025-08-06 09:{i:02d}"}
                for i in range(15)
            ]
        },
        {
            "name": "History with Calendar References",
            "history": [
                {"role": "user", "content": "I want to use my work calendar", "timestamp": "2025-08-06 09:00"},
                {"role": "assistant", "content": "Setting up work calendar access", "timestamp": "2025-08-06 09:01"},
                {"role": "user", "content": "Actually, let's use Sarah's calendar instead", "timestamp": "2025-08-06 09:02"},
                {"role": "assistant", "content": "Switching to Sarah's calendar", "timestamp": "2025-08-06 09:03"},
                {"role": "user", "content": "Create a meeting at 2pm", "timestamp": "2025-08-06 09:04"}
            ]
        }
    ]
    
    for test in test_histories:
        print(f"\n--- {test['name']} ---")
        print(f"Original history length: {len(test['history'])}")
        
        formatted = format_conversation_history(test['history'])
        print(f"Formatted history:\n{formatted}")
        print("-" * 40)

async def main():
    """Run all tests"""
    print("🧪 CaliBOT Context and Calendar Selection Tests")
    print(f"Timestamp: {datetime.now()}")
    
    await test_conversation_formatting()
    await test_context_handling()
    
    print_section("TESTS COMPLETED")
    print("Review the results above to see if context handling and calendar selection work correctly.")
    print("Key things to check:")
    print("1. Calendar names are extracted from current messages")
    print("2. Calendar context is preserved from conversation history") 
    print("3. Multiple events are detected and processed correctly")
    print("4. Conversation history is formatted clearly with message numbers")

if __name__ == "__main__":
    asyncio.run(main())
