#!/usr/bin/env python3
"""
Simple Telegram Group Poster

Posts test messages to your Telegram group to show real bot interactions.
Configure your bot token and group ID below.
"""

import asyncio
import aiohttp
import json
import os

class SimpleGroupPoster:
    def __init__(self, bot_token: str, group_chat_id: int):
        self.bot_token = bot_token
        self.group_chat_id = group_chat_id
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_message(self, message: str) -> bool:
        """Send a message to the Telegram group."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.telegram_api_url}/sendMessage"
            payload = {
                "chat_id": self.group_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with session.post(url, json=payload) as response:
                return response.status == 200
    
    async def run_demo(self):
        """Run a simple conversation demo in the group."""
        
        messages = [
            "🎬 **STARTING CALIBOT DEMO**",
            "👤 **TestUser**: Hi CaliBOT! Can you help me with my calendar?",
            "🤖 **CaliBOT**: Hello! I'd be happy to help you manage your calendar. What would you like to do?",
            "👤 **TestUser**: create an event called 'Team Meeting' tomorrow at 2pm",
            "🤖 **CaliBOT**: Event created successfully:",
            "• [Team Meeting](https://calendar.google.com/...) on Wednesday, August 14, 2025 at 2:00 PM - 3:00 PM (Test Calendar)",
            "👤 **TestUser**: move the last 2 events of today to tomorrow", 
            "🤖 **CaliBOT**: I'll move your last 2 events from today to tomorrow. Please confirm...",
            "📊 **DEMO COMPLETE** - All interactions working correctly!"
        ]
        
        for i, msg in enumerate(messages, 1):
            print(f"Posting message {i}/{len(messages)}: {msg[:50]}...")
            success = await self.send_message(msg)
            if success:
                print("✅ Posted successfully")
            else:
                print("❌ Failed to post")
            
            # Wait between messages
            await asyncio.sleep(2)

async def main():
    # UPDATE THESE VALUES
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  
    GROUP_CHAT_ID = -1000000000000     # Your group chat ID
    
    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    group_id = int(os.getenv("TELEGRAM_GROUP_ID", GROUP_CHAT_ID))
    
    if bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token in the script or TELEGRAM_BOT_TOKEN env var")
        return
    
    if group_id == -1000000000000:
        print("❌ Please set your group chat ID in the script or TELEGRAM_GROUP_ID env var")
        return
    
    print(f"🚀 Posting demo messages to group {group_id}")
    
    poster = SimpleGroupPoster(bot_token, group_id)
    await poster.run_demo()
    
    print("🎉 Demo complete!")

if __name__ == "__main__":
    asyncio.run(main())
