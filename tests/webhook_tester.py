#!/usr/bin/env python3
"""
Webhook Tester - Tests if Calibot's webhook endpoint is working.
"""

import asyncio
import aiohttp
import json
import time

async def test_webhook_endpoint(base_url: str):
    """Test if the webhook endpoint is responding."""
    
    webhook_url = f"{base_url}/webhook"
    health_url = f"{base_url}/health"
    
    print(f"🔍 Testing Calibot deployment at: {base_url}")
    print("=" * 60)
    
    # Test payload similar to what Telegram sends
    test_payload = {
        "update_id": int(time.time()),
        "message": {
            "message_id": int(time.time()),
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 12345,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "test message"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        try:
            async with session.get(health_url, timeout=10) as response:
                status = response.status
                text = await response.text()
                print(f"   Status: {status}")
                print(f"   Response: {text[:100]}...")
                
                if status == 200:
                    print("   ✅ Health check passed")
                else:
                    print("   ❌ Health check failed")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        print()
        
        # Test webhook endpoint
        print("📡 Testing webhook endpoint...")
        try:
            async with session.post(webhook_url, json=test_payload, timeout=10) as response:
                status = response.status
                
                if response.content_type == 'application/json':
                    result = await response.json()
                    response_text = json.dumps(result, indent=2)
                else:
                    response_text = await response.text()
                
                print(f"   Status: {status}")
                print(f"   Response: {response_text[:200]}...")
                
                if 200 <= status < 300:
                    print("   ✅ Webhook is responding")
                else:
                    print("   ❌ Webhook failed")
                    
        except Exception as e:
            print(f"   ❌ Webhook error: {e}")

async def main():
    """Test webhook endpoints."""
    
    print("🤖 CALIBOT WEBHOOK TESTER")
    print("=" * 40)
    
    # Common Render URL patterns
    possible_urls = [
        "https://calibot.onrender.com",
        "https://calibot-api.onrender.com", 
        "https://calibot-backend.onrender.com",
    ]
    
    print("Enter your Calibot deployment URL:")
    print("(or press Enter to test common URLs)")
    
    custom_url = input("URL: ").strip()
    
    if custom_url:
        await test_webhook_endpoint(custom_url)
    else:
        print("\n🔍 Testing common Render URL patterns...")
        
        for url in possible_urls:
            print(f"\n📡 Testing: {url}")
            await test_webhook_endpoint(url)
            await asyncio.sleep(1)  # Brief pause between tests

if __name__ == "__main__":
    asyncio.run(main())
