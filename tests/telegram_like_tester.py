#!/usr/bin/env python3
"""
Telegram-like Tester for CaliBOT
Simulates actual bot-to-bot communication for testing the multi-event creation bug

This script sends a real message to the group chat via a test bot to trigger
the actual conversation flow as specified in the project rules.
"""
import asyncio
import json
import sys
import time
from datetime import datetime

# Project constants
TARGET_GROUP_CHAT = -4627994150  # From project rules
BACKEND_URL = "https://calibot-utq6.onrender.com"

def log_test(message, level="TEST"):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

async def send_test_message_via_webhook():
    """
    Send the actual failing message to trigger real bot behavior.
    This simulates what happens when a user types the message in Telegram.
    """
    import aiohttp
    
    log_test("🚀 Starting Real Bot-to-Bot Demo")
    log_test(f"📱 Target Group: {TARGET_GROUP_CHAT}")
    
    # The exact message that's failing
    test_message = "add two lessons to tonyas calendar today, at 11:30 and at 16:15"
    
    # Create realistic webhook payload
    webhook_payload = {
        "update_id": int(time.time() * 1000),  # Unique update ID
        "message": {
            "message_id": int(time.time()),
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "TestUser",
                "username": "testuser"
            },
            "chat": {
                "id": TARGET_GROUP_CHAT,
                "title": "CaliBOT Test Group",
                "type": "group"
            },
            "date": int(time.time()),
            "text": test_message
        }
    }
    
    log_test(f"📝 Sending: '{test_message}'")
    log_test("🔄 Processing via webhook...")
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(
                f"{BACKEND_URL}/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                status = response.status
                
                if status == 200:
                    result = await response.json()
                    log_test(f"✅ Webhook Success: {result}")
                    
                    log_test("=" * 60)
                    log_test("🎯 REAL BOT DEMO EXECUTED", "DEMO")
                    log_test("=" * 60)
                    log_test("📋 What should happen next:", "DEMO")
                    log_test("1. CaliBOT should receive the message", "DEMO")
                    log_test("2. Extract 'create' intent with 2 events", "DEMO") 
                    log_test("3. Create 2 lessons (11:30 and 16:15)", "DEMO")
                    log_test("4. Send success confirmation to group", "DEMO")
                    log_test("", "DEMO")
                    log_test("❌ If bot responds with 'No matching events found':", "DEMO")
                    log_test("   → Intent is being misclassified as 'query'", "DEMO")
                    log_test("   → OR there's still a flow logic bug", "DEMO")
                    log_test("", "DEMO")
                    log_test(f"👀 CHECK GROUP CHAT {TARGET_GROUP_CHAT} FOR BOT RESPONSE", "DEMO")
                    log_test("=" * 60)
                    
                    return True
                else:
                    error_text = await response.text()
                    log_test(f"❌ Webhook Failed: {status} - {error_text}", "ERROR")
                    return False
                    
    except Exception as e:
        log_test(f"❌ Connection Error: {e}", "ERROR")
        return False

async def main():
    """Main test execution"""
    log_test("🤖 CaliBOT Bot-to-Bot Demo", "HEADER")
    log_test("Testing: Multi-Event Creation Bug", "HEADER")
    log_test("=" * 60, "HEADER")
    
    # Verify backend is available
    log_test("Step 1: Backend Health Check")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    version = data.get("version")
                    log_test(f"✅ Backend Online: v{version}")
                else:
                    log_test("❌ Backend unavailable")
                    return
    except Exception as e:
        log_test(f"❌ Backend error: {e}")
        return
    
    log_test("")
    
    # Execute the real test
    log_test("Step 2: Real Bot Message Test")
    success = await send_test_message_via_webhook()
    
    if success:
        log_test("")
        log_test("✅ Demo message sent successfully!")
        log_test("🔍 Now observe the actual bot behavior in Telegram")
    else:
        log_test("❌ Demo failed - check backend connectivity")

if __name__ == "__main__":
    # Install aiohttp if needed
    try:
        import aiohttp
    except ImportError:
        print("Installing aiohttp...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
        import aiohttp
    
    # Run the demo
    asyncio.run(main())