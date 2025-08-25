#!/usr/bin/env python3
"""
Live Bot-to-Bot Demo Script for CaliBOT
Tests the exact failing scenario with real bot in group chat -4627994150
"""
import asyncio
import json
import sys
import time
from datetime import datetime

# Constants from project rules
TARGET_GROUP_CHAT = -4627994150
BACKEND_URL = "https://calibot-utq6.onrender.com"

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

async def test_bot_webhook_direct():
    """
    Test the exact failing message by sending it directly to the webhook
    This simulates what happens when a user sends a message in Telegram
    """
    import aiohttp
    
    log_message("🚀 Starting Live Bot-to-Bot Demo", "DEMO")
    log_message(f"📱 Target Group Chat: {TARGET_GROUP_CHAT}")
    log_message(f"🌐 Backend URL: {BACKEND_URL}")
    
    # Create the exact message that's failing
    test_message = "add two lessons to tonyas calendar today, at 11:30 and at 16:15"
    
    # Construct webhook payload (same format as Telegram sends)
    webhook_payload = {
        "update_id": 12345,
        "message": {
            "chat": {"id": TARGET_GROUP_CHAT},
            "text": test_message,
            "message_id": 12345,
            "date": int(time.time())
        }
    }
    
    log_message(f"📝 Test Message: '{test_message}'")
    log_message("🔄 Sending to webhook endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                log_message(f"📊 Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    log_message(f"✅ Webhook Response: {json.dumps(result, indent=2)}")
                    
                    if result.get("status") == "ok":
                        log_message("✅ WEBHOOK SUCCESS: Message processed successfully")
                        log_message("💬 Check the Telegram group chat for the bot's response")
                        log_message("🔍 Expected: Bot should create 2 events, not show 'No matching events found'")
                    else:
                        log_message("❌ WEBHOOK ERROR: Unexpected response status")
                        
                else:
                    error_text = await response.text()
                    log_message(f"❌ WEBHOOK FAILED: {response.status} - {error_text}", "ERROR")
                    
    except Exception as e:
        log_message(f"❌ CONNECTION ERROR: {e}", "ERROR")

async def check_backend_status():
    """Check backend health and version"""
    import aiohttp
    
    log_message("🔍 Checking backend status...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    version = data.get("version", "unknown")
                    status = data.get("status", "unknown")
                    log_message(f"✅ Backend Online - Version: {version}, Status: {status}")
                    
                    if version != "0.1.167":
                        log_message(f"⚠️  WARNING: Expected version 0.1.167, got {version}")
                    else:
                        log_message("✅ Correct version deployed with the fix")
                        
                    return True
                else:
                    log_message(f"❌ Backend health check failed: {response.status}")
                    return False
    except Exception as e:
        log_message(f"❌ Backend connection error: {e}")
        return False

async def main():
    """Main demo function"""
    log_message("=" * 60, "DEMO")
    log_message("🤖 CaliBOT Live Bot-to-Bot Demo", "DEMO")
    log_message("📋 Testing: Event Creation Multi-Event Bug Fix", "DEMO")
    log_message("=" * 60, "DEMO")
    
    # Step 1: Check backend status
    log_message("STEP 1: Backend Health Check")
    if not await check_backend_status():
        log_message("❌ Backend not available. Aborting demo.", "ERROR")
        return
    
    log_message("")
    
    # Step 2: Send test message
    log_message("STEP 2: Sending Test Message to Bot")
    await test_bot_webhook_direct()
    
    log_message("")
    log_message("=" * 60, "DEMO")
    log_message("🎯 DEMO COMPLETE", "DEMO")
    log_message("👀 Check Telegram group chat for bot response", "DEMO") 
    log_message("✅ Expected: Bot creates 2 events successfully", "DEMO")
    log_message("❌ Bug Still Present: Bot shows 'No matching events found'", "DEMO")
    log_message("=" * 60, "DEMO")

if __name__ == "__main__":
    # Install aiohttp if not available
    try:
        import aiohttp
    except ImportError:
        log_message("Installing aiohttp for HTTP requests...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
        import aiohttp
    
    # Run the demo
    asyncio.run(main())
