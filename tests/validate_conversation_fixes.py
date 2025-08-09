#!/usr/bin/env python3
"""
Quick validation that the specific conversation issues are fixed.
Tests the exact patterns mentioned in the user's message.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_no_truncation():
    """Test that message formatters don't truncate event lists"""
    from app.utils.message_formatter import MessageFormatter
    
    # Create 7 events like in the conversation
    events = []
    for i in range(7):
        event = {
            'summary': 'lesson',
            'start': f'2025-08-10T{8+i:02d}:00:00Z',
            'end': f'2025-08-10T{9+i:02d}:00:00Z',
            'calendar_name': 'Tonya',
            'id': f'event{i}',
            'htmlLink': f'https://calendar.google.com/calendar/event?eid=event{i}'
        }
        events.append(event)
    
    # Test confirmation message
    confirmation = MessageFormatter.format_confirmation_message("delete", events, 7)
    
    print("🔍 Testing truncation fix:")
    print(f"Events created: {len(events)}")
    print(f"Events in message: {confirmation.count('[Lesson]')}")
    
    # CRITICAL: Should show ALL 7 events, not truncate
    assert confirmation.count('[Lesson]') == 7, f"Should show all 7 events, found {confirmation.count('[Lesson]')}"
    assert '... and' not in confirmation, "Should not contain truncation text"
    assert 'more events' not in confirmation, "Should not contain 'more events'"
    
    print("✅ FIXED: No truncation - all 7 events shown")
    return True

def test_hyperlinks():
    """Test that all events have hyperlinks"""
    from app.utils.message_formatter import MessageFormatter
    
    event = {
        'summary': 'lesson',
        'start': '2025-08-10T08:00:00Z',
        'end': '2025-08-10T09:00:00Z',
        'calendar_name': 'Tonya',
        'id': 'event123',
        'htmlLink': 'https://calendar.google.com/calendar/event?eid=event123'
    }
    
    # Test single event display
    event_display = MessageFormatter.format_single_event_display(event)
    
    print("\n🔍 Testing hyperlink fix:")
    print(f"Event display: {event_display}")
    
    # CRITICAL: Should have hyperlink, not plain text
    assert '[Lesson](' in event_display, "Event name should be hyperlinked"
    assert 'https://calendar.google.com/' in event_display, "Should contain calendar URL"
    assert event_display.startswith('• ['), "Should start with bullet and hyperlink"
    
    # Should NOT be the old format
    assert not event_display.startswith('• lesson -'), "Should not use old plain text format"
    
    print("✅ FIXED: All events have hyperlinks")
    return True

def test_inline_keyboards():
    """Test that inline keyboards are available"""
    from app.utils.inline_keyboard import InlineKeyboardHelper
    
    print("\n🔍 Testing inline keyboard fix:")
    
    # Test multi-event keyboard
    keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("delete")
    
    print(f"Keyboard structure: {keyboard}")
    
    # Should have the expected buttons
    buttons = keyboard['inline_keyboard']
    assert len(buttons) == 2, "Should have 2 rows of buttons"
    assert len(buttons[0]) == 2, "First row should have 2 buttons"
    assert len(buttons[1]) == 1, "Second row should have 1 button"
    
    # Check button text matches BOT_RULES.md
    assert buttons[0][0]['text'] == '🔄 All', "First button should be 'All'"
    assert buttons[0][1]['text'] == '1️⃣ One by One', "Second button should be 'One by One'"
    assert buttons[1][0]['text'] == '❌ Cancel', "Third button should be 'Cancel'"
    
    print("✅ FIXED: Inline keyboards implemented")
    return True

def test_conversation_examples():
    """Test the exact patterns from the user's conversation"""
    from app.utils.message_formatter import MessageFormatter
    
    print("\n🔍 Testing exact conversation patterns:")
    
    # Recreate the exact scenario: 7 lessons on Sunday Aug 10
    events = [
        {
            'summary': 'lesson',
            'start': '2025-08-10T08:00:00Z',
            'end': '2025-08-10T09:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event1',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event1'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T09:00:00Z',
            'end': '2025-08-10T10:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event2',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event2'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T10:00:00Z',
            'end': '2025-08-10T11:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event3',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event3'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T12:00:00Z',
            'end': '2025-08-10T13:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event4',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event4'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T13:00:00Z',
            'end': '2025-08-10T14:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event5',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event5'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T14:00:00Z',
            'end': '2025-08-10T15:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event6',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event6'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T16:00:00Z',
            'end': '2025-08-10T17:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event7',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event7'
        }
    ]
    
    # Generate the new confirmation message
    confirmation = MessageFormatter.format_confirmation_message("delete", events, 7)
    print("New confirmation message:")
    print(confirmation)
    print()
    
    # Generate success message
    success = MessageFormatter.format_success_message_delete(7, '2025-08-10')
    print("New success message:")
    print(success)
    print()
    
    # Verify fixes
    checks = [
        (confirmation.count('[Lesson]') == 7, "All 7 events shown with hyperlinks"),
        ('... and' not in confirmation, "No truncation text"),
        ('Sunday, August 10, 2025' in confirmation, "Proper date format"),
        ('Choose an option:' in confirmation, "Clear action options"),
        (success == "Successfully deleted all 7 events on Sunday, August 10, 2025!", "Proper success message")
    ]
    
    for check, description in checks:
        if check:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 CaliBOT Message Consistency Validation")
    print("=" * 50)
    print("Testing fixes for specific conversation issues...\n")
    
    try:
        test_no_truncation()
        test_hyperlinks()
        test_inline_keyboards()
        test_conversation_examples()
        
        print("\n" + "=" * 50)
        print("🎉 ALL CONVERSATION ISSUES FIXED!")
        print("✅ No more truncated event lists")
        print("✅ All events have hyperlinks")
        print("✅ Inline keyboards implemented")
        print("✅ Consistent professional formatting")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
