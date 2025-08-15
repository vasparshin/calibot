#!/usr/bin/env python3
"""
NO USER INPUT AUTO-RUNNING TESTBOT SIMULATION
Shows visible TestBot messages + CaliBOT responses in group chat
Tests ALL multi-event scenarios automatically
"""

import requests
import json
import time

# Configuration - NO USER INPUT REQUIRED
CHAT_ID = -4627994150  # Your group chat
BACKEND_URL = "https://calibot-utq6.onrender.com"

# Try multiple TestBot tokens to find working one
TESTBOT_TOKENS = [
    "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA",  # Latest
    "7638628162:AAE-0eKLVAVjfNaP1sZgdYUzPbVmJkMjfN0",  # Backup 1
    "7425086142:AAEb3FUJGlhUfpMu5DRnDNfYW9g_cQHFVys",  # Backup 2
]

def find_working_testbot_token():
    """Find a working TestBot token automatically"""
    for token in TESTBOT_TOKENS:
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    print(f"✅ Found working TestBot: {bot_info['result']['first_name']} (@{bot_info['result']['username']})")
                    return token
        except:
            continue
    return None

def send_testbot_message(token, text):
    """Send visible TestBot message to group chat"""
    if not token:
        print(f"❌ No working TestBot token - message: {text[:30]}...")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ TestBot: {text[:40]}...")
            return True
        else:
            print(f"❌ TestBot failed ({response.status_code}): {text[:30]}...")
            return False
    except Exception as e:
        print(f"❌ TestBot error: {e}")
        return False

def send_webhook_to_calibot(text=None, callback_data=None):
    """Send webhook to CaliBOT backend"""
    timestamp = int(time.time())
    
    if callback_data:
        data = {
            "update_id": timestamp,
            "callback_query": {
                "id": f"test_{timestamp}",
                "from": {
                    "id": 999999999,
                    "first_name": "TestUser",
                    "username": "testuser",
                    "is_bot": False
                },
                "message": {
                    "message_id": timestamp - 1,
                    "chat": {
                        "id": CHAT_ID,
                        "type": "supergroup",
                        "title": "Calendar testing"
                    },
                    "date": timestamp - 1,
                    "text": "Multi-event message",
                    "from": {
                        "id": 7669505498,
                        "first_name": "CaliBOT", 
                        "username": "CaliBOT_bot",
                        "is_bot": True
                    }
                },
                "data": callback_data
            }
        }
    else:
        data = {
            "update_id": timestamp,
            "message": {
                "message_id": timestamp,
                "from": {
                    "id": 999999999,
                    "first_name": "TestUser",
                    "username": "testuser",
                    "is_bot": False
                },
                "chat": {
                    "id": CHAT_ID,
                    "type": "supergroup", 
                    "title": "Calendar testing"
                },
                "date": timestamp,
                "text": text
            }
        }
    
    try:
        response = requests.post(f"{BACKEND_URL}/webhook", json=data, timeout=30)
        status = response.status_code
        print(f"   📡 Webhook → {status}")
        return status
    except Exception as e:
        print(f"   ❌ Webhook error: {e}")
        return None

def run_auto_scenario(testbot_token, scenario_name, steps):
    """Run scenario automatically with visible TestBot messages"""
    print(f"\n{'='*60}")
    print(f"🎬 AUTO-RUNNING: {scenario_name}")
    print(f"{'='*60}")
    
    # TestBot announces scenario start
    send_testbot_message(testbot_token, f"🎬 <b>TESTBOT AUTO-DEMO: {scenario_name}</b>\n\nStarting automated multi-event test...")
    time.sleep(2)
    
    for i, step in enumerate(steps, 1):
        step_desc = step['desc']
        
        print(f"\n📋 AUTO-STEP {i}: {step_desc}")
        
        # TestBot announces what it's doing
        send_testbot_message(testbot_token, f"📋 <b>Step {i}:</b> {step_desc}")
        time.sleep(1)
        
        # Execute action
        if step['type'] == 'message':
            send_testbot_message(testbot_token, f"💬 TestBot sends: <code>{step['content']}</code>")
            status = send_webhook_to_calibot(text=step['content'])
        elif step['type'] == 'button':
            send_testbot_message(testbot_token, f"🔘 TestBot presses: <code>{step['content']}</code>")
            status = send_webhook_to_calibot(callback_data=step['content'])
        
        # Wait for CaliBOT response
        time.sleep(4)
    
    # Scenario completion
    send_testbot_message(testbot_token, f"✅ <b>SCENARIO COMPLETE:</b> {scenario_name}")
    print(f"✅ AUTO-COMPLETED: {scenario_name}")

def main():
    print("🤖 AUTO-RUNNING COMPREHENSIVE TESTBOT SIMULATION")
    print("=" * 60)
    print("🎯 NO USER INPUT REQUIRED - RUNS AUTOMATICALLY")
    print("📺 Shows visible TestBot messages + CaliBOT responses")
    print("🔄 Tests ALL multi-event workflow scenarios")
    print()
    
    # Find working TestBot token automatically
    print("🔍 Finding working TestBot token...")
    testbot_token = find_working_testbot_token()
    
    if not testbot_token:
        print("❌ NO WORKING TESTBOT TOKENS FOUND")
        print("📋 Will run webhook tests without visible TestBot messages")
        testbot_token = None
    
    print(f"🏠 Group Chat: {CHAT_ID}")
    print(f"🔗 Backend: {BACKEND_URL}")
    print()
    
    # Step 1: Create fake events for testing
    fake_event_names = [f"TestB2B_{i:03d}" for i in range(1, 4)]
    create_steps = []
    for idx, name in enumerate(fake_event_names):
        # Stagger times for clarity
        hour = 10 + idx
        create_steps.append({
            "type": "message",
            "desc": f"Create fake event {name}",
            "content": f"create event {name} tomorrow at {hour}:00"
        })

    # Step 2: Multi-event update targeting only fake events
    update_steps = [
        {
            "type": "message",
            "desc": "Request multi-event update for fake events",
            "content": f"move all TestB2B events tomorrow to next Monday at 15:00"
        },
        {"type": "button", "desc": "Press One by One", "content": "confirm_one_update"},
        {"type": "button", "desc": "Accept Event 1", "content": "queue_confirm_0"},
        {"type": "button", "desc": "Accept Event 2", "content": "queue_confirm_1"},
        {"type": "button", "desc": "Accept Event 3", "content": "queue_confirm_2"}
    ]

    # Step 3: Clean up fake events
    cleanup_steps = [
        {
            "type": "message",
            "desc": "Delete all fake events",
            "content": "delete all TestB2B events next Monday"
        },
        {"type": "button", "desc": "Press All button", "content": "confirm_all_delete"}
    ]

    # Combine all steps
    all_steps = create_steps + update_steps + cleanup_steps

    # Run as a single scenario
    print("\n🔄 AUTO-RUNNING scenario: FAKE EVENTS ONE-BY-ONE UPDATE TEST")
    run_auto_scenario(testbot_token, "FAKE EVENTS ONE-BY-ONE UPDATE TEST", all_steps)

    # Final summary
    if testbot_token:
        send_testbot_message(testbot_token, "🎊 <b>ALL AUTO-SCENARIOS COMPLETE!</b>\n\nTested:\n• Fake event creation\n• One by one update\n• Cleanup\n\nCheck CaliBOT responses above!")

    print(f"\n{'='*60}")
    print("🎊 COMPREHENSIVE AUTO-SIMULATION COMPLETE!")
    print("✅ Tested fake event one-by-one update and cleanup automatically")
    print("📺 Visible TestBot explanations for each action")
    print("👁️ CHECK YOUR GROUP CHAT for complete conversation!")
    print("📋 All scenarios ran without user input")
    print("="*60)

if __name__ == "__main__":
    main()
