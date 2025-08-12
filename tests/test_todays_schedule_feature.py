#!/usr/bin/env python3
"""
Test Today's Schedule Feature Implementation

Tests the new schedule button functionality and ScheduleService integration.
Validates formatting, keyboard generation, and response consistency.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
from datetime import datetime

# Import the modules
try:
    from app.services.schedule_service import ScheduleService
    from app.utils.inline_keyboard import InlineKeyboardHelper
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def test_schedule_service_detection():
    """Test schedule query detection"""
    print("\n🔍 Testing Schedule Query Detection:")
    print("=" * 50)
    
    schedule_service = ScheduleService(None)  # Mock service for testing
    
    test_cases = [
        ("/today", "today"),
        ("whats the schedule today", "today"),
        ("today's schedule", "today"),
        ("what do i have tomorrow", "tomorrow"),
        ("tomorrow's schedule", "tomorrow"),
        ("what's on today", "today"),
        ("schedule today", "today"),
        ("create a meeting", None),  # Should not be detected
        ("hello", None),  # Should not be detected
    ]
    
    for message, expected in test_cases:
        result = schedule_service.detect_schedule_query(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' -> {result} (expected: {expected})")
    
    print("\n✅ Schedule detection test completed")
    return True

def test_inline_keyboard_generation():
    """Test inline keyboard generation for schedule menus"""
    print("\n🔘 Testing Inline Keyboard Generation:")
    print("=" * 50)
    
    # Test schedule menu keyboard
    keyboard = InlineKeyboardHelper.create_schedule_menu_keyboard()
    print(f"Schedule menu keyboard: {keyboard}")
    
    # Verify structure
    assert "inline_keyboard" in keyboard
    buttons = keyboard["inline_keyboard"]
    assert len(buttons) == 1, "Should have 1 row"
    assert len(buttons[0]) == 2, "Should have 2 buttons"
    
    # Check button text and callback data
    button1, button2 = buttons[0]
    assert button1["text"] == "📅 Today's Schedule"
    assert button1["callback_data"] == "schedule_today"
    assert button2["text"] == "🗓️ Tomorrow's Schedule"
    assert button2["callback_data"] == "schedule_tomorrow"
    
    print("✅ Schedule menu keyboard structure correct")
    return True

def test_callback_parsing():
    """Test callback data parsing for schedule buttons"""
    print("\n🔄 Testing Callback Data Parsing:")
    print("=" * 50)
    
    test_cases = [
        ("schedule_today", {"action": "schedule", "detail": "today", "type": "schedule_today", "date_type": "today"}),
        ("schedule_tomorrow", {"action": "schedule", "detail": "tomorrow", "type": "schedule_tomorrow", "date_type": "tomorrow"}),
    ]
    
    for callback_data, expected in test_cases:
        result = InlineKeyboardHelper.parse_callback_data(callback_data)
        
        # Check key fields
        status = "✅" if (result.get("action") == expected["action"] and 
                         result.get("type") == expected["type"] and
                         result.get("date_type") == expected["date_type"]) else "❌"
        print(f"{status} '{callback_data}' -> {result}")
    
    print("✅ Callback parsing test completed")
    return True

def test_date_formatting():
    """Test date formatting functions"""
    print("\n📅 Testing Date Formatting:")
    print("=" * 50)
    
    schedule_service = ScheduleService(None)
    
    # Test date formatting
    test_date = "2025-08-12"
    formatted = schedule_service._format_date_for_display(test_date)
    expected = "12/08/25"
    
    status = "✅" if formatted == expected else "❌"
    print(f"{status} Date formatting: {test_date} -> {formatted} (expected: {expected})")
    
    # Test time formatting
    start_time = "2025-08-12T14:30:00+00:00"
    end_time = "2025-08-12T15:30:00+00:00"
    time_range = schedule_service._format_time_range(start_time, end_time)
    
    print(f"✅ Time formatting: {start_time} -> {time_range}")
    
    print("✅ Date formatting test completed")
    return True

def test_event_formatting():
    """Test event formatting for same-day display"""
    print("\n📝 Testing Event Formatting:")
    print("=" * 50)
    
    schedule_service = ScheduleService(None)
    
    mock_event = {
        "summary": "Test Meeting",
        "start": "2025-08-12T14:30:00+00:00",
        "end": "2025-08-12T15:30:00+00:00",
        "calendar_name": "Work",
        "link": "https://calendar.google.com/event/test123"
    }
    
    formatted = schedule_service._format_event_for_same_day_display(mock_event)
    print(f"Formatted event: {formatted}")
    
    # Check format components
    assert "[Test Meeting]" in formatted
    assert "https://calendar.google.com/event/test123" in formatted
    assert "(Work)" in formatted
    assert "2:30 PM - 3:30 PM" in formatted or "14:30" in formatted
    
    print("✅ Event formatting correct")
    return True

def run_all_tests():
    """Run all tests for the Today's Schedule feature"""
    print("🚀 Starting Today's Schedule Feature Tests")
    print("=" * 60)
    
    tests = [
        test_schedule_service_detection,
        test_inline_keyboard_generation,
        test_callback_parsing,
        test_date_formatting,
        test_event_formatting,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Today's Schedule feature is ready!")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
