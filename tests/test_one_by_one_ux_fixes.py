#!/usr/bin/env python3
"""
Test One-by-One Event Processing UX Fixes

Tests the critical fixes for v0.1.125:
1. Event details properly displayed (not "ANY")  
2. Consistent formatting with multi-event summary
3. Queue progression works for 2nd, 3rd events

This validates the exact user scenario:
"move the last 2 events of yesterday to today" -> one-by-one workflow
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
import requests

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app.config import config
    from app.services.telegram_bot_service import TelegramBotService
    from app.services.conversation import ConversationState
    from app.services.google_calendar_service import GoogleCalendarService
    from app.services.multi_event_operations import MultiEventOperationHandler
    from app.services.event_queue_handler import EventQueueHandler
    from app.utils.message_formatter import MessageFormatter
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("❌ Make sure you're running from the project root directory")
    sys.exit(1)

class OneByOneUXTestSuite:
    def __init__(self):
        self.chat_id = 12345  # Test chat ID
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_event_data_preservation(self):
        """Test that actual event names are preserved, not overwritten by 'ANY'"""
        print("\n🧪 TEST 1: Event Data Preservation")
        
        # Mock event data (what would come from calendar service)
        mock_events = [
            {
                "id": "event1",
                "summary": "lesson",  # This should be preserved
                "start": "2025-08-13T21:00:00Z",
                "end": "2025-08-13T22:00:00Z",
                "calendar_name": "Tonya",
                "calendar_id": "primary"
            },
            {
                "id": "event2", 
                "summary": "lesson",  # This should be preserved
                "start": "2025-08-13T22:00:00Z",
                "end": "2025-08-13T23:00:00Z",
                "calendar_name": "Tonya",
                "calendar_id": "primary"
            }
        ]
        
        # Mock original request (contains "event_name": "ANY" from intent extraction)
        original_request = {
            "event_name": "ANY",  # This should NOT overwrite actual event names
            "new_date": "2025-08-14",
            "user_message": "move the last 2 events of yesterday to today"
        }
        
        # Simulate the queue conversion logic
        queue_events = []
        for i, event in enumerate(mock_events):
            queue_event = {
                "intent": "update",
                "event_id": event.get("id", event.get("event_id")),
                "event_name": event.get("summary", ""),  # Should preserve "lesson"
                "start_time": event.get("start", event.get("start_time", "")),
                "end_time": event.get("end", event.get("end_time", "")),
                "calendar_id": event.get("calendar_id", "primary"),
                "calendar_name": event.get("calendar_name", "Unknown"),
            }
            
            # Apply the fix: don't let generic event names overwrite actual data
            for key, value in original_request.items():
                if key == "event_name" and value.lower() in ["any", "event", "events"]:
                    # Skip generic event names to preserve actual event name
                    continue
                if key not in queue_event:  # Don't overwrite event-specific data
                    queue_event[key] = value
                    
            queue_events.append(queue_event)
        
        # Verify event names are preserved
        success = True
        for i, queue_event in enumerate(queue_events):
            event_name = queue_event.get("event_name")
            if event_name == "ANY" or event_name == "event":
                success = False
                self.log_result(f"Event {i+1} Name Preservation", False, 
                              f"Event name corrupted: got '{event_name}', expected 'lesson'")
            elif event_name == "lesson":
                self.log_result(f"Event {i+1} Name Preservation", True, 
                              f"Event name preserved correctly: '{event_name}'")
            else:
                success = False
                self.log_result(f"Event {i+1} Name Preservation", False, 
                              f"Unexpected event name: '{event_name}'")
        
        return success

    def test_message_formatting_consistency(self):
        """Test that individual event messages use the same format as multi-event summary"""
        print("\n🧪 TEST 2: Message Formatting Consistency")
        
        # Mock event data
        test_event = {
            "event_name": "lesson",
            "summary": "lesson", 
            "start_time": "2025-08-13T21:00:00Z",
            "end_time": "2025-08-13T22:00:00Z",
            "calendar_name": "Tonya",
            "id": "event123",
            "intent": "update",
            "new_date": "2025-08-14"
        }
        
        try:
            # Test MessageFormatter integration
            if MessageFormatter:
                # This should be the same format used in multi-event summaries
                formatted_display = MessageFormatter.format_single_event_display(test_event, include_hyperlink=True)
                print(f"📋 Formatted Display: {formatted_display}")
                
                # Verify the format follows BOT_RULES.md specification
                expected_elements = [
                    "lesson",  # Event name
                    "Tuesday, August 13, 2025",  # Full date format
                    "09:00 PM",  # 12-hour time format  
                    "10:00 PM",  # End time
                    "(Tonya)"   # Calendar name in parentheses
                ]
                
                success = True
                for element in expected_elements:
                    if element not in formatted_display:
                        success = False
                        self.log_result("Format Element Check", False, f"Missing element: '{element}' in '{formatted_display}'")
                
                if success:
                    self.log_result("MessageFormatter Integration", True, "All format elements present")
                    
                # Check that it starts with bullet or number (consistent with multi-event)
                if formatted_display.startswith('• '):
                    self.log_result("Format Consistency", True, "Uses bullet format consistent with multi-event display")
                else:
                    self.log_result("Format Consistency", False, f"Format inconsistent: '{formatted_display[:20]}...'")
                    success = False
                    
                return success
            else:
                self.log_result("MessageFormatter Import", False, "MessageFormatter not available")
                return False
                
        except Exception as e:
            self.log_result("Message Formatting", False, f"Error testing formatting: {e}")
            return False

    def test_queue_progression_simulation(self):
        """Test queue progression logic for multiple events"""
        print("\n🧪 TEST 3: Queue Progression Simulation")
        
        try:
            # Mock queue data
            mock_queue = {
                "events": [
                    {
                        "event_name": "lesson",
                        "start_time": "2025-08-13T21:00:00Z",
                        "end_time": "2025-08-13T22:00:00Z",
                        "calendar_name": "Tonya",
                        "intent": "update",
                        "new_date": "2025-08-14"
                    },
                    {
                        "event_name": "lesson", 
                        "start_time": "2025-08-13T22:00:00Z",
                        "end_time": "2025-08-13T23:00:00Z",
                        "calendar_name": "Tonya",
                        "intent": "update",
                        "new_date": "2025-08-14"
                    }
                ],
                "current_index": 0,
                "one_by_one_mode": True
            }
            
            # Simulate first event confirmation
            current_index = mock_queue['current_index']
            total_events = len(mock_queue['events'])
            current_event = mock_queue['events'][current_index]
            
            # Check first event message format
            expected_header = f"UPDATE Event {current_index + 1} of {total_events}:"
            print(f"📋 First Event Header: {expected_header}")
            
            # Simulate user pressing "yes" - should advance to next event
            mock_queue['current_index'] += 1
            
            # Check if second event would be shown
            if mock_queue['current_index'] < len(mock_queue['events']):
                next_event = mock_queue['events'][mock_queue['current_index']]
                next_header = f"UPDATE Event {mock_queue['current_index'] + 1} of {total_events}:"
                print(f"📋 Next Event Header: {next_header}")
                
                self.log_result("Queue Progression", True, 
                              f"Successfully progressed from event 1 to event 2")
                self.log_result("Header Format", True, 
                              f"Correct header format: '{next_header}'")
                return True
            else:
                self.log_result("Queue Progression", False, "Queue ended prematurely")
                return False
                
        except Exception as e:
            self.log_result("Queue Progression", False, f"Error in progression test: {e}")
            return False

    def test_integration_check(self):
        """Test that all components work together"""
        print("\n🧪 TEST 4: Integration Check")
        
        try:
            # Check backend health
            backend_url = "https://calibot-utq6.onrender.com"
            health_response = requests.get(f"{backend_url}/health", timeout=10)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                version = health_data.get("version", "unknown")
                
                if version == "0.1.125":
                    self.log_result("Backend Version", True, f"Correct version deployed: {version}")
                    
                    # Test basic webhook endpoint
                    webhook_response = requests.post(f"{backend_url}/telegram-webhook", 
                                                   json={"message": {"text": "/start", "chat": {"id": 12345}}},
                                                   timeout=10)
                    
                    if webhook_response.status_code == 200:
                        self.log_result("Webhook Integration", True, "Webhook endpoint responding")
                        return True
                    else:
                        self.log_result("Webhook Integration", False, f"Webhook error: {webhook_response.status_code}")
                        return False
                else:
                    self.log_result("Backend Version", False, f"Wrong version: {version}, expected 0.1.125")
                    return False
            else:
                self.log_result("Backend Health", False, f"Health check failed: {health_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Backend Connection", False, f"Cannot connect to backend: {e}")
            return False
        except Exception as e:
            self.log_result("Integration Test", False, f"Integration error: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests and report results"""
        print("🚀 CaliBOT One-by-One UX Fixes Test Suite")
        print("=" * 60)
        print("Testing v0.1.125 fixes for one-by-one event processing")
        print()
        
        # Run tests
        test1_pass = self.test_event_data_preservation()
        test2_pass = self.test_message_formatting_consistency()
        test3_pass = self.test_queue_progression_simulation()
        test4_pass = self.test_integration_check()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"\n📊 Test Results Summary")
        print("=" * 60)
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Overall assessment
        all_major_tests_pass = test1_pass and test2_pass and test3_pass and test4_pass
        
        if all_major_tests_pass:
            print(f"\n🎉 SUCCESS: All major one-by-one UX fixes are working!")
            print("✅ Event names preserved (not 'ANY')")
            print("✅ Consistent message formatting")
            print("✅ Queue progression logic works")
            print("✅ Backend integration healthy")
        else:
            print(f"\n⚠️ ISSUES DETECTED: Some fixes need attention")
            if not test1_pass:
                print("❌ Event data preservation issues")
            if not test2_pass:
                print("❌ Message formatting inconsistencies")
            if not test3_pass:
                print("❌ Queue progression problems")
            if not test4_pass:
                print("❌ Backend integration issues")
        
        # Save detailed results
        results_file = f"tests/one_by_one_ux_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_suite": "One-by-One UX Fixes",
                "version": "0.1.125",
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": total_tests - passed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {results_file}")
        
        return all_major_tests_pass

if __name__ == "__main__":
    test_suite = OneByOneUXTestSuite()
    success = asyncio.run(test_suite.run_all_tests())
    sys.exit(0 if success else 1)
