#!/usr/bin/env python3
"""
Debug Intent Extraction - Tests the exact intent extraction logic to identify the issue
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import conversation_state

async def test_intent_extraction():
    """Test intent extraction with the problematic message."""
    
    print("🔍 DEBUGGING INTENT EXTRACTION")
    print("=" * 50)
    
    # Initialize the NLP agent
    nlp_agent = NLPAgent()
    
    # Test messages that should trigger different intents
    test_cases = [
        {
            "message": "move the last 2 events of today to tomorrow",
            "expected": "update",
            "description": "Move events to different date"
        },
        {
            "message": "show me tomorrow's schedule",
            "expected": "query", 
            "description": "Query for events"
        },
        {
            "message": "create an event called 'Test Meeting' tomorrow at 3pm",
            "expected": "create",
            "description": "Create single event"
        }
    ]
    
    chat_id = 12345
    conversation_history = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"📝 Message: '{test_case['message']}'")
        print(f"🎯 Expected Intent: {test_case['expected']}")
        
        try:
            # Test relevancy check first
            print("\n📋 Step 1: Checking relevancy...")
            relevancy_result = await nlp_agent.check_relevancy(test_case['message'], conversation_history)
            print(f"   Relevancy: {relevancy_result}")
            
            if not relevancy_result.get("relevant"):
                print("   ❌ Message deemed irrelevant - this might be the issue!")
                continue
            
            # Test intent extraction
            print("\n📋 Step 2: Extracting intent...")
            intent_result = await nlp_agent.extract_intent(test_case['message'], conversation_history)
            print(f"   Intent Result: {intent_result}")
            
            extracted_intent = intent_result.get("intent") if isinstance(intent_result, dict) else "UNKNOWN"
            print(f"   Extracted Intent: {extracted_intent}")
            
            if extracted_intent == test_case['expected']:
                print("   ✅ CORRECT - Intent matches expected")
            else:
                print(f"   ❌ INCORRECT - Expected '{test_case['expected']}', got '{extracted_intent}'")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_intent_extraction())
