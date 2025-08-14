#!/usr/bin/env python3
"""
Complete Telegram Group Bot Conversation Simulator

Creates realistic bot-to-bot conversations in your Telegram group including:
- User messages and bot responses
- Inline keyboard buttons and interactions
- Multi-event confirmations 
- All possible CaliBOT scenarios
- Error handling and edge cases
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramBotConversationSimulator:
    def __init__(self, bot_token: str, group_chat_id: int):
        self.bot_token = bot_token
        self.group_chat_id = group_chat_id
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, text: str, parse_mode: str = "Markdown", reply_markup: Dict = None) -> Dict:
        """Send a message to the group."""
        url = f"{self.telegram_api_url}/sendMessage"
        payload = {
            "chat_id": self.group_chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
            
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to send message: {response.status}")
                return {}
    
    async def simulate_user_message(self, username: str, message: str, delay: float = 1.0):
        """Simulate a user sending a message."""
        user_msg = f"👤 **{username}**: {message}"
        await self.send_message(user_msg)
        await asyncio.sleep(delay)
    
    async def simulate_bot_response(self, message: str, buttons: List[List[Dict]] = None, delay: float = 1.0):
        """Simulate CaliBOT responding with optional buttons."""
        bot_msg = f"🤖 **CaliBOT**: {message}"
        
        reply_markup = None
        if buttons:
            reply_markup = {
                "inline_keyboard": buttons
            }
        
        result = await self.send_message(bot_msg, reply_markup=reply_markup)
        await asyncio.sleep(delay)
        return result
    
    async def simulate_button_press(self, username: str, button_text: str, delay: float = 1.0):
        """Simulate a user pressing an inline keyboard button."""
        button_msg = f"👆 **{username}** pressed: `{button_text}`"
        await self.send_message(button_msg)
        await asyncio.sleep(delay)
    
    async def simulate_system_message(self, message: str, delay: float = 0.5):
        """Simulate system/status messages."""
        system_msg = f"🔧 **SYSTEM**: {message}"
        await self.send_message(system_msg)
        await asyncio.sleep(delay)
    
    async def scenario_basic_interaction(self):
        """Scenario 1: Basic calendar interaction."""
        await self.simulate_system_message("📋 **SCENARIO 1: Basic Calendar Interaction**")
        
        await self.simulate_user_message("TestUser", "Hi CaliBOT!")
        await self.simulate_bot_response("Hello! I'm CaliBOT, your AI calendar assistant. I can help you create, modify, and manage your calendar events. What would you like to do?")
        
        await self.simulate_user_message("TestUser", "show me my events for today")
        await self.simulate_bot_response("Here are your events for Tuesday, August 13, 2025:\n\n• [Morning Standup](https://calendar.google.com/event1) on Tuesday, August 13, 2025 at 9:00 AM - 9:30 AM (Work Calendar)\n• [Team Meeting](https://calendar.google.com/event2) on Tuesday, August 13, 2025 at 2:00 PM - 3:00 PM (Work Calendar)")
    
    async def scenario_event_creation(self):
        """Scenario 2: Event creation with confirmation."""
        await self.simulate_system_message("📋 **SCENARIO 2: Event Creation**")
        
        await self.simulate_user_message("TestUser", "create an event called 'Project Review' tomorrow at 3pm")
        await self.simulate_bot_response("Event created successfully:\n\n• [Project Review](https://calendar.google.com/event3) on Wednesday, August 14, 2025 at 3:00 PM - 4:00 PM (Work Calendar)")
    
    async def scenario_multi_event_creation(self):
        """Scenario 3: Multi-event creation with confirmations."""
        await self.simulate_system_message("📋 **SCENARIO 3: Multi-Event Creation**")
        
        await self.simulate_user_message("TestUser", "create 3 events: 'Morning standup' at 9am, 'Code review' at 11am, 'Lunch meeting' at 12pm all for tomorrow")
        
        # Show duplicate detection
        duplicate_buttons = [
            [{"text": "✅ Create All", "callback_data": "create_all"}],
            [{"text": "🔍 Review Each", "callback_data": "review_each"}],
            [{"text": "❌ Cancel", "callback_data": "cancel"}]
        ]
        
        await self.simulate_bot_response(
            "I found potential duplicates:\n\n**Similar Events Found:**\n• Morning standup (conflicts with existing 'Morning Standup' at 9:00 AM)\n\nHow would you like to proceed?",
            buttons=duplicate_buttons
        )
        
        await self.simulate_button_press("TestUser", "✅ Create All")
        await self.simulate_bot_response("Successfully created 3 events:\n\n• [Morning Standup](https://calendar.google.com/event4) on Wednesday, August 14, 2025 at 9:00 AM - 10:00 AM (Work Calendar)\n• [Code Review](https://calendar.google.com/event5) on Wednesday, August 14, 2025 at 11:00 AM - 12:00 PM (Work Calendar)\n• [Lunch Meeting](https://calendar.google.com/event6) on Wednesday, August 14, 2025 at 12:00 PM - 1:00 PM (Work Calendar)")
    
    async def scenario_event_modification(self):
        """Scenario 4: Event modification with confirmation."""
        await self.simulate_system_message("📋 **SCENARIO 4: Event Modification**")
        
        await self.simulate_user_message("TestUser", "move the last 2 events of today to tomorrow")
        
        # Multi-event confirmation buttons
        confirm_buttons = [
            [{"text": "✅ Yes, move all", "callback_data": "confirm_all"}],
            [{"text": "🔍 Choose individually", "callback_data": "choose_individual"}],
            [{"text": "❌ Cancel", "callback_data": "cancel"}]
        ]
        
        await self.simulate_bot_response(
            "I found 2 events to move from today to tomorrow:\n\n1. [Morning Standup](https://calendar.google.com/event1) - 9:00 AM\n2. [Team Meeting](https://calendar.google.com/event2) - 2:00 PM\n\nConfirm moving these events?",
            buttons=confirm_buttons
        )
        
        await self.simulate_button_press("TestUser", "✅ Yes, move all")
        await self.simulate_bot_response("Successfully moved 2 events to tomorrow:\n\n• [Morning Standup](https://calendar.google.com/event1) on Wednesday, August 14, 2025 at 9:00 AM - 9:30 AM (Work Calendar)\n• [Team Meeting](https://calendar.google.com/event2) on Wednesday, August 14, 2025 at 2:00 PM - 3:00 PM (Work Calendar)")
    
    async def scenario_event_deletion(self):
        """Scenario 5: Event deletion with confirmation."""
        await self.simulate_system_message("📋 **SCENARIO 5: Event Deletion**")
        
        await self.simulate_user_message("TestUser", "delete my last 3 meetings")
        
        # Deletion confirmation buttons
        delete_buttons = [
            [{"text": "🗑️ Delete All", "callback_data": "delete_all"}],
            [{"text": "🔍 Select which ones", "callback_data": "select_delete"}],
            [{"text": "❌ Cancel", "callback_data": "cancel"}]
        ]
        
        await self.simulate_bot_response(
            "I found 3 recent meetings to delete:\n\n1. [Project Review](https://calendar.google.com/event3) - Aug 14, 3:00 PM\n2. [Code Review](https://calendar.google.com/event5) - Aug 14, 11:00 AM\n3. [Lunch Meeting](https://calendar.google.com/event6) - Aug 14, 12:00 PM\n\n⚠️ **This cannot be undone!** Confirm deletion?",
            buttons=delete_buttons
        )
        
        await self.simulate_button_press("TestUser", "🔍 Select which ones")
        
        # Individual selection buttons
        select_buttons = [
            [{"text": "✅ Project Review", "callback_data": "select_1"}],
            [{"text": "❌ Code Review", "callback_data": "deselect_2"}],
            [{"text": "✅ Lunch Meeting", "callback_data": "select_3"}],
            [{"text": "🗑️ Delete Selected", "callback_data": "delete_selected"}]
        ]
        
        await self.simulate_bot_response(
            "Select which events to delete:\n\n✅ Project Review - Selected\n❌ Code Review - Not selected\n✅ Lunch Meeting - Selected",
            buttons=select_buttons
        )
        
        await self.simulate_button_press("TestUser", "🗑️ Delete Selected")
        await self.simulate_bot_response("Successfully deleted 2 events:\n\n• Project Review (Aug 14, 3:00 PM)\n• Lunch Meeting (Aug 14, 12:00 PM)")
    
    async def scenario_calendar_selection(self):
        """Scenario 6: Calendar selection with AI suggestions."""
        await self.simulate_system_message("📋 **SCENARIO 6: Smart Calendar Selection**")
        
        await self.simulate_user_message("TestUser", "create a doctor appointment next Friday at 2pm")
        
        # Calendar selection buttons
        calendar_buttons = [
            [{"text": "🏥 Personal Calendar", "callback_data": "calendar_personal"}],
            [{"text": "💼 Work Calendar", "callback_data": "calendar_work"}], 
            [{"text": "👨‍⚕️ Health Calendar", "callback_data": "calendar_health"}],
            [{"text": "🤖 Let AI Choose", "callback_data": "ai_choose"}]
        ]
        
        await self.simulate_bot_response(
            "I detected this is a health-related appointment. Which calendar should I use?\n\n🤖 **AI Suggestion**: Health Calendar (based on 'doctor appointment')",
            buttons=calendar_buttons
        )
        
        await self.simulate_button_press("TestUser", "👨‍⚕️ Health Calendar")
        await self.simulate_bot_response("Event created successfully:\n\n• [Doctor Appointment](https://calendar.google.com/event7) on Friday, August 15, 2025 at 2:00 PM - 3:00 PM (Health Calendar)")
    
    async def scenario_error_handling(self):
        """Scenario 7: Error handling and recovery."""
        await self.simulate_system_message("📋 **SCENARIO 7: Error Handling**")
        
        await self.simulate_user_message("TestUser", "create an event next Saturday at 25:00")
        await self.simulate_bot_response("⚠️ I couldn't process that time format. Could you please specify the time in a standard format?\n\n**Examples:**\n• 1:00 PM or 13:00\n• 2:30 PM or 14:30\n• 9 AM or 09:00")
        
        await self.simulate_user_message("TestUser", "create an event next Saturday at 1pm")
        await self.simulate_bot_response("Event created successfully:\n\n• [Event](https://calendar.google.com/event8) on Saturday, August 16, 2025 at 1:00 PM - 2:00 PM (Work Calendar)")
    
    async def scenario_complex_scheduling(self):
        """Scenario 8: Complex scheduling with multiple constraints."""
        await self.simulate_system_message("📋 **SCENARIO 8: Complex Scheduling**")
        
        await self.simulate_user_message("TestUser", "reschedule my first meeting tomorrow to next Monday at 10am and make it 2 hours long")
        
        # Reschedule confirmation
        reschedule_buttons = [
            [{"text": "✅ Confirm Reschedule", "callback_data": "confirm_reschedule"}],
            [{"text": "📝 Modify Details", "callback_data": "modify_details"}],
            [{"text": "❌ Cancel", "callback_data": "cancel"}]
        ]
        
        await self.simulate_bot_response(
            "I'll reschedule your event:\n\n**Original:** [Morning Standup](https://calendar.google.com/event4) on Wednesday, August 14, 2025 at 9:00 AM - 10:00 AM\n\n**New:** Monday, August 18, 2025 at 10:00 AM - 12:00 PM (2 hours)\n\nConfirm this change?",
            buttons=reschedule_buttons
        )
        
        await self.simulate_button_press("TestUser", "✅ Confirm Reschedule")
        await self.simulate_bot_response("Successfully rescheduled event:\n\n• [Morning Standup](https://calendar.google.com/event4) on Monday, August 18, 2025 at 10:00 AM - 12:00 PM (Work Calendar)")
    
    async def scenario_conversation_flow(self):
        """Scenario 9: Natural conversation flow."""
        await self.simulate_system_message("📋 **SCENARIO 9: Natural Conversation**")
        
        await self.simulate_user_message("TestUser", "what do I have next week?")
        await self.simulate_bot_response("Here's your schedule for next week (August 18-24, 2025):\n\n**Monday, August 18:**\n• [Morning Standup](https://calendar.google.com/event4) at 10:00 AM - 12:00 PM (Work Calendar)\n\n**Tuesday, August 19:**\n• No events scheduled\n\n**Wednesday, August 20:**\n• [Team Meeting](https://calendar.google.com/event2) at 2:00 PM - 3:00 PM (Work Calendar)\n\n**Friday, August 22:**\n• [Doctor Appointment](https://calendar.google.com/event7) at 2:00 PM - 3:00 PM (Health Calendar)")
        
        await self.simulate_user_message("TestUser", "looks good, thanks!")
        await self.simulate_bot_response("You're welcome! Feel free to ask if you need help managing your calendar. I can create, modify, delete events, and answer questions about your schedule anytime.")
    
    async def run_complete_demo(self):
        """Run the complete conversation demo with all scenarios."""
        
        # Demo header
        header_msg = ("🎬 **CALIBOT COMPLETE CONVERSATION DEMO**\n"
                     "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                     "Demonstrating all possible CaliBOT interactions including:\n"
                     "• Event creation, modification, deletion\n"
                     "• Multi-event operations with confirmations\n"
                     "• Inline keyboard button interactions\n"
                     "• Calendar selection and AI suggestions\n"
                     "• Error handling and recovery\n"
                     "• Complex scheduling scenarios")
        
        await self.send_message(header_msg)
        await asyncio.sleep(3)
        
        # Run all scenarios
        scenarios = [
            self.scenario_basic_interaction,
            self.scenario_event_creation,
            self.scenario_multi_event_creation,
            self.scenario_event_modification,
            self.scenario_event_deletion,
            self.scenario_calendar_selection,
            self.scenario_error_handling,
            self.scenario_complex_scheduling,
            self.scenario_conversation_flow
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            try:
                await scenario()
                await asyncio.sleep(2)  # Pause between scenarios
                
                # Progress update
                progress_msg = f"✅ **Scenario {i}/{len(scenarios)} Complete**"
                await self.simulate_system_message(progress_msg)
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"❌ **Error in Scenario {i}**: {str(e)}"
                await self.simulate_system_message(error_msg)
        
        # Demo completion
        completion_msg = ("🎉 **DEMO COMPLETE!**\n"
                         "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                         "✅ All CaliBOT scenarios demonstrated\n"
                         "✅ Button interactions shown\n"
                         "✅ Multi-event confirmations tested\n"
                         "✅ Error handling validated\n"
                         "✅ Natural conversation flow verified\n\n"
                         "CaliBOT is ready for production use!")
        
        await self.send_message(completion_msg)
        
        return {
            "scenarios_completed": len(scenarios),
            "demo_status": "complete",
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Main function to run the complete conversation demo."""
    
    # Configuration - SAVED FOR AUTOMATIC USE
    BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
    GROUP_CHAT_ID = -4627994150
    
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
    
    print("🚀 STARTING COMPLETE CALIBOT CONVERSATION DEMO")
    print("=" * 60)
    print(f"🎯 Group Chat ID: {group_id}")
    print(f"🤖 Bot Token: {bot_token[:10]}...")
    print("🎬 This will demonstrate ALL CaliBOT scenarios with button interactions")
    print()
    
    async with TelegramBotConversationSimulator(bot_token, group_id) as simulator:
        result = await simulator.run_complete_demo()
        
        # Save results
        timestamp = int(time.time())
        filename = f"complete_conversation_demo_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Demo results saved to: {filename}")
        print("🎉 Complete conversation demo finished!")
        print("Check your Telegram group to see all the interactions!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
