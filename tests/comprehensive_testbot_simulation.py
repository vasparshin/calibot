#!/usr/bin/env python3

import requests
import json
import time
import os

# Configuration
CHAT_ID = -4627994150  # Your group chat
BACKEND_URL = "https://calibot-utq6.onrender.com"
TESTBOT_TOKEN = "7669505498:AAE5H3K3iLk7H-cxuAEWucxqhcuBU4QzEk4"  # TestBot token

def send_testbot_message(text):
    """Send visible message as TestBot to group chat"""
    url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ TestBot message sent: {text[:50]}...")
        else:
            print(f"❌ TestBot message failed: {response.status_code}")
    except Exception as e:
        print(f"❌ TestBot error: {e}")

def send_webhook_to_calibot(text=None, callback_data=None):
    """Send webhook to CaliBOT backend"""
    if callback_data:
        # Button press simulation
        data = {
            "callback_query": {
                "id": "testbot_callback",
                "from": {"id": 12345, "first_name": "TestBot", "username": "TestBot"},
                "message": {
                    "message_id": int(time.time()),
                    "chat": {"id": CHAT_ID, "type": "supergroup"},
                    "date": int(time.time())
                },
                "data": callback_data
            }
        }
    else:
        # Text message
        data = {
            "message": {
                "message_id": int(time.time()),
                "from": {"id": 12345, "first_name": "TestBot", "username": "TestBot"},
                "chat": {"id": CHAT_ID, "type": "supergroup"},
                "date": int(time.time()),
                "text": text
            }
        }
    
    try:
        response = requests.post(f"{BACKEND_URL}/webhook", json=data, timeout=30)
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

def run_scenario(scenario_name, steps):
    """Run a complete test scenario"""
    print(f"\n{'='*60}")
    print(f"🎬 SCENARIO: {scenario_name}")
    print(f"{'='*60}")
    
    # Announce scenario start
    send_testbot_message(f"🎬 <b>TESTBOT SCENARIO: {scenario_name}</b>\n\nStarting comprehensive test...")
    time.sleep(2)
    
    for i, step in enumerate(steps, 1):
        step_text = step['text']
        step_action = step['action']
        
        print(f"\n📝 STEP {i}: {step_text}")
        
        # TestBot announces what it's doing
        send_testbot_message(f"📝 <b>Step {i}:</b> {step_text}")
        time.sleep(1)
        
        # Execute the action
        if step_action['type'] == 'message':
            status = send_webhook_to_calibot(text=step_action['content'])
            send_testbot_message(f"💬 TestBot sent: <code>{step_action['content']}</code>")
        elif step_action['type'] == 'button':
            status = send_webhook_to_calibot(callback_data=step_action['content'])
            send_testbot_message(f"🔘 TestBot pressed button: <code>{step_action['content']}</code>")
        
        print(f"   → Webhook status: {status}")
        time.sleep(3)  # Wait for CaliBOT response
    
    # Scenario completion
    send_testbot_message(f"✅ <b>SCENARIO COMPLETE:</b> {scenario_name}\n\nCheck CaliBOT responses above!")
    print(f"\n✅ SCENARIO COMPLETE: {scenario_name}")

# Define all test scenarios
scenarios = [
    {
        "name": "Scenario 1: ALL AT ONCE workflow",
        "steps": [
            {
                "text": "Request multi-event move",
                "action": {"type": "message", "content": "🤖 TESTBOT: move my last 2 events from yesterday to today at 2pm and 3pm"}
            },
            {
                "text": "Press 'All' button",
                "action": {"type": "button", "content": "confirm_all_update"}
            }
        ]
    },
    {
        "name": "Scenario 2: ONE BY ONE - Accept All",
        "steps": [
            {
                "text": "Request multi-event move", 
                "action": {"type": "message", "content": "🤖 TESTBOT: move my last 2 events from yesterday to today at 4pm and 5pm"}
            },
            {
                "text": "Press 'One by One' button",
                "action": {"type": "button", "content": "confirm_one_update"}
            },
            {
                "text": "Press 'Yes' for Event 1",
                "action": {"type": "button", "content": "queue_confirm_0"}
            },
            {
                "text": "Press 'Yes' for Event 2", 
                "action": {"type": "button", "content": "queue_confirm_1"}
            }
        ]
    },
    {
        "name": "Scenario 3: ONE BY ONE - Mixed Responses",
        "steps": [
            {
                "text": "Request multi-event move",
                "action": {"type": "message", "content": "🤖 TESTBOT: move my last 2 events from yesterday to today at 6pm and 7pm"}
            },
            {
                "text": "Press 'One by One' button",
                "action": {"type": "button", "content": "confirm_one_update"}
            },
            {
                "text": "Press 'Yes' for Event 1",
                "action": {"type": "button", "content": "queue_confirm_0"}
            },
            {
                "text": "Press 'Skip' for Event 2",
                "action": {"type": "button", "content": "queue_skip_1"}
            }
        ]
    },
    {
        "name": "Scenario 4: ONE BY ONE - Skip First, Accept Second",
        "steps": [
            {
                "text": "Request multi-event move",
                "action": {"type": "message", "content": "🤖 TESTBOT: move my last 2 events from yesterday to today at 8pm and 9pm"}
            },
            {
                "text": "Press 'One by One' button", 
                "action": {"type": "button", "content": "confirm_one_update"}
            },
            {
                "text": "Press 'Skip' for Event 1",
                "action": {"type": "button", "content": "queue_skip_0"}
            },
            {
                "text": "Press 'Yes' for Event 2",
                "action": {"type": "button", "content": "queue_confirm_1"}
            }
        ]
    },
    {
        "name": "Scenario 5: CANCEL workflow",
        "steps": [
            {
                "text": "Request multi-event move",
                "action": {"type": "message", "content": "🤖 TESTBOT: move my last 2 events from yesterday to today at 10pm and 11pm"}
            },
            {
                "text": "Press 'Cancel' button",
                "action": {"type": "button", "content": "cancel_update"}
            }
        ]
    },
    {
        "name": "Scenario 6: ONE BY ONE - Cancel Mid-Process",
        "steps": [
            {
                "text": "Request multi-event move",
                "action": {"type": "message", "content": "🤖 TESTBOT: move my last 2 events from yesterday to today at 1pm and 2pm"}
            },
            {
                "text": "Press 'One by One' button",
                "action": {"type": "button", "content": "confirm_one_update"}
            },
            {
                "text": "Press 'Yes' for Event 1", 
                "action": {"type": "button", "content": "queue_confirm_0"}
            },
            {
                "text": "Press 'Cancel' for remaining events",
                "action": {"type": "button", "content": "queue_cancel"}
            }
        ]
    }
]

def main():
    print("🤖 COMPREHENSIVE TESTBOT SIMULATION")
    print("=" * 60)
    print("🎯 This TestBot will:")
    print("   1. Send VISIBLE messages to group chat explaining each action")
    print("   2. Simulate button presses with webhook calls")
    print("   3. Test ALL possible multi-event scenarios")
    print("   4. Show exactly what's happening step by step")
    print()
    print(f"🏠 Group Chat: {CHAT_ID}")
    print(f"🔗 Backend: {BACKEND_URL}")
    print()
    
    # Startup announcement
    send_testbot_message("🤖 <b>TESTBOT COMPREHENSIVE SIMULATION STARTING</b>\n\nTesting ALL multi-event scenarios with visible explanations!")
    time.sleep(3)
    
    # Run all scenarios
    for scenario in scenarios:
        run_scenario(scenario["name"], scenario["steps"])
        time.sleep(5)  # Wait between scenarios
    
    # Final summary
    send_testbot_message("🎊 <b>ALL SCENARIOS COMPLETE!</b>\n\nTestBot tested:\n• All at once\n• One by one (various combinations)\n• Cancel workflows\n• Mixed responses\n\nCheck CaliBOT responses for each scenario!")
    
    print("\n" + "=" * 60)
    print("🎊 COMPREHENSIVE SIMULATION COMPLETE!")
    print("✅ All 6 scenarios tested with visible TestBot messages")
    print("👁️ Check your group chat for complete conversation!")
    print("=" * 60)

if __name__ == "__main__":
    main()
