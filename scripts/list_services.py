#!/usr/bin/env python3
"""
List all services to find CaliBOT service ID
"""

import asyncio
import aiohttp
import json

RENDER_API_KEY = 'rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP'

async def list_services():
    """List all services to find CaliBOT"""
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    services_url = "https://api.render.com/v1/services"
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Listing all services...")
        try:
            async with session.get(services_url, headers=headers) as response:
                print(f"Status: {response.status}")
                data = await response.text()
                
                if response.status == 200:
                    json_data = json.loads(data)
                    print(f"✅ API Response received!")
                    
                    # Handle different response formats
                    services = []
                    if isinstance(json_data, list):
                        services = json_data
                        print("Response is a list of services")
                    elif isinstance(json_data, dict) and 'services' in json_data:
                        services = json_data['services']
                        print(f"Response keys: {list(json_data.keys())}")
                    else:
                        print(f"Unexpected response format: {type(json_data)}")
                        print(f"Response: {json_data}")
                        return
                    
                    print(f"Found {len(services)} services!")
                    
                    print("\n📋 Your services:")
                    for i, item in enumerate(services):
                        # Extract the actual service data
                        if 'service' in item:
                            service = item['service']
                        else:
                            service = item
                        
                        name = service.get('name', 'Unknown')
                        service_id = service.get('id', 'Unknown')
                        service_type = service.get('type', 'Unknown')
                        suspended = service.get('suspended', 'Unknown')
                        owner_id = service.get('ownerId', 'Unknown')
                        
                        print(f"   {i+1}. {name}")
                        print(f"      ID: {service_id}")
                        print(f"      Type: {service_type}")
                        print(f"      Status: {suspended}")
                        print(f"      Owner ID: {owner_id}")
                        print()
                        
                        # If this looks like CaliBOT, test logs
                        if 'calibot' in name.lower() or 'bot' in name.lower():
                            if owner_id and owner_id != 'Unknown':
                                print(f"🎯 Found CaliBOT! Testing logs for {name}...")
                                await test_logs_for_service(session, service_id, owner_id)
                        
                else:
                    print(f"❌ Error: {data}")
        except Exception as e:
            print(f"❌ Exception: {e}")

async def test_logs_for_service(session, service_id, owner_id):
    """Test logs for a specific service"""
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    logs_url = "https://api.render.com/v1/logs"
    params = {
        'ownerId': owner_id,
        'limit': 5
    }
    
    try:
        async with session.get(logs_url, headers=headers, params=params) as response:
            if response.status == 200:
                json_data = await response.json()
                logs = json_data.get('logs', [])
                print(f"   ✅ SUCCESS! Found {len(logs)} logs")
                
                if logs:
                    print("   📝 Recent logs:")
                    for log in logs[:3]:
                        message = log.get('message', '')
                        timestamp = log.get('timestamp', '')
                        print(f"      {timestamp[:19]}: {message[:80]}...")
                
                # Now we know the correct format, save the working parameters
                print(f"\n🎯 WORKING PARAMETERS:")
                print(f"   Service ID: {service_id}")
                print(f"   Owner ID: {owner_id}")
                print(f"   API URL: {logs_url}")
                print(f"   Parameters: {params}")
                
            else:
                error_text = await response.text()
                print(f"   ❌ Logs error: {error_text[:100]}...")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(list_services())
