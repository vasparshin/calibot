#!/usr/bin/env python3
"""
Get owner ID and service info from Render API
"""

import asyncio
import aiohttp
import json

RENDER_API_KEY = 'rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP'
SERVICE_ID = 'srv-ctglj6qj1k6c73fpjbeg'

async def get_service_info():
    """Get service info to find owner ID"""
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Try to get service info first
    service_url = f"https://api.render.com/v1/services/{SERVICE_ID}"
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Getting service information...")
        try:
            async with session.get(service_url, headers=headers) as response:
                print(f"Status: {response.status}")
                data = await response.text()
                
                if response.status == 200:
                    json_data = json.loads(data)
                    print("✅ Service info retrieved!")
                    print(f"Service name: {json_data.get('name', 'Unknown')}")
                    print(f"Service type: {json_data.get('type', 'Unknown')}")
                    print(f"Owner ID: {json_data.get('ownerId', 'Not found')}")
                    
                    # Try to get logs with the owner ID
                    owner_id = json_data.get('ownerId')
                    if owner_id:
                        await test_logs_with_owner_id(session, owner_id)
                    
                else:
                    print(f"❌ Error: {data}")
        except Exception as e:
            print(f"❌ Exception: {e}")

async def test_logs_with_owner_id(session, owner_id):
    """Test logs API with owner ID"""
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    logs_url = "https://api.render.com/v1/logs"
    
    # Test with owner ID and different service parameter combinations
    test_params = [
        {'ownerId': owner_id, 'serviceId': SERVICE_ID},
        {'ownerId': owner_id, 'resource': SERVICE_ID},
        {'ownerId': owner_id, 'limit': 10},
        {'ownerId': owner_id},
    ]
    
    for i, params in enumerate(test_params):
        print(f"\n🧪 Log Test {i+1}: {params}")
        try:
            async with session.get(logs_url, headers=headers, params=params) as response:
                print(f"   Status: {response.status}")
                data = await response.text()
                
                if response.status == 200:
                    json_data = json.loads(data)
                    logs = json_data.get('logs', [])
                    print(f"   ✅ SUCCESS! Found {len(logs)} logs")
                    if logs:
                        print(f"   Sample log: {logs[0].get('message', '')[:100]}...")
                        # Show the first few logs
                        for j, log in enumerate(logs[:3]):
                            print(f"   Log {j+1}: {log.get('message', '')[:80]}...")
                    break
                else:
                    print(f"   ❌ Error: {data[:200]}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(get_service_info())
