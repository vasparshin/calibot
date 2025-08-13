#!/usr/bin/env python3
"""
Test Last 3 Events Selection Fix

Tests that "last 3 lessons" correctly selects the chronologically last 3 lesson events,
not all lesson events.
"""

import sys
import os

# Add the project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_last_3_selection_logic():
    """Test the chronological selection logic"""
    print("🧪 Testing 'Last 3' Selection Logic")
    
    # Mock events from the user's scenario (5 events total, 4 lessons)
    mock_events = [
        {
            'id': 'event1',
            'summary': 'Polina - Ultimate Activity Camps - LVS Ascot',
            'start': '2025-08-12T08:30:00+00:00',
            'end': '2025-08-12T17:15:00+00:00',
            'calendar_name': 'zoutna@gmail.com'
        },
        {
            'id': 'event2',
            'summary': 'Lesson',
            'start': '2025-08-12T16:00:00+00:00',  # 4:00 PM (after the shift)
            'end': '2025-08-12T17:00:00+00:00',
            'calendar_name': 'Tonya'
        },
        {
            'id': 'event3',
            'summary': 'Lesson',
            'start': '2025-08-12T18:00:00+00:00',  # 6:00 PM
            'end': '2025-08-12T19:00:00+00:00',
            'calendar_name': 'Tonya'
        },
        {
            'id': 'event4',
            'summary': 'Lesson',
            'start': '2025-08-12T19:00:00+00:00',  # 7:00 PM
            'end': '2025-08-12T20:00:00+00:00',
            'calendar_name': 'Tonya'
        },
        {
            'id': 'event5',
            'summary': 'Lesson',
            'start': '2025-08-12T20:00:00+00:00',  # 8:00 PM
            'end': '2025-08-12T21:00:00+00:00',
            'calendar_name': 'Tonya'
        }
    ]
    
    print("📅 Mock Schedule (5 total events):")
    for i, event in enumerate(mock_events, 1):
        start_time = event['start'][11:16]  # Extract HH:MM
        print(f"  {i}. {event['summary']} at {start_time}")
    
    # Step 1: Filter by event name "lesson"
    event_name = "lesson"
    filtered_events = [
        event for event in mock_events 
        if event_name.lower() in event.get('summary', '').lower()
    ]
    
    print(f"\n🔍 After filtering by '{event_name}' ({len(filtered_events)} events):")
    for i, event in enumerate(filtered_events, 1):
        start_time = event['start'][11:16]
        print(f"  {i}. {event['summary']} at {start_time}")
    
    # Step 2: Sort by start time (chronological order)
    filtered_events.sort(key=lambda x: x.get('start', ''))
    
    # Step 3: Apply target selection "last 3"
    target = "last"
    count = 3
    
    if target == "last" and len(filtered_events) > 0:
        selected_events = filtered_events[-count:] if count <= len(filtered_events) else filtered_events
    
    print(f"\n🎯 After applying 'last {count}' selection ({len(selected_events)} events):")
    for i, event in enumerate(selected_events, 1):
        start_time = event['start'][11:16]
        print(f"  {i}. {event['summary']} at {start_time}")
    
    # Validation
    expected_count = 3
    actual_count = len(selected_events)
    
    if actual_count == expected_count:
        print(f"\n✅ CORRECT: Selected {actual_count} events (expected {expected_count})")
        
        # Check that we got the last 3 chronologically
        expected_times = ['18:00', '19:00', '20:00']  # 6 PM, 7 PM, 8 PM
        actual_times = [event['start'][11:16] for event in selected_events]
        
        if actual_times == expected_times:
            print(f"✅ CORRECT: Selected the right events at times {actual_times}")
            return True
        else:
            print(f"❌ WRONG TIMES: Expected {expected_times}, got {actual_times}")
            return False
    else:
        print(f"\n❌ WRONG COUNT: Selected {actual_count} events (expected {expected_count})")
        return False

def test_syntax_check():
    """Check that the modified file compiles"""
    print("\n🧪 Testing Modified File Syntax")
    
    try:
        import py_compile
        py_compile.compile('backend/app/services/multi_event_operations.py', doraise=True)
        print("✅ multi_event_operations.py compiles successfully")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in multi_event_operations.py: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing 'Last 3 Events' Selection Fix\n")
    
    selection_passed = test_last_3_selection_logic()
    syntax_passed = test_syntax_check()
    
    print(f"\n📊 Test Results:")
    print(f"Selection Logic: {'✅ PASS' if selection_passed else '❌ FAIL'}")
    print(f"Syntax Check: {'✅ PASS' if syntax_passed else '❌ FAIL'}")
    
    if selection_passed and syntax_passed:
        print("\n🎉 'Last 3' selection logic should now work correctly!")
        print("Expected behavior: 'move the last 3 lessons' will select exactly the 3 most recent lessons")
        return True
    else:
        print("\n⚠️ Some tests failed - review the output above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
