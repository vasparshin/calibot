#!/usr/bin/env python3
"""
Test the specific intent extraction issue found in logs.
"""

import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set required environment variables
os.environ['LITELLM_MODEL'] = 'gpt-4.1-mini'
os.environ['GOOGLE_CLIENT_ID'] = 'test'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test'
os.environ['TELEGRAM_BOT_TOKEN'] = 'test'

def test_intent_extraction_prompt():
    """Test the specific case from logs"""
    print("=== Testing Intent Extraction Issue ===")
    
    from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT
    from datetime import datetime
    
    # Test the exact message from logs
    user_message = "move the last 2 events of today to tomorrow"
    conversation_history = ""
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    
    # Format the prompt exactly as it would be sent to LLM
    formatted_prompt = INTENT_EXTRACTION_PROMPT.format(
        conversation_history=conversation_history,
        current_date=current_date
    )
    
    print(f"User message: '{user_message}'")
    print(f"Current date: {current_date}")
    print(f"\nPrompt examples related to update:")
    
    # Extract lines with update examples
    lines = formatted_prompt.split('\n')
    for line in lines:
        if 'update' in line.lower() and ('move' in line.lower() or 'tomorrow' in line.lower() or 'events' in line.lower()):
            print(f"  {line.strip()}")
    
    print(f"\nLooking for matching patterns:")
    patterns = [
        "move",
        "last 2",
        "events",
        "to tomorrow",
        "today to tomorrow"
    ]
    
    for pattern in patterns:
        if pattern in user_message:
            print(f"  ✅ Found: '{pattern}'")
        else:
            print(f"  ❌ Missing: '{pattern}'")
    
    # Check if our updated examples cover this case
    if "move the last 2 events of today to tomorrow" in formatted_prompt:
        print(f"\n✅ Exact example found in prompt")
    elif "last 2" in formatted_prompt and "tomorrow" in formatted_prompt:
        print(f"\n⚠️  Similar patterns found but not exact match")
    else:
        print(f"\n❌ No matching examples in prompt")
        
    # Check the specific pattern format in prompt
    print(f"\nChecking for date movement patterns:")
    date_patterns = [
        'new_date',
        'move to',
        'events.*tomorrow',
        'today to tomorrow'
    ]
    
    for pattern in date_patterns:
        import re
        if re.search(pattern, formatted_prompt, re.IGNORECASE):
            print(f"  ✅ Found date pattern: '{pattern}'")
        else:
            print(f"  ❌ Missing date pattern: '{pattern}'")

def identify_likely_causes():
    """Identify why intent extraction might be failing"""
    print(f"\n=== Likely Causes Analysis ===")
    
    causes = [
        {
            "cause": "LLM not seeing 'move...to tomorrow' as update intent",
            "solution": "Add more explicit examples with date movement",
            "priority": "HIGH"
        },
        {
            "cause": "Ambiguous phrasing 'last 2 events' not recognized",
            "solution": "Add examples with 'events' instead of specific types",
            "priority": "HIGH"
        },
        {
            "cause": "Missing tomorrow -> ISO date conversion in examples",
            "solution": "Add explicit tomorrow date conversion examples",
            "priority": "MEDIUM"
        },
        {
            "cause": "LLM treating as query because 'events' is generic",
            "solution": "Update prompt to clarify 'move' = update intent",
            "priority": "HIGH"
        }
    ]
    
    for i, cause in enumerate(causes, 1):
        print(f"{i}. {cause['cause']}")
        print(f"   Solution: {cause['solution']}")
        print(f"   Priority: {cause['priority']}\n")

def main():
    print("🔍 Investigating Intent Extraction Issue from Logs")
    print("=" * 60)
    
    test_intent_extraction_prompt()
    identify_likely_causes()
    
    print("=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. Add explicit examples for 'move events to date' patterns")
    print("2. Clarify that 'move' with date = update intent, not query")
    print("3. Add 'events' as valid event_name for generic references")
    print("4. Test with improved prompt examples")

if __name__ == "__main__":
    main()
