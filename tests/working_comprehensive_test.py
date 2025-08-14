#!/usr/bin/env python3

import requests
import json
import time

# Configuration
CHAT_ID = -4627994150  # Your group chat
BACKEND_URL = "https://calibot-utq6.onrender.com"

def send_webhook_to_calibot(text=None, callback_data=None, scenario_name="", step_name=""):
    """Send properly formatted webhook to CaliBOT backend"""
    timestamp = int(time.time())
    update_id = timestamp  # Use timestamp as update_id
    
    if callback_data:
        # Button press simulation - proper Telegram callback query format
        data = {
            "update_id": update_id,
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
                    "text": "Multi-event operation message",
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
        action_desc = f"🔘 BUTTON: {callback_data}"
    else:
        # Text message simulation - proper Telegram message format
        data = {
            "update_id": update_id,
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
        action_desc = f"💬 MESSAGE: {text}"
    
    print(f"\n🚀 {scenario_name}")
    print(f"   📋 {step_name}")
    print(f"   {action_desc}")
    print(f"   📡 Sending webhook...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/webhook", json=data, timeout=30)
        status = response.status_code
        if status == 200:
            print(f"   ✅ SUCCESS: {status}")
        else:
            print(f"   ❌ FAILED: {status}")
            if response.text:
                print(f"   📄 Error: {response.text[:100]}...")
        return status
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return f"Error: {e}"

def wait_and_prompt(step_desc):
    """Wait and prompt user to check group chat"""
    print(f"   ⏳ Waiting 3 seconds for CaliBOT response...")
    time.sleep(3)
    print(f"   👁️ CHECK GROUP CHAT: CaliBOT should respond to '{step_desc}'")

def run_quick_scenario(name, description, steps):
    """Run a test scenario efficiently"""
    print(f"\n{'='*70}")
    print(f"🎬 {name}")
    print(f"📝 {description}")
    print(f"{'='*70}")
    
    for i, step in enumerate(steps, 1):
        step_name = f"Step {i}: {step['desc']}"
        
        if step['type'] == 'message':
            status = send_webhook_to_calibot(
                text=step['content'], 
                scenario_name=name,
                step_name=step_name
            )
        elif step['type'] == 'button':
            status = send_webhook_to_calibot(
                callback_data=step['content'],
                scenario_name=name, 
                step_name=step_name
            )
        
        wait_and_prompt(step['desc'])
    
    print(f"✅ {name} COMPLETE!")

def main():
    print("🤖 COMPREHENSIVE MULTI-EVENT WORKFLOW TESTING")
    print("=" * 70)
    print("🎯 This will test ALL multi-event scenarios:")
    print("   • All at once vs One by one")
    print("   • Accept, skip, and cancel combinations")
    print("   • Proper button press simulations")
    print()
    print(f"🏠 Group: {CHAT_ID}")
    print(f"🔗 Backend: {BACKEND_URL}")
    print()
    
    scenarios = [
        {
            "name": "SCENARIO 1: All At Once",
            "desc": "Process both events immediately with 'All' button",
            "steps": [
                {"type": "message", "desc": "Multi-event request", "content": "🧪 DEMO 1: move my last 2 events from yesterday to today at 2pm and 3pm"},
                {"type": "button", "desc": "Press All button", "content": "confirm_all_update"}
            ]
        },
        {
            "name": "SCENARIO 2: One by One - Accept Both", 
            "desc": "Review each event individually, accept both",
            "steps": [
                {"type": "message", "desc": "Multi-event request", "content": "🧪 DEMO 2: move my last 2 events from yesterday to today at 4pm and 5pm"},
                {"type": "button", "desc": "Press One by One", "content": "confirm_one_update"},
                {"type": "button", "desc": "Accept Event 1", "content": "queue_confirm_0"},
                {"type": "button", "desc": "Accept Event 2", "content": "queue_confirm_1"}
            ]
        },
        {
            "name": "SCENARIO 3: One by One - Mixed Response",
            "desc": "Accept first event, skip second event", 
            "steps": [
                {"type": "message", "desc": "Multi-event request", "content": "🧪 DEMO 3: move my last 2 events from yesterday to today at 6pm and 7pm"},
                {"type": "button", "desc": "Press One by One", "content": "confirm_one_update"},
                {"type": "button", "desc": "Accept Event 1", "content": "queue_confirm_0"},
                {"type": "button", "desc": "Skip Event 2", "content": "queue_skip_1"}
            ]
        },
        {
            "name": "SCENARIO 4: Cancel Workflow",
            "desc": "Start multi-event operation then cancel immediately",
            "steps": [
                {"type": "message", "desc": "Multi-event request", "content": "🧪 DEMO 4: move my last 2 events from yesterday to today at 8pm and 9pm"},
                {"type": "button", "desc": "Press Cancel", "content": "cancel_update"}
            ]
        },
        {
            "name": "SCENARIO 5: Mid-Process Cancel",
            "desc": "Accept first event, then cancel remaining",
            "steps": [
                {"type": "message", "desc": "Multi-event request", "content": "🧪 DEMO 5: move my last 2 events from yesterday to today at 10pm and 11pm"},
                {"type": "button", "desc": "Press One by One", "content": "confirm_one_update"},
                {"type": "button", "desc": "Accept Event 1", "content": "queue_confirm_0"},
                {"type": "button", "desc": "Cancel remaining", "content": "queue_cancel"}
            ]
        }
    ]
    
    print("🚀 Starting comprehensive testing...")
    print("👁️ WATCH YOUR GROUP CHAT for CaliBOT responses!")
    print()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔄 Running scenario {i}/{len(scenarios)}...")
        run_quick_scenario(scenario["name"], scenario["desc"], scenario["steps"])
        
        if i < len(scenarios):
            print(f"\n⏳ Pause before next scenario...")
            time.sleep(5)
    
    print(f"\n{'='*70}")
    print("🎊 ALL TESTING COMPLETE!")
    print("✅ Tested 5 comprehensive multi-event scenarios")
    print("🎯 Expected results:")
    print("   • Scenario 1: Both events processed at once")
    print("   • Scenario 2: Both events processed individually") 
    print("   • Scenario 3: First event processed, second skipped")
    print("   • Scenario 4: Operation cancelled, no events processed")
    print("   • Scenario 5: First event processed, then cancelled")
    print()
    print("👁️ CHECK YOUR GROUP CHAT for all CaliBOT responses!")
    print("📋 If no responses, run: python scripts/recent_logs.py")
    print("="*70)

if __name__ == "__main__":
    main()
