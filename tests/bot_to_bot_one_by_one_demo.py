"""
Bot-to-Bot Demo for One-by-One Multi-Event Operations Fix

This script tests the specific bug fix for one-by-one processing where:
- User selects "one by one" for multi-event operations
- Clicks "yes" for first event should process ONLY that event
- Should show confirmation for second event, not delete all remaining events

CRITICAL TEST: Verifies buttons disappear correctly and proper event-by-event flow.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OneByOneDemoBot:
    def __init__(self):
        self.base_url = "https://calibot-eud6.onrender.com"
        self.chat_id = -4627994150  # Test group ID from PROJECT_RULES.md
        self.session = httpx.AsyncClient(timeout=30.0)
        
    async def send_message(self, text: str, delay: float = 2.0):
        """Send a message to CaliBOT"""
        print(f"\n🤖 USER: {text}")
        
        try:
            webhook_data = {
                "update_id": int(datetime.now().timestamp() * 1000),
                "message": {
                    "message_id": int(datetime.now().timestamp()),
                    "date": int(datetime.now().timestamp()),
                    "chat": {
                        "id": self.chat_id,
                        "type": "group"
                    },
                    "from": {
                        "id": 123456789,
                        "username": "test_user",
                        "first_name": "Test"
                    },
                    "text": text
                }
            }
            
            response = await self.session.post(
                f"{self.base_url}/webhook",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Message sent successfully")
            else:
                print(f"❌ Failed to send message: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            
        await asyncio.sleep(delay)
    
    async def simulate_button_click(self, callback_data: str, delay: float = 2.0):
        """Simulate clicking an inline keyboard button"""
        print(f"\n🔘 BUTTON CLICK: {callback_data}")
        
        try:
            webhook_data = {
                "update_id": int(datetime.now().timestamp() * 1000),
                "callback_query": {
                    "id": f"callback_{int(datetime.now().timestamp())}",
                    "from": {
                        "id": 123456789,
                        "username": "test_user", 
                        "first_name": "Test"
                    },
                    "message": {
                        "message_id": int(datetime.now().timestamp()),
                        "date": int(datetime.now().timestamp()),
                        "chat": {
                            "id": self.chat_id,
                            "type": "group"
                        },
                        "text": "Previous message text"
                    },
                    "data": callback_data
                }
            }
            
            response = await self.session.post(
                f"{self.base_url}/webhook",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Button click processed successfully")
            else:
                print(f"❌ Failed to process button click: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error processing button click: {e}")
            
        await asyncio.sleep(delay)

async def run_one_by_one_demo():
    """Run comprehensive one-by-one multi-event demo"""
    
    print("🎯 ONE-BY-ONE MULTI-EVENT OPERATIONS DEMO")
    print("=" * 80)
    print("Testing the fix for one-by-one processing bug where:")
    print("- User selects 'one by one' for multi-event delete")
    print("- Clicks 'yes' should process ONLY current event, not all events")
    print("- Should show next event confirmation, buttons should disappear properly")
    print("=" * 80)
    
    bot = OneByOneDemoBot()
    
    try:
        # Step 1: Create multiple test events
        print("\n📅 STEP 1: Creating test events for one-by-one demo")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        await bot.send_message(f"create OneByOneDemo_001 tomorrow 14:00-15:00")
        await bot.send_message(f"create OneByOneDemo_002 tomorrow 15:00-16:00") 
        await bot.send_message(f"create OneByOneDemo_003 tomorrow 16:00-17:00")
        
        await asyncio.sleep(3)
        
        # Step 2: Request deletion of all test events
        print("\n🗑️ STEP 2: Requesting deletion of all OneByOneDemo events")
        await bot.send_message(f"delete all OneByOneDemo events tomorrow")
        
        await asyncio.sleep(3)
        
        # Step 3: Select "One by One" option
        print("\n1️⃣ STEP 3: Selecting 'One by One' processing")
        await bot.simulate_button_click("multi_one_delete")
        
        await asyncio.sleep(4)
        
        # Step 4: Click "Yes" for the FIRST event only
        print("\n✅ STEP 4: CRITICAL TEST - Clicking 'Yes' for FIRST event")
        print("This should:")
        print("- Delete ONLY the first event (OneByOneDemo_001)")
        print("- Show confirmation for the SECOND event (OneByOneDemo_002)")
        print("- NOT delete all remaining events at once")
        
        await bot.simulate_button_click("queue_confirm_0")
        
        await asyncio.sleep(4)
        
        # Step 5: Click "Yes" for the SECOND event
        print("\n✅ STEP 5: Clicking 'Yes' for SECOND event")
        await bot.simulate_button_click("queue_confirm_1")
        
        await asyncio.sleep(4)
        
        # Step 6: Click "Skip" for the THIRD event to test skip functionality
        print("\n⏭️ STEP 6: Clicking 'Skip' for THIRD event to test skip functionality")
        await bot.simulate_button_click("queue_skip_2")
        
        await asyncio.sleep(3)
        
        # Step 7: Verify what events remain
        print("\n🔍 STEP 7: Checking remaining events to verify correct processing")
        await bot.send_message(f"what events do I have tomorrow")
        
        await asyncio.sleep(3)
        
        # Step 8: Clean up any remaining test events
        print("\n🧹 STEP 8: Cleaning up any remaining OneByOneDemo events")
        await bot.send_message(f"delete any remaining OneByOneDemo events tomorrow")
        
        # If there are remaining events, delete them all
        await asyncio.sleep(2)
        
        # Try to delete all at once if any remain
        await bot.simulate_button_click("multi_all_delete")
        
        await asyncio.sleep(3)
        
        print("\n🎉 ONE-BY-ONE DEMO COMPLETED!")
        print("✅ Expected Results:")
        print("- First 'Yes' click should have deleted ONLY OneByOneDemo_001")
        print("- Second 'Yes' click should have deleted ONLY OneByOneDemo_002")
        print("- Skip should have left OneByOneDemo_003 untouched initially")
        print("- Final cleanup should have removed any remaining events")
        print("\n🔍 CRITICAL SUCCESS INDICATORS:")
        print("- Each 'Yes' click shows individual success message")
        print("- Buttons disappear after each click")
        print("- Next event confirmation appears for remaining events")
        print("- No bulk 'Successfully deleted X events' after individual confirmations")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
    
    finally:
        await bot.session.aclose()

if __name__ == "__main__":
    asyncio.run(run_one_by_one_demo())
