#!/usr/bin/env python3
"""
Real CaliBOT Chat Test - Send to YOUR actual chat
=================================================

This sends real webhook requests to CaliBOT using YOUR user ID
so the messages will appear in YOUR CaliBOT private chat.
"""

import asyncio
import httpx
import time

# Your actual user ID and CaliBOT webhook
YOUR_USER_ID = 5650181676  # Your real Telegram user ID
CALIBOT_WEBHOOK = "https://calibot-utq6.onrender.com/webhook"

class RealChatTester:
    def __init__(self):
        self.message_counter = 2000
        
    async def send_to_your_calibot_chat(self, message_text, callback_data=None):
        """Send a real message to YOUR CaliBOT private chat"""
        
        if callback_data:
            # Button callback
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "callback_query": {
                    "id": f"real_test_{int(time.time())}",
                    "from": {
                        "id": YOUR_USER_ID,
                        "is_bot": False,
                        "first_name": "Vas",
                        "username": "vasparshin"
                    },
                    "message": {
                        "message_id": self.message_counter,
                        "from": {
                            "id": 7425086142,  # CaliBOT's ID
                            "is_bot": True,
                            "first_name": "CaliBOT"
                        },
                        "chat": {
                            "id": YOUR_USER_ID,
                            "first_name": "Vas",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Previous message"
                    },
                    "data": callback_data
                }
            }
            print(f"🔘 Sending button press '{callback_data}' to YOUR CaliBOT chat...")
        else:
            # Text message
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "message": {
                    "message_id": self.message_counter,
                    "from": {
                        "id": YOUR_USER_ID,
                        "is_bot": False,
                        "first_name": "Vas",
                        "username": "vasparshin"
                    },
                    "chat": {
                        "id": YOUR_USER_ID,
                        "first_name": "Vas",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": message_text
                }
            }
            print(f"📱 Sending message '{message_text}' to YOUR CaliBOT chat...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: CaliBOT should respond in your private chat!")
            else:
                print(f"   ❌ FAILED: {response.status_code} - {response.text}")
                
            return response.status_code == 200

async def test_your_actual_chat():
    """Send real test messages to YOUR CaliBOT private chat"""
    
    print("🎯 REAL CALIBOT CHAT TEST")
    print("=" * 50)
    print(f"👤 Your User ID: {YOUR_USER_ID}")
    print(f"🤖 Target: Your CaliBOT private chat")
    print(f"📱 You should see messages appear in your CaliBOT chat!")
    print("=" * 50)
    
    tester = RealChatTester()
    
    # Test 1: Send a multi-event request
    print(f"\n🧪 TEST 1: Multi-event request")
    success = await tester.send_to_your_calibot_chat(
        "🧪 TEST: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if success:
        print(f"   👁️ CHECK YOUR CALIBOT CHAT - should show multi-event options!")
        
    await asyncio.sleep(5)
    
    # Test 2: Press "one by one" button
    print(f"\n🔘 TEST 2: Press 'One by one' button")
    success = await tester.send_to_your_calibot_chat(None, "multi_event_one_by_one")
    
    if success:
        print(f"   👁️ CHECK YOUR CALIBOT CHAT - should show individual event!")
        
    await asyncio.sleep(5)
    
    # Test 3: Press "Yes" button
    print(f"\n✅ TEST 3: Press 'Yes' button")
    success = await tester.send_to_your_calibot_chat(None, "event_yes")
    
    if success:
        print(f"   👁️ CHECK YOUR CALIBOT CHAT - should process the event!")
        
    await asyncio.sleep(5)
    
    # Test 4: Press "Skip" button  
    print(f"\n⏭️ TEST 4: Press 'Skip' button")
    success = await tester.send_to_your_calibot_chat(None, "event_skip")
    
    if success:
        print(f"   👁️ CHECK YOUR CALIBOT CHAT - should skip the event!")
    
    print(f"\n🏁 TESTING COMPLETE!")
    print(f"📱 Go check your CaliBOT private chat to see all the responses!")
    print(f"✅ If you see proper responses, the queue processing bug is FIXED!")

if __name__ == "__main__":
    asyncio.run(test_your_actual_chat())
