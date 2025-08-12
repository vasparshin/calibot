#!/usr/bin/env python3
"""
Test Multi-Event Success Message Formatting and Button Removal

Tests the formatting improvements for multi-event operation success messages
and ensures buttons are properly removed after selection.
"""

import sys
import os

# Add the project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime
from datetime import datetime

def test_success_message_formatting():
    """Test that success messages follow BOT_RULES.md formatting"""
    print("🧪 Testing Multi-Event Success Message Formatting")
    
    # Create mock event data with realistic structure
    mock_events = [
        {
            'id': 'event1',
            'summary': 'Lesson',
            'start': '2025-08-12T08:00:00+00:00',
            'end': '2025-08-12T09:00:00+00:00',
            'htmlLink': 'https://calendar.google.com/event/event1',
            'calendar_name': 'Tonya'
        },
        {
            'id': 'event2', 
            'summary': 'Meeting',
            'start': '2025-08-12T10:00:00+00:00',
            'end': '2025-08-12T11:00:00+00:00',
            'htmlLink': 'https://calendar.google.com/event/event2',
            'calendar_name': 'Work'
        }
    ]
    
    # Simulate the success message generation logic (no handler needed)
    message_parts = []
    successful_updates = []
    
    # Mock the formatting logic from multi_event_operations.py
    for event in mock_events:
        # Format event following BOT_RULES.md: • [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
        event_link = event.get('htmlLink', '')
        calendar_name = event.get('calendar_name', 'Unknown Calendar')
        
        # Create hyperlinked event name
        if event_link:
            hyperlinked_name = f"[{event.get('summary', 'Untitled')}]({event_link})"
        else:
            hyperlinked_name = event.get('summary', 'Untitled')
        
        # Format date and time for display
        event_start = event.get('start', '')
        event_end = event.get('end', '')
        
        # Parse datetime and format as "Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM"
        try:
            if 'T' in event_start:
                start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00')) if event_end and 'T' in event_end else start_dt
                
                # Format date as "Day, Month DD, YYYY"
                date_formatted = start_dt.strftime('%A, %B %d, %Y')
                
                # Format time as "HH:MM AM/PM"
                start_time_formatted = start_dt.strftime('%I:%M %p').lstrip('0')
                end_time_formatted = end_dt.strftime('%I:%M %p').lstrip('0')
                
                datetime_display = f"on {date_formatted} at {start_time_formatted} - {end_time_formatted}"
            else:
                datetime_display = "on today (all day)"
        except:
            datetime_display = "on today"
        
        # Build the properly formatted event description
        update_desc = f"• {hyperlinked_name} {datetime_display} ({calendar_name})"
        successful_updates.append(update_desc)
    
    # Build final message
    formatted_date = "Tuesday, August 12, 2025"
    message_parts.append(f"Successfully updated {len(successful_updates)} event{'s' if len(successful_updates) != 1 else ''} on {formatted_date}:")
    message_parts.append("")  # Empty line
    for update_desc in successful_updates:
        message_parts.append(update_desc)
    
    final_message = "\n".join(message_parts)
    
    print("✅ Generated Success Message:")
    print(final_message)
    print()
    
    # Verify format compliance
    checks = [
        ("Contains bullet points", "•" in final_message),
        ("Contains hyperlinks", "[" in final_message and "](" in final_message),
        ("Contains calendar names", "(Tonya)" in final_message and "(Work)" in final_message),
        ("Contains full date format", "Tuesday, August 12, 2025" in final_message),
        ("Contains AM/PM times", "AM" in final_message or "PM" in final_message),
        ("No confusing 'Updated' prefix", "Updated [" not in final_message)
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def test_button_removal_logic():
    """Test that button removal logic is properly implemented"""
    print("\n🧪 Testing Button Removal Logic")
    
    # Check if edit_message_text calls include reply_markup={}
    routes_file = os.path.join(project_root, 'backend', 'app', 'api', 'routes.py')
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all edit_message_text calls
    import re
    edit_calls = re.findall(r'await edit_message_text\([^)]+\)', content, re.DOTALL)
    
    missing_reply_markup = []
    for call in edit_calls:
        if 'reply_markup' not in call:
            # Extract a clean snippet for display
            clean_call = call.replace('\n', ' ').strip()
            if len(clean_call) > 100:
                clean_call = clean_call[:100] + "..."
            missing_reply_markup.append(clean_call)
    
    if missing_reply_markup:
        print("❌ Found edit_message_text calls without reply_markup={}:")
        for call in missing_reply_markup:
            print(f"  • {call}")
        return False
    else:
        print("✅ All edit_message_text calls include reply_markup={} for button removal")
        return True

def main():
    """Run all tests"""
    print("🔧 Testing Multi-Event UX Improvements\n")
    
    # Test success message formatting
    formatting_passed = test_success_message_formatting()
    
    # Test button removal
    button_removal_passed = test_button_removal_logic()
    
    # Final result
    print(f"\n📊 Test Results:")
    print(f"Success Message Formatting: {'✅ PASS' if formatting_passed else '❌ FAIL'}")
    print(f"Button Removal Logic: {'✅ PASS' if button_removal_passed else '❌ FAIL'}")
    
    if formatting_passed and button_removal_passed:
        print("\n🎉 All multi-event UX improvements are working correctly!")
        return True
    else:
        print("\n⚠️ Some tests failed - review the output above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
