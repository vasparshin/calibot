#!/usr/bin/env python3
"""
Bot Diagnostics - Check why your bot isn't responding.

This script helps diagnose common issues:
1. Bot token validity
2. Webhook status
3. Group chat permissions
4. Recent updates/errors
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotDiagnostics:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_me(self) -> dict:
        """Get bot information."""
        url = f"{self.telegram_api_url}/getMe"
        async with self.session.get(url) as response:
            return await response.json()
    
    async def get_webhook_info(self) -> dict:
        """Get webhook status."""
        url = f"{self.telegram_api_url}/getWebhookInfo"
        async with self.session.get(url) as response:
            return await response.json()
    
    async def get_updates(self) -> dict:
        """Get recent updates."""
        url = f"{self.telegram_api_url}/getUpdates"
        params = {"limit": 10}
        async with self.session.get(url, params=params) as response:
            return await response.json()
    
    async def delete_webhook(self) -> dict:
        """Delete webhook (for testing)."""
        url = f"{self.telegram_api_url}/deleteWebhook"
        async with self.session.get(url) as response:
            return await response.json()
    
    async def set_webhook(self, webhook_url: str) -> dict:
        """Set webhook URL."""
        url = f"{self.telegram_api_url}/setWebhook"
        params = {"url": webhook_url}
        async with self.session.get(url, params=params) as response:
            return await response.json()
    
    async def run_full_diagnostics(self):
        """Run complete diagnostics."""
        print("🔧 BOT DIAGNOSTICS")
        print("=" * 50)
        
        # 1. Check bot token
        print("\n1️⃣ Testing Bot Token...")
        bot_info = await self.get_me()
        
        if bot_info.get("ok"):
            result = bot_info["result"]
            print(f"✅ Bot connected successfully!")
            print(f"   🤖 Name: {result['first_name']}")
            print(f"   📛 Username: @{result['username']}")
            print(f"   🆔 ID: {result['id']}")
            print(f"   🔧 Can join groups: {result.get('can_join_groups', 'Unknown')}")
            print(f"   📖 Can read all group messages: {result.get('can_read_all_group_messages', 'Unknown')}")
            print(f"   🎮 Supports inline queries: {result.get('supports_inline_queries', 'Unknown')}")
        else:
            print(f"❌ Bot token invalid: {bot_info}")
            return
        
        # 2. Check webhook status
        print("\n2️⃣ Checking Webhook Status...")
        webhook_info = await self.get_webhook_info()
        
        if webhook_info.get("ok"):
            webhook_data = webhook_info["result"]
            webhook_url = webhook_data.get("url", "")
            
            if webhook_url:
                print(f"✅ Webhook is set!")
                print(f"   🌐 URL: {webhook_url}")
                print(f"   📊 Pending updates: {webhook_data.get('pending_update_count', 0)}")
                
                if webhook_data.get('last_error_date'):
                    error_date = datetime.fromtimestamp(webhook_data['last_error_date'])
                    print(f"   ⚠️ Last error: {webhook_data.get('last_error_message', 'Unknown')}")
                    print(f"   ⏰ Error time: {error_date}")
                else:
                    print(f"   ✅ No recent errors")
            else:
                print(f"⚠️ No webhook set - bot is in polling mode")
        else:
            print(f"❌ Error getting webhook info: {webhook_info}")
        
        # 3. Check recent updates
        print("\n3️⃣ Checking Recent Updates...")
        updates = await self.get_updates()
        
        if updates.get("ok"):
            update_list = updates["result"]
            
            if update_list:
                print(f"✅ Found {len(update_list)} recent updates:")
                
                for update in update_list[-5:]:  # Show last 5
                    update_id = update["update_id"]
                    
                    if "message" in update:
                        msg = update["message"]
                        chat = msg["chat"]
                        user = msg["from"]
                        text = msg.get("text", "")[:50]
                        
                        chat_type = chat["type"]
                        chat_title = chat.get("title", chat.get("first_name", f"Chat {chat['id']}"))
                        
                        print(f"   📨 Update {update_id}: {chat_type} '{chat_title}' - '{text}...'")
                    
                    elif "callback_query" in update:
                        callback = update["callback_query"]
                        data = callback.get("data", "")
                        print(f"   🔘 Update {update_id}: Callback '{data}'")
                    
                    else:
                        print(f"   ❓ Update {update_id}: Unknown type")
            else:
                print(f"⚠️ No recent updates found")
        else:
            print(f"❌ Error getting updates: {updates}")
        
        # 4. Recommendations
        print("\n4️⃣ Recommendations:")
        
        if not webhook_url:
            print("   💡 Set up webhook for better performance")
            print("   💡 Your backend URL should be: https://your-app.onrender.com/webhook")
        
        if webhook_data.get('pending_update_count', 0) > 0:
            print("   ⚠️ You have pending updates - your backend might not be responding")
            print("   💡 Check your backend logs")
        
        if webhook_data.get('last_error_date'):
            print("   ❌ Your webhook is failing - check backend URL and SSL")
        
        # 5. Group chat specific checks
        print("\n5️⃣ Group Chat Troubleshooting:")
        print("   📋 Common group chat issues:")
        print("   1. Bot needs to be added as admin in groups")
        print("   2. Bot privacy mode might be enabled (only sees commands starting with /)")
        print("   3. Group might have restricted bot permissions")
        print("   4. Bot needs 'can_read_all_group_messages' permission")
        
        print("\n🔧 Quick Fixes:")
        print("   1. Remove bot from group and re-add as admin")
        print("   2. Use @BotFather to disable privacy mode: /setprivacy -> Disable")
        print("   3. Test in private chat first")
        
        return True

async def main():
    """Main diagnostics function."""
    
    # Get bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_API_TOKEN")
    
    if not bot_token:
        print("❌ No bot token found!")
        print("💡 Set TELEGRAM_BOT_TOKEN environment variable")
        print("💡 Or check your .env file")
        bot_token = input("\nEnter bot token manually: ").strip()
        
        if not bot_token:
            print("❌ Bot token required")
            return
    
    async with BotDiagnostics(bot_token) as diagnostics:
        success = await diagnostics.run_full_diagnostics()
        
        if success:
            print("\n" + "="*50)
            print("✅ Diagnostics completed!")
            print("\n💡 Next steps:")
            print("1. Test in private chat first")
            print("2. If private works, check group permissions")
            print("3. Use local_test_bot.py to send test messages")
            print("4. Check backend logs for webhook errors")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Diagnostics interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
