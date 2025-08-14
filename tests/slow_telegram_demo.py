#!/usr/bin/env python3
"""
SLOW TELEGRAM CONVERSATION DEMO
Demonstrates CaliBOT conversations with proper rate limiting
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Bot configuration - SAVED FOR AUTOMATIC USE
BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
GROUP_CHAT_ID = -4627994150

# Rate limiting configuration
DELAY_BETWEEN_MESSAGES = 3  # 3 seconds between messages to avoid rate limits

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlowTelegramDemo:
    def __init__(self, bot_token: str, chat_id: int):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_message(self, text: str, reply_markup: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a message with rate limiting"""
        import aiohttp
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/sendMessage", json=payload) as response:
                    result = await response.json()
                    if response.status == 200:
                        print(f"✅ Sent: {text[:50]}...")
                        return result
                    else:
                        print(f"❌ Failed: {result}")
                        return result
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"ok": False, "error": str(e)}
    
    async def demo_conversation_1(self):
        """Event Creation with Confirmation"""
        print("\n🎬 SCENARIO 1: Event Creation with Confirmation")
        
        # User message
        await self.send_message("👤 <b>User:</b> Create a team meeting tomorrow at 2 PM")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Bot response with confirmation
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Confirm", "callback_data": "confirm_create"},
                {"text": "❌ Cancel", "callback_data": "cancel_create"}
            ]]
        }
        await self.send_message(
            "🤖 <b>CaliBOT:</b> I'll create a team meeting for tomorrow at 2:00 PM.\n\n"
            "<b>📅 Event Details:</b>\n"
            "• <b>Title:</b> Team meeting\n"
            "• <b>Date:</b> August 14, 2025\n"
            "• <b>Time:</b> 2:00 PM - 3:00 PM\n"
            "• <b>Calendar:</b> Work Calendar\n\n"
            "Please confirm to create this event:",
            keyboard
        )
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # User confirmation
        await self.send_message("👤 <b>User:</b> [Pressed ✅ Confirm button]")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Bot success response
        await self.send_message(
            "🤖 <b>CaliBOT:</b> ✅ Event created successfully!\n\n"
            "<b>📅 Team meeting</b>\n"
            "📅 August 14, 2025\n"
            "🕐 2:00 PM - 3:00 PM\n"
            "📋 Work Calendar\n\n"
            "<a href='https://calendar.google.com/calendar/event?eid=example'>View in Calendar</a>"
        )
        
    async def demo_conversation_2(self):
        """Multiple Event Deletion"""
        print("\n🎬 SCENARIO 2: Multiple Event Deletion")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # User message
        await self.send_message("👤 <b>User:</b> Delete all my meetings this week")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Bot response with multi-event list
        keyboard = {
            "inline_keyboard": [[
                {"text": "🗑️ Delete All", "callback_data": "delete_all"},
                {"text": "❌ Cancel", "callback_data": "cancel_delete"}
            ]]
        }
        await self.send_message(
            "🤖 <b>CaliBOT:</b> I found 3 meetings this week to delete:\n\n"
            "<b>📋 Events to Delete:</b>\n"
            "1. <b>Team Standup</b> - August 14, 2025 at 9:00 AM\n"
            "2. <b>Client Review</b> - August 15, 2025 at 3:00 PM\n"
            "3. <b>Project Planning</b> - August 16, 2025 at 10:00 AM\n\n"
            "⚠️ This will permanently delete all 3 events. Confirm?",
            keyboard
        )
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # User confirmation
        await self.send_message("👤 <b>User:</b> [Pressed 🗑️ Delete All button]")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Bot success response
        await self.send_message(
            "🤖 <b>CaliBOT:</b> ✅ Successfully deleted 3 events!\n\n"
            "<b>🗑️ Deleted Events:</b>\n"
            "• Team Standup (Aug 14)\n"
            "• Client Review (Aug 15)\n"
            "• Project Planning (Aug 16)\n\n"
            "All events have been removed from your calendar."
        )
        
    async def demo_conversation_3(self):
        """Error Handling and Recovery"""
        print("\n🎬 SCENARIO 3: Error Handling and Recovery")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # User message with ambiguous request
        await self.send_message("👤 <b>User:</b> Schedule something important")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Bot clarification request
        await self.send_message(
            "🤖 <b>CaliBOT:</b> I'd be happy to help schedule something important! "
            "However, I need a few more details:\n\n"
            "<b>📝 Please provide:</b>\n"
            "• What is the event about?\n"
            "• When should it be scheduled?\n"
            "• How long will it take?\n\n"
            "For example: 'Schedule a doctor appointment tomorrow at 10 AM for 1 hour'"
        )
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # User provides details
        await self.send_message("👤 <b>User:</b> Schedule a doctor appointment tomorrow at 10 AM for 1 hour")
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Bot creates event
        await self.send_message(
            "🤖 <b>CaliBOT:</b> ✅ Perfect! I've created your doctor appointment.\n\n"
            "<b>📅 Doctor Appointment</b>\n"
            "📅 August 14, 2025\n"
            "🕐 10:00 AM - 11:00 AM\n"
            "📋 Personal Calendar\n\n"
            "<a href='https://calendar.google.com/calendar/event?eid=example2'>View in Calendar</a>"
        )

    async def run_complete_demo(self):
        """Run all conversation scenarios"""
        print("🚀 STARTING SLOW CALIBOT CONVERSATION DEMO")
        print("=" * 60)
        print(f"🎯 Group Chat ID: {self.chat_id}")
        print(f"🤖 Bot Token: {self.bot_token[:15]}...")
        print("⏱️ Using 3-second delays to respect rate limits")
        print()
        
        # Opening message
        await self.send_message(
            "🎬 <b>CALIBOT CONVERSATION DEMO STARTING</b>\n\n"
            "This demo shows realistic bot conversations with:\n"
            "• Event creation and confirmation\n"
            "• Multi-event operations\n"
            "• Button interactions\n"
            "• Error handling\n\n"
            "Watch the conversation unfold below! 👇"
        )
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Run scenarios
        await self.demo_conversation_1()
        await self.demo_conversation_2()
        await self.demo_conversation_3()
        
        # Closing message
        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
        await self.send_message(
            "🎉 <b>DEMO COMPLETED!</b>\n\n"
            "✅ Showed event creation with confirmation\n"
            "✅ Demonstrated multi-event deletion\n"
            "✅ Showed error handling and recovery\n"
            "✅ All button interactions simulated\n\n"
            "CaliBOT is ready for real user interactions! 🤖✨"
        )
        
        print("\n🎉 Demo completed! Check your Telegram group for the full conversation.")

async def main():
    """Main execution function"""
    try:
        demo = SlowTelegramDemo(BOT_TOKEN, GROUP_CHAT_ID)
        await demo.run_complete_demo()
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
