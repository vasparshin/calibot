#!/usr/bin/env python3
"""
Test script to validate NLP agent fallback fixes
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.agent.nlp_agent import NLPAgent

async def test_nlp_fallbacks():
    """Test the enhanced NLP agent fallback logic"""
    
    print("Testing NLP Agent Fallback Logic")
    print("=" * 50)
    
    agent = NLPAgent()
    
    # Test the specific failing scenarios from the user logs
    test_cases = [
        {
            "message": "Move the last two lessons forward an hr",
            "expected_intent": "update",
            "expected_fields": ["event_name", "time_shift", "target"]
        },
        {
            "message": "Delete the last lesson today", 
            "expected_intent": "delete",
            "expected_fields": ["event_name", "target"]
        },
        {
            "message": "Move the 2nd lesson today to tomorrow",
            "expected_intent": "update", 
            "expected_fields": ["event_name", "new_date"]
        },
        {
            "message": "Move the lessons end time to an HR after the start time instead of 30 min",
            "expected_intent": "update",
            "expected_fields": ["event_name"]
        },
        {
            "message": "What's the schedule for today",
            "expected_intent": "query",
            "expected_fields": ["date"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['message']}")
        print("-" * 40)
        
        try:
            # Test the intent extraction
            result = await agent.extract_intent(test_case['message'], [])
            
            print(f"Result: {result}")
            print(f"Type: {type(result)}")
            
            # Validate the result
            success = True
            issues = []
            
            # Check if result is a dict
            if not isinstance(result, dict):
                success = False
                issues.append(f"Result is not a dict: {type(result)}")
            else:
                # Check intent
                if result.get("intent") != test_case["expected_intent"]:
                    success = False
                    issues.append(f"Wrong intent: got '{result.get('intent')}', expected '{test_case['expected_intent']}'")
                
                # Check required fields exist
                for field in test_case["expected_fields"]:
                    if field not in result:
                        issues.append(f"Missing expected field: {field}")
                
                # Check for basic required fields
                if "intent" not in result:
                    success = False
                    issues.append("Missing 'intent' field")
            
            # Report results
            if success and not issues:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                for issue in issues:
                    print(f"   - {issue}")
            
            results.append({
                "test": test_case['message'],
                "success": success,
                "issues": issues,
                "result": result
            })
            
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results.append({
                "test": test_case['message'],
                "success": False,
                "issues": [f"Exception: {e}"],
                "result": None
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The NLP fallback fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Issues found:")
        for result in results:
            if not result["success"]:
                print(f"\n❌ {result['test']}")
                for issue in result["issues"]:
                    print(f"   - {issue}")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(test_nlp_fallbacks())
    sys.exit(0 if success else 1)
