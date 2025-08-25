#!/usr/bin/env python3
"""
Real Bot-to-Bot Test for CaliBOT
This script will help diagnose the actual issue by testing the real bot flow
"""
import asyncio
import json
import sys
import time
from datetime import datetime

# Test group chat from project rules
TARGET_GROUP_CHAT = -4627994150
BACKEND_URL = "https://calibot-utq6.onrender.com"

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

async def test_intent_extraction_endpoint():
    """Test the intent extraction directly to see what's being extracted"""
    import aiohttp
    
    log_message("🧠 Testing Intent Extraction", "TEST")
    
    # Test the message that's failing
    test_message = "add two lessons to tonyas calendar today, at 11:30 and at 16:15"
    
    # Create a mock conversation history (empty)
    test_payload = {
        "user_message": test_message,
        "conversation_history": []
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test if there's an intent extraction endpoint
            log_message(f"Testing message: '{test_message}'")
            
            # Since we can't directly test intent extraction, let's test the webhook with detailed logging
            webhook_payload = {
                "update_id": int(time.time()),
                "message": {
                    "chat": {"id": TARGET_GROUP_CHAT},
                    "text": test_message,
                    "message_id": int(time.time()),
                    "date": int(time.time()),
                    "from": {"id": 12345, "first_name": "TestUser"}
                }
            }
            
            log_message("📤 Sending webhook request...")
            async with session.post(
                f"{BACKEND_URL}/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                status = response.status
                result = await response.json() if response.status == 200 else await response.text()
                
                log_message(f"📨 Webhook Response: {status}")
                log_message(f"📋 Response Body: {result}")
                
                if status == 200 and isinstance(result, dict) and result.get("status") == "ok":
                    log_message("✅ Webhook processed successfully", "SUCCESS")
                    log_message("👀 Now check the Telegram group chat for the actual bot response", "INFO")
                    log_message(f"📱 Group Chat ID: {TARGET_GROUP_CHAT}", "INFO")
                    return True
                else:
                    log_message(f"❌ Webhook failed: {status} - {result}", "ERROR")
                    return False
                    
    except Exception as e:
        log_message(f"❌ Request failed: {e}", "ERROR")
        return False

async def test_auth_status():
    """Check if authentication is working"""
    import aiohttp
    
    log_message("🔐 Checking Authentication Status", "TEST")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/auth/status") as response:
                if response.status == 200:
                    data = await response.json()
                    authenticated = data.get("authenticated", False)
                    log_message(f"🔐 Authentication Status: {authenticated}")
                    
                    if not authenticated:
                        log_message("❌ Bot is NOT authenticated with Google Calendar!", "ERROR")
                        log_message("This could explain why events aren't being created", "ERROR")
                        auth_url = data.get("auth_url", "Not available")
                        log_message(f"🔗 Auth URL: {auth_url}", "INFO")
                        return False
                    else:
                        log_message("✅ Bot is authenticated with Google Calendar", "SUCCESS")
                        return True
                else:
                    log_message(f"❌ Auth status check failed: {response.status}", "ERROR")
                    return False
    except Exception as e:
        log_message(f"❌ Auth check failed: {e}", "ERROR")
        return False

async def main():
    """Main test function"""
    log_message("=" * 60, "TEST")
    log_message("🤖 Real CaliBOT Diagnosis Test", "TEST")
    log_message("🎯 Investigating: 'No matching events found' error", "TEST")
    log_message("=" * 60, "TEST")
    
    # Step 1: Check backend version
    log_message("STEP 1: Backend Version Check", "TEST")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    version = data.get("version", "unknown")
                    log_message(f"✅ Backend Version: {version}")
                else:
                    log_message(f"❌ Backend check failed: {response.status}")
                    return
    except Exception as e:
        log_message(f"❌ Backend connection failed: {e}")
        return
    
    log_message("")
    
    # Step 2: Check authentication
    log_message("STEP 2: Authentication Check", "TEST")
    auth_ok = await test_auth_status()
    if not auth_ok:
        log_message("❌ Authentication issue detected - this may be the root cause!", "ERROR")
    
    log_message("")
    
    # Step 3: Test the actual message
    log_message("STEP 3: Real Message Test", "TEST")
    success = await test_intent_extraction_endpoint()
    
    log_message("")
    log_message("=" * 60, "TEST")
    log_message("🎯 DIAGNOSIS COMPLETE", "TEST")
    log_message("=" * 60, "TEST")
    
    if not auth_ok:
        log_message("🔍 PRIMARY ISSUE: Bot is not authenticated with Google Calendar", "RESULT")
        log_message("💡 SOLUTION: Complete OAuth authentication via /auth/login", "RESULT")
    elif success:
        log_message("🔍 ISSUE: Webhook processes OK but bot response is wrong", "RESULT")
        log_message("💡 SOLUTION: Check intent extraction or response generation logic", "RESULT")
    else:
        log_message("🔍 ISSUE: Webhook processing failed", "RESULT")
        log_message("💡 SOLUTION: Check backend logs and webhook handling", "RESULT")
    
    log_message("👀 Check Telegram group chat for actual bot behavior", "RESULT")

if __name__ == "__main__":
    # Install aiohttp if needed
    try:
        import aiohttp
    except ImportError:
        log_message("Installing aiohttp...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
        import aiohttp
    
    asyncio.run(main())
