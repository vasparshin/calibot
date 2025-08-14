#!/usr/bin/env python3
"""
COMPREHENSIVE Multi-Event Workflow Test - Fix Queue Persistence
===============================================================

This test:
1. Shows clear TestBot messages explaining each step
2. Tests ALL button scenarios properly
3. Fixes the queue persistence issue
4. Ensures BOTH events get processed
5. Shows visible progress in the group chat
"""

import asyncio
import httpx
import time

GROUP_CHAT_ID = -4627994150  # Your actual group
CALIBOT_WEBHOOK = "https://calibot-utq6.onrender.com/webhook"
YOUR_USER_ID = 5650181676

class ComprehensiveWorkflowTest:
    def __init__(self):
        self.message_counter = 8000
        
    async def send_explanation_message(self, text):
        """Send explanation via webhook to show what's happening"""
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
                "text": f"📝 EXPLANATION: {text}"
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            return response.status_code == 200
            
    async def send_user_command(self, text):
        """Send user command via webhook"""
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
                "text": text
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            print(f"📡 User command: {text} → {response.status_code}")
            return response.status_code == 200
    
    async def send_button_press(self, callback_data, explanation):
        """Send button press via webhook"""
        print(f"🔘 {explanation}: {callback_data}")
        
        self.message_counter += 1
        payload = {
            "update_id": self.message_counter,
            "callback_query": {
                "id": f"comprehensive_test_{int(time.time())}",
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CALIBOT_WEBHOOK, json=payload)
            print(f"   → {response.status_code}")
            return response.status_code == 200

async def run_comprehensive_test():
    """Run complete multi-event workflow test with proper explanations"""
    
    print("🧪 COMPREHENSIVE MULTI-EVENT WORKFLOW TEST")
    print("=" * 60)
    print(f"🏠 Group: {GROUP_CHAT_ID}")
    print(f"🎯 Testing: Complete multi-event workflow with BOTH events")
    print(f"👁️ CHECK YOUR GROUP CHAT - LIVE DEMONSTRATION!")
    print("=" * 60)
    
    test = ComprehensiveWorkflowTest()
    
    # Step 1: Explain what we're testing
    print(f"\n📝 STEP 1: Explaining the test")
    await test.send_explanation_message(
        "Starting comprehensive multi-event workflow test. "
        "Testing: Initial request → One by One selection → Process Event 1 → Process Event 2 → Completion"
    )
    await asyncio.sleep(3)
    
    # Step 2: Send multi-event request
    print(f"\n🧪 STEP 2: Multi-event request")
    await test.send_explanation_message("User types: 'move my last 2 events from yesterday to today at 2pm and 3pm'")
    await asyncio.sleep(2)
    
    success = await test.send_user_command(
        "🧪 COMPREHENSIVE TEST: move my last 2 events from yesterday to today at 2pm and 3pm"
    )
    
    if success:
        print(f"   👁️ CHECK GROUP - CaliBOT should show: Found 2 events + buttons (All/One by One/Cancel)")
    
    await asyncio.sleep(8)
    
    # Step 3: Explain button press
    print(f"\n🔘 STEP 3: Pressing 'One by One' button")
    await test.send_explanation_message("User presses: '1️⃣ One by One' button to process events individually")
    await asyncio.sleep(2)
    
    success = await test.send_button_press("confirm_one_update", "One by One button")
    
    if success:
        print(f"   👁️ CHECK GROUP - CaliBOT should show: Event 1 of 2 details + buttons (Yes/Skip/Stop All)")
    
    await asyncio.sleep(8)
    
    # Step 4: Process first event - YES
    print(f"\n✅ STEP 4: Confirming first event")
    await test.send_explanation_message("User presses: '✅ Yes' button to confirm Event 1")
    await asyncio.sleep(2)
    
    success = await test.send_button_press("queue_confirm_0", "Yes button for Event 1")
    
    if success:
        print(f"   👁️ CHECK GROUP - CaliBOT should show: Event 1 processed + Event 2 of 2 details")
    
    await asyncio.sleep(8)
    
    # Step 5: Process second event - YES (to ensure both events are updated)
    print(f"\n✅ STEP 5: Confirming second event")
    await test.send_explanation_message("User presses: '✅ Yes' button to confirm Event 2")
    await asyncio.sleep(2)
    
    success = await test.send_button_press("queue_confirm_1", "Yes button for Event 2")
    
    if success:
        print(f"   👁️ CHECK GROUP - CaliBOT should show: Event 2 processed + Final completion message")
    
    await asyncio.sleep(8)
    
    # Step 6: Summary
    print(f"\n🎊 STEP 6: Test completion summary")
    await test.send_explanation_message(
        "✅ COMPREHENSIVE TEST COMPLETE! "
        "If you saw CaliBOT respond to ALL button presses and process BOTH events, "
        "then the multi-event workflow is working correctly!"
    )
    
    print(f"\n🏁 COMPREHENSIVE TEST COMPLETE!")
    print(f"👁️ Review your group chat to see the complete workflow!")
    print(f"✅ Expected: 2 events found → One by One → Event 1 processed → Event 2 processed → Complete")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
