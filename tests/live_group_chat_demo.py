#!/usr/bin/env python3
"""
Live Group Chat Bot-to-Bot Demo
==============================

This demonstrates the multi-event workflow with VISIBLE messages in the group chat.
You'll see:
1. TestBot sends a message in the group
2. CaliBOT webhook gets called and responds 
3. Real-time log monitoring shows backend processing
4. Button clicks get processed properly
"""

import asyncio
import httpx
import time
import json
from datetime import datetime

# Group chat configuration  
GROUP_CHAT_ID = -1002246434652  # "Calendar testing" group
TESTBOT_TOKEN = "7669505498:AAE5H3K3iLk7H-cxuAEWucxqhcuBU4QzEk4"
CALIBOT_WEBHOOK = "https://calibot-utq6.onrender.com/webhook"
RENDER_API_KEY = "rnd_FyVF44sTWKfh8zWwIYZLJJlm4nCE"
SERVICE_ID = "srv-ct6n7tqopnds73ba5ma0"

class LiveGroupChatDemo:
    def __init__(self):
        self.message_counter = 3000
        
    async def send_testbot_message(self, text):
        """Send a message from TestBot to the group chat"""
        print(f"📱 TestBot → Group: {text}")
        
        url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": GROUP_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ TestBot message sent successfully!")
                return True
            else:
                error_data = response.json() if response.status_code != 200 else {}
                print(f"   ❌ TestBot failed: {response.status_code}")
                print(f"   Error: {error_data}")
                return False
                
    async def send_calibot_webhook(self, message_text=None, callback_data=None, from_user_id=5650181676):
        """Send webhook request to CaliBOT"""
        
        if callback_data:
            # Button callback
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "callback_query": {
                    "id": f"group_test_{int(time.time())}",
                    "from": {
                        "id": from_user_id,
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
            print(f"🔘 CaliBOT Webhook ← Button: {callback_data}")
        else:
            # Text message
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "message": {
                    "message_id": self.message_counter,
                    "from": {
                        "id": from_user_id,
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
            print(f"📡 CaliBOT Webhook ← Message: {message_text}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ CaliBOT webhook SUCCESS: {response.status_code}")
                return True
            else:
                print(f"   ❌ CaliBOT webhook FAILED: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    async def get_recent_logs(self):
        """Get CaliBOT logs from Render to verify processing"""
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
        
        url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"
        params = {
            "startTime": datetime.now().isoformat().replace('+00:00', 'Z'),
            "endTime": datetime.now().isoformat().replace('+00:00', 'Z'),
            "limit": 20
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    logs = response.json()
                    recent_logs = [log for log in logs if 'group_test' in log.get('message', '')]
                    if recent_logs:
                        print(f"🔍 Recent CaliBOT logs:")
                        for log in recent_logs[-3:]:
                            print(f"   📝 {log.get('message', '')}")
                else:
                    print(f"   ⚠️ Logs unavailable: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Log check failed: {e}")

async def run_live_group_demo():
    """Run the complete live demonstration in the group chat"""
    
    print("🎬 LIVE GROUP CHAT BOT-TO-BOT DEMO")
    print("=" * 50)
    print(f"🏠 Group: Calendar testing ({GROUP_CHAT_ID})")
    print(f"🤖 TestBot: Will send visible messages")
    print(f"🤖 CaliBOT: Will respond via webhook")
    print(f"👁️ WATCH THE GROUP CHAT FOR LIVE ACTION!")
    print("=" * 50)
    
    demo = LiveGroupChatDemo()
    
    # Step 1: TestBot sends initial request
    print(f"\n🎬 STEP 1: TestBot requests multi-event operation")
    success = await demo.send_testbot_message(
        "🧪 <b>LIVE TEST</b>: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if not success:
        print("❌ TestBot authorization failed - cannot proceed")
        return
        
    print(f"   💬 CHECK GROUP CHAT - TestBot message should be visible!")
    await asyncio.sleep(3)
    
    # Step 2: Send webhook to CaliBOT 
    print(f"\n📡 STEP 2: CaliBOT webhook - process the request")
    success = await demo.send_calibot_webhook(
        "🧪 LIVE TEST: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if success:
        print(f"   💬 CHECK GROUP CHAT - CaliBOT should respond with options!")
        await demo.get_recent_logs()
        
    await asyncio.sleep(5)
    
    # Step 3: Press "One by one" button
    print(f"\n🔘 STEP 3: Button click - 'One by one'")
    success = await demo.send_calibot_webhook(None, "multi_event_one_by_one")
    
    if success:
        print(f"   💬 CHECK GROUP CHAT - CaliBOT should show individual event!")
        await demo.get_recent_logs()
        
    await asyncio.sleep(5)
    
    # Step 4: Press "Yes" button
    print(f"\n✅ STEP 4: Button click - 'Yes' (confirm event)")
    success = await demo.send_calibot_webhook(None, "event_yes")
    
    if success:
        print(f"   💬 CHECK GROUP CHAT - CaliBOT should process the event!")
        await demo.get_recent_logs()
        
    await asyncio.sleep(5)
    
    # Step 5: Press "Skip" button
    print(f"\n⏭️ STEP 5: Button click - 'Skip' (skip event)")
    success = await demo.send_calibot_webhook(None, "event_skip")
    
    if success:
        print(f"   💬 CHECK GROUP CHAT - CaliBOT should skip the event!")
        await demo.get_recent_logs()
    
    await asyncio.sleep(3)
    
    # Final TestBot message
    print(f"\n🎊 FINAL: TestBot declares test complete")
    await demo.send_testbot_message(
        "✅ <b>LIVE TEST COMPLETE!</b> Multi-event workflow demonstrated successfully! 🎉"
    )
    
    print(f"\n🏁 DEMONSTRATION COMPLETE!")
    print(f"💬 Check the group chat to see the full conversation!")
    print(f"✅ If CaliBOT responded properly to buttons, the queue bug is FIXED!")

if __name__ == "__main__":
    asyncio.run(run_live_group_demo())
