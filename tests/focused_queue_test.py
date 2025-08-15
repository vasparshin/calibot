#!/usr/bin/env python3
"""
FOCUSED QUEUE PROGRESSION TEST
Tests specifically the one-by-one button progression issue
"""

import requests
import json
import time

# Configuration
CHAT_ID = -4627994150
BACKEND_URL = "https://calibot-utq6.onrender.com"
TESTBOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"

def send_testbot_message(text):
    """Send visible TestBot message"""
    url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ TestBot: {text[:50]}...")
            return True
        else:
            print(f"❌ TestBot failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ TestBot error: {e}")
        return False

def send_webhook(text=None, callback_data=None):
    """Send webhook to CaliBOT"""
    timestamp = int(time.time())
    
    if callback_data:
        data = {
            "update_id": timestamp,
            "callback_query": {
                "id": f"test_{timestamp}",
                "from": {"id": 999999999, "first_name": "TestUser", "username": "testuser", "is_bot": False},
                "message": {
                    "message_id": timestamp - 1,
                    "chat": {"id": CHAT_ID, "type": "supergroup", "title": "Calendar testing"},
                    "date": timestamp - 1,
                    "text": "Multi-event message",
                    "from": {"id": 7669505498, "first_name": "CaliBOT", "username": "CaliBOT_bot", "is_bot": True}
                },
                "data": callback_data
            }
        }
        action = f"🔘 BUTTON: {callback_data}"
    else:
        data = {
            "update_id": timestamp,
            "message": {
                "message_id": timestamp,
                "from": {"id": 999999999, "first_name": "TestUser", "username": "testuser", "is_bot": False},
                "chat": {"id": CHAT_ID, "type": "supergroup", "title": "Calendar testing"},
                "date": timestamp,
                "text": text
            }
        }
        action = f"💬 MESSAGE: {text}"
    
    try:
        response = requests.post(f"{BACKEND_URL}/webhook", json=data, timeout=30)
        status = response.status_code
        print(f"   📡 {action} → {status}")
        return status
    except Exception as e:
        print(f"   ❌ {action} → Error: {e}")
        return None

def main():
    print("🔍 FOCUSED QUEUE PROGRESSION TEST")
    print("=" * 50)
    print("🎯 Testing the exact one-by-one button progression issue")
    print("👁️ WATCH GROUP CHAT for CaliBOT responses!")
    print()
    
    # Start test
    send_testbot_message("🔍 <b>FOCUSED QUEUE TEST</b>\n\nTesting one-by-one progression step by step...")
    time.sleep(2)
    
    print("📋 STEP 1: Multi-event request (should find events and show buttons)")
    send_testbot_message("📋 Step 1: Sending multi-event request")
    status = send_webhook(text="🔍 QUEUE TEST: move my last 2 lessons from today to tomorrow")
    time.sleep(4)
    
    print("📋 STEP 2: Press 'One by One' button (should start queue mode)")
    send_testbot_message("📋 Step 2: Pressing One by One button")
    status = send_webhook(callback_data="confirm_one_update")
    time.sleep(4)
    
    print("📋 STEP 3: Press 'Yes' for Event 1 (should show Event 2 of 2)")
    send_testbot_message("📋 Step 3: Pressing Yes for Event 1 - should show Event 2")
    status = send_webhook(callback_data="queue_confirm_0")
    time.sleep(4)
    
    print("📋 STEP 4: Press 'Yes' for Event 2 (should complete)")
    send_testbot_message("📋 Step 4: Pressing Yes for Event 2 - should complete")
    status = send_webhook(callback_data="queue_confirm_1")
    time.sleep(4)
    
    send_testbot_message("✅ <b>TEST COMPLETE</b>\n\nExpected behavior:\n• Step 1: Show events + buttons\n• Step 2: Show Event 1 of 2\n• Step 3: Show Event 2 of 2\n• Step 4: Completion message")
    
    print("\n🎯 CRITICAL CHECKS:")
    print("✅ After Step 2: Should see 'UPDATE Event 1 of 2'")
    print("✅ After Step 3: Should see 'UPDATE Event 2 of 2' (THIS IS THE BUG)")
    print("✅ After Step 4: Should see completion message")
    print("\n👁️ CHECK YOUR GROUP CHAT to see what actually happened!")
    print("📋 Run: python scripts/recent_logs.py to see backend processing")

if __name__ == "__main__":
    main()
