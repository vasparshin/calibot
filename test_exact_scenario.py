#!/usr/bin/env python3
"""
Quick test to verify the exact user scenario works
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.agent.nlp_agent import NLPAgent

async def test_exact_user_scenario():
    """Test the exact message that was failing in the logs"""
    
    print("🧪 Testing exact user scenario from logs")
    print("="*60)
    
    # The exact message from the logs that was failing
    user_message = "please create 1 hr events for today for 8am, 10 am, 11, 12, 13, 14 each titles \"lesson for tonyas calendar\""
    
    print(f"User message: {user_message}")
    print()
    
    try:
        nlp_agent = NLPAgent()
        result = await nlp_agent.extract_intent(user_message, [])
        
        print(f"✅ Result: {result}")
        print()
        
        if result.get('intent') == 'batch_create':
            events = result.get('events', [])
            print(f"🎉 SUCCESS! Detected {len(events)} events:")
            for i, event in enumerate(events):
                print(f"  {i+1}. {event['event_name']} at {event['start_time']}-{event['end_time']}")
        elif result.get('intent') == 'create':
            print(f"❌ PROBLEM: Only single event detected")
            print(f"   Event: {result.get('event_name')} at {result.get('start_time')}-{result.get('end_time')}")
        else:
            print(f"❌ UNEXPECTED: Intent = {result.get('intent')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_exact_user_scenario())
