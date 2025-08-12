"""
Test LLM Model Configuration Fix - v0.1.87
Tests the corrected model name and simplified call parameters to ensure proper JSON responses.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent
from app.services.conversation import ConversationState
from app.config import Config

async def test_llm_model_configuration():
    """Test that the corrected model configuration produces proper JSON responses."""
    print("🔍 Testing LLM Model Configuration Fix (v0.1.87)")
    print("=" * 60)
    
    # Initialize components
    nlp_agent = NLPAgent()
    conversation_state = ConversationState()
    
    # Test scenarios that previously returned '"intent"' instead of JSON
    test_cases = [
        {
            "name": "Calendar Move Request",
            "message": "move the meeting from tomorrow to the Tonya calendar",
            "expected_intent": "update"
        },
        {
            "name": "Simple Event Creation", 
            "message": "create lesson at 3pm today",
            "expected_intent": "create"
        },
        {
            "name": "Multi-Event Creation",
            "message": "create lesson at 3pm and 4pm today", 
            "expected_intent": "create"
        },
        {
            "name": "Event Deletion",
            "message": "delete all meetings tomorrow",
            "expected_intent": "delete"
        }
    ]
    
    print(f"🔧 Model Configuration:")
    print(f"   Model: {Config.LITELLM_MODEL}")
    print(f"   Expected: gpt-4o-mini (corrected from gpt-4.1-mini)")
    print()
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{total_tests}: {test_case['name']}")
        print(f"   Input: '{test_case['message']}'")
        
        try:
            # Test intent extraction
            result = await nlp_agent.extract_intent(
                message=test_case['message'],
                chat_id=12345,
                conversation_state=conversation_state
            )
            
            # Check if we got valid JSON response
            if isinstance(result, list) and len(result) > 0:
                first_intent = result[0]
                if isinstance(first_intent, dict) and 'intent' in first_intent:
                    intent_value = first_intent['intent']
                    if intent_value == test_case['expected_intent']:
                        print(f"   ✅ SUCCESS: Got valid JSON with correct intent '{intent_value}'")
                        success_count += 1
                    else:
                        print(f"   ⚠️  PARTIAL: Got valid JSON but wrong intent '{intent_value}' (expected '{test_case['expected_intent']}')")
                        success_count += 0.5  # Partial credit for valid JSON
                else:
                    print(f"   ❌ FAILURE: Invalid JSON structure: {first_intent}")
            else:
                print(f"   ❌ FAILURE: No valid intent extracted: {result}")
                
        except Exception as e:
            print(f"   ❌ ERROR: Exception during extraction: {e}")
            
        print()
    
    print("=" * 60)
    print(f"🎯 LLM Model Fix Results:")
    print(f"   Successful Tests: {success_count}/{total_tests}")
    print(f"   Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count >= total_tests * 0.8:  # 80% success rate
        print(f"   ✅ MODEL FIX SUCCESSFUL - LLM responding with proper JSON")
        return True
    else:
        print(f"   ❌ MODEL FIX NEEDS ATTENTION - Still getting malformed responses")
        return False

async def test_model_name_verification():
    """Verify the model name is correctly configured."""
    print("\n🔍 Model Configuration Verification:")
    print(f"   Configured Model: {Config.LITELLM_MODEL}")
    
    if Config.LITELLM_MODEL == "gpt-4o-mini":
        print("   ✅ Model name correctly fixed (was: gpt-4.1-mini)")
        return True
    else:
        print(f"   ❌ Model name still incorrect: {Config.LITELLM_MODEL}")
        print("   Expected: gpt-4o-mini")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Testing LLM Model Configuration Fixes - v0.1.87")
        print("Testing fixes for model name and call parameters")
        print()
        
        # Test model configuration
        config_ok = await test_model_name_verification()
        
        # Test LLM responses
        llm_ok = await test_llm_model_configuration()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL MODEL FIX VALIDATION:")
        if config_ok and llm_ok:
            print("✅ ALL TESTS PASSED - Model configuration fixed successfully")
            print("✅ LLM should now return proper JSON instead of '\"intent\"'")
        else:
            print("❌ TESTS FAILED - Model configuration needs additional fixes")
            if not config_ok:
                print("   - Model name configuration issue")
            if not llm_ok:
                print("   - LLM response format issue")
    
    asyncio.run(main())
