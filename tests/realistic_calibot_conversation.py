#!/usr/bin/env python3
"""
REALISTIC CALIBOT CONVERSATION TESTER
Sends realistic user queries to trigger actual CaliBOT responses via webhook
"""

import requests
import time
import json
from datetime import datetime, timedelta

# Configuration - SAVED FOR AUTOMATIC USE
BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
GROUP_CHAT_ID = -4627994150
DELAY_BETWEEN_MESSAGES = 4  # 4 seconds to allow CaliBOT to respond

class RealisticConversationTester:
    def __init__(self, bot_token: str, chat_id: int):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    def send_user_message(self, message: str, user_name: str = "TestUser") -> bool:
        """Send a message as a simulated user to trigger CaliBOT"""
        payload = {
            "chat_id": self.chat_id,
            "text": f"👤 <b>{user_name}:</b> {message}",
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            if response.status_code == 200:
                print(f"✅ User query sent: {message[:50]}...")
                return True
            else:
                print(f"❌ Failed to send: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def wait_for_response(self, expected_delay: int = 3):
        """Wait for CaliBOT to respond"""
        print(f"⏱️ Waiting {expected_delay} seconds for CaliBOT response...")
        time.sleep(expected_delay)
    
    def run_realistic_conversation(self):
        """Run a realistic conversation that triggers CaliBOT"""
        print("🚀 STARTING REALISTIC CALIBOT CONVERSATION")
        print("=" * 60)
        print(f"🎯 Group Chat ID: {self.chat_id}")
        print(f"🤖 TestBot Token: {self.bot_token[:15]}...")
        print("🎬 This will send real user queries to trigger CaliBOT responses")
        print()
        
        # Scenario 1: Event Creation
        print("\n🎬 SCENARIO 1: Simple Event Creation")
        print("-" * 40)
        
        self.send_user_message("Create a meeting tomorrow at 2 PM", "Alice")
        self.wait_for_response(5)
        
        # Scenario 2: Complex Event with Details
        print("\n🎬 SCENARIO 2: Detailed Event Creation")
        print("-" * 40)
        
        self.send_user_message("Schedule a client presentation on Friday at 3:30 PM for 90 minutes", "Bob")
        self.wait_for_response(5)
        
        # Scenario 3: Event Query
        print("\n🎬 SCENARIO 3: Event Query")
        print("-" * 40)
        
        self.send_user_message("What meetings do I have this week?", "Carol")
        self.wait_for_response(5)
        
        # Scenario 4: Event Deletion
        print("\n🎬 SCENARIO 4: Event Deletion")
        print("-" * 40)
        
        self.send_user_message("Cancel my meeting tomorrow", "Dave")
        self.wait_for_response(5)
        
        # Scenario 5: Multiple Events
        print("\n🎬 SCENARIO 5: Multiple Event Operations")
        print("-" * 40)
        
        self.send_user_message("Delete all my meetings this Friday", "Eve")
        self.wait_for_response(5)
        
        # Scenario 6: Event Modification
        print("\n🎬 SCENARIO 6: Event Modification")
        print("-" * 40)
        
        self.send_user_message("Move my 2 PM meeting to 3 PM tomorrow", "Frank")
        self.wait_for_response(5)
        
        # Scenario 7: Unclear Request (Error Handling)
        print("\n🎬 SCENARIO 7: Unclear Request")
        print("-" * 40)
        
        self.send_user_message("Schedule something important", "Grace")
        self.wait_for_response(5)
        
        # Scenario 8: Calendar Selection
        print("\n🎬 SCENARIO 8: Calendar Selection")
        print("-" * 40)
        
        self.send_user_message("Create a doctor appointment in my personal calendar next Monday at 10 AM", "Henry")
        self.wait_for_response(5)
        
        # Scenario 9: Time Zone Handling
        print("\n🎬 SCENARIO 9: Complex Time")
        print("-" * 40)
        
        self.send_user_message("Schedule a call with the London team tomorrow at 9 AM EST", "Iris")
        self.wait_for_response(5)
        
        # Final summary message
        print("\n🎬 FINAL: Test Summary")
        print("-" * 40)
        
        self.send_user_message("@calibot show me all events for next week", "TestUser")
        self.wait_for_response(5)
        
        print("\n🎉 CONVERSATION TEST COMPLETED!")
        print("=" * 60)
        print("✅ Sent 10 realistic user queries")
        print("🤖 CaliBOT should have responded to each via webhook")
        print("📱 Check your Telegram group for the full conversation!")
        print("🔍 Each query tests different CaliBOT functionality")

def main():
    """Main execution"""
    try:
        tester = RealisticConversationTester(BOT_TOKEN, GROUP_CHAT_ID)
        tester.run_realistic_conversation()
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
