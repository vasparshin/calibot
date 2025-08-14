#!/usr/bin/env python3
"""Quick webhook test"""

import requests
import json

# Test single webhook call
url = "https://calibot-utq6.onrender.com/webhook"
payload = {
    "update_id": 12345,
    "message": {
        "message_id": 1,
        "from": {"id": 123456789, "first_name": "TestUser"},
        "chat": {"id": -4627994150, "type": "group"},
        "date": 1234567890,
        "text": "Create a test meeting tomorrow at 2 PM"
    }
}

print("🔄 Testing webhook call...")
response = requests.post(url, json=payload, timeout=15)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
