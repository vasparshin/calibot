#!/usr/bin/env python3

import requests
import json
import time

# Your actual group chat ID
CHAT_ID = -4627994150
BACKEND_URL = "https://calibot-utq6.onrender.com"

def send_webhook(text, callback_data=None):
    """Send webhook to CaliBOT backend"""
    if callback_data:
        # Button press
        data = {
            "callback_query": {
                "id": "test_callback",
                "from": {"id": 12345, "first_name": "Test"},
                "message": {
                    "message_id": 1,
                    "chat": {"id": CHAT_ID, "type": "group"},
                    "date": int(time.time())
                },
                "data": callback_data
            }
        }
    else:
        # Text message
        data = {
            "message": {
                "message_id": 1,
                "from": {"id": 12345, "first_name": "Test"},
                "chat": {"id": CHAT_ID, "type": "group"},
                "date": int(time.time()),
                "text": text
            }
        }
    
    try:
        response = requests.post(f"{BACKEND_URL}/webhook", json=data, timeout=30)
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

print("🔧 FINAL VERIFICATION - MessageFormatter Fix")
print("=" * 50)
print(f"🎯 Testing backend after v0.1.131 deployment")
print(f"🏠 Group: {CHAT_ID}")
print()

# Test 1: Basic multi-event request
print("📝 STEP 1: Multi-event request")
status = send_webhook("🔧 FINAL TEST: move my last 2 events from yesterday to today at 2pm and 3pm")
print(f"   → {status}")

time.sleep(2)

# Test 2: One by One button
print("🔘 STEP 2: One by One button")
status = send_webhook("", "confirm_one_update")
print(f"   → {status}")

time.sleep(2)

# Test 3: First event confirmation
print("✅ STEP 3: First event Yes")
status = send_webhook("", "queue_confirm_0")
print(f"   → {status}")

time.sleep(2)

# Test 4: Second event confirmation
print("✅ STEP 4: Second event Yes")
status = send_webhook("", "queue_confirm_1")
print(f"   → {status}")

print()
print("🎊 FINAL VERIFICATION COMPLETE!")
print("✅ All webhooks should return 200 if MessageFormatter fix is working")
print("👁️ Check your group chat for CaliBOT responses!")
