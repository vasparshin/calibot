#!/usr/bin/env python3
"""
Quick Test - Send a test message to your deployed backend directly.
"""

import asyncio
import aiohttp
import json
import time

async def test_backend_directly():
    """Test your deployed backend with the critical scenario."""
    
    # Your bot's info
    backend_url = "https://calibot-utq6.onrender.com/webhook"
    
    # Simulate a webhook payload
    test_payload = {
        "update_id": int(time.time()),
        "message": {
            "message_id": int(time.time()),
            "from": {
                "id": 4627994150,  # Your chat ID
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 4627994150,  # Your chat ID
                "type": "private"
            },
            "date": int(time.time()),
            "text": "move the last 2 events of today to tomorrow"
        }
    }
    
    print("🧪 Testing the critical intent extraction issue...")
    print(f"📡 Sending to: {backend_url}")
    print(f"💬 Message: 'move the last 2 events of today to tomorrow'")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(backend_url, json=test_payload, timeout=30) as response:
                status = response.status
                
                if response.content_type == 'application/json':
                    result = await response.json()
                else:
                    result = await response.text()
                
                print(f"✅ Status: {status}")
                print(f"📥 Response: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
                
                if status == 200:
                    print("\n🎉 SUCCESS! Your backend is responding correctly!")
                    print("Now test with your actual Telegram bot after fixing privacy mode.")
                else:
                    print(f"\n⚠️ Backend returned status {status}. Check logs.")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend_directly())
