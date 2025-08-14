import json
import requests

# Simple test to verify the backend is accessible
try:
    response = requests.get("https://calibot-utq6.onrender.com/health", timeout=10)
    print(f"Backend Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Version: {data.get('version', 'unknown')}")
        print(f"Health: {data.get('status', 'unknown')}")
        print("✅ Backend is accessible for testing")
    else:
        print(f"❌ Backend error: {response.status_code}")
except Exception as e:
    print(f"❌ Connection error: {e}")

# Test the one-by-one workflow
test_update = {
    "update_id": 12345,
    "message": {
        "message_id": 12345,
        "from": {"id": 987654321, "is_bot": False, "first_name": "TestUser"},
        "chat": {"id": 987654321, "type": "private"},
        "date": 1703123456,
        "text": "move the last 2 lessons today to tomorrow 5 and 6 pm"
    }
}

try:
    print("\n🧪 Testing one-by-one workflow request...")
    response = requests.post("https://calibot-utq6.onrender.com/webhook", json=test_update, timeout=15)
    print(f"Response Status: {response.status_code}")
    print(f"Response Preview: {response.text[:300]}...")
    
    if response.status_code == 200:
        print("✅ Initial request successful - check for multi-event confirmation options")
    else:
        print("❌ Request failed")
        
except Exception as e:
    print(f"❌ Test error: {e}")

print("\n📋 Manual Testing Steps:")
print("1. Send: 'move the last 2 lessons today to tomorrow 5 and 6 pm'")
print("2. Should show: Found 2 events with [All] [One by One] options")
print("3. Click: 'One by One' button")
print("4. Should show: Individual event with proposed changes and [Yes] [No] options")
print("5. Click: 'Yes' for first event")
print("6. Should show: Next individual event with [Yes] [No] options")
print("7. Verify: Each event shows complete change details (date + time)")
print("8. Verify: No 'operation not found' errors occur")
