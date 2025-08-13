#!/usr/bin/env python3
"""
Quick Telegram Group Test

Simple test to verify your bot token and group chat ID work.
Posts a few test messages to confirm setup before running the full demo.
"""

import asyncio
import aiohttp
import os

class QuickTelegramTest:
    def __init__(self, bot_token: str, group_chat_id: int):
        self.bot_token = bot_token
        self.group_chat_id = group_chat_id
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_message(self, text: str) -> bool:
        async with aiohttp.ClientSession() as session:
            url = f"{self.telegram_api_url}/sendMessage"
            payload = {
                "chat_id": self.group_chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print(f"✅ Message sent successfully: {text[:50]}...")
                    return True
                else:
                    error = await response.text()
                    print(f"❌ Failed to send message: {response.status}")
                    print(f"   Error: {error}")
                    return False
    
    async def test_connection(self):
        print("🧪 Testing Telegram connection...")
        
        success = await self.send_message("🧪 **TEST MESSAGE**\nThis is a test to verify the bot can post to this group.")
        
        if success:
            await asyncio.sleep(1)
            await self.send_message("✅ **CONNECTION SUCCESSFUL**\nBot token and group ID are working correctly!")
            await asyncio.sleep(1)
            await self.send_message("🚀 Ready to run complete CaliBOT conversation demo with `complete_telegram_simulator.py`")
            return True
        else:
            print("\n❌ CONNECTION FAILED")
            print("Check:")
            print("1. Bot token is correct")
            print("2. Bot is added to the group") 
            print("3. Group chat ID is correct (should be negative number)")
            print("4. Bot has permission to send messages")
            return False

async def main():
    # Configuration
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    GROUP_CHAT_ID = -1000000000000
    
    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    group_id = int(os.getenv("TELEGRAM_GROUP_ID", GROUP_CHAT_ID))
    
    if bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token!")
        print("Edit BOT_TOKEN in the script or set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    if group_id == -1000000000000:
        print("❌ Please set your group chat ID!")
        print("Edit GROUP_CHAT_ID in the script or set TELEGRAM_GROUP_ID environment variable")
        return
    
    print("🔧 QUICK TELEGRAM SETUP TEST")
    print("=" * 40)
    print(f"🎯 Group Chat ID: {group_id}")
    print(f"🤖 Bot Token: {bot_token[:10]}...")
    print()
    
    tester = QuickTelegramTest(bot_token, group_id)
    success = await tester.test_connection()
    
    if success:
        print("\n🎉 SUCCESS! Your setup is working.")
        print("Now run: python complete_telegram_simulator.py")
    else:
        print("\n🔧 Please fix the setup issues above and try again.")

if __name__ == "__main__":
    asyncio.run(main())
