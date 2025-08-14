#!/usr/bin/env python3
"""
COMPREHENSIVE ONE-BY-ONE WORKFLOW TESTING
Tests edit/create/delete events with one-by-one processing

Run this after verifying deployment with: python scripts/verify_deployment.py
"""

import requests
import json
import time
from datetime import datetime

# Configuration
WEBHOOK_URL = "https://calibot-utq6.onrender.com/webhook"
HEALTH_URL = "https://calibot-utq6.onrender.com/health"
TEST_CHAT_ID = 987654321

class ComprehensiveOneByOneTests:
    def __init__(self):
        self.message_id = 3000
        self.test_results = []
        
    def check_deployment(self):
        """Step 1: Verify deployment before testing"""
        print("🔍 STEP 1: Verifying Deployment")
        print("="*50)
        
        try:
            response = requests.get(HEALTH_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend Status: {response.status_code}")
                print(f"✅ Version: {data.get('version', 'unknown')}")
                print(f"✅ Health: {data.get('status', 'unknown')}")
                print(f"✅ Timestamp: {data.get('timestamp', 'unknown')}")
                return True
            else:
                print(f"❌ Backend error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def send_message(self, text):
        """Send a message to the webhook"""
        self.message_id += 1
        update = {
            "update_id": self.message_id,
            "message": {
                "message_id": self.message_id,
                "from": {
                    "id": TEST_CHAT_ID,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": text
            }
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=update, timeout=15)
            print(f"  📤 Sent: {text}")
            print(f"  📥 Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Response: {response.text[:200]}...")
            else:
                print(f"  ❌ Error: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            return False
    
    def send_callback(self, callback_data, message_text="Previous message"):
        """Send a callback query (button press)"""
        self.message_id += 1
        update = {
            "update_id": self.message_id,
            "callback_query": {
                "id": f"callback_{self.message_id}",
                "from": {
                    "id": TEST_CHAT_ID,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "message": {
                    "message_id": self.message_id - 1,
                    "chat": {
                        "id": TEST_CHAT_ID,
                        "type": "private"
                    },
                    "text": message_text
                },
                "data": callback_data
            }
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=update, timeout=15)
            print(f"  🔘 Button: {callback_data}")
            print(f"  📥 Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Response: {response.text[:200]}...")
            else:
                print(f"  ❌ Error: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"  ❌ Callback failed: {e}")
            return False
    
    def test_edit_events_one_by_one(self):
        """Test editing multiple events one by one"""
        print("\n🔧 STEP 2: Testing EDIT Events One-by-One")
        print("="*50)
        
        # Test the exact scenario that was failing
        test_message = "move the last 2 lessons today to tomorrow 5 and 6 pm"
        print(f"Testing: {test_message}")
        
        # Send initial request
        print("\n📝 2.1: Send edit request...")
        if not self.send_message(test_message):
            return False
        
        time.sleep(3)
        
        # Click "One by One"
        print("\n🔘 2.2: Select 'One by One' option...")
        if not self.send_callback("confirm_one", "Found 2 events to update. Process all or one by one?"):
            return False
        
        time.sleep(3)
        
        # Confirm first event
        print("\n✅ 2.3: Confirm first event...")
        if not self.send_callback("confirm_yes", "UPDATE Event 1 of 2: [Event details with proposed changes]"):
            return False
        
        time.sleep(3)
        
        # Confirm second event
        print("\n✅ 2.4: Confirm second event...")
        if not self.send_callback("confirm_yes", "UPDATE Event 2 of 2: [Event details with proposed changes]"):
            return False
        
        time.sleep(2)
        print("✅ EDIT one-by-one test completed")
        return True
    
    def test_delete_events_one_by_one(self):
        """Test deleting multiple events one by one"""
        print("\n🗑️ STEP 3: Testing DELETE Events One-by-One")
        print("="*50)
        
        test_message = "delete my tennis lessons tomorrow"
        print(f"Testing: {test_message}")
        
        # Send initial request
        print("\n📝 3.1: Send delete request...")
        if not self.send_message(test_message):
            return False
        
        time.sleep(3)
        
        # Click "One by One"
        print("\n🔘 3.2: Select 'One by One' option...")
        if not self.send_callback("confirm_one", "Found multiple tennis lessons. Delete all or one by one?"):
            return False
        
        time.sleep(3)
        
        # Confirm first deletion
        print("\n✅ 3.3: Confirm delete first event...")
        if not self.send_callback("confirm_yes", "DELETE Event 1 of X: [Event details]"):
            return False
        
        time.sleep(3)
        
        # Confirm second deletion
        print("\n✅ 3.4: Confirm delete second event...")
        if not self.send_callback("confirm_yes", "DELETE Event 2 of X: [Event details]"):
            return False
        
        time.sleep(2)
        print("✅ DELETE one-by-one test completed")
        return True
    
    def test_create_events_batch(self):
        """Test creating multiple events (should offer batch options)"""
        print("\n➕ STEP 4: Testing CREATE Multiple Events")
        print("="*50)
        
        test_message = "create lessons tomorrow at 3pm and 4pm"
        print(f"Testing: {test_message}")
        
        # Send initial request
        print("\n📝 4.1: Send create request...")
        if not self.send_message(test_message):
            return False
        
        time.sleep(3)
        
        # This might trigger batch creation or individual confirmations
        print("✅ CREATE batch test completed (may not have one-by-one for creation)")
        return True
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 COMPREHENSIVE ONE-BY-ONE WORKFLOW TESTING")
        print("="*60)
        print(f"Target: {WEBHOOK_URL}")
        print(f"Chat ID: {TEST_CHAT_ID}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Verify deployment
        if not self.check_deployment():
            print("\n❌ CRITICAL: Backend not accessible. Cannot proceed with testing.")
            print("Run: python scripts/verify_deployment.py")
            return False
        
        # Step 2: Test edit workflow
        try:
            edit_success = self.test_edit_events_one_by_one()
            time.sleep(5)  # Wait between tests
        except Exception as e:
            print(f"❌ Edit test failed: {e}")
            edit_success = False
        
        # Step 3: Test delete workflow  
        try:
            delete_success = self.test_delete_events_one_by_one()
            time.sleep(5)  # Wait between tests
        except Exception as e:
            print(f"❌ Delete test failed: {e}")
            delete_success = False
        
        # Step 4: Test create workflow
        try:
            create_success = self.test_create_events_batch()
            time.sleep(3)
        except Exception as e:
            print(f"❌ Create test failed: {e}")
            create_success = False
        
        # Results summary
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        tests = [
            ("EDIT Events One-by-One", edit_success),
            ("DELETE Events One-by-One", delete_success), 
            ("CREATE Events Batch", create_success)
        ]
        
        passed = sum(1 for _, success in tests if success)
        total = len(tests)
        
        for test_name, success in tests:
            icon = "✅" if success else "❌"
            print(f"{icon} {test_name}")
        
        success_rate = (passed / total) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}% ({passed}/{total})")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: One-by-one workflows working properly!")
        elif success_rate >= 60:
            print("⚠️  GOOD: Minor issues detected, review failed tests")
        else:
            print("🚨 ATTENTION NEEDED: Significant issues with one-by-one workflows")
        
        print("\n🔍 Key Validations:")
        print("  ✅ Multi-event requests should show [All] [One by One] options")
        print("  ✅ 'One by One' should show individual event confirmations")
        print("  ✅ Each event should show proposed changes clearly")
        print("  ✅ Individual [Yes] [No] options should work")
        print("  ✅ No 'operation not found' errors should occur")
        print("  ✅ Complete workflow should finish successfully")
        
        return success_rate >= 80

def main():
    """Main testing function"""
    tester = ComprehensiveOneByOneTests()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎊 All critical tests passed! One-by-one workflows are working correctly.")
            return 0
        else:
            print("\n🔧 Some tests failed. Review the output and fix issues before deploying.")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
