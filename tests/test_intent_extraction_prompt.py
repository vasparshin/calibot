#!/usr/bin/env python3
"""
Test Intent Extraction for "Last 3" Scenarios

Tests what the LLM should extract for "move the last 3 lessons yesterday 1 hr later"
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT

def test_prompt_examples():
    """Test what the prompt should extract"""
    print("🧪 Testing Intent Extraction Prompt for 'Last 3' Scenarios")
    
    # Current date: August 13, 2025
    # Yesterday: August 12, 2025
    current_date = "2025-08-13 07:20"
    yesterday = "2025-08-12"
    
    # Test cases
    test_cases = [
        "move the last 3 lessons yesterday 1 hr later",
        "move last 3 lessons 1 hr later", 
        "delete the first 2 meetings today",
        "change the last lesson to 5pm"
    ]
    
    expected_results = [
        {"intent": "update", "event_name": "lesson", "date": yesterday, "target": "last 3", "time_shift": "1 hour", "confirmation_needed": True},
        {"intent": "update", "event_name": "lesson", "target": "last 3", "time_shift": "1 hour", "confirmation_needed": True},
        {"intent": "delete", "event_name": "meeting", "target": "first 2", "confirmation_needed": True},
        {"intent": "update", "event_name": "lesson", "target": "last", "new_start_time": "17:00", "confirmation_needed": True}
    ]
    
    print(f"📅 Current Date: {current_date}")
    print(f"📅 Yesterday: {yesterday}")
    print()
    
    for i, (user_message, expected) in enumerate(zip(test_cases, expected_results), 1):
        print(f"🔤 Test {i}: \"{user_message}\"")
        print(f"   Expected: {expected}")
        
        # Check if the prompt has the right example
        prompt_content = INTENT_EXTRACTION_PROMPT.format(
            conversation_history="", 
            current_date=current_date
        )
        
        # Verify the prompt contains relevant examples
        has_last_3_example = "last 3" in prompt_content
        has_numeric_target_rule = "preserve numbers in target" in prompt_content.lower()
        has_yesterday_rule = "yesterday" in prompt_content.lower()
        
        checks = [
            ("Contains 'last 3' example", has_last_3_example),
            ("Has numeric target preservation rule", has_numeric_target_rule), 
            ("Has yesterday date rule", has_yesterday_rule)
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        print()
    
    # Show the actual prompt for review
    print("📋 Current Prompt Content:")
    print("=" * 50)
    sample_prompt = INTENT_EXTRACTION_PROMPT.format(
        conversation_history="User: what's my schedule today\nAssistant: You have 3 meetings today",
        current_date=current_date
    )
    print(sample_prompt)
    
    return True

def main():
    """Run the prompt analysis"""
    print("🔧 Analyzing Intent Extraction Prompt for 'Last 3' Support\n")
    
    test_prompt_examples()
    
    print("\n💡 Key Points:")
    print("- The LLM should extract exactly what's in the EXAMPLES section")
    print("- If the prompt is correct but LLM still fails, it's an LLM reasoning issue")
    print("- If the prompt is missing examples, that's the root cause")
    print("- Check production logs for 'Raw LLM response' to see actual extraction")

if __name__ == "__main__":
    main()
