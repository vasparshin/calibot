#!/usr/bin/env python3
"""
Test script to validate the one-by-one multi-event update fix
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

# Test configuration
BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
WEBHOOK_URL = "https://calibot-utq6.onrender.com/webhook"
TEST_CHAT_ID = 987654321

class OneByOneTestRunner:
    def __init__(self):
        self.message_id_counter = 1000
        self.session = requests.Session()
    
    def send_webhook_request(self, update_data: Dict[str, Any]) -> bool:
        """Send webhook request to CaliBOT backend"""
        try:
            response = self.session.post(
                WEBHOOK_URL,
                json=update_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"✅ Webhook Response ({response.status_code}): {response.text[:200]}...")
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Webhook Error: {e}")
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
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "first_name": "Test",
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
                    "first_name": "Test",
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
                        "first_name": "Test",
                        "username": "testuser",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": message_text
                },
                "data": callback_data
            }
        }
    
    def run_one_by_one_update_test(self):
        """Test the one-by-one update workflow that was previously broken"""
        print("\n" + "="*70)
        print("🧪 TESTING ONE-BY-ONE UPDATE WORKFLOW FIX")
        print("="*70)
        
        # Step 1: Create an update request that will find multiple events
        print("\n📝 Step 1: Send update request for multiple events...")
        update_request = self.create_message_update("update my tennis lessons to 1 hour later")
        
        success = self.send_webhook_request(update_request)
        if not success:
            print("❌ Failed to send initial update request")
            return False
        
        # Wait for processing
        print("⏳ Waiting 3 seconds for processing...")
        time.sleep(3)
        
        # Step 2: Send "one by one" callback confirmation
        print("\n🔘 Step 2: Send 'one by one' confirmation...")
        callback_update = self.create_callback_update(
            "confirm_one", 
            "Found multiple tennis lessons. Would you like to update all or one by one?"
        )
        
        success = self.send_webhook_request(callback_update)
        if not success:
            print("❌ Failed to send one-by-one callback")
            return False
        
        # Wait for processing
        print("⏳ Waiting 3 seconds for processing...")
        time.sleep(3)
        
        # Step 3: Send confirmation for first event
        print("\n✅ Step 3: Send confirmation for first event...")
        confirm_update = self.create_callback_update(
            "confirm_yes",
            "Update tennis lesson on Monday at 10:00 AM to 11:00 AM?"
        )
        
        success = self.send_webhook_request(confirm_update)
        if not success:
            print("❌ Failed to send first event confirmation")
            return False
        
        print("⏳ Waiting 3 seconds for processing...")
        time.sleep(3)
        
        print("\n✅ ONE-BY-ONE UPDATE TEST COMPLETED")
        print("🔍 Check the logs to verify:")
        print("  1. Initial update request created pending operation")
        print("  2. 'One by one' callback processed correctly as UPDATE operation")
        print("  3. Individual event confirmations work properly")
        print("  4. No delete operations should appear in logs")
        
        return True
    
    def run_delete_comparison_test(self):
        """Test delete one-by-one to compare with update behavior"""
        print("\n" + "="*70)
        print("🗑️ TESTING DELETE ONE-BY-ONE FOR COMPARISON")
        print("="*70)
        
        # Step 1: Create a delete request
        print("\n📝 Step 1: Send delete request for multiple events...")
        delete_request = self.create_message_update("delete my tennis lessons tomorrow")
        
        success = self.send_webhook_request(delete_request)
        if not success:
            print("❌ Failed to send delete request")
            return False
        
        # Wait for processing
        print("⏳ Waiting 3 seconds for processing...")
        time.sleep(3)
        
        # Step 2: Send "one by one" callback confirmation
        print("\n🔘 Step 2: Send 'one by one' confirmation for delete...")
        callback_update = self.create_callback_update(
            "confirm_one", 
            "Found multiple tennis lessons. Would you like to delete all or one by one?"
        )
        
        success = self.send_webhook_request(callback_update)
        if not success:
            print("❌ Failed to send one-by-one delete callback")
            return False
        
        print("⏳ Waiting 3 seconds for processing...")
        time.sleep(3)
        
        print("\n✅ DELETE ONE-BY-ONE TEST COMPLETED")
        print("🔍 This should show DELETE operation in logs (correct behavior)")
        
        return True

def main():
    """Run the one-by-one fix validation tests"""
    print("🚀 Starting One-by-One Multi-Event Fix Validation")
    print(f"🎯 Target: {WEBHOOK_URL}")
    print(f"👤 Test Chat ID: {TEST_CHAT_ID}")
    
    runner = OneByOneTestRunner()
    
    try:
        # Test the fixed update workflow
        if not runner.run_one_by_one_update_test():
            print("❌ Update test failed")
            return
        
        # Wait between tests
        print("\n⏳ Waiting 5 seconds between tests...")
        time.sleep(5)
        
        # Test delete workflow for comparison
        if not runner.run_delete_comparison_test():
            print("❌ Delete comparison test failed")
            return
        
        print("\n" + "="*70)
        print("🎉 ALL ONE-BY-ONE TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\n🔍 KEY VALIDATION POINTS:")
        print("  ✅ Update requests should maintain UPDATE operation type")
        print("  ✅ Delete requests should maintain DELETE operation type")
        print("  ✅ 'One by one' callbacks should preserve original operation type")
        print("  ✅ Individual confirmations should process correctly")
        print("  ✅ No operation type confusion in logs")
        print("\n📊 Review the backend logs to confirm proper operation handling!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
