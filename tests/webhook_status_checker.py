#!/usr/bin/env python3
"""
Webhook Status Checker - Checks if Telegram webhook is properly configured for Calibot.
"""

import asyncio
import aiohttp
import json

async def check_webhook_status(bot_token: str):
    """Check the current webhook configuration for a Telegram bot."""
    
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    print(f"🔍 Checking webhook status for bot...")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                if result.get("ok"):
                    webhook_info = result.get("result", {})
                    
                    print("✅ Webhook Info Retrieved:")
                    print(f"📡 URL: {webhook_info.get('url', 'NOT SET')}")
                    print(f"🔗 Has Custom Certificate: {webhook_info.get('has_custom_certificate', False)}")
                    print(f"⏰ Pending Update Count: {webhook_info.get('pending_update_count', 0)}")
                    print(f"🕐 Last Error Date: {webhook_info.get('last_error_date', 'None')}")
                    print(f"❌ Last Error Message: {webhook_info.get('last_error_message', 'None')}")
                    print(f"🔢 Max Connections: {webhook_info.get('max_connections', 'Default')}")
                    print(f"📝 Allowed Updates: {webhook_info.get('allowed_updates', 'All')}")
                    
                    # Check if webhook is properly configured
                    webhook_url = webhook_info.get('url', '')
                    if not webhook_url:
                        print("\n❌ PROBLEM: No webhook URL set!")
                        print("💡 SOLUTION: Calibot needs to set its webhook URL with Telegram")
                        return False
                    elif 'localhost' in webhook_url or '127.0.0.1' in webhook_url:
                        print("\n❌ PROBLEM: Webhook URL points to localhost!")
                        print("💡 SOLUTION: Webhook URL must be publicly accessible (like Render URL)")
                        return False
                    else:
                        print(f"\n✅ Webhook URL looks good: {webhook_url}")
                        
                        # Check for errors
                        if webhook_info.get('last_error_message'):
                            print(f"\n⚠️ WARNING: Recent webhook error detected")
                            print(f"   Error: {webhook_info.get('last_error_message')}")
                            return False
                        
                        return True
                else:
                    print(f"❌ API Error: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

async def main():
    """Check webhook status for both bots."""
    
    print("🤖 TELEGRAM WEBHOOK STATUS CHECKER")
    print("=" * 50)
    
    # You'll need to provide your main Calibot token
    print("This tool checks if your Calibot's webhook is properly configured.")
    print("We need your main Calibot bot token to check this.")
    print()
    
    main_bot_token = input("Enter your main Calibot bot token: ").strip()
    
    if not main_bot_token:
        print("❌ Bot token is required")
        return
    
    print(f"\n🎯 MAIN CALIBOT WEBHOOK STATUS")
    main_ok = await check_webhook_status(main_bot_token)
    
    print(f"\n🤖 TEST BOT WEBHOOK STATUS")
    test_bot_token = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
    test_ok = await check_webhook_status(test_bot_token)
    
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"Main Calibot Webhook: {'✅ OK' if main_ok else '❌ ISSUE'}")
    print(f"Test Bot Webhook: {'✅ OK' if test_ok else '❌ ISSUE'}")
    
    if not main_ok:
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print("1. Check if Calibot is properly setting its webhook URL on startup")
        print("2. Verify the webhook URL is your Render deployment URL + '/webhook'")
        print("3. Check Render logs for webhook setup errors")

if __name__ == "__main__":
    asyncio.run(main())
