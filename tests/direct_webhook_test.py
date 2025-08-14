#!/usr/bin/env python3
"""
Direct CaliBOT Webhook Test with Live Log Monitoring
===================================================

This sends webhook requests directly to CaliBOT and monitors logs in real-time
so you can see exactly what's happening in the backend.
"""

import asyncio
import httpx
import time
import subprocess
import sys

CALIBOT_WEBHOOK = "https://calibot-utq6.onrender.com/webhook"
YOUR_USER_ID = 5650181676

class DirectWebhookTester:
    def __init__(self):
        self.message_counter = 4000
        
    async def send_webhook(self, message_text=None, callback_data=None):
        """Send webhook request directly to CaliBOT"""
        
        if callback_data:
            # Button callback
            self.message_counter += 1
            payload = {
                "update_id": self.message_counter,
                "callback_query": {
                    "id": f"direct_test_{int(time.time())}",
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
            print(f"🔘 WEBHOOK ← Button: {callback_data}")
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
            print(f"📡 WEBHOOK ← Message: {message_text}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: CaliBOT responded (status: {response.status_code})")
                return True
            else:
                print(f"   ❌ FAILED: {response.status_code} - {response.text}")
                return False
                
    def check_logs(self):
        """Get latest logs immediately"""
        print(f"🔍 CHECKING LATEST LOGS...")
        try:
            result = subprocess.run([
                sys.executable, "scripts/recent_logs.py"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                # Get last 15 lines that contain useful info
                relevant_lines = [line for line in lines[-20:] if any(keyword in line.lower() for keyword in 
                    ['multi_event', 'callback', 'button', 'event_yes', 'event_skip', 'confirm', 'queue', 'update operation'])]
                
                if relevant_lines:
                    print(f"📋 RECENT RELEVANT LOGS:")
                    for line in relevant_lines[-5:]:  # Last 5 relevant entries
                        print(f"   {line}")
                else:
                    print(f"   📋 No relevant logs found in last 20 entries")
            else:
                print(f"   ⚠️ Log check failed: {result.stderr}")
        except Exception as e:
            print(f"   ⚠️ Log check error: {e}")

async def run_direct_webhook_test():
    """Run direct webhook test with live monitoring"""
    
    print("🎯 DIRECT CALIBOT WEBHOOK TEST")
    print("=" * 50)
    print(f"👤 Your User ID: {YOUR_USER_ID}")
    print(f"🎯 Target: CaliBOT webhook directly")
    print(f"📊 Live log monitoring included")
    print("=" * 50)
    
    tester = DirectWebhookTester()
    
    # Test 1: Multi-event request
    print(f"\n🧪 TEST 1: Multi-event request")
    success = await tester.send_webhook(
        "🧪 DIRECT TEST: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if success:
        print(f"✅ Check your CaliBOT private chat for response!")
        await asyncio.sleep(2)
        tester.check_logs()
        
    await asyncio.sleep(3)
    
    # Test 2: One by one button  
    print(f"\n🔘 TEST 2: 'One by one' button")
    success = await tester.send_webhook(None, "confirm_one_update")
    
    if success:
        await asyncio.sleep(2)
        tester.check_logs()
        
    await asyncio.sleep(3)
    
    # Test 3: Yes button (queue navigation)
    print(f"\n✅ TEST 3: 'Yes' button")
    success = await tester.send_webhook(None, "queue_confirm_0")
    
    if success:
        await asyncio.sleep(2)
        tester.check_logs()
        
    await asyncio.sleep(3)
    
    # Test 4: Skip button (queue navigation)
    print(f"\n⏭️ TEST 4: 'Skip' button")
    success = await tester.send_webhook(None, "queue_skip_0")
    
    if success:
        await asyncio.sleep(2)
        tester.check_logs()
    
    print(f"\n🏁 TESTING COMPLETE!")
    print(f"📱 Check your CaliBOT private chat to see all responses")
    print(f"📊 Logs above show backend processing details")

if __name__ == "__main__":
    asyncio.run(run_direct_webhook_test())
