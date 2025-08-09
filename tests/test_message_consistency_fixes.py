"""
Test for message consistency fixes per BOT_RULES.md specifications.
Validates that all success/confirmation messages follow the new standards.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.utils.message_formatter import MessageFormatter
from app.utils.inline_keyboard import InlineKeyboardHelper


def test_message_formatter_consistency():
    """Test that MessageFormatter creates consistent messages per BOT_RULES.md"""
    
    # Sample event data
    events = [
        {
            'summary': 'lesson',
            'start': '2025-08-10T08:00:00Z',
            'end': '2025-08-10T09:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event123',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event123'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T09:00:00Z',
            'end': '2025-08-10T10:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event456',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event456'
        },
        {
            'summary': 'lesson',
            'start': '2025-08-10T10:00:00Z',
            'end': '2025-08-10T11:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event789',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event789'
        }
    ]
    
    print("Testing Event Display Formatting:")
    print("=" * 50)
    
    # Test single event display
    single_event_display = MessageFormatter.format_single_event_display(events[0])
    print(f"Single event: {single_event_display}")
    
    # Verify format matches BOT_RULES.md:
    # • [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
    assert single_event_display.startswith('• [')
    assert '](https://calendar.google.com/' in single_event_display
    assert 'Sunday, August 10, 2025' in single_event_display  # Corrected day
    assert '08:00 AM - 09:00 AM' in single_event_display
    assert '(Tonya)' in single_event_display
    
    print("\n✅ Single event format correct")
    
    # Test success message for creation
    create_success = MessageFormatter.format_success_message_create(events, 3)
    print(f"\nCreate success message:\n{create_success}")
    
    # Verify all events are shown (no truncation)
    assert 'Successfully created 3 events:' in create_success
    assert create_success.count('[Lesson]') == 3  # All events shown
    assert '... and' not in create_success  # No truncation
    
    print("✅ Create success message correct")
    
    # Test confirmation message
    confirmation = MessageFormatter.format_confirmation_message("delete", events, 3)
    print(f"\nConfirmation message:\n{confirmation}")
    
    # Verify all events are shown with hyperlinks
    assert 'Found 3 events to delete:' in confirmation
    assert confirmation.count('[Lesson]') == 3  # All events shown
    assert '... and' not in confirmation  # No truncation
    assert 'Choose an option:' in confirmation
    
    print("✅ Confirmation message correct")
    
    # Test update success message
    update_success = MessageFormatter.format_success_message_update(events, 3, '2025-08-10')
    print(f"\nUpdate success message:\n{update_success}")
    
    assert 'Successfully updated all 3 events on Sunday, August 10, 2025:' in update_success
    assert '• Updated [Lesson]' in update_success
    
    print("✅ Update success message correct")
    
    # Test delete success message
    delete_success = MessageFormatter.format_success_message_delete(3, '2025-08-10')
    print(f"\nDelete success message:\n{delete_success}")
    
    assert delete_success == "Successfully deleted all 3 events on Sunday, August 10, 2025!"
    
    print("✅ Delete success message correct")


def test_inline_keyboard_consistency():
    """Test that inline keyboards are properly formatted"""
    
    print("\n\nTesting Inline Keyboard Formatting:")
    print("=" * 50)
    
    # Test multi-event confirmation keyboard
    multi_keyboard = InlineKeyboardHelper.create_multi_event_confirmation_keyboard("delete")
    print(f"Multi-event keyboard: {multi_keyboard}")
    
    # Should have 3 buttons: All, One by One, Cancel
    assert len(multi_keyboard['inline_keyboard']) == 2  # Two rows
    assert len(multi_keyboard['inline_keyboard'][0]) == 2  # First row: All, One by One
    assert len(multi_keyboard['inline_keyboard'][1]) == 1  # Second row: Cancel
    
    # Check button texts
    buttons = multi_keyboard['inline_keyboard']
    assert buttons[0][0]['text'] == '🔄 All'
    assert buttons[0][1]['text'] == '1️⃣ One by One'
    assert buttons[1][0]['text'] == '❌ Cancel'
    
    print("✅ Multi-event keyboard correct")
    
    # Test single event confirmation keyboard
    single_keyboard = InlineKeyboardHelper.create_single_event_confirmation_keyboard("delete")
    print(f"Single event keyboard: {single_keyboard}")
    
    # Should have 2 buttons: Yes, No
    assert len(single_keyboard['inline_keyboard']) == 1  # One row
    assert len(single_keyboard['inline_keyboard'][0]) == 2  # Yes, No
    
    buttons = single_keyboard['inline_keyboard'][0]
    assert buttons[0]['text'] == '✅ Yes'
    assert buttons[1]['text'] == '❌ No'
    
    print("✅ Single event keyboard correct")
    
    # Test duplicate confirmation keyboard
    duplicate_keyboard = InlineKeyboardHelper.create_duplicate_confirmation_keyboard()
    print(f"Duplicate keyboard: {duplicate_keyboard}")
    
    # Should have 2 buttons: Create Anyway, Cancel
    assert len(duplicate_keyboard['inline_keyboard']) == 1  # One row
    assert len(duplicate_keyboard['inline_keyboard'][0]) == 2  # Create Anyway, Cancel
    
    buttons = duplicate_keyboard['inline_keyboard'][0]
    assert buttons[0]['text'] == '✅ Create Anyway'
    assert buttons[1]['text'] == '❌ Cancel'
    
    print("✅ Duplicate keyboard correct")


def test_no_truncation_rule():
    """Test the critical rule: NEVER truncate event lists"""
    
    print("\n\nTesting No Truncation Rule:")
    print("=" * 50)
    
    # Create a large number of events to test truncation handling
    many_events = []
    for i in range(15):  # 15 events - more than typical display limits
        event = {
            'summary': f'lesson {i+1}',
            'start': f'2025-08-10T{8+i:02d}:00:00Z',
            'end': f'2025-08-10T{9+i:02d}:00:00Z',
            'calendar_name': 'Tonya',
            'id': f'event{i}',
            'htmlLink': f'https://calendar.google.com/calendar/event?eid=event{i}'
        }
        many_events.append(event)
    
    # Test confirmation message with many events
    confirmation = MessageFormatter.format_confirmation_message("delete", many_events, 15)
    
    # Count the number of events displayed
    event_count = confirmation.count('[Lesson ')  # Count hyperlinked events
    print(f"Events in confirmation message: {event_count}")
    print(f"Confirmation message length: {len(confirmation)} characters")
    
    # CRITICAL: Must show ALL events, never truncate
    assert event_count == 15, f"Expected 15 events, found {event_count}"
    assert '... and' not in confirmation, "Found truncation in confirmation message"
    assert 'more events' not in confirmation, "Found truncation language in confirmation message"
    
    print("✅ No truncation rule verified - all 15 events shown")
    
    # Test success message with many events
    success = MessageFormatter.format_success_message_create(many_events, 15)
    success_event_count = success.count('[Lesson ')
    print(f"Events in success message: {success_event_count}")
    
    assert success_event_count == 15, f"Expected 15 events in success, found {success_event_count}"
    assert '... and' not in success, "Found truncation in success message"
    
    print("✅ No truncation rule verified for success messages")


def test_hyperlink_requirement():
    """Test that ALL events have hyperlinks in user-facing messages"""
    
    print("\n\nTesting Hyperlink Requirement:")
    print("=" * 50)
    
    events = [
        {
            'summary': 'lesson',
            'start': '2025-08-10T08:00:00Z',
            'end': '2025-08-10T09:00:00Z',
            'calendar_name': 'Tonya',
            'id': 'event123',
            'htmlLink': 'https://calendar.google.com/calendar/event?eid=event123'
        }
    ]
    
    # Test that hyperlink is included
    event_display = MessageFormatter.format_single_event_display(events[0], include_hyperlink=True)
    print(f"Event with hyperlink: {event_display}")
    
    assert '[Lesson](' in event_display, "Event name should be hyperlinked"
    assert 'https://calendar.google.com/' in event_display, "Should contain calendar URL"
    
    print("✅ Hyperlink requirement verified")
    
    # Test event without hyperlink
    event_no_link = {
        'summary': 'lesson',
        'start': '2025-08-10T08:00:00Z',
        'end': '2025-08-10T09:00:00Z',
        'calendar_name': 'Tonya',
        'id': 'event123',
        'htmlLink': None
    }
    
    event_display_fallback = MessageFormatter.format_single_event_display(event_no_link, include_hyperlink=True)
    print(f"Event with fallback link: {event_display_fallback}")
    
    # Should still have a hyperlink generated from event ID
    assert '[Lesson](' in event_display_fallback, "Should generate hyperlink from event ID"
    
    print("✅ Hyperlink fallback verified")


if __name__ == "__main__":
    print("CaliBOT Message Consistency Validation")
    print("=" * 50)
    
    try:
        test_message_formatter_consistency()
        test_inline_keyboard_consistency()
        test_no_truncation_rule()
        test_hyperlink_requirement()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Messages now comply with BOT_RULES.md specifications")
        print("✅ No truncation - all events always shown")
        print("✅ All events have hyperlinks")
        print("✅ Consistent formatting across all operations")
        print("✅ Inline keyboards properly implemented")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
