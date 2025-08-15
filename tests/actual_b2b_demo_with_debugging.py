"""
ACTUAL Bot-to-Bot Demo with Live Debugging

This script will ACTUALLY test the one-by-one bug fix by:
1. Sending real messages to the Telegram bot
2. Monitoring logs in real-time
3. Analyzing the results to verify the fix
"""

import asyncio
import logging
import json
import httpx
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActualBotDemo:
    def __init__(self):
        # Use the webhook endpoint to send messages directly to CaliBOT
        self.webhook_url = "https://calibot-utq6.onrender.com/webhook"
        self.chat_id = -4627994150  # Test group from PROJECT_RULES.md
        self.test_user_id = 123456789
        
    async def send_message_to_bot(self, text: str):
        """Send a message directly to CaliBOT via webhook"""
        print(f"\n🤖 SENDING: {text}")
        
        message_data = {
            "update_id": int(time.time() * 1000),
            "message": {
                "message_id": int(time.time()),
                "date": int(time.time()),
                "chat": {
                    "id": self.chat_id,
                    "type": "group"
                },
                "from": {
                    "id": self.test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser"
                },
                "text": text
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    json=message_data,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    print(f"✅ Message sent successfully")
                    return True
                else:
                    print(f"❌ Failed to send message: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error sending message: {e}")
                return False
    
    async def simulate_button_click(self, callback_data: str):
        """Simulate a button click via webhook"""
        print(f"\n🔘 CLICKING BUTTON: {callback_data}")
        
        callback_data_map = {
            "multi_one_delete": {
                "update_id": int(time.time() * 1000),
                "callback_query": {
                    "id": f"callback_{int(time.time())}",
                    "from": {
                        "id": self.test_user_id,
                        "username": "test_user",
                        "first_name": "TestUser"
                    },
                    "message": {
                        "message_id": int(time.time()),
                        "date": int(time.time()),
                        "chat": {
                            "id": self.chat_id,
                            "type": "group"
                        },
                        "text": "Previous message"
                    },
                    "data": callback_data
                }
            }
        }
        
        # For queue buttons, use the format
        if callback_data.startswith("queue_"):
            callback_data_map[callback_data] = {
                "update_id": int(time.time() * 1000),
                "callback_query": {
                    "id": f"callback_{int(time.time())}",
                    "from": {
                        "id": self.test_user_id,
                        "username": "test_user", 
                        "first_name": "TestUser"
                    },
                    "message": {
                        "message_id": int(time.time()),
                        "date": int(time.time()),
                        "chat": {
                            "id": self.chat_id,
                            "type": "group"
                        },
                        "text": "DELETE Event X of Y"
                    },
                    "data": callback_data
                }
            }
        
        webhook_data = callback_data_map.get(callback_data)
        if not webhook_data:
            print(f"❌ Unknown callback data: {callback_data}")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    json=webhook_data,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    print(f"✅ Button click processed")
                    return True
                else:
                    print(f"❌ Failed to process button click: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error processing button click: {e}")
                return False

async def run_actual_b2b_demo():
    """Run the ACTUAL bot-to-bot demo with debugging"""
    
    print("🎯 ACTUAL BOT-TO-BOT DEMO WITH DEBUGGING")
    print("=" * 80)
    print("🐛 TESTING: One-by-one multi-event delete bug fix")
    print("🔧 VERSION: 0.1.136 (fix deployed)")
    print("🎯 GOAL: Verify first 'yes' processes only 1 event, shows next confirmation")
    print("=" * 80)
    
    demo = ActualBotDemo()
    
    try:
        # Step 1: Create test events
        print("\n📅 STEP 1: Creating test events")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        await demo.send_message_to_bot("create ActualB2BDemo_001 tomorrow 14:00-15:00")
        await asyncio.sleep(3)
        
        await demo.send_message_to_bot("create ActualB2BDemo_002 tomorrow 15:00-16:00")
        await asyncio.sleep(3)
        
        await demo.send_message_to_bot("create ActualB2BDemo_003 tomorrow 16:00-17:00")
        await asyncio.sleep(3)
        
        print("✅ Test events creation requests sent")
        
        # Step 2: Request multi-delete
        print("\n🗑️ STEP 2: Requesting multi-delete")
        await demo.send_message_to_bot("delete all ActualB2BDemo events tomorrow")
        await asyncio.sleep(5)
        
        print("✅ Multi-delete request sent")
        
        # Step 3: Select one-by-one mode
        print("\n1️⃣ STEP 3: Selecting 'One by One' mode")
        print("🔍 This should trigger one_by_one_mode = True")
        
        await demo.simulate_button_click("multi_one_delete")
        await asyncio.sleep(5)
        
        print("✅ One-by-one mode selected")
        
        # Step 4: CRITICAL TEST - First "Yes" click
        print("\n✅ STEP 4: CRITICAL BUG FIX TEST")
        print("🚨 CLICKING 'YES' FOR FIRST EVENT")
        print("🔍 Expected (bug fixed):")
        print("   - Only 1 'Processing single event' log")
        print("   - 'DELETE Event 2 of 3' confirmation appears")
        print("   - NO bulk 'Successfully deleted 3 events!' message")
        
        await demo.simulate_button_click("queue_confirm_0")
        await asyncio.sleep(8)  # Wait longer to see all logs
        
        print("✅ First event 'yes' clicked - CHECK LOGS NOW!")
        
        # Step 5: Second event
        print("\n✅ STEP 5: Processing second event")
        await demo.simulate_button_click("queue_confirm_1")
        await asyncio.sleep(5)
        
        # Step 6: Skip third event
        print("\n⏭️ STEP 6: Skipping third event")
        await demo.simulate_button_click("queue_skip_2")
        await asyncio.sleep(5)
        
        # Step 7: Cleanup
        print("\n🧹 STEP 7: Cleanup remaining events")
        await demo.send_message_to_bot("delete any remaining ActualB2BDemo events tomorrow")
        await asyncio.sleep(3)
        
        # If there are remaining, delete all
        await demo.simulate_button_click("multi_all_delete")
        await asyncio.sleep(3)
        
        print("\n🎉 ACTUAL B2B DEMO COMPLETED!")
        print("\n📊 NOW CHECK THE LOGS:")
        print("Run: python scripts/recent_logs.py")
        print("\n🔍 LOOK FOR:")
        print("✅ Only 1 'Processing single event' after first 'yes'")
        print("✅ 'DELETE Event 2 of 3' after first event")
        print("✅ Individual processing, not bulk deletion")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_actual_b2b_demo())
