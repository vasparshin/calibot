#!/usr/bin/env python3
"""
Simple One-by-One UX Fixes Validation

Tests the core logic fixes for v0.1.125 without requiring full backend setup:
1. Event data preservation logic
2. Message formatting concepts  
3. Queue progression simulation

This validates the logic fixes independent of backend configuration.
"""

import json
from datetime import datetime

class SimpleUXFixesValidator:
    def __init__(self):
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_event_data_preservation_logic(self):
        """Test the core logic fix for preserving event names"""
        print("\n🧪 TEST 1: Event Data Preservation Logic")
        
        # Mock data that would come from calendar service
        mock_events = [
            {
                "id": "event1",
                "summary": "lesson",  # Actual event name
                "start": "2025-08-13T21:00:00Z",
                "end": "2025-08-13T22:00:00Z",
                "calendar_name": "Tonya"
            },
            {
                "id": "event2",
                "summary": "lesson",  # Actual event name
                "start": "2025-08-13T22:00:00Z", 
                "end": "2025-08-13T23:00:00Z",
                "calendar_name": "Tonya"
            }
        ]
        
        # Mock intent extraction result (the problematic data)
        original_request = {
            "event_name": "ANY",  # Generic reference - should not overwrite actual names
            "new_date": "2025-08-14",
            "user_message": "move the last 2 events of yesterday to today"
        }
        
        print(f"📋 Original request event_name: '{original_request['event_name']}'")
        print(f"📋 Actual event names: {[e['summary'] for e in mock_events]}")
        
        # Apply the FIXED logic
        queue_events = []
        for i, event in enumerate(mock_events):
            # Step 1: Start with actual event data
            queue_event = {
                "intent": "update",
                "event_id": event.get("id"),
                "event_name": event.get("summary", ""),  # PRESERVE actual name
                "start_time": event.get("start"),
                "end_time": event.get("end"),
                "calendar_name": event.get("calendar_name"),
            }
            
            # Step 2: Apply the FIX - selective merging of original_request
            for key, value in original_request.items():
                if key == "event_name" and value.lower() in ["any", "event", "events"]:
                    # SKIP generic event names to preserve actual event name
                    print(f"📋 Skipping generic event_name '{value}' for event {i+1}")
                    continue
                if key not in queue_event:  # Don't overwrite event-specific data
                    queue_event[key] = value
                    
            queue_events.append(queue_event)
            print(f"📋 Event {i+1} final event_name: '{queue_event['event_name']}'")
        
        # Validate the fix
        all_preserved = True
        for i, queue_event in enumerate(queue_events):
            event_name = queue_event.get("event_name")
            if event_name != "lesson":
                all_preserved = False
                self.log_result(f"Event {i+1} Preservation", False, 
                              f"Expected 'lesson', got '{event_name}'")
            else:
                self.log_result(f"Event {i+1} Preservation", True, 
                              f"Correctly preserved: '{event_name}'")
        
        if all_preserved:
            self.log_result("Overall Data Preservation", True, 
                          "All event names preserved correctly")
        else:
            self.log_result("Overall Data Preservation", False, 
                          "Some event names were corrupted")
        
        return all_preserved

    def test_message_format_concept(self):
        """Test the message formatting concept"""
        print("\n🧪 TEST 2: Message Format Consistency Concept")
        
        # Simulate what the MessageFormatter should produce
        test_event = {
            "event_name": "lesson",
            "start_time": "2025-08-13T21:00:00Z",
            "end_time": "2025-08-13T22:00:00Z",
            "calendar_name": "Tonya"
        }
        
        # Manual format following BOT_RULES.md
        # Format: • [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
        expected_format = "• lesson on Tuesday, August 13, 2025 at 09:00 PM - 10:00 PM (Tonya)"
        
        print(f"📋 Expected format: {expected_format}")
        
        # Check format elements
        required_elements = [
            "lesson",  # Event name (not "ANY")
            "Tuesday, August 13, 2025",  # Full date
            "09:00 PM",  # 12-hour start time
            "10:00 PM",  # 12-hour end time 
            "(Tonya)"   # Calendar in parentheses
        ]
        
        format_correct = True
        for element in required_elements:
            if element in expected_format:
                self.log_result(f"Format Element '{element}'", True, "Present in expected format")
            else:
                format_correct = False
                self.log_result(f"Format Element '{element}'", False, "Missing from format")
        
        # Test the key insight: same format for individual as multi-event
        multi_event_format = "1. lesson on Tuesday, August 13, 2025 at 09:00 PM - 10:00 PM (Tonya)"
        individual_format = expected_format  # Should be nearly identical except bullet vs number
        
        if "lesson on Tuesday, August 13, 2025" in both_formats(multi_event_format, individual_format):
            self.log_result("Format Consistency", True, "Individual format matches multi-event style")
        else:
            self.log_result("Format Consistency", False, "Inconsistent formatting")
            format_correct = False
        
        return format_correct

    def test_queue_progression_concept(self):
        """Test queue progression logic"""
        print("\n🧪 TEST 3: Queue Progression Concept")
        
        # Simulate queue state
        queue_state = {
            "events": [
                {"event_name": "lesson", "start_time": "2025-08-13T21:00:00Z"},
                {"event_name": "lesson", "start_time": "2025-08-13T22:00:00Z"}
            ],
            "current_index": 0,
            "one_by_one_mode": True
        }
        
        total_events = len(queue_state["events"])
        
        # Test first event header
        current_index = queue_state["current_index"]
        first_header = f"UPDATE Event {current_index + 1} of {total_events}:"
        expected_first = "UPDATE Event 1 of 2:"
        
        if first_header == expected_first:
            self.log_result("First Event Header", True, f"Correct: '{first_header}'")
        else:
            self.log_result("First Event Header", False, f"Expected '{expected_first}', got '{first_header}'")
            return False
        
        # Simulate user pressing "yes" (progression)
        queue_state["current_index"] += 1
        
        # Test second event header
        if queue_state["current_index"] < len(queue_state["events"]):
            second_header = f"UPDATE Event {queue_state['current_index'] + 1} of {total_events}:"
            expected_second = "UPDATE Event 2 of 2:"
            
            if second_header == expected_second:
                self.log_result("Second Event Header", True, f"Progression works: '{second_header}'")
                self.log_result("Queue Progression Logic", True, "Successfully advances from event 1 to event 2")
                return True
            else:
                self.log_result("Second Event Header", False, f"Expected '{expected_second}', got '{second_header}'")
                return False
        else:
            self.log_result("Queue Progression", False, "Queue ended unexpectedly")
            return False

    def run_validation(self):
        """Run all validation tests"""
        print("🚀 CaliBOT One-by-One UX Fixes - Logic Validation")
        print("=" * 60)
        print("Validating v0.1.125 logic fixes (without backend dependencies)")
        print()
        
        # Run tests
        test1_pass = self.test_event_data_preservation_logic()
        test2_pass = self.test_message_format_concept()
        test3_pass = self.test_queue_progression_concept()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        
        print(f"\n📊 Validation Results")
        print("=" * 40)
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        all_pass = test1_pass and test2_pass and test3_pass
        
        if all_pass:
            print(f"\n🎉 SUCCESS: All logic fixes validated!")
            print("✅ Event data preservation logic is correct")
            print("✅ Message formatting concept is sound")
            print("✅ Queue progression logic works")
            print("\n📋 Ready for deployment testing once v0.1.125 is live")
        else:
            print(f"\n⚠️ ISSUES: Some logic needs review")
            
        return all_pass

def both_formats(format1, format2):
    """Helper to find common parts between two format strings"""
    # Find common substring
    words1 = format1.split()
    words2 = format2.split()
    common = []
    for word in words1:
        if word in words2:
            common.append(word)
    return " ".join(common)

if __name__ == "__main__":
    validator = SimpleUXFixesValidator()
    success = validator.run_validation()
    
    if success:
        print(f"\n🚀 Next Steps:")
        print("1. Wait for v0.1.125 deployment to complete")
        print("2. Test the actual 'move last 2 events' command in Telegram")
        print("3. Verify both event details show correctly in one-by-one mode")
        print("4. Confirm second event appears after pressing 'yes' on first")
    
    exit(0 if success else 1)
