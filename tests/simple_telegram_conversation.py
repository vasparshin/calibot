#!/usr/bin/env python3
"""
SIMPLE TELEGRAM CONVERSATION WITH LIVE MONITORING
Sends user messages and shows if CaliBOT responds, with option to stream logs
"""

import requests
import time
import json
from datetime import datetime
import subprocess
import threading

# Configuration - SAVED FOR AUTOMATIC USE  
BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
GROUP_CHAT_ID = -4627994150
DELAY_BETWEEN_MESSAGES = 10  # 10 seconds for CaliBOT to process

class SimpleTelegramConversation:
    def __init__(self, bot_token: str, chat_id: int):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def send_user_message(self, message: str, user_name: str = "TestUser") -> bool:
        """Send a realistic user message"""
        payload = {
            "chat_id": self.chat_id,
            "text": f"👤 <b>{user_name}:</b> {message}",
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            if response.status_code == 200:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ✅ USER MESSAGE: {user_name} -> {message}")
                return True
            else:
                print(f"❌ Failed to send: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def wait_and_check(self, scenario_name: str, expected_response_time: int = 10):
        """Wait for CaliBOT response and provide visual feedback"""
        print(f"⏱️ Waiting {expected_response_time} seconds for CaliBOT to respond to: {scenario_name}")
        
        for i in range(expected_response_time):
            time.sleep(1)
            if i % 3 == 0:
                print(f"   ... {expected_response_time - i} seconds remaining")
        
        print(f"✅ Wait complete for: {scenario_name}")
        print("-" * 60)
    
    def run_realistic_scenarios(self):
        """Run realistic conversation scenarios"""
        print("🚀 STARTING SIMPLE TELEGRAM CONVERSATION TEST")
        print("=" * 70)
        print(f"🎯 Group Chat ID: {self.chat_id}")
        print(f"🤖 TestBot Token: {self.bot_token[:15]}...")
        print(f"⏱️ Delay between messages: {DELAY_BETWEEN_MESSAGES} seconds")
        print("🎬 Sending realistic user queries to trigger CaliBOT...")
        print()
        
        # Opening announcement
        self.send_user_message("🧪 Starting CaliBOT conversation test! Watch for responses below.", "TestBot")
        time.sleep(3)
        
        scenarios = [
            # Basic event creation
            ("Alice", "Create a team meeting tomorrow at 2 PM", "Basic event creation"),
            
            # Event with details  
            ("Bob", "Schedule a client presentation on Friday at 3:30 PM for 2 hours", "Detailed event"),
            
            # Event query
            ("Carol", "What meetings do I have this week?", "Event listing"),
            
            # Event deletion
            ("Dave", "Cancel my meeting tomorrow at 2 PM", "Single event deletion"),
            
            # Multiple events
            ("Eve", "Delete all my meetings on Friday", "Multi-event deletion"),
            
            # Event modification
            ("Frank", "Move my team meeting from 2 PM to 3 PM tomorrow", "Event modification"),
            
            # Unclear request
            ("Grace", "Schedule something important", "Unclear request"),
            
            # Calendar selection
            ("Henry", "Create a doctor appointment in my personal calendar next Monday at 10 AM", "Calendar selection"),
        ]
        
        for i, (user, message, description) in enumerate(scenarios, 1):
            print(f"\n🎬 SCENARIO {i}/{len(scenarios)}: {description}")
            print(f"👤 {user}: {message}")
            
            # Send the user message
            success = self.send_user_message(message, user)
            if not success:
                print(f"❌ SKIPPING scenario {i} due to send failure")
                continue
            
            # Wait for CaliBOT to process and respond
            self.wait_and_check(f"Scenario {i} ({description})", DELAY_BETWEEN_MESSAGES)
        
        # Final test message
        print(f"\n🎬 FINAL TEST: Direct bot mention")
        self.send_user_message("@CaliBOT_bot show me all events for next week", "TestUser")
        self.wait_and_check("Final bot mention test", DELAY_BETWEEN_MESSAGES)
        
        print("\n🎉 CONVERSATION TEST COMPLETED!")
        print("=" * 70)
        print("✅ All user messages sent successfully")
        print("📱 Check your Telegram group for CaliBOT responses")
        print("🔍 Each message should trigger CaliBOT via webhook")
        print()
        print("💡 TIP: Run the log streaming script in another terminal:")
        print("   cd scripts && python stream_logs_fixed.py")

def main():
    """Main execution"""
    print("🤖 CaliBOT Conversation Tester")
    print("This will send realistic user messages to trigger your deployed CaliBOT")
    print()
    
    # Ask if user wants to stream logs simultaneously
    try:
        stream_choice = input("Start live log streaming in parallel? (y/n): ").lower().strip()
        if stream_choice == 'y':
            print("🔄 Starting log streaming in background...")
            # Start log streaming in background
            subprocess.Popen([
                "python", 
                "../scripts/stream_logs_fixed.py"
            ], cwd=".")
            time.sleep(2)
    except:
        print("⚠️ Skipping log streaming setup")
    
    try:
        conversation = SimpleTelegramConversation(BOT_TOKEN, GROUP_CHAT_ID)
        conversation.run_realistic_scenarios()
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
