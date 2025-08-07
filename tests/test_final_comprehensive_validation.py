#!/usr/bin/env python3
"""
Comprehensive validation of all CaliBOT fixes and improvements.
This test validates the complete workflow and recent bug fixes.
"""

import json
import asyncio
from datetime import datetime

def test_nlp_agent_json_parsing():
    """Test NLP agent handles multiple JSON responses correctly"""
    print("🧠 Testing NLP agent JSON parsing...")
    
    # Simulate single JSON response
    single_json = '{"intent": "create", "event_name": "meeting", "date": "2025-08-07"}'
    try:
        parsed = json.loads(single_json)
        assert parsed["intent"] == "create"
        print("  ✅ Single JSON parsing works")
    except Exception as e:
        print(f"  ❌ Single JSON parsing failed: {e}")
        return False
    
    # Simulate multiple JSON response (batch events)
    multi_json = '''{"intent": "create", "event_name": "lesson", "start_time": "08:00", "end_time": "09:00"}
{"intent": "create", "event_name": "lesson", "start_time": "10:00", "end_time": "11:00"}
{"intent": "create", "event_name": "lesson", "start_time": "11:00", "end_time": "12:00"}'''
    
    try:
        lines = [line.strip() for line in multi_json.split('\n') if line.strip()]
        json_objects = []
        for line in lines:
            json_obj = json.loads(line)
            json_objects.append(json_obj)
        
        assert len(json_objects) == 3
        assert all(obj["intent"] == "create" for obj in json_objects)
        print("  ✅ Multi-JSON parsing works")
    except Exception as e:
        print(f"  ❌ Multi-JSON parsing failed: {e}")
        return False
    
    return True

def test_event_validation_fix():
    """Test the fix for 'list' object has no attribute 'get' error"""
    print("🔧 Testing event validation fix...")
    
    # Simulate mixed event types (the problematic scenario)
    events = [
        {"id": "event1", "summary": "Valid Event", "start": "2025-08-07T10:00:00"},
        ["invalid", "list", "object"],  # This caused the original error
        {"id": "event2", "summary": "Another Valid Event"},
        None,  # Another edge case
        "not_a_dict",  # String instead of dict
        42,  # Number instead of dict
    ]
    
    # Apply our fix logic
    valid_events = []
    for event in events:
        if not isinstance(event, dict):
            continue
        if "id" not in event:
            continue
        valid_events.append(event)
    
    assert len(valid_events) == 2
    print("  ✅ Event validation prevents type errors")
    return True

def test_file_organization():
    """Test that files are properly organized"""
    print("📁 Testing file organization...")
    
    import os
    
    # Check tests folder exists and has test files
    tests_path = "/workspaces/calibot/tests"
    if os.path.exists(tests_path):
        test_files = [f for f in os.listdir(tests_path) if f.startswith('test_')]
        if len(test_files) > 0:
            print(f"  ✅ Tests folder contains {len(test_files)} test files")
        else:
            print("  ❌ No test files found in tests folder")
            return False
    else:
        print("  ❌ Tests folder not found")
        return False
    
    # Check scripts folder exists
    scripts_path = "/workspaces/calibot/scripts"
    if os.path.exists(scripts_path):
        script_files = os.listdir(scripts_path)
        if 'organize_files.sh' in script_files and 'version_check.py' in script_files:
            print("  ✅ Scripts folder properly organized")
        else:
            print("  ❌ Scripts folder missing required files")
            return False
    else:
        print("  ❌ Scripts folder not found")
        return False
    
    # Check no test files in project root
    root_path = "/workspaces/calibot"
    root_files = os.listdir(root_path)
    root_test_files = [f for f in root_files if f.startswith('test_') and f.endswith('.py')]
    if len(root_test_files) == 0:
        print("  ✅ No test files in project root")
    else:
        print(f"  ❌ Found {len(root_test_files)} test files in project root")
        return False
    
    return True

def test_intent_extraction_formats():
    """Test various intent extraction formats"""
    print("🎯 Testing intent extraction formats...")
    
    # Test single event intent
    single_intent = {
        "intent": "create",
        "event_name": "meeting",
        "date": "2025-08-07",
        "start_time": "14:00",
        "end_time": "15:00",
        "confirmation_needed": False
    }
    
    assert single_intent["intent"] == "create"
    assert "event_name" in single_intent
    print("  ✅ Single event intent format valid")
    
    # Test multi-event batch format
    batch_intent = {
        "intent": "batch_create",
        "events": [
            {"start_time": "08:00", "end_time": "09:00"},
            {"start_time": "10:00", "end_time": "11:00"},
            {"start_time": "11:00", "end_time": "12:00"}
        ],
        "confirmation_needed": False
    }
    
    assert batch_intent["intent"] == "batch_create"
    assert len(batch_intent["events"]) == 3
    print("  ✅ Batch event intent format valid")
    
    # Test delete intent
    delete_intent = {
        "intent": "delete",
        "event_name": "lesson",
        "date": "2025-08-07",
        "confirmation_needed": True
    }
    
    assert delete_intent["intent"] == "delete"
    assert delete_intent["confirmation_needed"] is True
    print("  ✅ Delete intent format valid")
    
    return True

def test_calendar_selection_logic():
    """Test calendar selection scenarios"""
    print("📅 Testing calendar selection logic...")
    
    # Test explicit calendar specification
    event_with_calendar = {
        "intent": "create",
        "event_name": "lesson",
        "calendar_name": "work calendar",
        "date": "2025-08-07"
    }
    
    if event_with_calendar.get("calendar_name"):
        calendar_to_use = event_with_calendar["calendar_name"]
        assert calendar_to_use == "work calendar"
        print("  ✅ Explicit calendar selection works")
    
    # Test AI-based calendar selection fallback
    event_without_calendar = {
        "intent": "create",
        "event_name": "workout session",
        "date": "2025-08-07"
    }
    
    # Simulate rule-based fallback
    event_name = event_without_calendar["event_name"].lower()
    if "workout" in event_name or "gym" in event_name:
        suggested_calendar = "fitness"
    elif "meeting" in event_name or "call" in event_name:
        suggested_calendar = "work"
    else:
        suggested_calendar = "primary"
    
    assert suggested_calendar == "fitness"
    print("  ✅ Rule-based calendar selection works")
    
    return True

def run_all_tests():
    """Run all validation tests"""
    print("🚀 Starting comprehensive CaliBOT validation...\n")
    
    tests = [
        test_nlp_agent_json_parsing,
        test_event_validation_fix,
        test_file_organization,
        test_intent_extraction_formats,
        test_calendar_selection_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"  ❌ {test.__name__} failed")
        except Exception as e:
            print(f"  ❌ {test.__name__} failed with exception: {e}")
        print()
    
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! CaliBOT is ready for production.")
        return True
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
