#!/usr/bin/env python3
"""
Direct Group Chat Demo - UPDATE Event 2 of 2 Fix
Sends actual messages to the group chat to demonstrate the fix.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os

class DirectGroupDemo:
    def __init__(self):
        # Use environment variables directly
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.group_chat_id = os.getenv('TEST_GROUP_CHAT_ID', "-1002187605085")
        self.backend_url = os.getenv('BACKEND_URL', 'https://calibot-fhfs.onrender.com')
        
        if not self.bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found in environment")
            return
    
    async def send_message_to_group(self, text):
        """Send message directly to group chat"""
        if not self.bot_token:
            print("❌ No bot token available")
            return
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.group_chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if result.get('ok'):
                    print(f"✅ Message sent to group: {text}")
                    return result['result']
                else:
                    print(f"❌ Failed to send message: {result}")
                    return None
    
    async def demo_workflow(self):
        """Demonstrate the complete workflow"""
        print("🚀 DIRECT GROUP CHAT DEMO - UPDATE Event 2 of 2 Fix")
        print("=" * 60)
        print(f"📱 Group Chat ID: {self.group_chat_id}")
        print(f"🌐 Backend URL: {self.backend_url}")
        print()
        
        if not self.bot_token:
            print("❌ Cannot proceed without bot token")
            return
        
        # Send demo message to group
        demo_message = """🧪 LIVE DEMO STARTING NOW!

Testing the fixed "UPDATE Event 2 of 2" functionality.

🎯 What to expect:
1. I'll send a multi-event update request
2. Bot will show confirmation options
3. We'll select "One by One" processing  
4. Bot shows "UPDATE Event 1 of 2"
5. After confirming Event 1, bot should show "UPDATE Event 2 of 2"

This demonstrates the fix for the bug where Event 2 wasn't appearing!

Starting demo in 5 seconds..."""
        
        await self.send_message_to_group(demo_message)
        await asyncio.sleep(5)
        
        # Send the actual test message that triggers multi-event processing
        test_message = "update my lessons tomorrow"
        
        await self.send_message_to_group(f"🧪 TEST COMMAND: {test_message}")
        
        print("\n✅ Demo messages sent to group chat!")
        print("📱 Now check the group chat to see the interaction")
        print("🎯 Look for the 'UPDATE Event 2 of 2' message after confirming Event 1")
        print("\n🔍 Next steps in group chat:")
        print("1. Bot should respond with multi-event confirmation")
        print("2. Click '1️⃣ One by One' button")
        print("3. Bot shows 'UPDATE Event 1 of 2'")
        print("4. Click '✅ Yes' to confirm Event 1") 
        print("5. Bot should show 'UPDATE Event 2 of 2' ← THIS IS THE FIX!")
        print("6. Click '✅ Yes' to confirm Event 2")
        print("7. Both events get updated successfully")

async def main():
    """Run the direct group demo"""
    demo = DirectGroupDemo()
    await demo.demo_workflow()

if __name__ == "__main__":
    asyncio.run(main())
