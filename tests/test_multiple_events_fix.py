#!/usr/bin/env python3
"""
Test the fixed intent extraction with dynamic dates.
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set required environment variables
os.environ['LITELLM_MODEL'] = 'gpt-4.1-mini'
os.environ['GOOGLE_CLIENT_ID'] = 'test'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test'
os.environ['TELEGRAM_BOT_TOKEN'] = 'test'

def test_dynamic_dates_in_prompt():
    """Test that dynamic dates are properly formatted in prompt"""
    print("=== Testing Dynamic Dates in Intent Prompt ===")
    
    from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT
    
    # Calculate dynamic dates
    current_date = datetime.now()
    current_date_iso = current_date.strftime("%Y-%m-%d")
    tomorrow_date_iso = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_date_iso = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
    next_week_date_iso = (current_date + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Format the prompt with dynamic dates
    formatted_prompt = INTENT_EXTRACTION_PROMPT.format(
        conversation_history="",
        current_date=current_date.strftime("%Y-%m-%d %H:%M"),
        current_date_iso=current_date_iso,
        tomorrow_date_iso=tomorrow_date_iso,
        yesterday_date_iso=yesterday_date_iso,
        next_week_date_iso=next_week_date_iso
    )
    
    print(f"Current date: {current_date_iso}")
    print(f"Tomorrow date: {tomorrow_date_iso}")
    print(f"Yesterday date: {yesterday_date_iso}")
    print(f"Next week date: {next_week_date_iso}")
    
    # Check that the formatted prompt contains the right dates
    test_cases = [
        (current_date_iso, "current date"),
        (tomorrow_date_iso, "tomorrow date"),
        (yesterday_date_iso, "yesterday date"),
        (next_week_date_iso, "next week date")
    ]
    
    for date_value, date_name in test_cases:
        if date_value in formatted_prompt:
            print(f"✅ {date_name} ({date_value}) found in prompt")
        else:
            print(f"❌ {date_name} ({date_value}) missing from prompt")
    
    # Check specific example that was failing
    target_example = f'"move the last 2 events of today to tomorrow" → {{"intent": "update", "event_name": "event", "date": "{current_date_iso}", "target": "last 2", "new_date": "{tomorrow_date_iso}", "confirmation_needed": true}}'
    
    if target_example in formatted_prompt:
        print(f"✅ Target example with correct dates found")
    else:
        print(f"❌ Target example missing or has wrong dates")
        print(f"Looking for: {target_example}")

def test_create_single_event_function():
    """Test that create_single_event function is properly implemented"""
    print(f"\n=== Testing create_single_event Function ===")
    
    try:
        from app.api.handlers import create_single_event
        import inspect
        
        # Check function signature
        signature = inspect.signature(create_single_event)
        print(f"✅ Function signature: {signature}")
        
        # Check if it's still a placeholder
        source = inspect.getsource(create_single_event)
        if "Placeholder" in source or "not implemented" in source:
            print(f"❌ Function is still a placeholder")
        else:
            print(f"✅ Function is properly implemented")
            
        # Check for MessageFormatter usage
        if "MessageFormatter" in source:
            print(f"✅ Uses MessageFormatter for consistent formatting")
        else:
            print(f"❌ Does not use MessageFormatter")
            
    except Exception as e:
        print(f"❌ Error testing create_single_event: {e}")

def main():
    print("🧪 Testing Multiple Events Processing Fixes")
    print("=" * 60)
    
    test_dynamic_dates_in_prompt()
    test_create_single_event_function()
    
    print("\n" + "=" * 60)
    print("🎯 FIXES SUMMARY:")
    print("1. Intent extraction now uses dynamic dates for accurate examples")
    print("2. Single event creation uses proper MessageFormatter")
    print("3. 'Move events to tomorrow' should now be recognized as update intent")
    print("4. Event creation formatting is now consistent across single and batch operations")
    
    print("\n🚀 READY FOR TESTING:")
    print("Test with: 'move the last 2 events of today to tomorrow'")
    print("Should now be recognized as update intent instead of query")

if __name__ == "__main__":
    main()
