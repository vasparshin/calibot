#!/usr/bin/env python3
"""
Test CaliBOT endpoint connectivity
"""

import requests
import json

# Test endpoints
CALIBOT_BASE = "https://calibot-utq6.onrender.com"
ENDPOINTS_TO_TEST = [
    "/",
    "/webhook",
    "/api/webhook", 
    "/health",
    "/status"
]

def test_endpoint(url):
    """Test a single endpoint"""
    try:
        print(f"🔍 Testing: {url}")
        
        # Try GET first
        response = requests.get(url, timeout=10)
        print(f"   GET {response.status_code}: {response.text[:100]}")
        
        if response.status_code == 405:  # Method not allowed
            # Try POST
            test_payload = {
                "update_id": 12345,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "first_name": "Test"},
                    "chat": {"id": -4627994150, "type": "group"},
                    "date": 1234567890,
                    "text": "test message"
                }
            }
            
            post_response = requests.post(url, json=test_payload, timeout=10)
            print(f"   POST {post_response.status_code}: {post_response.text[:100]}")
        
        return response.status_code
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0

def main():
    """Test all endpoints"""
    print("🚀 TESTING CALIBOT ENDPOINT CONNECTIVITY")
    print("=" * 60)
    
    results = {}
    
    for endpoint in ENDPOINTS_TO_TEST:
        url = f"{CALIBOT_BASE}{endpoint}"
        status = test_endpoint(url)
        results[endpoint] = status
        print()
    
    print("📊 RESULTS SUMMARY:")
    print("-" * 30)
    for endpoint, status in results.items():
        status_icon = "✅" if status == 200 else "❌" if status == 0 else "⚠️"
        print(f"  {status_icon} {endpoint}: {status}")
    
    # Find working endpoint
    working_endpoints = [ep for ep, status in results.items() if status in [200, 405]]
    if working_endpoints:
        print(f"\n💡 Likely webhook endpoint: {CALIBOT_BASE}{working_endpoints[0]}")
    else:
        print(f"\n❌ No working endpoints found. Check if CaliBOT service is running.")

if __name__ == "__main__":
    main()
