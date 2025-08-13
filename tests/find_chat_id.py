#!/usr/bin/env python3
"""
Chat ID Finder - Helps find the correct chat ID for the Calendar testing group.
"""

import asyncio
import aiohttp
import json

async def find_chat_id():
    """Find chat IDs from recent bot activity."""
    
    bot_token = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    print("🔍 Looking for chat IDs from recent bot activity...")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
    
    if not result.get("ok"):
        print(f"❌ API Error: {result}")
        return
    
    updates = result.get("result", [])
    chats = {}
    
    for update in updates:
        if "message" in update:
            chat = update["message"]["chat"]
            chat_id = chat["id"]
            chat_title = chat.get("title", chat.get("first_name", "Private Chat"))
            chat_type = chat.get("type", "unknown")
            
            if chat_id not in chats:
                chats[chat_id] = {
                    "title": chat_title,
                    "type": chat_type,
                    "last_message": update["message"].get("text", "No text")[:50]
                }
    
    if not chats:
        print("❌ No recent chat activity found.")
        print("\n💡 TO GET CHAT ID:")
        print("1. Send a message to the test bot in the 'Calendar testing' group")
        print("2. Type anything like: 'Hello test bot'")
        print("3. Run this script again")
        return
    
    print("📋 Found these chats:")
    print()
    
    for chat_id, info in chats.items():
        print(f"Chat ID: {chat_id}")
        print(f"  Title: {info['title']}")
        print(f"  Type: {info['type']}")
        print(f"  Last message: {info['last_message']}...")
        print()
    
    # Look for Calendar testing specifically
    calendar_chats = []
    for chat_id, info in chats.items():
        if "calendar" in info["title"].lower() and "test" in info["title"].lower():
            calendar_chats.append((chat_id, info))
    
    if calendar_chats:
        print("🎯 FOUND CALENDAR TESTING CHATS:")
        for chat_id, info in calendar_chats:
            print(f"  ✅ Chat ID: {chat_id} - {info['title']}")
    else:
        print("⚠️ No 'Calendar testing' group found in recent messages.")
        print("Make sure to send a message in that group first.")

if __name__ == "__main__":
    asyncio.run(find_chat_id())
