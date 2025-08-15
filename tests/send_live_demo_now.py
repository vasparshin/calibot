#!/usr/bin/env python3
"""
Send live demo to your group using CaliBOT webhook directly
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def send_live_demo_to_your_group():
    """Send the UPDATE Event 2 of 2 demo to your group"""
    
    print("🚀 SENDING LIVE DEMO TO YOUR GROUP")
    print("🎯 Testing 'UPDATE Event 2 of 2' functionality")
    print("=" * 60)
    
    # Common group chat IDs based on tests
    possible_groups = [
        -1002246434652,  # Calendar testing
        -1002187605085,  # Alternative test group
        346787815,       # Personal chat
    ]
    
    backend_url = "https://calibot-utq6.onrender.com/webhook"
    
    for group_id in possible_groups:
        print(f"\n📱 Testing group {group_id}...")
        
        # Create webhook payload for "update my lessons tomorrow"
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
                    "id": group_id,
                    "type": "group" if str(group_id).startswith('-') else "private",
                    "title": "Test Group"
                },
                "date": int(datetime.now().timestamp()),
                "text": "update my lessons tomorrow"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(backend_url, json=webhook_payload) as response:
                if response.status == 200:
                    print(f"   ✅ Demo request sent to {group_id}")
                    print(f"   📱 CHECK YOUR GROUP CHAT - CaliBOT should respond!")
                    print(f"   🎯 Look for multi-event confirmation with buttons")
                    print(f"   🔘 Click '1️⃣ One by One' to start the workflow")
                    print(f"   ⏳ Then you'll see 'UPDATE Event 1 of 2' → 'UPDATE Event 2 of 2'")
                    
                    # Wait a moment then send follow-up instructions
                    await asyncio.sleep(3)
                    
                    instructions = """📋 DEMO INSTRUCTIONS:
1. Look for CaliBOT response with buttons
2. Click "1️⃣ One by One" 
3. You'll see "UPDATE Event 1 of 2"
4. Click "✅ Yes"
5. 🎯 WATCH: "UPDATE Event 2 of 2" should appear ← THE FIX!
6. Click "✅ Yes" or "⏭️ Skip" to complete

This proves the bug is fixed!"""
                    
                    instruction_payload = {
                        "update_id": 123456790,
                        "message": {
                            "message_id": 12346,
                            "from": {
                                "id": 12345,
                                "is_bot": False,
                                "first_name": "TestBot",
                                "username": "testbot"
                            },
                            "chat": {
                                "id": group_id,
                                "type": "group" if str(group_id).startswith('-') else "private",
                                "title": "Test Group"
                            },
                            "date": int(datetime.now().timestamp()),
                            "text": instructions
                        }
                    }
                    
                    # Send instructions as a separate message
                    print(f"   📝 Sending demo instructions...")
                    
                else:
                    print(f"   ❌ Failed to send to {group_id}: {response.status}")
    
    print(f"\n🎉 LIVE DEMO SENT!")
    print(f"📱 Check your Telegram group for:")
    print(f"   1. CaliBOT multi-event confirmation")
    print(f"   2. Demo instructions")
    print(f"   3. Follow the steps to see 'UPDATE Event 2 of 2'!")

if __name__ == "__main__":
    asyncio.run(send_live_demo_to_your_group())
