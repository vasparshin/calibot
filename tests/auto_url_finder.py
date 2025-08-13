#!/usr/bin/env python3
"""
Auto URL Tester - Tests common Render URL patterns to find your backend
"""

import asyncio
import aiohttp

async def find_calibot_backend():
    """Test common URL patterns to find the working backend."""
    
    # Common patterns for Render URLs
    possible_urls = [
        "https://calibot.onrender.com",
        "https://calibot-backend.onrender.com", 
        "https://calibot-api.onrender.com",
        "https://calibot-utq6.onrender.com",  # From earlier test
        "https://vas-calibot.onrender.com",
        "https://calibot-vas.onrender.com",
        "https://calibot-bot.onrender.com"
    ]
    
    print("🔍 TESTING COMMON CALIBOT URL PATTERNS")
    print("=" * 50)
    
    working_urls = []
    
    async with aiohttp.ClientSession() as session:
        for url in possible_urls:
            try:
                webhook_url = f"{url}/webhook"
                print(f"🧪 Testing: {url}")
                
                # Test webhook endpoint
                test_payload = {
                    "update_id": 123,
                    "message": {
                        "message_id": 456,
                        "from": {"id": 789, "is_bot": False, "first_name": "Test"},
                        "chat": {"id": 789, "type": "private"},
                        "date": 1234567890,
                        "text": "test"
                    }
                }
                
                async with session.post(webhook_url, json=test_payload, timeout=10) as response:
                    if response.status == 200:
                        print(f"   ✅ FOUND WORKING BACKEND: {url}")
                        working_urls.append(url)
                    else:
                        print(f"   ❌ Status {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:50]}...")
    
    print(f"\n📊 RESULTS")
    print("=" * 20)
    
    if working_urls:
        print(f"✅ Found {len(working_urls)} working backend(s):")
        for url in working_urls:
            print(f"   🎯 {url}")
        
        # Use the first working URL for testing
        best_url = working_urls[0]
        print(f"\n🚀 Using {best_url} for testing...")
        
        return best_url
    else:
        print("❌ No working backends found")
        print("💡 Please provide your Render URL manually")
        return None

async def main():
    backend_url = await find_calibot_backend()
    
    if backend_url:
        print(f"\n🎯 Ready to test with: {backend_url}")
        print("Run the backend_bridge_tester.py with this URL!")

if __name__ == "__main__":
    asyncio.run(main())
