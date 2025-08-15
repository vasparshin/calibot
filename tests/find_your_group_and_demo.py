#!/usr/bin/env python3
"""
Find YOUR group chat ID and send the demo there
"""
import asyncio
import aiohttp
import json
import os

# Use the working testbot token
TESTBOT_TOKEN = "7669505498:AAE5H3K3iLk7H-cxuAEWucxqhcuBU4QzEk4"

async def find_and_test_your_group():
    """Find your group chat and send the demo"""
    
    print("🔍 FINDING YOUR GROUP CHAT (last message 07:57)")
    print("=" * 60)
    
    # Get recent updates to find your group
    url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/getUpdates"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            
        if not result.get('ok'):
            print(f"❌ Can't get updates: {result}")
            return
            
        updates = result.get('result', [])
        print(f"📊 Found {len(updates)} recent updates")
        
        # Look for group chats in recent updates
        group_chats = {}
        for update in updates:
            if 'message' in update:
                chat = update['message']['chat']
                if chat['type'] in ['group', 'supergroup']:
                    chat_id = chat['id']
                    title = chat.get('title', 'Unknown')
                    group_chats[chat_id] = title
                    
        print("📱 Found these group chats:")
        for chat_id, title in group_chats.items():
            print(f"   {chat_id}: {title}")
            
        # Test message to all found groups
        test_message = """🧪 LIVE DEMO TEST - UPDATE Event 2 of 2

I'm testing if this is YOUR group where you saw the last message at 07:57.

If you can see this message, then I found the right group and can now demonstrate the "UPDATE Event 2 of 2" fix!

Next: I'll send a multi-event request to show you the working functionality."""

        for chat_id in group_chats.keys():
            print(f"\n📤 Sending test message to {chat_id} ({group_chats[chat_id]})")
            
            send_url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': test_message,
                'parse_mode': 'HTML'
            }
            
            async with session.post(send_url, json=payload) as send_response:
                result = await send_response.json()
                if result.get('ok'):
                    print(f"   ✅ Message sent successfully to {group_chats[chat_id]}")
                    
                    # Now send the actual demo request
                    await asyncio.sleep(2)
                    
                    demo_message = "update my lessons tomorrow"
                    demo_payload = {
                        'chat_id': chat_id,
                        'text': f"🤖 TestBot: {demo_message}",
                        'parse_mode': 'HTML'
                    }
                    
                    async with session.post(send_url, json=demo_payload) as demo_response:
                        demo_result = await demo_response.json()
                        if demo_result.get('ok'):
                            print(f"   ✅ Demo request sent: '{demo_message}'")
                            print(f"   🎯 Watch for CaliBOT response with multi-event buttons!")
                        else:
                            print(f"   ❌ Demo failed: {demo_result}")
                            
                else:
                    print(f"   ❌ Failed to send to {group_chats[chat_id]}: {result}")

if __name__ == "__main__":
    asyncio.run(find_and_test_your_group())
