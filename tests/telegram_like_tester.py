#!/usr/bin/env python3
"""
Telegram-Like Visual Testing System

Creates a visual representation of bot-to-bot conversation that simulates 
real Telegram interactions. Shows user messages and bot responses in a 
chat-like format for easier understanding and debugging.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramLikeTester:
    def __init__(self, calibot_backend_url: str = "https://calibot-utq6.onrender.com"):
        self.backend_url = calibot_backend_url
        self.webhook_url = f"{calibot_backend_url}/webhook"
        self.test_chat_id = -4627994150
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_telegram_update(self, message_text: str, user_id: int = 123456789) -> Dict[str, Any]:
        """Create a realistic Telegram webhook payload."""
        return {
            "update_id": int(time.time()),
            "message": {
                "message_id": int(time.time()),
                "from": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User", 
                    "username": "testuser",
                    "language_code": "en"
                },
                "chat": {
                    "id": self.test_chat_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": message_text
            }
        }
    
    def print_telegram_header(self):
        """Print a Telegram-like header."""
        print("━" * 60)
        print("📱 CALIBOT TELEGRAM CHAT SIMULATION")
        print("━" * 60)
        print("👤 TestUser  •  🤖 CaliBOT")
        print("━" * 60)
        print()
    
    def print_user_message(self, message: str, timestamp: str = None):
        """Print a user message in Telegram-like format."""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
        
        print(f"👤 TestUser  {timestamp}")
        print(f"   {message}")
        print()
    
    def print_bot_response(self, response: str, timestamp: str = None, status: str = "✅"):
        """Print a bot response in Telegram-like format."""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
        
        print(f"🤖 CaliBOT  {timestamp}  {status}")
        if response:
            # Format multi-line responses nicely
            for line in response.split('\n'):
                if line.strip():
                    print(f"   {line}")
        else:
            print("   [No response received]")
        print()
    
    def print_system_message(self, message: str):
        """Print a system message."""
        print(f"🔧 SYSTEM: {message}")
        print()
    
    async def send_message_and_show_response(self, message: str) -> Dict[str, Any]:
        """Send a message and display the interaction visually."""
        
        # Show user sending message
        send_time = datetime.now().strftime("%H:%M")
        self.print_user_message(message, send_time)
        
        # Create webhook payload
        payload = self.create_telegram_update(message)
        
        try:
            # Send to backend
            async with self.session.post(self.webhook_url, json=payload) as response:
                response_time = datetime.now().strftime("%H:%M")
                
                if response.status == 200:
                    try:
                        response_data = await response.json()
                        
                        # Extract bot response from the webhook response
                        bot_message = "Message processed successfully"
                        if "response" in response_data:
                            bot_message = response_data["response"]
                        elif "message" in response_data:
                            bot_message = response_data["message"]
                        
                        self.print_bot_response(bot_message, response_time, "✅")
                        
                        return {
                            "success": True,
                            "message": message,
                            "bot_response": bot_message,
                            "status_code": response.status,
                            "response_data": response_data
                        }
                        
                    except json.JSONDecodeError:
                        response_text = await response.text()
                        self.print_bot_response(f"Invalid JSON response: {response_text[:100]}...", response_time, "⚠️")
                        
                        return {
                            "success": False,
                            "message": message,
                            "error": "Invalid JSON response",
                            "status_code": response.status,
                            "response_text": response_text[:200]
                        }
                else:
                    error_text = await response.text()
                    self.print_bot_response(f"HTTP {response.status}: {error_text[:100]}...", response_time, "❌")
                    
                    return {
                        "success": False,
                        "message": message,
                        "error": f"HTTP {response.status}",
                        "status_code": response.status,
                        "response_text": error_text[:200]
                    }
                    
        except Exception as e:
            error_time = datetime.now().strftime("%H:%M")
            self.print_bot_response(f"Connection error: {str(e)}", error_time, "💥")
            
            return {
                "success": False,
                "message": message,
                "error": str(e),
                "status_code": 0
            }
    
    async def run_telegram_like_conversation(self):
        """Run a series of tests that look like a real Telegram conversation."""
        
        self.print_telegram_header()
        
        # Test messages that simulate a real user workflow
        test_messages = [
            "Hi CaliBOT! Can you help me with my calendar?",
            "show me my events for today", 
            "create an event called 'Team Meeting' tomorrow at 2pm",
            "move the last 2 events of today to tomorrow",
            "delete my last meeting",
            "what do I have scheduled for next week?",
            "reschedule my first meeting tomorrow to Monday at 10am",
            "Thanks for your help!"
        ]
        
        results = []
        
        for i, message in enumerate(test_messages, 1):
            # Add some realistic timing between messages
            if i > 1:
                await asyncio.sleep(2)
            
            self.print_system_message(f"Test {i}/{len(test_messages)}: Testing intent extraction and response...")
            
            result = await self.send_message_and_show_response(message)
            results.append(result)
            
            # Add separator between conversations
            if i < len(test_messages):
                print("  ┈" * 20)
                print()
        
        # Print summary
        print("━" * 60)
        print("📊 CONVERSATION SUMMARY")
        print("━" * 60)
        
        successful = sum(1 for r in results if r.get("success", False))
        print(f"✅ Successful interactions: {successful}/{len(results)}")
        print(f"❌ Failed interactions: {len(results) - successful}/{len(results)}")
        print(f"📈 Success rate: {(successful/len(results)*100):.1f}%")
        
        # Show critical test results
        print("\n🎯 CRITICAL TEST ANALYSIS:")
        move_test = next((r for r in results if "move the last 2 events" in r["message"]), None)
        if move_test:
            if move_test.get("success"):
                print("✅ Intent extraction fix: 'move events' correctly processed")
            else:
                print("❌ Intent extraction issue: 'move events' still failing")
        
        return {
            "total_tests": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "success_rate": successful/len(results)*100,
            "detailed_results": results
        }

async def main():
    """Main function - run visual Telegram-like testing."""
    print("🎭 STARTING TELEGRAM-LIKE CONVERSATION SIMULATION")
    print("=" * 60)
    print("This creates a visual chat interface showing real bot interactions")
    print("Backend: https://calibot-utq6.onrender.com")
    print()
    
    async with TelegramLikeTester() as tester:
        summary = await tester.run_telegram_like_conversation()
        
        # Save results
        timestamp = int(time.time())
        filename = f"telegram_simulation_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Conversation simulation saved to: {filename}")
        
        if summary["success_rate"] >= 80:
            print("\n🎉 EXCELLENT! Bot is responding well to user interactions!")
        elif summary["success_rate"] >= 60:
            print("\n⚠️ GOOD but some interactions need improvement")
        else:
            print("\n🔧 NEEDS ATTENTION - Multiple interaction failures detected")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Conversation simulation interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
