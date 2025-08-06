#!/usr/bin/env python3
"""
Test script to verify calendar selection from conversation context.
Tests that calendar references from earlier in the conversation are remembered.
"""

import asyncio
import json
import sys
import os
sys.path.append('/workspaces/calibot/backend')

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import conversation_state

async def test_calendar_context_memory():
    """Test that calendar context is remembered from earlier conversation"""
    print("🧪 Testing Calendar Context Memory")
    print("=" * 60)
    
    nlp_agent = NLPAgent()
    chat_id = "context_memory_test"
    
    # Clear any existing conversation
    if chat_id in conversation_state.conversations:
        del conversation_state.conversations[chat_id]
    
    # Simulate a conversation where user mentions calendar preference early
    conversation_steps = [
        {
            "role": "user",
            "message": "Hi, I want to manage my work calendar today",
            "expected_response": "Should remember 'work calendar' preference"
        },
        {
            "role": "assistant", 
            "message": "Great! I'll help you with your work calendar. What would you like to do?",
            "expected_response": "Bot confirms work calendar"
        },
        {
            "role": "user",
            "message": "Let me first check what I have scheduled",
            "expected_response": "Query intent"
        },
        {
            "role": "assistant",
            "message": "Here's your current schedule for today...",
            "expected_response": "Shows schedule"
        },
        {
            "role": "user",
            "message": "Now add a team meeting at 3pm for 1 hour",
            "expected_response": "Should use work calendar from earlier context"
        }
    ]
    
    print("Simulating conversation:")
    for i, step in enumerate(conversation_steps):
        print(f"\nStep {i+1}: {step['role'].capitalize()}")
        print(f"Message: {step['message']}")
        
        if step['role'] == 'user':
            # Add user message to conversation
            conversation_state.add_message(chat_id, "user", step['message'])
            
            # Extract intent for user messages
            history = conversation_state.get_conversation_history(chat_id)
            result = await nlp_agent.extract_intent(step['message'], history)
            
            print(f"Extracted Intent: {json.dumps(result, indent=2)}")
            
            # Check for calendar references
            calendar_found = None
            if 'calendar_name' in result:
                calendar_found = result['calendar_name']
            elif result.get('intent') == 'batch_create' and 'events' in result:
                for event in result['events']:
                    if 'calendar_name' in event:
                        calendar_found = event['calendar_name']
                        break
            
            if calendar_found:
                print(f"✅ Calendar detected: '{calendar_found}'")
            else:
                print("❌ No calendar detected")
                
            # For the final message, check if it remembers work calendar
            if i == 4:  # Last user message
                if calendar_found and 'work' in calendar_found.lower():
                    print("✅ SUCCESS: Remembered work calendar from earlier context!")
                else:
                    print("❌ FAILURE: Did not remember work calendar from context")
                    print("Expected: calendar_name should contain 'work'")
        else:
            # Add assistant message to conversation
            conversation_state.add_message(chat_id, "assistant", step['message'])
    
    print("\n" + "=" * 60)
    print("Calendar Context Memory Test Complete")

async def test_calendar_context_switching():
    """Test calendar switching in conversation"""
    print("\n🧪 Testing Calendar Context Switching")
    print("=" * 60)
    
    nlp_agent = NLPAgent()
    chat_id = "context_switching_test"
    
    # Clear conversation
    if chat_id in conversation_state.conversations:
        del conversation_state.conversations[chat_id]
    
    # Simulate switching calendars
    steps = [
        ("user", "I'm working with my personal calendar"),
        ("assistant", "Got it, I'll use your personal calendar"),
        ("user", "Actually, let's switch to my work calendar"),
        ("assistant", "Switching to your work calendar"),
        ("user", "Add a meeting at 2pm"),  # Should use work calendar
    ]
    
    for role, message in steps:
        conversation_state.add_message(chat_id, role, message)
        print(f"{role.capitalize()}: {message}")
        
        if role == "user" and "add" in message.lower():
            history = conversation_state.get_conversation_history(chat_id)
            result = await nlp_agent.extract_intent(message, history)
            
            calendar_name = result.get('calendar_name', 'Not found')
            print(f"Final intent: {json.dumps(result, indent=2)}")
            
            if 'work' in calendar_name.lower():
                print("✅ SUCCESS: Correctly switched to work calendar")
            else:
                print(f"❌ FAILURE: Expected work calendar, got '{calendar_name}'")

async def main():
    await test_calendar_context_memory()
    await test_calendar_context_switching()

if __name__ == "__main__":
    asyncio.run(main())
