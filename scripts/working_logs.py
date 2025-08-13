#!/usr/bin/env python3
"""
Working CaliBOT log viewer using correct Render API
Usage: python scripts/working_logs.py
"""
import requests
import json
import time
from datetime import datetime

# Correct configuration from service discovery
SERVICE_ID = "srv-d1vqbkp5pdvs73echbeg"
OWNER_ID = "tea-d1vp1ph5pdvs73ebf50g"
API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

# Correct API endpoint
LOGS_URL = "https://api.render.com/v1/logs"

print("🔄 Getting CaliBOT logs...")
print(f"📡 Service: {SERVICE_ID}")
print(f"👤 Owner: {OWNER_ID}")
print("=" * 80)

# API call with correct parameters
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Parameters that work (simpler approach)
params = {
    "ownerId": OWNER_ID,
    "limit": 50
}

try:
    response = requests.get(LOGS_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        logs_data = response.json()
        logs = logs_data.get("logs", [])
        print(f"✅ Retrieved {len(logs)} log entries")
        print("-" * 80)
        
        # Display recent logs
        for log_entry in logs[-30:]:  # Show last 30 entries
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
            if "🔍" in message or "LLM" in message:
                print(f"🔍 {time_str} | {message}")
            elif "🎯" in message or "Target" in message or "target" in message:
                print(f"🎯 {time_str} | {message}")
            elif "🤖" in message or "Bot sending" in message:
                print(f"🤖 {time_str} | {message}")
            elif "ERROR" in message or "🚨" in message or "error" in message.lower():
                print(f"❌ {time_str} | {message}")
            elif "INFO:" in message:
                print(f"ℹ️  {time_str} | {message}")
            else:
                print(f"📝 {time_str} | {message}")
                
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("💡 This shows recent logs. Send a message to CaliBOT and run again to see new activity!")
print(f"💡 Command: python scripts/working_logs.py")
