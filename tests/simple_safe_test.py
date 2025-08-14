#!/usr/bin/env python3
"""
SIMPLE SAFE TEST for CaliBOT Multi-Event
- Creates ONE clearly marked test event
- Shows you the live logs 
- Tests deletion of ONLY that test event
"""

import asyncio
import aiohttp
import requests
import time
from datetime import datetime, timedelta

class SimpleeSafeTest:
    def __init__(self):
        self.backend_url = "https://calibot-utq6.onrender.com"
        self.webhook_url = f"{self.backend_url}/webhook"
        self.testbot_token = "7638628162:AAE-0eKLVAVjfNaP1sZgdYUzPbVmJkMjfN0"
        self.group_chat_id = -4627994150
        self.render_api_key = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"
        self.message_id = 1000
    
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
                    "first_name": "SafeTestUser",
                    "username": "safe_test_user"
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
    
    async def send_testbot_message(self, message: str):
        """Send visual message to Telegram group"""
        try:
            url = f"https://api.telegram.org/bot{self.testbot_token}/sendMessage"
            data = {
                "chat_id": self.group_chat_id,
                "text": f"[SafeTest] TestUser: {message}",
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print(f"[CHECK] Visual message sent to group: {message}")
                return True
            else:
                print(f"[X] Failed to send visual message: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[X] TestBot error: {e}")
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
                    
                    if status == 200:
                        print(f"[CHECK] Webhook sent to CaliBOT: {message}")
                        return True
                    else:
                        print(f"[X] Webhook failed: {status}")
                        return False
                        
        except Exception as e:
            print(f"[X] Webhook error: {e}")
            return False
    
    async def get_recent_logs(self):
        """Get recent logs from Render API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.render_api_key}",
                "Content-Type": "application/json"
            }
            
            # Get logs from last 2 minutes
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=2)
            
            url = f"https://api.render.com/v1/services/srv-ctfbqacl6cac73aro0q0/logs"
            params = {
                "startTime": start_time.isoformat() + "Z",
                "endTime": end_time.isoformat() + "Z",
                "limit": 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logs = data.get("logs", [])
                        
                        print(f"\n[CLOCK] RECENT LOGS ({len(logs)} entries):")
                        print("-" * 60)
                        
                        for log in logs[-10:]:  # Show last 10
                            timestamp = log.get("timestamp", "")[:19].replace("T", " ")
                            message = log.get("message", "")[:80]
                            print(f"[LOG] {timestamp} | {message}")
                        
                        return True
                    else:
                        print(f"[X] Failed to get logs: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"[X] Log fetch error: {e}")
            return False

async def main():
    """Run simple safe test"""
    print("[ROBOT] SIMPLE SAFE CALIBOT TEST")
    print("=" * 50)
    print("[CHECK] This test will:")
    print("  • Create ONE test event: TEST_SAFE_EVENT_001")
    print("  • Send BOTH visual TestBot message AND webhook to CaliBOT") 
    print("  • Show you live logs from Render")
    print("  • Test deletion of ONLY that test event")
    print()
    
    tester = SimpleeSafeTest()
    
    # Step 1: Create safe test event
    print("[FIX] STEP 1: Creating safe test event...")
    create_message = "create TEST_SAFE_EVENT_001 tomorrow at 2pm-3pm for testing"
    
    print(f"[MSG] Message: {create_message}")
    visual_sent = await tester.send_testbot_message(create_message)
    webhook_sent = await tester.send_webhook_to_calibot(create_message)
    
    if visual_sent and webhook_sent:
        print("[CHECK] Both visual message and webhook sent!")
    else:
        print("[X] Failed to send messages properly")
    
    # Wait and check logs
    print("\n[CLOCK] Waiting 5 seconds for processing...")
    await asyncio.sleep(5)
    
    print("\n[STATS] CHECKING LOGS...")
    await tester.get_recent_logs()
    
    # Step 2: Test deletion of ONLY our test event
    print("\n[FIX] STEP 2: Testing safe deletion...")
    delete_message = "delete TEST_SAFE_EVENT_001"
    
    print(f"[MSG] Message: {delete_message}")
    visual_sent = await tester.send_testbot_message(delete_message)
    webhook_sent = await tester.send_webhook_to_calibot(delete_message)
    
    # Wait and check logs again
    print("\n[CLOCK] Waiting 5 seconds for processing...")
    await asyncio.sleep(5)
    
    print("\n[STATS] CHECKING LOGS AFTER DELETION...")
    await tester.get_recent_logs()
    
    print("\n[CHECK] Safe test completed!")
    print("[REPORT] Check your Telegram group for:")
    print("  • TestBot messages (visual)")
    print("  • CaliBOT responses (via webhook)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[X] Test interrupted")
    except Exception as e:
        print(f"\n[X] Error: {e}")
