#!/usr/bin/env python3
"""
Local Bot Tester - Runs Calibot locally with polling for interactive testing.

This script:
1. Starts your bot locally with Telegram polling (no webhook)
2. Shows real messages being sent/received
3. Provides live debugging with detailed logs
4. Allows you to test via real Telegram messages
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.telegram import send_telegram_message
from app.api.routes import process_telegram_message
from app.config import TELEGRAM_API_TOKEN
import httpx
import json
from datetime import datetime

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('local_bot_test.log')
    ]
)
logger = logging.getLogger(__name__)

class LocalBotTester:
    def __init__(self):
        self.token = TELEGRAM_API_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.running = False
        
    async def get_bot_info(self):
        """Get bot information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}/getMe")
            if response.status_code == 200:
                bot_info = response.json()["result"]
                print(f"🤖 Bot Info:")
                print(f"   Name: {bot_info['first_name']}")
                print(f"   Username: @{bot_info['username']}")
                print(f"   ID: {bot_info['id']}")
                return bot_info
            else:
                print(f"❌ Failed to get bot info: {response.text}")
                return None
    
    async def send_test_message(self, chat_id: int, message: str):
        """Send a test message to verify bot can send messages"""
        try:
            await send_telegram_message(
                chat_id=chat_id,
                text=f"🧪 Test message sent at {datetime.now().strftime('%H:%M:%S')}: {message}"
            )
            print(f"✅ Test message sent to chat {chat_id}")
        except Exception as e:
            print(f"❌ Failed to send test message: {e}")
    
    async def get_updates(self):
        """Get updates from Telegram using polling"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_url}/getUpdates",
                    params={
                        "offset": self.offset,
                        "timeout": 10,
                        "allowed_updates": ["message", "callback_query"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["ok"]:
                        return data["result"]
                    else:
                        logger.error(f"Telegram API error: {data}")
                else:
                    logger.error(f"HTTP error {response.status_code}: {response.text}")
                    
        except asyncio.TimeoutError:
            # Timeout is normal for long polling
            pass
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
        
        return []
    
    async def process_update(self, update):
        """Process a single update from Telegram"""
        try:
            # Handle regular messages
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                user = message["from"]
                text = message.get("text", "")
                
                print(f"\n📨 RECEIVED MESSAGE")
                print(f"   From: {user.get('first_name', '')} {user.get('last_name', '')} (@{user.get('username', 'no_username')})")
                print(f"   Chat ID: {chat_id}")
                print(f"   Text: '{text}'")
                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                
                # Update offset to avoid reprocessing
                self.offset = update["update_id"] + 1
                
                # Process the message through your bot logic
                print(f"\n🔄 PROCESSING MESSAGE...")
                try:
                    await process_telegram_message(update)
                    print(f"✅ Message processed successfully")
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    logger.exception("Message processing error")
                    
                    # Send error message to user
                    await send_telegram_message(
                        chat_id=chat_id,
                        text=f"❌ Sorry, I encountered an error processing your message: {str(e)}"
                    )
            
            # Handle callback queries (inline keyboard responses)
            elif "callback_query" in update:
                callback = update["callback_query"]
                chat_id = callback["message"]["chat"]["id"]
                user = callback["from"]
                data = callback.get("data", "")
                
                print(f"\n🎯 RECEIVED CALLBACK")
                print(f"   From: {user.get('first_name', '')} {user.get('last_name', '')}")
                print(f"   Chat ID: {chat_id}")
                print(f"   Data: '{data}'")
                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                
                # Update offset
                self.offset = update["update_id"] + 1
                
                # Process callback through your bot logic
                print(f"\n🔄 PROCESSING CALLBACK...")
                try:
                    await process_telegram_message(update)
                    print(f"✅ Callback processed successfully")
                except Exception as e:
                    print(f"❌ Error processing callback: {e}")
                    logger.exception("Callback processing error")
                    
        except Exception as e:
            logger.exception(f"Error processing update: {e}")
            print(f"❌ Update processing error: {e}")
    
    async def start_polling(self):
        """Start the polling loop"""
        print(f"\n🚀 STARTING LOCAL BOT TESTER")
        print("="*60)
        
        # Get bot info
        bot_info = await self.get_bot_info()
        if not bot_info:
            print("❌ Cannot start - bot info unavailable")
            return
        
        print(f"\n📱 Send messages to @{bot_info['username']} to test!")
        print(f"💡 Or add the bot to a group chat and test there")
        print(f"🔍 Watching for messages...")
        print("="*60)
        
        self.running = True
        
        try:
            while self.running:
                updates = await self.get_updates()
                
                for update in updates:
                    await self.process_update(update)
                
                # Small delay to prevent spam
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Bot stopped by user")
        except Exception as e:
            logger.exception(f"Polling error: {e}")
            print(f"❌ Polling error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the bot"""
        self.running = False

async def main():
    """Main function"""
    print("🤖 CALIBOT LOCAL TESTER")
    print("="*50)
    print("This will run your bot locally with real Telegram messages!")
    print("You'll see all messages sent and received in real-time.")
    print("\nPress Ctrl+C to stop the bot\n")
    
    # Check token
    if not TELEGRAM_API_TOKEN:
        print("❌ TELEGRAM_API_TOKEN not found in environment")
        return
    
    # Start the bot
    tester = LocalBotTester()
    
    try:
        await tester.start_polling()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Main error")

if __name__ == "__main__":
    asyncio.run(main())
