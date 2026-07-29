import os
#!/usr/bin/env python3
"""
Telegram-like Tester for CaliBOT
Simulates actual bot-to-bot communication for testing multi-event operations

This script sends real messages to the group chat via TestBot to trigger
the actual conversation flow as specified in PROJECT_RULES.md.

USAGE: python tests/telegram_like_tester.py
"""

import asyncio
import json
import sys
import time
from datetime import datetime

# Project constants from PROJECT_RULES.md
TARGET_GROUP_CHAT = -4627994150  # Your actual group chat ID
BACKEND_URL = "https://calibot-utq6.onrender.com"
TESTBOT_TOKEN = os.environ.get("TESTBOT_TOKEN","")  # @calibot_testbot

def log_test(message, level="TEST"):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

async def send_testbot_message(message_text: str, session):
    """Send message via TestBot to group chat"""
    try:
        # Send via Telegram Bot API
        bot_url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TARGET_GROUP_CHAT,
            "text": message_text,
            "parse_mode": "HTML"
        }

        async with session.post(bot_url, json=payload) as response:
            if response.status == 200:
                log_test(f"✅ TestBot message sent: '{message_text}'")
                return True
            else:
                log_test(f"❌ Failed to send TestBot message: {response.status}")
                return False
    except Exception as e:
        log_test(f"❌ Error sending TestBot message: {e}")
        return False

async def wait_for_bot_response(session, timeout=30):
    """Wait for CaliBOT response via webhook monitoring"""
    log_test(f"⏳ Waiting {timeout}s for CaliBOT response...")
    await asyncio.sleep(timeout)
    log_test("✅ Response timeout reached")

async def run_visual_test():
    """Run visual test for multi-event operations"""
    log_test("🎯 STARTING VISUAL TEST - CaliBOT Multi-Event Operations")
    log_test("=" * 60)

    async with aiohttp.ClientSession() as session:
        # Test 1: Multi-event creation
        log_test("📝 Test 1: Multi-event creation")
        await send_testbot_message(
            "Create math lesson from 8-9am and 10-11am on Monday",
            session
        )
        await wait_for_bot_response(session)

        # Test 2: Multi-event update (one-by-one)
        log_test("📝 Test 2: Multi-event update (one-by-one)")
        await send_testbot_message(
            "Update the math lessons",
            session
        )
        await wait_for_bot_response(session)
        # Note: Manual button presses required for this test

        # Test 3: Single event creation
        log_test("📝 Test 3: Single event creation")
        await send_testbot_message(
            "Add physics class at 2pm tomorrow",
            session
        )
        await wait_for_bot_response(session)

    log_test("🎯 VISUAL TEST COMPLETE")
    log_test("📋 Check the group chat for CaliBOT responses")
    log_test("🔍 Monitor logs with: python scripts/render_api_logs.py")

if __name__ == "__main__":
    try:
        import aiohttp
    except ImportError:
        print("❌ aiohttp required. Install with: pip install aiohttp")
        sys.exit(1)

    try:
        asyncio.run(run_visual_test())
    except KeyboardInterrupt:
        log_test("🛑 Test interrupted by user")
    except Exception as e:
        log_test(f"❌ Test failed: {e}")
