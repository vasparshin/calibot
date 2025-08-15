#!/usr/bin/env python3
"""
Simple Test: Quick verification of queue progression fix
Tests the exact user workflow that was broken
"""

import requests
import time

# Configuration
TEST_CHAT_ID = -1002486493418  # Group chat with CaliBOT and TestBot
WEBHOOK_URL = "https://srv-ctglj6qj1k6c73fpjbeg.onrender.com/api/webhook"

class SimpleQueueTest:
    def __init__(self):
        self.message_id = 1000
        
    def send_message(self, text):
        """Send a regular message"""
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
                    "type": "supergroup",
                    "title": "CaliBOT Testing Group"
                },
                "date": int(time.time()),
                "text": text
            }
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=update, timeout=15)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"  {status} MESSAGE: {text[:50]}... → {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"  ❌ Message failed: {e}")
            return False
            
    def send_callback(self, callback_data):
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
                        "type": "supergroup"
                    },
                    "text": "Previous message"
                },
                "data": callback_data
            }
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=update, timeout=15)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"  {status} BUTTON: {callback_data} → {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"  ❌ Button failed: {e}")
            return False

def main():
    """Run the simple queue test"""
    print("🧪 SIMPLE QUEUE PROGRESSION TEST")
    print("=" * 40)
    print("👁️ WATCH THE GROUP CHAT for real behavior!")
    print()
    
    tester = SimpleQueueTest()
    
    print("🎯 Step 1: Send multi-event request")
    tester.send_message("move my lessons from today to tomorrow")
    time.sleep(3)
    
    print("\n🎯 Step 2: Press 'One by One' button")
    tester.send_callback("confirm_one_update")
    time.sleep(3)
    
    print("\n🎯 Step 3: Press 'Yes' for Event 1 (CRITICAL TEST)")
    print("   📝 Should show 'Event 1 processed' AND 'UPDATE Event 2 of 2'")
    tester.send_callback("queue_confirm_0")
    time.sleep(3)
    
    print("\n🎯 Expected: You should now see 'UPDATE Event 2 of 2' message!")
    print("   🔍 If both events processed simultaneously = BUG STILL EXISTS")
    print("   ✅ If Event 2 confirmation appears = BUG FIXED!")
    
    print("\n👁️ CHECK GROUP CHAT NOW!")

if __name__ == "__main__":
    main()
