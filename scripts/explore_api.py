#!/usr/bin/env python3
"""
Explore Render API to find the correct logs endpoint
"""
import requests
import json

API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"
SERVICE_ID = "srv-ctglj6qj1k6c73fpjbeg"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("🔍 Exploring Render API endpoints...")

# Try different possible endpoints
endpoints_to_try = [
    f"https://api.render.com/v1/services/{SERVICE_ID}/logs",
    f"https://api.render.com/v1/services/{SERVICE_ID}/events", 
    f"https://api.render.com/v1/services/{SERVICE_ID}/deploys",
    f"https://api.render.com/v1/services/{SERVICE_ID}",
]

for endpoint in endpoints_to_try:
    print(f"\n📡 Trying: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Keys: {list(data.keys()) if isinstance(data, dict) else f'Array with {len(data)} items'}")
            
            # If it's the service info, look for logs-related fields
            if endpoint.endswith(SERVICE_ID):
                print("Service details:")
                for key, value in data.items():
                    if 'log' in key.lower() or 'event' in key.lower():
                        print(f"  {key}: {value}")
        else:
            print(f"❌ Failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*50)
print("🔍 Let's also check the API documentation structure...")

# Try to get the service info to see what's available
try:
    response = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}", headers=headers)
    if response.status_code == 200:
        service_data = response.json()
        print("\n📋 Service information:")
        print(json.dumps(service_data, indent=2)[:1000] + "...")  # First 1000 chars
except Exception as e:
    print(f"❌ Can't get service info: {e}")
