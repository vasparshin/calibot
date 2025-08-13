#!/usr/bin/env python3
"""
Local Test Bot - Sends messages to test Calibot in group chat.

This bot can send test messages to your "Calendar testing" group chat
and monitor responses from your deployed Calibot bot.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalTestBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        self.chat_id = None  # Will be discovered from group
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_chat_info(self):
        """Get information about available chats."""
        url = f"{self.telegram_api_url}/getUpdates"
        
        async with self.session.get(url) as response:
            result = await response.json()
            
        if result.get("ok"):
            updates = result.get("result", [])
            chats = {}
            
            for update in updates:
                if "message" in update:
                    chat = update["message"]["chat"]
                    chat_id = chat["id"]
                    chat_title = chat.get("title", chat.get("first_name", "Unknown"))
                    chat_type = chat.get("type", "unknown")
                    chats[chat_id] = {"title": chat_title, "type": chat_type}
            
            return chats
        return {}
    
    async def find_testing_group(self):
        """Find the 'Calendar testing' group chat."""
        chats = await self.get_chat_info()
        
        for chat_id, info in chats.items():
            if "calendar testing" in info["title"].lower():
                self.chat_id = chat_id
                logger.info(f"Found testing group: {info['title']} (ID: {chat_id})")
                return chat_id
        
        # If not found, show available chats
        logger.warning("Calendar testing group not found. Available chats:")
        for chat_id, info in chats.items():
            logger.info(f"  - {info['title']} (ID: {chat_id}, Type: {info['type']})")
        
        return None
    
    async def send_message(self, text: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """Send a message to the group chat."""
        if not chat_id and not self.chat_id:
            await self.find_testing_group()
        
        target_chat_id = chat_id or self.chat_id
        
        if not target_chat_id:
            logger.error("No chat ID available. Please specify chat_id or ensure bot is in the testing group.")
            return {"error": "No chat ID"}
        
        url = f"{self.telegram_api_url}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": text
        }
        
        logger.info(f"📤 Sending to chat {target_chat_id}: {text}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if result.get("ok"):
                    logger.info(f"✅ Message sent successfully")
                else:
                    logger.error(f"❌ Failed to send message: {result}")
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Exception sending message: {e}")
            return {"error": str(e)}
    
    async def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from the chat."""
        url = f"{self.telegram_api_url}/getUpdates"
        params = {"limit": limit}
        
        try:
            async with self.session.get(url, params=params) as response:
                result = await response.json()
                
            if result.get("ok"):
                messages = []
                for update in result.get("result", []):
                    if "message" in update:
                        message = update["message"]
                        if message.get("chat", {}).get("id") == self.chat_id:
                            messages.append({
                                "text": message.get("text", ""),
                                "from": message.get("from", {}).get("first_name", "Unknown"),
                                "is_bot": message.get("from", {}).get("is_bot", False),
                                "date": datetime.fromtimestamp(message.get("date", 0)),
                                "message_id": message.get("message_id")
                            })
                
                return sorted(messages, key=lambda x: x["date"])[-limit:]
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
        
        return []
    
    async def run_test_scenario(self, scenario_name: str, test_messages: List[str], 
                               wait_between: int = 3, monitor_responses: bool = True) -> Dict[str, Any]:
        """Run a test scenario with multiple messages and monitor responses."""
        
        logger.info(f"🚀 Starting scenario: {scenario_name}")
        
        scenario_results = {
            "scenario": scenario_name,
            "start_time": datetime.now().isoformat(),
            "messages_sent": [],
            "responses_observed": [],
            "success": True,
            "errors": []
        }
        
        for i, message in enumerate(test_messages):
            try:
                # Get messages before sending
                if monitor_responses:
                    messages_before = await self.get_recent_messages()
                
                # Send test message
                send_result = await self.send_message(message)
                scenario_results["messages_sent"].append({
                    "text": message,
                    "sent_at": datetime.now().isoformat(),
                    "result": send_result
                })
                
                if not send_result.get("ok"):
                    scenario_results["errors"].append(f"Failed to send: {message}")
                    scenario_results["success"] = False
                
                # Wait for response
                if monitor_responses:
                    await asyncio.sleep(wait_between)
                    
                    # Get new messages
                    messages_after = await self.get_recent_messages()
                    new_messages = []
                    
                    for msg in messages_after:
                        if msg not in messages_before:
                            new_messages.append(msg)
                    
                    # Filter for bot responses
                    bot_responses = [msg for msg in new_messages if msg["is_bot"]]
                    
                    if bot_responses:
                        logger.info(f"📥 Got {len(bot_responses)} bot response(s)")
                        for response in bot_responses:
                            logger.info(f"   🤖 {response['from']}: {response['text'][:100]}...")
                            scenario_results["responses_observed"].append({
                                "text": response["text"],
                                "from": response["from"],
                                "received_at": response["date"].isoformat(),
                                "in_response_to": message
                            })
                    else:
                        logger.warning(f"⚠️ No bot response detected for: {message}")
                
            except Exception as e:
                error_msg = f"Error in scenario step {i+1}: {e}"
                logger.error(error_msg)
                scenario_results["errors"].append(error_msg)
                scenario_results["success"] = False
        
        scenario_results["end_time"] = datetime.now().isoformat()
        
        logger.info(f"✅ Scenario completed: {scenario_name}")
        logger.info(f"   📤 Messages sent: {len(scenario_results['messages_sent'])}")
        logger.info(f"   📥 Responses received: {len(scenario_results['responses_observed'])}")
        logger.info(f"   ❌ Errors: {len(scenario_results['errors'])}")
        
        return scenario_results

# Test scenarios specifically for the intent extraction issue
CRITICAL_TEST_SCENARIOS = {
    "intent_extraction_issue": [
        "move the last 2 events of today to tomorrow",  # This should trigger UPDATE intent
        "show me tomorrow's schedule",  # This should trigger QUERY intent
    ],
    
    "multiple_events_processing": [
        "create 3 events: 'Test Meeting 1' at 9am, 'Test Meeting 2' at 11am, 'Test Meeting 3' at 2pm all for tomorrow",
        "show me tomorrow's events",
        "move the last 2 events of tomorrow to Friday",
    ],
    
    "single_event_formatting": [
        "create an event called 'Format Test Event' tomorrow at 3pm",  # Should use consistent formatting
    ],
    
    "complex_operations": [
        "reschedule my first meeting tomorrow to next Monday at 10am",
        "delete the last event created today",
    ]
}

async def main():
    """Run the local test bot."""
    
    # Your test bot token
    TEST_BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
    
    print("🤖 CALIBOT LOCAL TEST BOT")
    print("="*50)
    print("This bot will send test messages to your 'Calendar testing' group")
    print("and monitor responses from your deployed Calibot.\n")
    
    async with LocalTestBot(TEST_BOT_TOKEN) as test_bot:
        
        # Find the testing group
        await test_bot.find_testing_group()
        
        if not test_bot.chat_id:
            print("❌ Could not find 'Calendar testing' group automatically.")
            print("\n🔧 OPTIONS:")
            print("1. Send a message in the 'Calendar testing' group first, then restart this bot")
            print("2. Enter the group chat ID manually")
            print("3. Show all available chats")
            
            manual_choice = input("\nChoose option (1-3): ").strip()
            
            if manual_choice == "2":
                chat_id_input = input("Enter the group chat ID (negative number): ").strip()
                try:
                    test_bot.chat_id = int(chat_id_input)
                    print(f"✅ Using chat ID: {test_bot.chat_id}")
                except ValueError:
                    print("❌ Invalid chat ID format")
                    return
            elif manual_choice == "3":
                chats = await test_bot.get_chat_info()
                print("\n💬 Available Chats:")
                for chat_id, info in chats.items():
                    print(f"  - {info['title']} (ID: {chat_id}, Type: {info['type']})")
                
                chat_id_input = input("\nEnter the chat ID you want to use: ").strip()
                try:
                    test_bot.chat_id = int(chat_id_input)
                    print(f"✅ Using chat ID: {test_bot.chat_id}")
                except ValueError:
                    print("❌ Invalid chat ID format")
                    return
            else:
                print("Please send a message in the group first and restart the bot.")
                return
        
        print(f"✅ Found testing group (ID: {test_bot.chat_id})")
        
        # Show menu
        print("\n📋 TEST OPTIONS:")
        print("1. Run Critical Issue Tests (intent extraction)")
        print("2. Run All Test Scenarios")
        print("3. Send Custom Message")
        print("4. Monitor Recent Messages")
        print("5. Show Available Chats")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            print("\n🎯 Running Critical Issue Tests...")
            scenario = await test_bot.run_test_scenario(
                "critical_intent_extraction", 
                CRITICAL_TEST_SCENARIOS["intent_extraction_issue"]
            )
            
            # Save results
            with open(f"critical_test_results_{int(time.time())}.json", "w") as f:
                json.dump(scenario, f, indent=2)
        
        elif choice == "2":
            print("\n🚀 Running All Test Scenarios...")
            all_results = []
            
            for scenario_name, messages in CRITICAL_TEST_SCENARIOS.items():
                result = await test_bot.run_test_scenario(scenario_name, messages)
                all_results.append(result)
                
                # Brief pause between scenarios
                await asyncio.sleep(2)
            
            # Save all results
            with open(f"full_test_results_{int(time.time())}.json", "w") as f:
                json.dump(all_results, f, indent=2)
            
            # Summary
            successful = sum(1 for r in all_results if r["success"])
            print(f"\n📊 SUMMARY: {successful}/{len(all_results)} scenarios successful")
        
        elif choice == "3":
            custom_message = input("Enter message to send: ").strip()
            if custom_message:
                await test_bot.send_message(custom_message)
                print("✅ Message sent! Check the group chat for responses.")
        
        elif choice == "4":
            print("\n📥 Recent Messages:")
            messages = await test_bot.get_recent_messages(20)
            for msg in messages[-10:]:  # Show last 10
                sender = "🤖" if msg["is_bot"] else "👤"
                print(f"{sender} {msg['from']}: {msg['text'][:80]}...")
        
        elif choice == "5":
            print("\n💬 Available Chats:")
            chats = await test_bot.get_chat_info()
            for chat_id, info in chats.items():
                print(f"  - {info['title']} (ID: {chat_id}, Type: {info['type']})")
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Test bot stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
