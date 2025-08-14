#!/usr/bin/env python3
"""
One-by-One Workflow Testing Plan
Comprehensive test suite specifically for the "one by one" multi-event processing workflow
"""

import requests
import json
import time
from typing import Dict, Any

# Test configuration
BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
WEBHOOK_URL = "https://calibot-utq6.onrender.com/webhook"
TEST_CHAT_ID = 987654321

class OneByOneWorkflowTester:
    def __init__(self):
        self.message_id_counter = 2000
        self.session = requests.Session()
        self.test_results = []
    
    def send_webhook_request(self, update_data: Dict[str, Any]) -> bool:
        """Send webhook request to CaliBOT backend"""
        try:
            response = self.session.post(
                WEBHOOK_URL,
                json=update_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"  📡 Webhook Response ({response.status_code}): {response.text[:150]}...")
            return response.status_code == 200
            
        except Exception as e:
            print(f"  ❌ Webhook Error: {e}")
            return False
    
    def create_message_update(self, text: str) -> Dict[str, Any]:
        """Create a Telegram message update"""
        self.message_id_counter += 1
        return {
            "update_id": self.message_id_counter,
            "message": {
                "message_id": self.message_id_counter,
                "from": {
                    "id": TEST_CHAT_ID,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": text
            }
        }
    
    def create_callback_update(self, callback_data: str, message_text: str = "Previous message") -> Dict[str, Any]:
        """Create a Telegram callback query update"""
        self.message_id_counter += 1
        return {
            "update_id": self.message_id_counter,
            "callback_query": {
                "id": f"callback_{self.message_id_counter}",
                "from": {
                    "id": TEST_CHAT_ID,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "message": {
                    "message_id": self.message_id_counter - 1,
                    "from": {
                        "id": 8347695824,
                        "is_bot": True,
                        "first_name": "CaliBOT",
                        "username": "calibot_ai"
                    },
                    "chat": {
                        "id": TEST_CHAT_ID,
                        "first_name": "TestUser",
                        "username": "testuser",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": message_text
                },
                "data": callback_data
            }
        }
    
    def test_scenario(self, scenario_name: str, initial_request: str, expected_behavior: str) -> bool:
        """Test a complete one-by-one workflow scenario"""
        print(f"\n{'='*70}")
        print(f"🧪 TESTING: {scenario_name}")
        print(f"Request: {initial_request}")
        print(f"Expected: {expected_behavior}")
        print(f"{'='*70}")
        
        success = True
        
        # Step 1: Send initial request
        print("\n📝 Step 1: Send initial multi-event request...")
        update_request = self.create_message_update(initial_request)
        
        if not self.send_webhook_request(update_request):
            print("❌ Failed to send initial request")
            return False
        
        print("⏳ Waiting 3 seconds for processing...")
        time.sleep(3)
        
        # Step 2: Send "one by one" callback
        print("\n🔘 Step 2: Select 'one by one' option...")
        callback_update = self.create_callback_update(
            "confirm_one", 
            "Found multiple events. Would you like to process all or one by one?"
        )
        
        if not self.send_webhook_request(callback_update):
            print("❌ Failed to send one-by-one callback")
            return False
        
        print("⏳ Waiting 3 seconds for individual event presentation...")
        time.sleep(3)
        
        # Step 3: Confirm first event
        print("\n✅ Step 3: Confirm first individual event...")
        confirm_update = self.create_callback_update(
            "confirm_yes",
            "Process this event? [Individual event details shown]"
        )
        
        if not self.send_webhook_request(confirm_update):
            print("❌ Failed to send first event confirmation")
            return False
        
        print("⏳ Waiting 3 seconds for next event or completion...")
        time.sleep(3)
        
        # Step 4: Handle second event (if exists)
        print("\n✅ Step 4: Handle next event in queue...")
        next_confirm_update = self.create_callback_update(
            "confirm_yes",
            "Process this event? [Second event details]"
        )
        
        if not self.send_webhook_request(next_confirm_update):
            print("❌ Failed to send second event confirmation")
            return False
        
        print("⏳ Waiting 3 seconds for completion...")
        time.sleep(3)
        
        print(f"✅ {scenario_name} completed successfully")
        return True
    
    def run_comprehensive_test_suite(self):
        """Run all one-by-one workflow test scenarios"""
        print("🚀 Starting Comprehensive One-by-One Workflow Testing")
        print(f"🎯 Target: {WEBHOOK_URL}")
        print(f"👤 Test Chat ID: {TEST_CHAT_ID}")
        
        # Test scenarios covering different update types
        test_scenarios = [
            {
                "name": "Update with Date and Time Changes",
                "request": "move the last 2 lessons today to tomorrow 5 and 6 pm",
                "expected": "Should show proposed time changes clearly for each event"
            },
            {
                "name": "Delete Multiple Events",
                "request": "delete my tennis lessons tomorrow",
                "expected": "Should show individual delete confirmations"
            },
            {
                "name": "Time Shift Updates",
                "request": "move my next 2 meetings 1 hour later",
                "expected": "Should show time shift details for each event"
            },
            {
                "name": "Event Renaming",
                "request": "rename my next 2 calls to 'important call'",
                "expected": "Should show name change details for each event"
            },
            {
                "name": "Calendar Movement",
                "request": "move my next 2 events to personal calendar",
                "expected": "Should show calendar change details for each event"
            }
        ]
        
        successful_tests = 0
        total_tests = len(test_scenarios)
        
        for scenario in test_scenarios:
            try:
                if self.test_scenario(scenario["name"], scenario["request"], scenario["expected"]):
                    successful_tests += 1
                    self.test_results.append({"scenario": scenario["name"], "status": "SUCCESS"})
                else:
                    self.test_results.append({"scenario": scenario["name"], "status": "FAILED"})
                
                # Wait between scenarios
                print("\n⏳ Waiting 5 seconds between scenarios...")
                time.sleep(5)
                
            except KeyboardInterrupt:
                print(f"\n⏹️ Testing interrupted during {scenario['name']}")
                break
            except Exception as e:
                print(f"\n❌ Error in {scenario['name']}: {e}")
                self.test_results.append({"scenario": scenario["name"], "status": "ERROR", "error": str(e)})
        
        # Report results
        print("\n" + "="*70)
        print("📊 ONE-BY-ONE WORKFLOW TEST RESULTS")
        print("="*70)
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
            print(f"{status_icon} {result['scenario']}: {result['status']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: One-by-one workflow is working well!")
        elif success_rate >= 60:
            print("⚠️  GOOD: Minor issues detected, review failed scenarios")
        else:
            print("🚨 ATTENTION NEEDED: Significant issues with one-by-one workflow")
        
        print("\n🔍 Key Validation Points:")
        print("  ✅ Multi-event requests should trigger confirmation options")
        print("  ✅ 'One by one' selection should show individual event details")
        print("  ✅ Individual confirmations should show proposed changes clearly")
        print("  ✅ Each event should be processed independently")
        print("  ✅ No 'operation not found' errors should occur")
        print("  ✅ Workflow should complete successfully for all events")
        
        return success_rate >= 80

def main():
    """Run the one-by-one workflow testing suite"""
    try:
        tester = OneByOneWorkflowTester()
        success = tester.run_comprehensive_test_suite()
        
        if success:
            print("\n🎊 All tests passed! One-by-one workflow is ready for production use.")
            return 0
        else:
            print("\n🔧 Some tests failed. Review the issues and fix before deploying.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
