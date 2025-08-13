#!/usr/bin/env python3
"""
Simple CaliBOT log viewer using Render API
Usage: python scripts/simple_logs.py
"""
import requests
import json
import time
from datetime import datetime

# Configuration from the working service discovery
SERVICE_ID = "srv-ctglj6qj1k6c73fpjbeg"
OWNER_ID = "usr-ctgkpv6j1k6c73fpmfgg"
API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

# API endpoint
LOGS_URL = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"

print("🔄 Getting CaliBOT logs...")
print(f"📡 Service: {SERVICE_ID}")
print("=" * 80)

# Simple API call to get recent logs
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

try:
    # Get recent logs (last 100 entries)
    response = requests.get(LOGS_URL, headers=headers, params={"limit": 100})
    
    if response.status_code == 200:
        logs_data = response.json()
        print(f"✅ Retrieved {len(logs_data)} log entries")
        print("-" * 80)
        
        # Display recent logs
        for log_entry in logs_data[-20:]:  # Show last 20 entries
            timestamp = log_entry.get("timestamp", "unknown")
            message = log_entry.get("message", "").strip()
            
            # Format timestamp
            if timestamp != "unknown":
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:8]
            else:
                time_str = "unknown"
            
            # Color code important messages
            if "🔍" in message:
                print(f"🔍 {time_str} | {message}")
            elif "🎯" in message or "Target" in message:
                print(f"🎯 {time_str} | {message}")
            elif "🤖" in message or "Bot sending" in message:
                print(f"🤖 {time_str} | {message}")
            elif "ERROR" in message or "🚨" in message:
                print(f"❌ {time_str} | {message}")
            else:
                print(f"📝 {time_str} | {message}")
                
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("💡 This shows recent logs. For real-time streaming, we need to implement polling.")
print("💡 Try sending a message to CaliBOT and run this script again to see new logs.")
