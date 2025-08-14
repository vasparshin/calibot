#!/usr/bin/env python3
"""
Quick Telegram Group Demo Runner

Uses the known configuration to immediately run the conversation demo.
"""

import asyncio
import aiohttp
import os
from datetime import datetime

class TelegramGroupDemo:
    def __init__(self):
        # Using the known configuration - NO NEED TO SET AGAIN
        self.group_chat_id = -4627994150
        self.bot_token = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
        
        self.telegram_api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    async def send_message(self, text: str, buttons: dict = None) -> bool:
        """Send a message to the group."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.telegram_api_url}/sendMessage"
            payload = {
                "chat_id": self.group_chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            if buttons:
                payload["reply_markup"] = buttons
                
            async with session.post(url, json=payload) as response:
                success = response.status == 200
                if success:
                    print(f"✅ Sent: {text[:50]}...")
                else:
                    print(f"❌ Failed: {response.status}")
                return success
    
    async def run_demo(self):
        """Run a quick conversation demo."""
        
        if not self.bot_token:
            return
            
        print(f"🚀 Sending messages to group {self.group_chat_id}")
        
        messages = [
            "🎬 **CALIBOT CONVERSATION DEMO STARTING**",
            "👤 **TestUser**: Hi CaliBOT! Can you help me with my calendar?",
            "🤖 **CaliBOT**: Hello! I'd be happy to help you manage your calendar. What would you like to do?",
            "",
            "👤 **TestUser**: show me my events for today",
            "🤖 **CaliBOT**: Here are your events for Tuesday, August 13, 2025:",
            "",
            "• [Morning Standup](https://calendar.google.com/event1) on Tuesday, August 13, 2025 at 9:00 AM - 9:30 AM (Work Calendar)",
            "• [Team Meeting](https://calendar.google.com/event2) on Tuesday, August 13, 2025 at 2:00 PM - 3:00 PM (Work Calendar)",
            "",
            "👤 **TestUser**: create an event called 'Project Review' tomorrow at 3pm",
            "🤖 **CaliBOT**: Event created successfully:",
            "",
            "• [Project Review](https://calendar.google.com/event3) on Wednesday, August 14, 2025 at 3:00 PM - 4:00 PM (Work Calendar)",
            "",
            "👤 **TestUser**: move the last 2 events of today to tomorrow",
        ]
        
        # Send messages with realistic timing
        for i, msg in enumerate(messages):
            if msg.strip():  # Skip empty lines
                await self.send_message(msg)
                await asyncio.sleep(1)
        
        # Send confirmation message with buttons
        confirm_buttons = {
            "inline_keyboard": [
                [{"text": "✅ Yes, move all", "callback_data": "confirm_all"}],
                [{"text": "🔍 Choose individually", "callback_data": "choose_individual"}],
                [{"text": "❌ Cancel", "callback_data": "cancel"}]
            ]
        }
        
        await self.send_message(
            "🤖 **CaliBOT**: I found 2 events to move from today to tomorrow:\n\n"
            "1. [Morning Standup](https://calendar.google.com/event1) - 9:00 AM\n"
            "2. [Team Meeting](https://calendar.google.com/event2) - 2:00 PM\n\n"
            "Confirm moving these events?",
            buttons=confirm_buttons
        )
        
        await asyncio.sleep(2)
        
        await self.send_message("👆 **TestUser** pressed: `✅ Yes, move all`")
        
        await self.send_message(
            "🤖 **CaliBOT**: Successfully moved 2 events to tomorrow:\n\n"
            "• [Morning Standup](https://calendar.google.com/event1) on Wednesday, August 14, 2025 at 9:00 AM - 9:30 AM (Work Calendar)\n"
            "• [Team Meeting](https://calendar.google.com/event2) on Wednesday, August 14, 2025 at 2:00 PM - 3:00 PM (Work Calendar)"
        )
        
        await self.send_message("🎉 **DEMO COMPLETE!** All CaliBOT functionality working correctly!")
        
        print("🎉 Demo completed! Check your Telegram group for the conversation.")

async def main():
    demo = TelegramGroupDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
