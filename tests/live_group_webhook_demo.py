#!/usr/bin/env python3
"""
LIVE CaliBOT Group Webhook Demo
===============================

This sends webhook requests as if you're typing in the group chat.
CaliBOT will respond directly in the group chat - you'll see the conversation!
"""

import asyncio
import httpx
import time

GROUP_CHAT_ID = -1002246434652  # "Calendar testing" group
CALIBOT_WEBHOOK = "https://calibot-utq6.onrender.com/webhook"
YOUR_USER_ID = 5650181676

class LiveGroupWebhookDemo:
    def __init__(self):
        self.message_counter = 6000
        
    async def send_group_message_webhook(self, message_text=None, callback_data=None):
        """Send webhook to CaliBOT as if you're typing in the group chat"""
        
        if callback_data:
            # Button callback in group
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "callback_query": {
                    "id": f"live_group_demo_{int(time.time())}",
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
            print(f"🔘 Sending GROUP button: {callback_data}")
        else:
            # Text message in group
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
            print(f"📡 Sending GROUP message: {message_text}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - CaliBOT should respond in GROUP CHAT!")
                return True
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                return False

async def run_live_group_webhook_demo():
    """Send webhooks to trigger CaliBOT responses in the group chat"""
    
    print("🎬 LIVE GROUP WEBHOOK DEMONSTRATION")
    print("=" * 60)
    print(f"🏠 Target: Calendar testing group ({GROUP_CHAT_ID})")
    print(f"👁️ GO TO YOUR TELEGRAM GROUP CHAT NOW!")
    print(f"🤖 CaliBOT will respond directly in the group as if you typed these messages")
    print("=" * 60)
    
    demo = LiveGroupWebhookDemo()
    
    # Step 1: Multi-event request
    print(f"\n🧪 STEP 1: Multi-event request (as if you typed in group)")
    success = await demo.send_group_message_webhook(
        "🧪 LIVE GROUP DEMO: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should respond with multi-event buttons!")
        
    await asyncio.sleep(8)  # Give time to see response
    
    # Step 2: "One by One" button
    print(f"\n🔘 STEP 2: Pressing 'One by One' button (in group)")
    success = await demo.send_group_message_webhook(None, "confirm_one_update")
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should show individual event!")
        
    await asyncio.sleep(8)
    
    # Step 3: "Yes" button  
    print(f"\n✅ STEP 3: Pressing 'Yes' button (in group)")
    success = await demo.send_group_message_webhook(None, "queue_confirm_0")
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should process the event!")
        
    await asyncio.sleep(8)
    
    # Step 4: "Skip" button
    print(f"\n⏭️ STEP 4: Pressing 'Skip' button (in group)")
    success = await demo.send_group_message_webhook(None, "queue_skip_0")
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should complete the workflow!")
        
    await asyncio.sleep(5)
    
    # Step 5: Completion message
    print(f"\n🎊 STEP 5: Sending completion message")
    await demo.send_group_message_webhook(
        "✅ LIVE DEMO COMPLETE! If CaliBOT responded to all button presses, the bug is FIXED! 🎉"
    )
    
    print(f"\n🏁 LIVE DEMONSTRATION COMPLETE!")
    print(f"👁️ Check your Calendar testing group chat to see all CaliBOT responses!")
    print(f"✅ If CaliBOT responded to buttons properly, the 'nothing happened' bug is RESOLVED!")

if __name__ == "__main__":
    asyncio.run(run_live_group_webhook_demo())
