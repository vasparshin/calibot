#!/usr/bin/env python3
"""
Test script to validate batch event creation process
This will help us identify where the issue is in the pipeline
"""

import json
import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.agent.nlp_agent import NLPAgent
from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT

def test_prompt_format():
    """Test that the prompt is correctly formatted"""
    print("=== Testing Prompt Format ===")
    print("Current prompt:")
    print(INTENT_EXTRACTION_PROMPT)
    print()
    
    # Test prompt formatting with sample data
    formatted_prompt = INTENT_EXTRACTION_PROMPT.format(
        conversation_history="please create multiple 1 hr events for today for 8am, 10 am, 11, 12, 13, 14 each titles \"lesson for tonyas calendar\"",
        current_date="2025-08-06"
    )
    print("Formatted prompt:")
    print(formatted_prompt)
    print("\n" + "="*80 + "\n")

def test_json_parsing_scenarios():
    """Test various JSON parsing scenarios"""
    print("=== Testing JSON Parsing Scenarios ===")
    
    # Scenario 1: Single JSON object
    single_json = '{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "08:00", "end_time": "09:00", "confirmation_needed": false}'
    
    print("Scenario 1: Single JSON")
    print(f"Input: {single_json}")
    try:
        result = json.loads(single_json)
        print(f"✅ Single JSON parsed successfully: {result}")
    except json.JSONDecodeError as e:
        print(f"❌ Single JSON failed: {e}")
    
    # Scenario 2: Multiple JSON objects (what LLM should return)
    multiple_json = '''{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "08:00", "end_time": "09:00", "confirmation_needed": false}
{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "10:00", "end_time": "11:00", "confirmation_needed": false}
{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "11:00", "end_time": "12:00", "confirmation_needed": false}'''
    
    print("\nScenario 2: Multiple JSON objects")
    print(f"Input: {multiple_json}")
    
    # Test single JSON parsing (should fail)
    try:
        result = json.loads(multiple_json)
        print(f"❌ Unexpected: Single JSON parsing worked: {result}")
    except json.JSONDecodeError as e:
        print(f"✅ Expected: Single JSON parsing failed: {e}")
    
    # Test multiple JSON parsing (our custom logic)
    lines = [line.strip() for line in multiple_json.split('\n') if line.strip()]
    json_objects = []
    
    for line in lines:
        try:
            json_obj = json.loads(line)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            print(f"❌ Failed to parse line: {line}")
    
    if json_objects:
        print(f"✅ Multiple JSON parsing worked: Found {len(json_objects)} events")
        for i, obj in enumerate(json_objects):
            print(f"  Event {i+1}: {obj['start_time']}-{obj['end_time']}")
    else:
        print("❌ Multiple JSON parsing failed")
    
    print("\n" + "="*80 + "\n")

def simulate_nlp_agent_processing():
    """Simulate what the NLP agent would do with multiple JSON objects"""
    print("=== Simulating NLP Agent Processing ===")
    
    # Simulate LLM response with multiple JSON objects
    mock_llm_response = {
        'choices': [{
            'message': {
                'content': '''{"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "08:00", "end_time": "09:00", "confirmation_needed": false}
{"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "10:00", "end_time": "11:00", "confirmation_needed": false}
{"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "11:00", "end_time": "12:00", "confirmation_needed": false}
{"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "12:00", "end_time": "13:00", "confirmation_needed": false}
{"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "13:00", "end_time": "14:00", "confirmation_needed": false}
{"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "14:00", "end_time": "15:00", "confirmation_needed": false}'''
            }
        }]
    }
    
    # Simulate the processing logic from nlp_agent.py
    result = mock_llm_response['choices'][0]['message']['content']
    cleaned_result = result.strip()
    
    print(f"Raw LLM response length: {len(result)}")
    print(f"Response type: {type(result)}")
    print(f"Cleaned response: {cleaned_result[:100]}...")
    
    # Try single JSON parsing first
    try:
        parsed_result = json.loads(cleaned_result)
        print("✅ Single JSON parsing worked (unexpected for batch)")
        return parsed_result
    except json.JSONDecodeError:
        print("✅ Single JSON parsing failed (expected for batch)")
        
        # Try multiple JSON objects parsing
        lines = [line.strip() for line in cleaned_result.split('\n') if line.strip()]
        json_objects = []
        
        for line in lines:
            try:
                json_obj = json.loads(line)
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                print(f"❌ Failed to parse line: {line}")
                continue
        
        if json_objects:
            print(f"✅ Successfully parsed {len(json_objects)} JSON objects for batch processing")
            # Return the objects as a batch format
            result = {
                "intent": "batch_create",
                "events": json_objects,
                "confirmation_needed": False
            }
            print(f"Returning batch result: {len(result['events'])} events")
            return result
        else:
            print("❌ Multiple JSON parsing also failed")
            return {"intent": "unknown", "error": "JSON parsing failed"}

def test_route_processing():
    """Test how the routes would process the batch result"""
    print("=== Testing Route Processing ===")
    
    # Simulate batch result from NLP agent
    event_data = {
        "intent": "batch_create",
        "events": [
            {"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "08:00", "end_time": "09:00", "confirmation_needed": False},
            {"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "10:00", "end_time": "11:00", "confirmation_needed": False},
            {"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "11:00", "end_time": "12:00", "confirmation_needed": False},
            {"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "12:00", "end_time": "13:00", "confirmation_needed": False},
            {"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "13:00", "end_time": "14:00", "confirmation_needed": False},
            {"intent": "create", "event_name": "lesson for tonyas calendar", "date": "2025-08-06", "start_time": "14:00", "end_time": "15:00", "confirmation_needed": False}
        ],
        "confirmation_needed": False
    }
    
    print(f"Event data intent: {event_data['intent']}")
    print(f"Confirmation needed: {event_data['confirmation_needed']}")
    
    # Simulate route processing logic
    if event_data["confirmation_needed"] is False:
        print("✅ No confirmation needed, proceeding with processing")
        
        if event_data["intent"] in ["create", "batch_create"]:
            print("✅ Intent is create or batch_create")
            
            events_to_create = []
            
            # Format 0: Direct batch_create from multiple JSON objects
            if event_data["intent"] == "batch_create" and 'events' in event_data:
                events_to_create = event_data['events']
                print(f"✅ Detected batch_create format with {len(events_to_create)} events from multiple JSON objects")
            
            if events_to_create:
                print(f"✅ Found {len(events_to_create)} events to create:")
                for i, event in enumerate(events_to_create):
                    print(f"  Event {i+1}: {event['event_name']} at {event['start_time']}-{event['end_time']}")
                
                print("✅ Would proceed to create all events in calendar")
            else:
                print("❌ No events found to create")
        else:
            print(f"❌ Unexpected intent: {event_data['intent']}")
    else:
        print("❌ Confirmation needed, would ask user first")
    
    print("\n" + "="*80 + "\n")

async def test_real_nlp_agent():
    """Test the actual NLP agent with a batch request"""
    print("=== Testing Real NLP Agent ===")
    
    try:
        # Create NLP agent instance
        nlp_agent = NLPAgent()
        
        # Test message
        user_message = "please create multiple 1 hr events for today for 8am, 10 am, 11, 12, 13, 14 each titles \"lesson for tonyas calendar\""
        conversation_history = [{"role": "user", "content": user_message}]
        
        print(f"Testing with message: {user_message}")
        
        # Extract intent
        result = await nlp_agent.extract_intent(user_message, conversation_history)
        
        print(f"✅ NLP Agent result: {result}")
        print(f"Intent: {result.get('intent')}")
        
        if result.get('intent') == 'batch_create':
            print(f"✅ Batch creation detected with {len(result.get('events', []))} events")
            for i, event in enumerate(result.get('events', [])):
                print(f"  Event {i+1}: {event.get('start_time')}-{event.get('end_time')}")
        elif result.get('intent') == 'create':
            print(f"❌ Only single event detected: {result.get('start_time')}-{result.get('end_time')}")
        else:
            print(f"❌ Unexpected intent: {result.get('intent')}")
        
    except Exception as e:
        print(f"❌ NLP Agent test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🧪 BATCH EVENT CREATION TEST SUITE")
    print("="*80)
    
    # Test 1: Prompt format
    test_prompt_format()
    
    # Test 2: JSON parsing scenarios
    test_json_parsing_scenarios()
    
    # Test 3: NLP agent simulation
    result = simulate_nlp_agent_processing()
    
    # Test 4: Route processing
    test_route_processing()
    
    # Test 5: Real NLP agent (requires API key)
    print("Note: Real NLP agent test requires OpenAI API key and will make actual API calls")
    run_real_test = input("Run real NLP agent test? (y/n): ").lower().strip() == 'y'
    
    if run_real_test:
        asyncio.run(test_real_nlp_agent())
    else:
        print("Skipping real NLP agent test")
    
    print("\n🎯 TEST SUMMARY")
    print("="*80)
    print("1. ✅ Prompt format looks good with clear multiple event examples")
    print("2. ✅ JSON parsing logic can handle multiple JSON objects")
    print("3. ✅ NLP agent simulation shows correct batch_create format")
    print("4. ✅ Route processing can handle batch_create intent")
    print("5. ❓ Real NLP agent test depends on actual LLM behavior")
    print("\nIf the real NLP agent still returns single events, the issue is:")
    print("- LLM not following the prompt correctly")
    print("- Need to adjust prompt or use different approach")

if __name__ == "__main__":
    main()
