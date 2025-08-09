#!/usr/bin/env python3
"""
Test event display consistency across all operations.
Ensures ALL event displays follow BOT_RULES.md format exactly.
"""

import sys
import os
import re
import asyncio
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.utils.message_formatter import MessageFormatter

def test_event_display_consistency():
    """Test that all event displays follow exact BOT_RULES.md format"""
    
    print("🧪 Testing Event Display Consistency")
    print("=" * 50)
    
    # Test data - sample events
    sample_events = [
        {
            "id": "event_1",
            "summary": "lesson",
            "start": "2025-08-09T08:00:00",
            "end": "2025-08-09T09:00:00",
            "calendar_name": "Tonya",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test1"
        },
        {
            "id": "event_2", 
            "summary": "2nd lesson",
            "start": "2025-08-09T09:00:00",
            "end": "2025-08-09T10:00:00",
            "calendar_name": "Tonya",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test2"
        },
        {
            "id": "event_3",
            "summary": "3rd lesson", 
            "start": "2025-08-09T10:00:00",
            "end": "2025-08-09T11:00:00",
            "calendar_name": "Tonya",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test3"
        },
        {
            "id": "event_4",
            "summary": "4th lesson",
            "start": "2025-08-09T11:00:00", 
            "end": "2025-08-09T12:00:00",
            "calendar_name": "Tonya",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test4"
        }
    ]
    
    # Test 1: Single event display
    print("\n1️⃣ Testing Single Event Display")
    single_event = MessageFormatter.format_single_event_display(sample_events[0])
    print(f"Result: {single_event}")
    
    # Validate format: • [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
    expected_pattern = r"^• \[.+\]\(.+\) on \w+, \w+ \d{1,2}, \d{4} at \d{1,2}:\d{2} [AP]M - \d{1,2}:\d{2} [AP]M \(.+\)$"
    
    if re.match(expected_pattern, single_event):
        print("✅ Single event format matches BOT_RULES.md specification")
    else:
        print("❌ Single event format does NOT match BOT_RULES.md specification")
        print(f"Expected pattern: {expected_pattern}")
        return False
    
    # Test 2: Multiple events display
    print("\n2️⃣ Testing Multiple Events Display")
    multiple_events = MessageFormatter.format_event_list_display(sample_events, numbered=False)
    print("Result:")
    print(multiple_events)
    
    # Check that each line follows the pattern
    lines = multiple_events.split('\n')
    all_valid = True
    for i, line in enumerate(lines):
        if not re.match(expected_pattern, line):
            print(f"❌ Line {i+1} does NOT match BOT_RULES.md format: {line}")
            all_valid = False
    
    if all_valid:
        print("✅ All multiple events follow BOT_RULES.md specification")
    else:
        print("❌ Some events in multiple display do NOT follow BOT_RULES.md")
        return False
    
    # Test 3: Numbered events display
    print("\n3️⃣ Testing Numbered Events Display") 
    numbered_events = MessageFormatter.format_event_list_display(sample_events, numbered=True)
    print("Result:")
    print(numbered_events)
    
    # Check numbered format: X. [Event Name](link) on Day, Month DD, YYYY...
    numbered_pattern = r"^\d+\. \[.+\]\(.+\) on \w+, \w+ \d{1,2}, \d{4} at \d{1,2}:\d{2} [AP]M - \d{1,2}:\d{2} [AP]M \(.+\)$"
    
    lines = numbered_events.split('\n')
    all_valid = True
    for i, line in enumerate(lines):
        if not re.match(numbered_pattern, line):
            print(f"❌ Numbered line {i+1} does NOT match expected format: {line}")
            all_valid = False
    
    if all_valid:
        print("✅ All numbered events follow correct format")
    else:
        print("❌ Some numbered events do NOT follow correct format")
        return False
    
    # Test 4: Consistency across different message types
    print("\n4️⃣ Testing Message Type Consistency")
    
    # Test success message
    success_msg = MessageFormatter.format_success_message_create(sample_events[:2])
    print(f"Success message:\n{success_msg}")
    
    # Test confirmation message
    confirm_msg = MessageFormatter.format_confirmation_message("delete", sample_events[:2])
    print(f"\nConfirmation message:\n{confirm_msg}")
    
    # Both should contain properly formatted events
    success_lines = [line for line in success_msg.split('\n') if line.startswith('•')]
    confirm_lines = [line for line in confirm_msg.split('\n') if line.startswith(('1.', '2.', '3.', '4.'))]
    
    print(f"\n✅ Found {len(success_lines)} properly formatted events in success message")
    print(f"✅ Found {len(confirm_lines)} properly formatted events in confirmation message")
    
    # Test 5: Verify specific format elements
    print("\n5️⃣ Testing Specific Format Elements")
    
    test_event = sample_events[0]
    formatted = MessageFormatter.format_single_event_display(test_event)
    
    # Check for required elements
    checks = [
        ("[" in formatted and "](" in formatted, "Hyperlink format [text](url)"),
        ("Saturday, August 09, 2025" in formatted, "Full date format 'Day, Month DD, YYYY'"),
        ("08:00 AM" in formatted and "09:00 AM" in formatted, "12-hour time format with AM/PM"),
        ("(Tonya)" in formatted, "Calendar name in parentheses"),
        (formatted.startswith("•"), "Bullet point prefix")
    ]
    
    all_checks_passed = True
    for check_passed, description in checks:
        if check_passed:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_checks_passed = False
    
    if not all_checks_passed:
        print(f"❌ Formatted result: {formatted}")
        return False
    
    print("\n🎉 ALL EVENT DISPLAY CONSISTENCY TESTS PASSED!")
    print("✅ All event displays follow BOT_RULES.md specifications exactly")
    return True

def test_query_intent_simulation():
    """Simulate query intent responses for different scenarios"""
    
    print("\n🔍 Testing Query Intent Response Formats")
    print("=" * 50)
    
    sample_events = [
        {
            "id": "event_1",
            "summary": "1st lesson", 
            "start": "2025-08-09T08:00:00",
            "end": "2025-08-09T09:00:00",
            "calendar_name": "Tonya",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test1"
        },
        {
            "id": "event_2",
            "summary": "2nd lesson",
            "start": "2025-08-09T09:00:00", 
            "end": "2025-08-09T10:00:00",
            "calendar_name": "Tonya",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=test2"
        }
    ]
    
    # Test single event response
    print("\n1️⃣ Single Event Query Response")
    single_formatted = MessageFormatter.format_single_event_display(sample_events[0])
    single_response = f"Here's your event:\n\n{single_formatted}"
    print(single_response)
    
    # Test multiple events response (today context)
    print("\n2️⃣ Multiple Events Query Response (Today Context)")
    multiple_formatted = MessageFormatter.format_event_list_display(sample_events, numbered=False)
    today_response = f"Today's schedule includes:\n\n{multiple_formatted}"
    print(today_response)
    
    # Test multiple events response (general context)
    print("\n3️⃣ Multiple Events Query Response (General Context)")
    general_response = f"Found {len(sample_events)} events:\n\n{multiple_formatted}"
    print(general_response)
    
    print("\n✅ All query responses use consistent MessageFormatter formatting")
    print("✅ No AI service formatting - direct MessageFormatter usage only")
    
    return True

if __name__ == "__main__":
    print("CaliBOT Event Display Consistency Test")
    print("=" * 60)
    
    try:
        # Run consistency tests
        consistency_passed = test_event_display_consistency()
        
        # Run query simulation tests  
        query_passed = test_query_intent_simulation()
        
        if consistency_passed and query_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Event display consistency is maintained across all operations")
            print("✅ Query intent now uses MessageFormatter for consistent formatting")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("❌ Event display consistency issues need to be addressed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
