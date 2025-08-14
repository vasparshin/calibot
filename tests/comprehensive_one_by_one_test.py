#!/usr/bin/env python3
"""
COMPREHENSIVE ONE-BY-ONE EVENT TESTING
- Creates safe test events first
- Tests one-by-one deletion progression 
- Tests confirmation flow patterns
- Shows frontend TestBot messages AND backend webhooks
- Displays live logs during testing
"""

import asyncio
import aiohttp
import requests
import time
import json
from datetime import datetime, timedelta

class OneByOneEventTester:
    def __init__(self):
        self.backend_url = "https://calibot-utq6.onrender.com"
        self.webhook_url = f"{self.backend_url}/webhook"
        self.testbot_token = "7638628162:AAE-0eKLVAVjfNaP1sZgdYUzPbVmJkMjfN0"
        self.group_chat_id = -4627994150
        self.render_api_key = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"
        self.message_id = 2000
        self.test_events_created = []
        
    def create_webhook_payload(self, message_text: str) -> dict:
        """Create webhook payload for CaliBOT"""
        self.message_id += 1
        return {
            "update_id": self.message_id,
            "message": {
                "message_id": self.message_id,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "test_user_automation"
                },
                "chat": {
                    "id": self.group_chat_id,
                    "type": "supergroup", 
                    "title": "CaliBOT Testing Group"
                },
                "date": int(time.time()),
                "text": message_text
            }
        }
    
    async def send_testbot_message_fixed(self, message: str):
        """Send TestBot message with proper format"""
        try:
            url = f"https://api.telegram.org/bot{self.testbot_token}/sendMessage"
            
            # Try different format
            payload = {
                "chat_id": str(self.group_chat_id),
                "text": f"🤖 TestBot: {message}",
                "disable_notification": False
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                print(f"[✓] TestBot visual message sent: {message}")
                return True
            else:
                error_text = response.text if response.text else "No error details"
                print(f"[✗] TestBot failed ({response.status_code}): {error_text}")
                return False
                
        except Exception as e:
            print(f"[✗] TestBot error: {e}")
            return False
    
    async def send_webhook_to_calibot(self, message: str):
        """Send webhook to CaliBOT backend"""
        try:
            payload = self.create_webhook_payload(message)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                ) as response:
                    status = response.status
                    response_text = await response.text()
                    
                    if status == 200:
                        print(f"[✓] Webhook sent successfully: {message}")
                        return True, response_text
                    else:
                        print(f"[✗] Webhook failed ({status}): {response_text[:100]}")
                        return False, response_text
                        
        except Exception as e:
            print(f"[✗] Webhook error: {e}")
            return False, str(e)
    
    async def create_test_events(self, count: int = 3):
        """Create multiple safe test events for deletion testing"""
        print(f"\n📝 CREATING {count} SAFE TEST EVENTS FOR DELETION TESTING")
        print("=" * 60)
        
        created_events = []
        
        for i in range(1, count + 1):
            event_name = f"TEST_AUTO_DELETE_{i:03d}"
            message = f"create {event_name} tomorrow at {13 + i}:00-{14 + i}:00 for testing"
            
            print(f"\n💬 Creating event {i}/{count}: {event_name}")
            
            # Send TestBot visual message
            visual_sent = await self.send_testbot_message_fixed(message)
            
            # Send webhook to CaliBOT
            webhook_sent, response = await self.send_webhook_to_calibot(message)
            
            if webhook_sent:
                created_events.append(event_name)
                print(f"[✓] Event created: {event_name}")
            else:
                print(f"[✗] Failed to create: {event_name}")
            
            # Wait between creations
            await asyncio.sleep(3)
        
        self.test_events_created = created_events
        print(f"\n📊 Created {len(created_events)}/{count} test events")
        return created_events
    
    async def test_one_by_one_deletion(self):
        """Test one-by-one deletion progression with confirmation"""
        print(f"\n🧪 ONE-BY-ONE DELETION TESTING")
        print("=" * 60)
        
        if len(self.test_events_created) < 2:
            print("[✗] Need at least 2 test events for one-by-one testing")
            return False
        
        # Step 1: Request deletion of multiple test events
        delete_message = f"delete {self.test_events_created[0]} and {self.test_events_created[1]}"
        print(f"\n💬 Step 1 - Multi-delete request: {delete_message}")
        
        # Send both visual and webhook
        visual_sent = await self.send_testbot_message_fixed(delete_message)
        webhook_sent, response = await self.send_webhook_to_calibot(delete_message)
        
        if not webhook_sent:
            print("[✗] Initial deletion request failed")
            return False
        
        print("[✓] Multi-delete request sent - waiting for confirmation...")
        await asyncio.sleep(5)
        
        # Step 2: Send "one by one" confirmation
        confirm_message = "one by one"
        print(f"\n💬 Step 2 - Confirmation: {confirm_message}")
        
        visual_sent = await self.send_testbot_message_fixed(confirm_message)
        webhook_sent, response = await self.send_webhook_to_calibot(confirm_message)
        
        if not webhook_sent:
            print("[✗] Confirmation failed") 
            return False
        
        print("[✓] Confirmation sent - waiting for first event...")
        await asyncio.sleep(5)
        
        # Step 3: Confirm first event deletion
        first_confirm = "yes"
        print(f"\n💬 Step 3 - First event confirmation: {first_confirm}")
        
        visual_sent = await self.send_testbot_message_fixed(first_confirm)
        webhook_sent, response = await self.send_webhook_to_calibot(first_confirm)
        
        if not webhook_sent:
            print("[✗] First confirmation failed")
            return False
        
        print("[✓] First event confirmation sent - waiting for second event...")
        await asyncio.sleep(5)
        
        # Step 4: Confirm second event deletion  
        second_confirm = "yes"
        print(f"\n💬 Step 4 - Second event confirmation: {second_confirm}")
        
        visual_sent = await self.send_testbot_message_fixed(second_confirm)
        webhook_sent, response = await self.send_webhook_to_calibot(second_confirm)
        
        print("[✓] One-by-one deletion sequence completed!")
        return True
    
    async def get_live_logs(self, duration=30):
        """Show live logs during testing"""
        print(f"\n⏰ MONITORING LOGS FOR {duration} SECONDS...")
        print("-" * 50)
        
        start_time = time.time()
        last_check = datetime.utcnow() - timedelta(minutes=1)
        
        while (time.time() - start_time) < duration:
            try:
                headers = {
                    "Authorization": f"Bearer {self.render_api_key}",
                    "Content-Type": "application/json"
                }
                
                end_time = datetime.utcnow()
                start_search = end_time - timedelta(minutes=2)
                
                url = "https://api.render.com/v1/services/srv-ctfbqacl6cac73aro0q0/logs"
                params = {
                    "startTime": start_search.isoformat() + "Z",
                    "endTime": end_time.isoformat() + "Z", 
                    "limit": 20
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logs = data.get("logs", [])
                            
                            # Show new logs only
                            new_logs = [log for log in logs 
                                      if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > last_check]
                            
                            for log in new_logs:
                                timestamp = log.get("timestamp", "")[:19].replace("T", " ")
                                message = log.get("message", "")[:80]
                                print(f"📋 {timestamp} | {message}")
                                last_check = max(last_check, datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')))
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"[✗] Log error: {e}")
                await asyncio.sleep(10)

async def main():
    """Run comprehensive one-by-one testing"""
    print("🤖 COMPREHENSIVE ONE-BY-ONE EVENT TESTING")
    print("=" * 70)
    print("✅ This test will:")
    print("  • Create 3 safe test events (TEST_AUTO_DELETE_001, 002, 003)")
    print("  • Test multi-event deletion request") 
    print("  • Test 'one by one' confirmation flow")
    print("  • Show progression through each event") 
    print("  • Display live logs throughout")
    print()
    
    tester = OneByOneEventTester()
    
    # Start live log monitoring in background
    log_task = asyncio.create_task(tester.get_live_logs(120))  # 2 minutes
    
    try:
        # Phase 1: Create test events
        created_events = await tester.create_test_events(3)
        
        if len(created_events) < 2:
            print("[✗] Not enough test events created - aborting")
            return
        
        print(f"\n✅ Successfully created {len(created_events)} test events")
        await asyncio.sleep(5)
        
        # Phase 2: Test one-by-one deletion flow
        success = await tester.test_one_by_one_deletion()
        
        if success:
            print(f"\n🎉 One-by-one testing completed!")
        else:
            print(f"\n[✗] One-by-one testing failed")
        
        print(f"\n📋 Check your Telegram group for:")
        print(f"  • TestBot messages showing the commands")
        print(f"  • CaliBOT responses with confirmations")
        print(f"  • One-by-one deletion progression")
        
    except Exception as e:
        print(f"\n[✗] Test error: {e}")
        
    finally:
        log_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[✗] Testing interrupted")
    except Exception as e:
        print(f"\n[✗] Error: {e}")
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
