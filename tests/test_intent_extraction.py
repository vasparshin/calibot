#!/usr/bin/env python3
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def test_intent_extraction():
    print("🔍 Testing intent extraction for multiple lessons...")
    
    try:
        from app.agent.nlp_agent import NLPAgent
        agent = NLPAgent()
        
        test_messages = [
            'tonya will have 3 lessons tomorrow, 9, 10 and 12am',
            'please schedule 3 lessons in tonyas calendar tomorrow, 9, 10 and 12am',
            'schedule 3 lessons for 9am, 10am, and 12pm tomorrow'
        ]
        
        for msg in test_messages:
            print(f'\n📝 Testing: "{msg}"')
            try:
                result = await agent.extract_intent(msg, [])
                print(f'  Intent: {result.get("intent")}')
                print(f'  Event name: {result.get("event_name")}')
                print(f'  Start time: {result.get("start_time")}')
                print(f'  End time: {result.get("end_time")}')
                print(f'  Events array: {result.get("events")}')
                print(f'  Description: {result.get("description")}')
                
                # Check if it's detecting multiple events
                if result.get("intent") == "batch_create" or result.get("events"):
                    print(f'  ✅ Detected as batch creation')
                elif isinstance(result.get("start_time"), list):
                    print(f'  ✅ Detected multiple start times')
                else:
                    print(f'  ❌ Only detected single event')
                    
            except Exception as e:
                print(f'  ❌ Error: {e}')
            print('-' * 60)
    
    except ImportError as e:
        print(f"Import error: {e}")
        print("Skipping intent extraction test")

if __name__ == "__main__":
    asyncio.run(test_intent_extraction())
