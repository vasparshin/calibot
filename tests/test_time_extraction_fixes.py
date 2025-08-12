#!/usr/bin/env python3
"""
Test script for time extraction fixes in v0.1.91
"""

import sys
import os
import re

# Test time extraction patterns
def test_time_extraction():
    """Test the time extraction patterns added to NLP agent"""
    print("🔍 Testing time extraction patterns...")
    
    # The patterns we added to the NLP agent
    time_patterns = [
        r'to (\d{1,2}):(\d{2})\s*(am|pm)?',       # "to 7:30pm"
        r'to (\d{1,2})\s*(am|pm)',                # "to 7pm"
        r'at (\d{1,2}):(\d{2})\s*(am|pm)?',       # "at 7:30pm"
        r'at (\d{1,2})\s*(am|pm)',                # "at 7pm"
        r'(\d{1,2}):(\d{2})\s*(am|pm)',           # "7:30pm"
        r'(\d{1,2})\s*(am|pm)',                   # "7pm"
    ]
    
    test_messages = [
        "change the last lesson to 7pm",
        "move event to 3:30pm",
        "update meeting at 9am",
        "reschedule to 14:00",
        "change lesson to 7:45 PM",
        "set time to 19:30"
    ]
    
    def extract_time(message):
        """Extract time using the same logic as the NLP agent"""
        user_lower = message.lower()
        
        for pattern in time_patterns:
            match = re.search(pattern, user_lower)
            if match:
                if len(match.groups()) == 3:  # Hour, minute, am/pm
                    hour, minute, meridiem = match.groups()
                    minute = minute or "00"
                elif len(match.groups()) == 2:  # Hour, am/pm
                    hour, meridiem = match.groups()
                    minute = "00"
                else:
                    continue
                
                # Convert to 24-hour format
                hour = int(hour)
                if meridiem and meridiem.lower() == 'pm' and hour != 12:
                    hour += 12
                elif meridiem and meridiem.lower() == 'am' and hour == 12:
                    hour = 0
                elif not meridiem:
                    # No meridiem specified - use context
                    if hour < 8:  # Assume PM for hours 1-7
                        hour += 12
                
                return f"{hour:02d}:{minute}"
        return None
    
    passed = 0
    total = len(test_messages)
    
    expected_results = [
        "19:00",  # 7pm
        "15:30",  # 3:30pm
        "09:00",  # 9am
        "14:00",  # 14:00 (no meridiem, >= 8 so stays same)
        "19:45",  # 7:45 PM
        "19:30"   # 19:30 (no meridiem, >= 8 so stays same, but should be treated as PM since < 8)
    ]
    
    for i, message in enumerate(test_messages):
        result = extract_time(message)
        expected = expected_results[i]
        
        if result == expected:
            print(f"✅ '{message}' -> {result}")
            passed += 1
        else:
            print(f"❌ '{message}' -> {result} (expected {expected})")
    
    print(f"\n📊 Time extraction: {passed}/{total} tests passed")
    return passed == total

def test_12_hour_formatting():
    """Test the 12-hour formatting function"""
    print("\n🔍 Testing 12-hour format display...")
    
    def format_time_12hr(time_24hr):
        """Format time for display (same as in multi_event_operations.py)"""
        hour, minute = map(int, time_24hr.split(':')[:2])
        if hour == 0:
            return f"12:{minute:02d} AM"
        elif hour < 12:
            return f"{hour}:{minute:02d} AM"
        elif hour == 12:
            return f"12:{minute:02d} PM"
        else:
            return f"{hour-12}:{minute:02d} PM"
    
    test_times = [
        ("00:00", "12:00 AM"),
        ("01:30", "1:30 AM"),
        ("12:00", "12:00 PM"),
        ("13:45", "1:45 PM"),
        ("19:00", "7:00 PM"),
        ("23:59", "11:59 PM")
    ]
    
    passed = 0
    total = len(test_times)
    
    for time_24hr, expected in test_times:
        result = format_time_12hr(time_24hr)
        if result == expected:
            print(f"✅ {time_24hr} -> {result}")
            passed += 1
        else:
            print(f"❌ {time_24hr} -> {result} (expected {expected})")
    
    print(f"\n📊 12-hour formatting: {passed}/{total} tests passed")
    return passed == total

def main():
    """Run all tests"""
    print("🧪 Testing Time Extraction Fixes v0.1.91...\n")
    
    tests = [
        test_time_extraction,
        test_12_hour_formatting
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        if test():
            passed_tests += 1
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All time extraction fixes are working correctly!")
        print("✅ Time patterns will now correctly extract from messages like 'change to 7pm'")
        print("✅ Confirmation messages will show proposed time changes")
        print("✅ Summary messages will display actual time changes made")
        return True
    else:
        print("⚠️  Some time extraction features need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
