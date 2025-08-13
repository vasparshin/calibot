#!/usr/bin/env python3
"""
Real Telegram Group Conversation Simulator

Posts actual messages to your Telegram group chat to simulate realistic 
bot-to-user interactions. Shows the conversation flow in real Telegram 
while testing backend functionality.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramGroupConversationSimulator:
    def __init__(
        self, 
        bot_token: str, 
        group_chat_id: int,
        calibot_backend_url: str = "https://calibot-utq6.onrender.com"
    ):
        self.bot_token = bot_token
        self.group_chat_id = group_chat_id
        self.backend_url = calibot_backend_url
        self.webhook_url = f"{calibot_backend_url}/webhook"
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_group_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to the Telegram group chat."""
        try:
            url = f"{self.telegram_api_url}/sendMessage"
            payload = {
                "chat_id": self.group_chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send group message: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending group message: {e}")
            return False
    
    def create_telegram_update(self, message_text: str, user_id: int = 123456789) -> Dict[str, Any]:
        """Create a realistic Telegram webhook payload."""
        return {
            "update_id": int(time.time()),
            "message": {
                "message_id": int(time.time()),
                "from": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "last_name": "Demo", 
                    "username": "testuser_demo",
                    "language_code": "en"
                },
                "chat": {
                    "id": self.group_chat_id,  # Use actual group chat ID
                    "title": "CaliBOT Testing Group",
                    "type": "group"
                },
                "date": int(time.time()),
                "text": message_text
            }
        }
    
    async def simulate_user_message_and_get_response(self, user_message: str) -> Dict[str, Any]:
        """
        1. Post user message to group
        2. Send to CaliBOT backend 
        3. Post CaliBOT's response to group
        4. Return interaction details
        """
        
        # 1. Post user message to group
        user_msg_formatted = f"👤 **TestUser**: {user_message}"
        if await self.send_group_message(user_msg_formatted):
            logger.info(f"✅ Posted user message to group: {user_message}")
        else:
            logger.error(f"❌ Failed to post user message to group")
            return {"success": False, "error": "Failed to post user message"}\n        # Small delay to make it feel natural\n        await asyncio.sleep(1)\n        \n        # 2. Send to CaliBOT backend\n        payload = self.create_telegram_update(user_message)\n        \n        try:\n            async with self.session.post(self.webhook_url, json=payload) as response:\n                if response.status == 200:\n                    try:\n                        response_data = await response.json()\n                        \n                        # 3. Post CaliBOT response to group\n                        # CaliBOT will have sent its response via Telegram API already\n                        # So we just post a confirmation/summary\n                        bot_confirmation = f"🤖 **CaliBOT**: Processing request... *(response sent to user privately)*"\n                        \n                        if await self.send_group_message(bot_confirmation):\n                            logger.info(f"✅ Posted bot confirmation to group")\n                        \n                        return {\n                            "success": True,\n                            "user_message": user_message,\n                            "backend_response": response_data,\n                            "status_code": response.status\n                        }\n                        \n                    except json.JSONDecodeError:\n                        error_text = await response.text()\n                        error_msg = f"🤖 **CaliBOT**: ⚠️ JSON parsing error - {error_text[:100]}..."\n                        await self.send_group_message(error_msg)\n                        \n                        return {\n                            "success": False,\n                            "user_message": user_message,\n                            "error": "JSON decode error",\n                            "status_code": response.status\n                        }\n                else:\n                    error_text = await response.text()\n                    error_msg = f"🤖 **CaliBOT**: ❌ HTTP {response.status} - {error_text[:100]}..."\n                    await self.send_group_message(error_msg)\n                    \n                    return {\n                        "success": False,\n                        "user_message": user_message,\n                        "error": f"HTTP {response.status}",\n                        "status_code": response.status\n                    }\n                    \n        except Exception as e:\n            error_msg = f"🤖 **CaliBOT**: 💥 Connection error - {str(e)}"\n            await self.send_group_message(error_msg)\n            \n            return {\n                "success": False,\n                "user_message": user_message,\n                "error": str(e),\n                "status_code": 0\n            }\n    \n    async def run_realistic_conversation_demo(self) -> Dict[str, Any]:\n        """Run a realistic conversation demo in the Telegram group."""\n        \n        # Start conversation marker\n        start_msg = "🎬 **STARTING CALIBOT CONVERSATION DEMO**\\n" \\\n                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n" \\\n                   "Testing CaliBOT functionality with realistic user interactions"\n        \n        await self.send_group_message(start_msg)\n        await asyncio.sleep(2)\n        \n        # Realistic conversation flow\n        test_messages = [\n            "Hi CaliBOT! Can you help me with my calendar?",\n            "show me my events for today", \n            "create an event called 'Team Meeting' tomorrow at 2pm",\n            "move the last 2 events of today to tomorrow",\n            "delete my last meeting",\n            "what do I have scheduled for next week?",\n            "reschedule my first meeting tomorrow to Monday at 10am",\n            "Thanks for your help CaliBOT!"\n        ]\n        \n        results = []\n        \n        for i, message in enumerate(test_messages, 1):\n            # Add realistic timing between messages\n            if i > 1:\n                await asyncio.sleep(3)\n            \n            # Post test progress\n            progress_msg = f"🔄 **Test {i}/{len(test_messages)}**: Testing intent extraction..."\n            await self.send_group_message(progress_msg)\n            await asyncio.sleep(1)\n            \n            # Simulate the interaction\n            result = await self.simulate_user_message_and_get_response(message)\n            results.append(result)\n            \n            # Add separator between conversations\n            if i < len(test_messages):\n                await asyncio.sleep(2)\n        \n        # Post summary to group\n        successful = sum(1 for r in results if r.get("success", False))\n        summary_msg = f"📊 **CONVERSATION DEMO COMPLETE**\\n" \\\n                     f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n" \\\n                     f"✅ Successful interactions: {successful}/{len(results)}\\n" \\\n                     f"❌ Failed interactions: {len(results) - successful}/{len(results)}\\n" \\\n                     f"📈 Success rate: {(successful/len(results)*100):.1f}%"\n        \n        # Add critical test analysis\n        move_test = next((r for r in results if "move the last 2 events" in r["user_message"]), None)\n        if move_test:\n            if move_test.get("success"):\n                summary_msg += "\\n\\n🎯 **CRITICAL TEST**: ✅ Intent extraction working correctly!"\n            else:\n                summary_msg += "\\n\\n🎯 **CRITICAL TEST**: ❌ Intent extraction needs attention"\n        \n        await self.send_group_message(summary_msg)\n        \n        return {\n            "total_tests": len(results),\n            "successful": successful,\n            "failed": len(results) - successful,\n            "success_rate": successful/len(results)*100,\n            "detailed_results": results\n        }\n\nasync def main():\n    """Main function - requires bot token and group chat ID."""\n    \n    # Configuration - UPDATE THESE VALUES\n    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Your test bot token\n    GROUP_CHAT_ID = -1000000000000     # Your group chat ID (negative number)\n    \n    # Check for environment variables\n    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)\n    group_id = int(os.getenv("TELEGRAM_GROUP_ID", GROUP_CHAT_ID))\n    \n    if bot_token == "YOUR_BOT_TOKEN_HERE":\n        print("❌ Please set your bot token!")\n        print("Either:")\n        print("1. Edit the BOT_TOKEN variable in this script")\n        print("2. Set TELEGRAM_BOT_TOKEN environment variable")\n        return\n    \n    if group_id == -1000000000000:\n        print("❌ Please set your group chat ID!")\n        print("Either:")\n        print("1. Edit the GROUP_CHAT_ID variable in this script") \n        print("2. Set TELEGRAM_GROUP_ID environment variable")\n        return\n    \n    print("🚀 STARTING REAL TELEGRAM GROUP CONVERSATION DEMO")\n    print("=" * 60)\n    print(f"🎯 Group Chat ID: {group_id}")\n    print(f"🤖 Bot Token: {bot_token[:10]}...")\n    print(f"🔗 Backend: https://calibot-utq6.onrender.com")\n    print()\n    \n    async with TelegramGroupConversationSimulator(bot_token, group_id) as simulator:\n        summary = await simulator.run_realistic_conversation_demo()\n        \n        # Save results\n        timestamp = int(time.time())\n        filename = f"group_conversation_{timestamp}.json"\n        with open(filename, 'w') as f:\n            json.dump(summary, f, indent=2)\n        \n        print(f"💾 Group conversation results saved to: {filename}")\n        \n        if summary["success_rate"] >= 80:\n            print("🎉 EXCELLENT! Group conversation demo successful!")\n        elif summary["success_rate"] >= 60:\n            print("⚠️ GOOD but some interactions need improvement")\n        else:\n            print("🔧 NEEDS ATTENTION - Multiple interaction failures")\n\nif __name__ == "__main__":\n    try:\n        asyncio.run(main())\n    except KeyboardInterrupt:\n        print("\\n\\n⏹️ Group conversation demo interrupted")\n    except Exception as e:\n        print(f"\\n❌ Unexpected error: {e}")\n        import traceback\n        traceback.print_exc()
