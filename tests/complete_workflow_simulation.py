#!/usr/bin/env python3

import requests
import json
import time

# Configuration
CHAT_ID = -4627994150  # Your group chat
BACKEND_URL = "https://calibot-utq6.onrender.com"

def send_webhook_to_calibot(text=None, callback_data=None, scenario_name="", step_name=""):
    """Send webhook to CaliBOT backend with proper validation"""
    timestamp = int(time.time())
    
    if callback_data:
        # Button press simulation
        data = {
            "callback_query": {
                "id": f"test_{timestamp}",
                "from": {
                    "id": 999999999,
                    "first_name": "TestUser", 
                    "username": "testuser",
                    "is_bot": False
                },
                "message": {
                    "message_id": timestamp,
                    "chat": {
                        "id": CHAT_ID, 
                        "type": "supergroup",
                        "title": "Calendar testing"
                    },
                    "date": timestamp,
                    "text": "Previous message with buttons",
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
        action_desc = f"🔘 BUTTON PRESS: {callback_data}"
    else:
        # Text message simulation
        data = {
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
    
    print(f"\n🚀 {scenario_name} - {step_name}")
    print(f"   {action_desc}")
    print(f"   📡 Sending webhook to CaliBOT...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/webhook", json=data, timeout=30)
        status = response.status_code
        print(f"   ✅ Webhook response: {status}")
        if status != 200:
            print(f"   ⚠️ Response text: {response.text[:200]}")
        return status
    except Exception as e:
        print(f"   ❌ Webhook error: {e}")
        return f"Error: {e}"

def wait_and_check_logs(scenario_step):
    """Wait for CaliBOT processing and suggest log check"""
    print(f"   ⏳ Waiting 4 seconds for CaliBOT to process...")
    time.sleep(4)
    print(f"   👁️ CHECK GROUP CHAT NOW - CaliBOT should have responded to: {scenario_step}")
    print(f"   📋 If no response, check logs with: python scripts/recent_logs.py")

def run_scenario(scenario_name, steps):
    """Run a complete test scenario"""
    print(f"\n{'='*80}")
    print(f"🎬 SCENARIO: {scenario_name}")
    print(f"{'='*80}")
    print(f"📝 This scenario will test: {scenario_name}")
    print(f"👁️ WATCH YOUR GROUP CHAT for CaliBOT responses!")
    
    for i, step in enumerate(steps, 1):
        step_text = step['text']
        step_action = step['action']
        
        print(f"\n📋 STEP {i}/{len(steps)}: {step_text}")
        
        # Execute the action
        if step_action['type'] == 'message':
            status = send_webhook_to_calibot(
                text=step_action['content'],
                scenario_name=scenario_name,
                step_name=f"Step {i}: {step_text}"
            )
        elif step_action['type'] == 'button':
            status = send_webhook_to_calibot(
                callback_data=step_action['content'],
                scenario_name=scenario_name,
                step_name=f"Step {i}: {step_text}"
            )
        
        wait_and_check_logs(step_text)
    
    print(f"\n✅ SCENARIO COMPLETE: {scenario_name}")
    print(f"🎯 Expected: CaliBOT should have processed all {len(steps)} steps")
    print(f"👁️ Check your group chat for complete conversation!")

# Define comprehensive test scenarios
scenarios = [
    {
        "name": "SCENARIO 1: All At Once Workflow",
        "steps": [
            {
                "text": "Multi-event request",
                "action": {"type": "message", "content": "🧪 TEST 1: move my last 2 events from yesterday to today at 2pm and 3pm"}
            },
            {
                "text": "Press 'All' button to process both events immediately",
                "action": {"type": "button", "content": "confirm_all_update"}
            }
        ]
    },
    {
        "name": "SCENARIO 2: One by One - Accept Both",
        "steps": [
            {
                "text": "Multi-event request",
                "action": {"type": "message", "content": "🧪 TEST 2: move my last 2 events from yesterday to today at 4pm and 5pm"}
            },
            {
                "text": "Press 'One by One' to review each event",
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
        "name": "SCENARIO 3: One by One - Accept First, Skip Second",
        "steps": [
            {
                "text": "Multi-event request",
                "action": {"type": "message", "content": "🧪 TEST 3: move my last 2 events from yesterday to today at 6pm and 7pm"}
            },
            {
                "text": "Press 'One by One'",
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
        "name": "SCENARIO 4: One by One - Skip First, Accept Second",
        "steps": [
            {
                "text": "Multi-event request",
                "action": {"type": "message", "content": "🧪 TEST 4: move my last 2 events from yesterday to today at 8pm and 9pm"}
            },
            {
                "text": "Press 'One by One'",
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
        "name": "SCENARIO 5: Cancel Immediately",
        "steps": [
            {
                "text": "Multi-event request",
                "action": {"type": "message", "content": "🧪 TEST 5: move my last 2 events from yesterday to today at 10pm and 11pm"}
            },
            {
                "text": "Press 'Cancel' to abort operation",
                "action": {"type": "button", "content": "cancel_update"}
            }
        ]
    },
    {
        "name": "SCENARIO 6: One by One - Cancel Mid-Process",
        "steps": [
            {
                "text": "Multi-event request",
                "action": {"type": "message", "content": "🧪 TEST 6: move my last 2 events from yesterday to today at 1pm and 2pm"}
            },
            {
                "text": "Press 'One by One'",
                "action": {"type": "button", "content": "confirm_one_update"}
            },
            {
                "text": "Press 'Yes' for Event 1",
                "action": {"type": "button", "content": "queue_confirm_0"}
            },
            {
                "text": "Press 'Cancel' to stop processing remaining events",
                "action": {"type": "button", "content": "queue_cancel"}
            }
        ]
    }
]

def main():
    print("🤖 COMPREHENSIVE MULTI-EVENT TESTING SIMULATION")
    print("=" * 80)
    print("🎯 Testing ALL possible multi-event workflow scenarios:")
    print("   • All at once processing")
    print("   • One by one with different combinations")
    print("   • Cancel workflows")
    print("   • Mixed accept/skip responses")
    print()
    print(f"🏠 Group Chat: {CHAT_ID}")
    print(f"🔗 Backend: {BACKEND_URL}")
    print()
    print("👁️ IMPORTANT: Watch your group chat for CaliBOT responses!")
    print("📋 If CaliBOT doesn't respond, check logs: python scripts/recent_logs.py")
    print()
    
    user_input = input("🚀 Ready to start comprehensive testing? (Press Enter to begin): ")
    
    # Run all scenarios
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔄 Starting scenario {i}/{len(scenarios)}...")
        run_scenario(scenario["name"], scenario["steps"])
        
        if i < len(scenarios):
            print(f"\n⏳ Waiting 8 seconds before next scenario...")
            time.sleep(8)
    
    print("\n" + "=" * 80)
    print("🎊 ALL SCENARIOS COMPLETE!")
    print("✅ Tested 6 comprehensive multi-event scenarios")
    print("🎯 Expected CaliBOT behaviors:")
    print("   • Scenario 1: Process both events immediately")
    print("   • Scenario 2: One-by-one confirmation, both accepted")
    print("   • Scenario 3: One-by-one, first accepted, second skipped")
    print("   • Scenario 4: One-by-one, first skipped, second accepted")
    print("   • Scenario 5: Immediate cancellation")
    print("   • Scenario 6: Mid-process cancellation after first event")
    print()
    print("👁️ CHECK YOUR GROUP CHAT for all CaliBOT responses!")
    print("📋 Run 'python scripts/recent_logs.py' to see backend processing")
    print("=" * 80)

if __name__ == "__main__":
    main()
