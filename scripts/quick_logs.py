#!/usr/bin/env python3
"""
✅ WORKING CaliBOT Log Viewer - Simple Version
Discovered: parameter is 'resource=serviceId' not 'resourceFilters'
"""
import requests
from datetime import datetime

# Working configuration
SERVICE_ID = "srv-d1vqbkp5pdvs73echbeg"
OWNER_ID = "tea-d1vp1ph5pdvs73ebf50g"
API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

def get_calibot_logs():
    """Get CaliBOT logs - THIS WORKS!"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # CORRECT parameters (discovered through testing)
    params = {
        "ownerId": OWNER_ID,
        "resource": SERVICE_ID,  # Key discovery: just service ID string!
        "limit": 100  # Get more logs to find the move command
    }
    
    try:
        response = requests.get("https://api.render.com/v1/logs", headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            return logs
        else:
            print(f"❌ API Error {response.status_code}: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def display_logs(logs):
    """Display logs with color coding"""
    print(f"📋 Found {len(logs)} log entries:")
    print("-" * 80)
    
    for log in logs[-50:]:  # Show last 50
        timestamp = log.get("timestamp", "")
        message = log.get("message", "").strip()
        
        # Format time
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp[:8] if timestamp else "unknown"
        
        # Color code by content
        if "🔍" in message or "LLM" in message:
            print(f"🔍 {time_str} | {message}")
        elif "🎯" in message or "Target" in message or "target" in message:
            print(f"🎯 {time_str} | {message}")
        elif "🤖" in message or "Bot sending" in message:
            print(f"🤖 {time_str} | {message}")
        elif "ERROR" in message or "🚨" in message:
            print(f"❌ {time_str} | {message}")
        else:
            print(f"📝 {time_str} | {message}")

if __name__ == "__main__":
    print("🔄 Getting CaliBOT logs...")
    print(f"📡 Service: {SERVICE_ID}")
    print("=" * 80)
    
    logs = get_calibot_logs()
    
    if logs:
        display_logs(logs)
        print("\n" + "=" * 80)
        print("✅ SUCCESS! Log viewing is working!")
        print("💡 Now send a message to CaliBOT and run this script again to see new activity")
        print("💡 Command: python scripts\\quick_logs.py")
    else:
        print("❌ No logs retrieved")
