#!/usr/bin/env python3
"""
Send demo to YOUR ACTUAL GROUP where you saw the 07:57 message
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def send_to_your_actual_group():
    """Send the demo to YOUR group -4627994150"""
    
    print("🎯 SENDING TO YOUR ACTUAL GROUP")
    print("📱 Group ID: -4627994150 (where you saw 07:57 message)")
    print("=" * 60)
    
    YOUR_GROUP_ID = -4627994150  # Your actual group from the files
    backend_url = "https://calibot-utq6.onrender.com/webhook"
    
    # Create webhook payload for your group
    webhook_payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 12345,
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "TestUser",
                "username": "testuser"
            },
            "chat": {
                "id": YOUR_GROUP_ID,
                "type": "group",
                "title": "Your Test Group"
            },
            "date": int(datetime.now().timestamp()),
            "text": "update my lessons tomorrow"
        }
    }
    
    print(f"📤 Sending 'update my lessons tomorrow' to group {YOUR_GROUP_ID}...")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(backend_url, json=webhook_payload) as response:
            if response.status == 200:
                print(f"✅ SUCCESS! Demo sent to your group!")
                print(f"📱 CHECK YOUR TELEGRAM GROUP NOW!")
                print(f"🎯 You should see CaliBOT respond with multi-event buttons")
                print(f"")
                print(f"🔘 WORKFLOW TO TEST:")
                print(f"1. Click '1️⃣ One by One' button")
                print(f"2. See 'UPDATE Event 1 of 2'")  
                print(f"3. Click '✅ Yes'")
                print(f"4. 🎯 WATCH: 'UPDATE Event 2 of 2' appears ← THE FIX!")
                print(f"5. Click '✅ Yes' or '⏭️ Skip'")
                print(f"")
                print(f"🏆 This proves the 'UPDATE Event 2 of 2' bug is FIXED!")
                
            else:
                print(f"❌ Failed: {response.status}")
                error_text = await response.text()
                print(f"Error: {error_text[:200]}")

if __name__ == "__main__":
    asyncio.run(send_to_your_actual_group())
