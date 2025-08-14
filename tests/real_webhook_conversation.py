#!/usr/bin/env python3
"""
REAL CALIBOT WEBHOOK CONVERSATION
Sends visual Telegram messages AND actual webhook calls to CaliBOT backend
"""

import requests
import time
import json
from datetime import datetime

# Configuration - SAVED FOR AUTOMATIC USE
BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
GROUP_CHAT_ID = -4627994150
CALIBOT_WEBHOOK_URL = "https://calibot-utq6.onrender.com/webhook"  # Your deployed CaliBOT
DELAY_BETWEEN_MESSAGES = 8  # 8 seconds for processing

class RealWebhookConversation:
    def __init__(self, bot_token: str, chat_id: int, webhook_url: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.webhook_url = webhook_url
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.user_id_counter = 100000000  # Fake user IDs
        
    def send_visual_message(self, message: str, user_name: str) -> bool:
        """Send visual message to Telegram group for display"""
        payload = {
            "chat_id": self.chat_id,
            "text": f"👤 <b>{user_name}:</b> {message}",
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Visual message error: {e}")
            return False
    
    def send_webhook_request(self, message: str, user_name: str) -> dict:
        """Send actual webhook request to CaliBOT backend"""
        self.user_id_counter += 1
        
        # Create realistic Telegram webhook payload
        webhook_payload = {
            "update_id": int(time.time()),
            "message": {
                "message_id": int(time.time()),
                "from": {
                    "id": self.user_id_counter,
                    "is_bot": False,
                    "first_name": user_name,
                    "username": user_name.lower(),
                    "language_code": "en"
                },
                "chat": {
                    "id": self.chat_id,
                    "title": "CaliBOT Test Group",
                    "type": "group"
                },
                "date": int(time.time()),
                "text": message
            }
        }
        
        try:
            print(f"🔄 Sending webhook request to CaliBOT backend...")
            response = requests.post(
                self.webhook_url, 
                json=webhook_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_text": response.text[:200] if response.text else "No response",
                "webhook_payload": webhook_payload
            }
            
            if result["success"]:
                print(f"✅ Webhook SUCCESS: CaliBOT processed the request")
            else:
                print(f"❌ Webhook FAILED: {response.status_code} - {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"❌ Webhook ERROR: {e}")
            return {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "webhook_payload": webhook_payload
            }
    
    def run_realistic_webhook_conversation(self):
        """Run conversation with both visual messages and real webhook calls"""
        print("🚀 STARTING REAL CALIBOT WEBHOOK CONVERSATION")
        print("=" * 70)
        print(f"🎯 Group Chat ID: {self.chat_id}")
        print(f"🤖 TestBot Token: {self.bot_token[:15]}...")
        print(f"🌐 CaliBOT Webhook: {self.webhook_url}")
        print(f"⏱️ Delay between messages: {DELAY_BETWEEN_MESSAGES} seconds")
        print("🎬 Sending REAL webhook requests + visual messages...")
        print()
        
        # Start conversation
        self.send_visual_message("🧪 Starting REAL CaliBOT webhook conversation test!", "TestBot")
        time.sleep(2)
        
        scenarios = [
            ("Alice", "Create a team meeting tomorrow at 2 PM", "Basic event creation"),
            ("Bob", "Schedule a client presentation on Friday at 3:30 PM for 2 hours", "Detailed event"),
            ("Carol", "What meetings do I have this week?", "Event listing"),
            ("Dave", "Cancel my meeting tomorrow at 2 PM", "Event deletion"),
            ("Eve", "Delete all my meetings on Friday", "Multi-event deletion"),
            ("Frank", "Move my team meeting from 2 PM to 3 PM tomorrow", "Event modification"),
            ("Grace", "Schedule something important", "Unclear request"),
            ("Henry", "Create a doctor appointment in my personal calendar next Monday at 10 AM", "Calendar selection"),
        ]
        
        webhook_results = []
        
        for i, (user, message, description) in enumerate(scenarios, 1):
            print(f"\n🎬 SCENARIO {i}/{len(scenarios)}: {description}")
            print(f"👤 {user}: {message}")
            print("-" * 50)
            
            # 1. Send visual message to Telegram group
            visual_success = self.send_visual_message(message, user)
            if visual_success:
                print(f"✅ Visual message sent to group")
            else:
                print(f"❌ Failed to send visual message")
            
            time.sleep(1)  # Brief pause
            
            # 2. Send ACTUAL webhook request to CaliBOT backend
            webhook_result = self.send_webhook_request(message, user)
            webhook_results.append({
                "scenario": i,
                "user": user,
                "message": message,
                "description": description,
                "result": webhook_result
            })
            
            # 3. Wait for CaliBOT to respond in the group
            print(f"⏱️ Waiting {DELAY_BETWEEN_MESSAGES} seconds for CaliBOT response...")
            time.sleep(DELAY_BETWEEN_MESSAGES)
            
            print(f"✅ Scenario {i} completed")
        
        # Final summary
        print(f"\n🎉 WEBHOOK CONVERSATION COMPLETED!")
        print("=" * 70)
        
        success_count = sum(1 for r in webhook_results if r["result"]["success"])
        print(f"📊 WEBHOOK RESULTS: {success_count}/{len(webhook_results)} successful")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in webhook_results:
            status = "✅" if result["result"]["success"] else "❌"
            print(f"  {status} Scenario {result['scenario']}: {result['description']}")
            if not result["result"]["success"]:
                error = result["result"].get("error", result["result"].get("response_text", "Unknown error"))
                print(f"     Error: {error}")
        
        print(f"\n📱 Check your Telegram group for:")
        print(f"  • Visual user messages from TestBot")
        print(f"  • Real CaliBOT responses triggered by webhooks")
        print(f"  • Complete conversation flow with actual bot interactions")
        
        return webhook_results

def main():
    """Main execution"""
    try:
        conversation = RealWebhookConversation(BOT_TOKEN, GROUP_CHAT_ID, CALIBOT_WEBHOOK_URL)
        results = conversation.run_realistic_webhook_conversation()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"logs/webhook_conversation_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ Webhook conversation failed: {e}")

if __name__ == "__main__":
    main()
