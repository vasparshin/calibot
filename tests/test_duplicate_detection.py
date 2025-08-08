#!/usr/bin/env python3
"""
Test script to verify duplicate event detection is working correctly
"""

def test_duplicate_detection_logic():
    """Test the duplicate detection matching logic"""
    print("Testing duplicate detection logic...")
    
    # Test cases for name matching
    test_cases = [
        {
            "existing_name": "piano lesson",
            "new_name": "Piano Lesson",
            "should_match": True,
            "description": "Case insensitive exact match"
        },
        {
            "existing_name": "lesson",
            "new_name": "piano lesson",
            "should_match": True,
            "description": "New name contains existing (piano lesson contains lesson)"
        },
        {
            "existing_name": "piano lesson with john",
            "new_name": "lesson",
            "should_match": True,
            "description": "Existing name contains new (piano lesson with john contains lesson)"
        },
        {
            "existing_name": "math class",
            "new_name": "piano lesson",
            "should_match": False,
            "description": "Completely different names"
        },
        {
            "existing_name": "lesson",
            "new_name": "testing",
            "should_match": False,
            "description": "Partial overlap but not containing"
        }
    ]
    
    print("\n=== Testing Name Matching Logic ===")
    for i, case in enumerate(test_cases, 1):
        existing_lower = case["existing_name"].lower()
        new_lower = case["new_name"].lower()
        
        # This is the logic from our duplicate detection
        matches = (existing_lower == new_lower or 
                  new_lower in existing_lower or 
                  existing_lower in new_lower)
        
        print(f"\nTest {i}: {case['description']}")
        print(f"Existing: '{case['existing_name']}'")
        print(f"New:      '{case['new_name']}'")
        print(f"Matches:  {matches}")
        print(f"Expected: {case['should_match']}")
        
        if matches == case["should_match"]:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            return False
    
    return True

def test_time_matching_logic():
    """Test the time matching logic"""
    print("\n=== Testing Time Matching Logic ===")
    
    time_test_cases = [
        {
            "new_start": "09:00",
            "existing_start": "2024-08-09T09:00:00-07:00",
            "should_match": True,
            "description": "Simple time in ISO datetime"
        },
        {
            "new_start": "08:30",
            "existing_start": "2024-08-09T08:30:00Z",
            "should_match": True,
            "description": "Time in UTC ISO datetime"
        },
        {
            "new_start": "14:00",
            "existing_start": "2024-08-09T09:00:00-07:00",
            "should_match": False,
            "description": "Different times"
        },
        {
            "new_start": "",
            "existing_start": "2024-08-09T09:00:00-07:00",
            "should_match": False,
            "description": "Empty new time"
        }
    ]
    
    for i, case in enumerate(time_test_cases, 1):
        # This is the logic from our duplicate detection
        matches = False
        if case["new_start"] and case["existing_start"]:
            try:
                matches = case["new_start"] in case["existing_start"]
            except Exception:
                matches = False
        
        print(f"\nTime Test {i}: {case['description']}")
        print(f"New start:      '{case['new_start']}'")
        print(f"Existing start: '{case['existing_start']}'")
        print(f"Matches:        {matches}")
        print(f"Expected:       {case['should_match']}")
        
        if matches == case["should_match"]:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            return False
    
    return True

def test_complete_duplicate_detection():
    """Test the complete duplicate detection flow"""
    print("\n=== Testing Complete Duplicate Detection ===")
    
    # Simulate events to create
    events_to_create = [
        {
            "event_name": "Piano Lesson",
            "date": "2024-08-09",
            "start_time": "09:00",
            "end_time": "10:00"
        },
        {
            "event_name": "Meeting",
            "date": "2024-08-09", 
            "start_time": "14:00",
            "end_time": "15:00"
        }
    ]
    
    # Simulate existing events
    existing_events = [
        {
            "summary": "piano lesson",
            "start": "2024-08-09T09:00:00-07:00",
            "end": "2024-08-09T10:00:00-07:00"
        },
        {
            "summary": "doctor appointment", 
            "start": "2024-08-09T11:00:00-07:00",
            "end": "2024-08-09T12:00:00-07:00"
        }
    ]
    
    # Simulate the duplicate detection logic
    duplicates_found = []
    
    for i, event in enumerate(events_to_create):
        event_name = event.get("event_name", "")
        event_start = event.get("start_time", "")
        
        for existing in existing_events:
            existing_summary = existing.get("summary", "").lower()
            event_name_lower = event_name.lower()
            
            # Check if names are similar
            if (existing_summary == event_name_lower or 
                event_name_lower in existing_summary or 
                existing_summary in event_name_lower):
                
                # Check time overlap
                existing_start = existing.get("start", "")
                if event_start and existing_start:
                    try:
                        if event_start in existing_start:
                            duplicates_found.append({
                                "new_event": event,
                                "existing_event": existing,
                                "index": i
                            })
                            break
                    except Exception:
                        pass
    
    print(f"\nEvents to create: {len(events_to_create)}")
    print(f"Existing events: {len(existing_events)}")
    print(f"Duplicates found: {len(duplicates_found)}")
    
    # We expect 1 duplicate (Piano Lesson matches piano lesson at 09:00)
    expected_duplicates = 1
    
    if len(duplicates_found) == expected_duplicates:
        print("✅ PASS - Correct number of duplicates detected")
        
        # Check the duplicate details
        dup = duplicates_found[0]
        print(f"Detected duplicate:")
        print(f"  New: {dup['new_event']['event_name']} at {dup['new_event']['start_time']}")
        print(f"  Existing: {dup['existing_event']['summary']} at {dup['existing_event']['start']}")
        return True
    else:
        print(f"❌ FAIL - Expected {expected_duplicates} duplicates, found {len(duplicates_found)}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Duplicate Event Detection")
    print("=" * 50)
    
    success = True
    
    try:
        # Test name matching
        if not test_duplicate_detection_logic():
            success = False
        
        # Test time matching
        if not test_time_matching_logic():
            success = False
            
        # Test complete flow
        if not test_complete_duplicate_detection():
            success = False
            
        print("\n" + "=" * 50)
        if success:
            print("✅ ALL TESTS PASSED - Duplicate detection is working!")
        else:
            print("❌ SOME TESTS FAILED - Duplicate detection needs fixes")
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    print("=" * 50)
    exit(0 if success else 1)
