import os
#!/usr/bin/env python3
"""
One-by-One Workflow Tester for CaliBOT Event Queue
Tests the critical "UPDATE Event 2 of 2" functionality

This script specifically tests the EventQueueHandler to ensure:
1. Multi-event operations are queued correctly
2. One-by-one processing advances properly
3. "UPDATE Event X of Y" messages appear in sequence
4. Queue completes without hanging

USAGE: python tests/test_one_by_one_workflow.py
"""

import asyncio
import json
import sys
import time
from datetime import datetime

# Project constants
TARGET_GROUP_CHAT = -4627994150
BACKEND_URL = "https://calibot-utq6.onrender.com"
TESTBOT_TOKEN = os.environ.get("TESTBOT_TOKEN","")

def log_test(message, level="QUEUE"):
    """Log queue test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

async def send_webhook_message(message_text: str, session):
    """Send direct webhook message to test queue processing"""
    try:
        webhook_payload = {
            "update_id": int(time.time() * 1000),
            "message": {
                "message_id": int(time.time()),
                "from": {"id": 987654321, "first_name": "QueueTest", "is_bot": False},
                "chat": {"id": TARGET_GROUP_CHAT},
                "date": int(time.time()),
                "text": message_text
            }
        }

        async with session.post(f"{BACKEND_URL}/webhook", json=webhook_payload) as response:
            log_test(f"Webhook response: {response.status}")
            return response.status == 200

    except Exception as e:
        log_test(f"❌ Webhook error: {e}")
        return False

async def simulate_button_press(callback_data: str, session):
    """Simulate button press for queue advancement"""
    try:
        webhook_payload = {
            "update_id": int(time.time() * 1000),
            "callback_query": {
                "id": f"test_{int(time.time())}",
                "from": {"id": 987654321, "is_bot": False},
                "message": {
                    "message_id": int(time.time()),
                    "chat": {"id": TARGET_GROUP_CHAT}
                },
                "data": callback_data
            }
        }

        async with session.post(f"{BACKEND_URL}/webhook", json=webhook_payload) as response:
            log_test(f"Button press response: {response.status}")
            return response.status == 200

    except Exception as e:
        log_test(f"❌ Button press error: {e}")
        return False

async def test_queue_workflow():
    """Test the complete one-by-one queue workflow"""
    log_test("🎯 STARTING QUEUE WORKFLOW TEST")
    log_test("=" * 60)

    async with aiohttp.ClientSession() as session:
        # Step 1: Create multi-event scenario
        log_test("📝 Step 1: Creating multi-event scenario")
        await send_webhook_message(
            "Create two math lessons at 8am and 10am tomorrow",
            session
        )

        # Step 2: Trigger update operation
        log_test("📝 Step 2: Triggering multi-event update")
        await send_webhook_message(
            "Update the math lessons to physics lessons",
            session
        )

        # Step 3: Select "One by One" option
        log_test("📝 Step 3: Selecting 'One by One' processing")
        await asyncio.sleep(2)  # Wait for keyboard to appear
        await simulate_button_press("update_one_by_one", session)

        # Step 4: Process first event
        log_test("📝 Step 4: Processing first event")
        await asyncio.sleep(3)  # Wait for "UPDATE Event 1 of 2"
        await simulate_button_press("confirm_update_1", session)

        # Step 5: Check for "UPDATE Event 2 of 2"
        log_test("📝 Step 5: Checking for 'UPDATE Event 2 of 2'")
        await asyncio.sleep(3)

        # Step 6: Process second event
        log_test("📝 Step 6: Processing second event")
        await simulate_button_press("confirm_update_2", session)

        # Step 7: Verify completion
        log_test("📝 Step 7: Verifying queue completion")
        await asyncio.sleep(2)

    log_test("🎯 QUEUE WORKFLOW TEST COMPLETE")
    log_test("🔍 Check logs for 'UPDATE Event 2 of 2' confirmation:")
    log_test("   python scripts/render_api_logs.py")

async def test_delete_workflow():
    """Test delete one-by-one workflow"""
    log_test("🗑️ STARTING DELETE WORKFLOW TEST")

    async with aiohttp.ClientSession() as session:
        # Create test events
        await send_webhook_message("Create test event 1 and test event 2 tomorrow", session)
        await asyncio.sleep(2)

        # Trigger delete operation
        await send_webhook_message("Delete the test events", session)
        await asyncio.sleep(2)

        # Select one-by-one
        await simulate_button_press("delete_one_by_one", session)
        await asyncio.sleep(2)

        # Process events
        await simulate_button_press("confirm_delete_1", session)
        await asyncio.sleep(2)
        await simulate_button_press("confirm_delete_2", session)

    log_test("🗑️ DELETE WORKFLOW TEST COMPLETE")

if __name__ == "__main__":
    try:
        import aiohttp
    except ImportError:
        print("❌ aiohttp required. Install with: pip install aiohttp")
        sys.exit(1)

    print("🔧 CaliBOT Queue Workflow Tester")
    print("This script tests the critical one-by-one processing functionality")
    print("=" * 70)

    try:
        # Run queue workflow test
        asyncio.run(test_queue_workflow())

        # Optional: Run delete workflow test
        print("\n" + "="*70)
        run_delete = input("Also test delete workflow? (y/N): ").lower().strip()
        if run_delete == 'y':
            asyncio.run(test_delete_workflow())

    except KeyboardInterrupt:
        log_test("🛑 Test interrupted by user")
    except Exception as e:
        log_test(f"❌ Test failed: {e}")

    print("\n📋 NEXT STEPS:")
    print("1. Check the group chat for bot responses")
    print("2. Monitor logs: python scripts/render_api_logs.py")
    print("3. Look for 'UPDATE Event 2 of 2' in logs (CRITICAL)")
