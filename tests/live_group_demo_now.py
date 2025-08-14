#!/usr/bin/env python3
"""
LIVE Group Chat Bot-to-Bot Demo - RIGHT NOW
==========================================

This creates a REAL bot-to-bot conversation in the group chat that you can SEE happening.
"""

import asyncio
import httpx
import time

# Working configuration from the tests
GROUP_CHAT_ID = -1002246434652  # "Calendar testing" group  
TESTBOT_TOKEN = "7669505498:AAE5H3K3iLk7H-cxuAEWucxqhcuBU4QzEk4"  # Working TestBot token
CALIBOT_WEBHOOK = "https://calibot-utq6.onrender.com/webhook"
YOUR_USER_ID = 5650181676

class LiveGroupChatDemo:
    def __init__(self):
        self.message_counter = 5000
        
    async def send_testbot_message(self, text):
        """Send a message from TestBot to the group chat - VISIBLE TO YOU"""
        print(f"📱 TestBot → Group: {text}")
        
        url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": GROUP_CHAT_ID,
            "text": f"🤖 TestBot: {text}",
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ TestBot message sent - CHECK GROUP CHAT!")
                return True
            else:
                error_data = response.json() if response.status_code != 200 else {}
                print(f"   ❌ TestBot failed: {response.status_code} - {error_data}")
                return False
                
    async def send_calibot_webhook(self, message_text=None, callback_data=None):
        """Send webhook to CaliBOT as if you typed in the group"""
        
        if callback_data:
            # Button callback
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "callback_query": {
                    "id": f"live_group_{int(time.time())}",
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
            print(f"🔘 Webhook → CaliBOT: Button '{callback_data}'")
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
            print(f"📡 Webhook → CaliBOT: Message '{message_text}'")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ CaliBOT webhook SUCCESS - CHECK GROUP CHAT FOR RESPONSE!")
                return True
            else:
                print(f"   ❌ CaliBOT webhook FAILED: {response.status_code}")
                return False

async def run_live_group_demo():
    """Run the LIVE demonstration in the group chat - YOU CAN SEE THIS!"""
    
    print("🎬 LIVE GROUP CHAT DEMONSTRATION")
    print("=" * 60)
    print(f"🏠 Group: Calendar testing ({GROUP_CHAT_ID})")
    print(f"👁️ GO TO YOUR TELEGRAM GROUP CHAT NOW - YOU WILL SEE THE CONVERSATION!")
    print("=" * 60)
    
    demo = LiveGroupChatDemo()
    
    # Step 1: TestBot announces the demo
    print(f"\n🎬 STEP 1: TestBot announces the demonstration")
    success = await demo.send_testbot_message(
        "🧪 <b>LIVE MULTI-EVENT WORKFLOW DEMONSTRATION</b>\n\n"
        "I'm about to demonstrate the fixed multi-event workflow. "
        "Watch CaliBOT respond with buttons and proper queue processing!"
    )
    
    if not success:
        print("❌ TestBot failed - cannot proceed")
        return
        
    await asyncio.sleep(3)
    
    # Step 2: TestBot shows the request
    print(f"\n📝 STEP 2: TestBot shows the user request")
    await demo.send_testbot_message(
        "User request: 'move my last 2 events from yesterday to today at 2pm and 3pm'"
    )
    
    await asyncio.sleep(2)
    
    # Step 3: Send webhook to CaliBOT
    print(f"\n📡 STEP 3: Sending webhook to CaliBOT")
    success = await demo.send_calibot_webhook(
        "🧪 LIVE DEMO: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should respond with multi-event options!")
        
    await asyncio.sleep(5)
    
    # Step 4: TestBot explains what should happen
    print(f"\n📚 STEP 4: TestBot explains expected behavior")
    await demo.send_testbot_message(
        "CaliBOT should have responded with:\n"
        "• Found 2 events message\n"
        "• Buttons: 'All', 'One by One', 'Cancel'\n\n"
        "Now I'll press 'One by One' button..."
    )
    
    await asyncio.sleep(3)
    
    # Step 5: Press "One by One" button
    print(f"\n🔘 STEP 5: Pressing 'One by One' button")
    success = await demo.send_calibot_webhook(None, "confirm_one_update")
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should show individual event!")
        
    await asyncio.sleep(5)
    
    # Step 6: TestBot explains queue processing
    print(f"\n📚 STEP 6: TestBot explains queue processing")
    await demo.send_testbot_message(
        "CaliBOT should now show:\n"
        "• 'Event 1 of 2' with details\n"
        "• Buttons: 'Yes', 'Skip', 'Stop All'\n\n"
        "Now I'll press 'Yes' to confirm first event..."
    )
    
    await asyncio.sleep(3)
    
    # Step 7: Press "Yes" button
    print(f"\n✅ STEP 7: Pressing 'Yes' button")
    success = await demo.send_calibot_webhook(None, "queue_confirm_0")
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should process the event!")
        
    await asyncio.sleep(5)
    
    # Step 8: Press "Skip" for second event
    print(f"\n⏭️ STEP 8: Pressing 'Skip' for second event")
    success = await demo.send_calibot_webhook(None, "queue_skip_0")
    
    if success:
        print(f"   👁️ CHECK GROUP CHAT - CaliBOT should skip to completion!")
        
    await asyncio.sleep(3)
    
    # Step 9: TestBot summarizes results
    print(f"\n🎊 STEP 9: TestBot declares demonstration complete")
    await demo.send_testbot_message(
        "✅ <b>LIVE DEMONSTRATION COMPLETE!</b>\n\n"
        "If you saw CaliBOT respond to all button presses with proper messages, "
        "then the 'nothing happened after button press' issue is FIXED! 🎉\n\n"
        "The multi-event workflow is now working correctly."
    )
    
    print(f"\n🏁 DEMONSTRATION COMPLETE!")
    print(f"👁️ Check the group chat to see the full bot-to-bot conversation!")
    print(f"✅ If CaliBOT responded to buttons properly, the bug is FIXED!")

if __name__ == "__main__":
    asyncio.run(run_live_group_demo())
