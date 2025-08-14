#!/usr/bin/env python3
"""
LIVE CaliBOT Demo - CORRECT Group Chat
======================================

Sending to YOUR actual group chat: -4627994150
"""

import asyncio
import httpx
import time

# YOUR ACTUAL GROUP CHAT ID
GROUP_CHAT_ID = -4627994150  # The group you're actually in
CALIBOT_WEBHOOK = "https://calibot-utq6.onrender.com/webhook"
YOUR_USER_ID = 5650181676

class CorrectGroupDemo:
    def __init__(self):
        self.message_counter = 7000
        
    async def send_webhook_to_your_group(self, message_text=None, callback_data=None):
        """Send webhook to CaliBOT in YOUR actual group chat"""
        
        if callback_data:
            # Button callback
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "callback_query": {
                    "id": f"correct_group_{int(time.time())}",
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
                            "id": GROUP_CHAT_ID,
                            "title": "Calendar testing",
                            "type": "group"
                        },
                        "date": int(time.time()),
                        "text": "Previous message"
                    },
                    "data": callback_data
                }
            }
            print(f"🔘 Button to YOUR group: {callback_data}")
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
                        "id": GROUP_CHAT_ID,
                        "title": "Calendar testing",
                        "type": "group"
                    },
                    "date": int(time.time()),
                    "text": message_text
                }
            }
            print(f"📡 Message to YOUR group: {message_text}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - Check YOUR group chat!")
                return True
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                return False

async def demo_in_correct_group():
    """Run demo in YOUR actual group chat"""
    
    print("🎬 DEMO IN YOUR ACTUAL GROUP CHAT")
    print("=" * 50)
    print(f"🏠 YOUR Group: {GROUP_CHAT_ID}")
    print(f"👁️ CHECK YOUR GROUP CHAT NOW!")
    print("=" * 50)
    
    demo = CorrectGroupDemo()
    
    # Step 1: Multi-event request to YOUR group
    print(f"\n🧪 STEP 1: Multi-event request in YOUR group")
    success = await demo.send_webhook_to_your_group(
        "🧪 CORRECT GROUP DEMO: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if success:
        print(f"   👁️ CHECK YOUR GROUP CHAT - CaliBOT should respond!")
        
    await asyncio.sleep(8)
    
    # Step 2: "One by One" button in YOUR group
    print(f"\n🔘 STEP 2: 'One by One' button in YOUR group")
    success = await demo.send_webhook_to_your_group(None, "confirm_one_update")
    
    if success:
        print(f"   👁️ CHECK YOUR GROUP CHAT - CaliBOT should show individual event!")
        
    await asyncio.sleep(8)
    
    # Step 3: "Yes" button in YOUR group
    print(f"\n✅ STEP 3: 'Yes' button in YOUR group")
    success = await demo.send_webhook_to_your_group(None, "queue_confirm_0")
    
    if success:
        print(f"   👁️ CHECK YOUR GROUP CHAT - CaliBOT should process event!")
        
    await asyncio.sleep(8)
    
    # Step 4: "Skip" button in YOUR group
    print(f"\n⏭️ STEP 4: 'Skip' button in YOUR group")
    success = await demo.send_webhook_to_your_group(None, "queue_skip_0")
    
    if success:
        print(f"   👁️ CHECK YOUR GROUP CHAT - CaliBOT should complete!")
        
    await asyncio.sleep(5)
    
    # Step 5: Completion in YOUR group
    print(f"\n🎊 STEP 5: Demo complete in YOUR group")
    await demo.send_webhook_to_your_group(
        "✅ CORRECT GROUP DEMO COMPLETE! Multi-event workflow is now working! 🎉"
    )
    
    print(f"\n🏁 DEMO COMPLETE IN YOUR ACTUAL GROUP!")
    print(f"👁️ Check YOUR group chat to see CaliBOT responses!")

if __name__ == "__main__":
    asyncio.run(demo_in_correct_group())
