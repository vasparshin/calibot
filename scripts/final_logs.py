#!/usr/bin/env python3
"""
🎉 WORKING CaliBOT Log Streaming Script
Discovered the correct API format: resource=serviceId (not resourceFilters)
Usage: python scripts/final_logs.py
"""
import requests
import json
import time
from datetime import datetime

# Correct configuration
SERVICE_ID = "srv-d1vqbkp5pdvs73echbeg"
OWNER_ID = "tea-d1vp1ph5pdvs73ebf50g" 
API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

# Working API endpoint and parameters
LOGS_URL = "https://api.render.com/v1/logs"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# CORRECT PARAMETERS (discovered through testing)
params = {
    "ownerId": OWNER_ID,
    "resource": SERVICE_ID,  # This is the key! Just service ID, not JSON
    "limit": 50
}

def get_logs():
    """Get latest logs from CaliBOT"""
    try:
        response = requests.get(LOGS_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("logs", [])
        elif response.status_code == 429:
            print("⏳ Rate limited, waiting...")
            time.sleep(10)
            return []
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def format_log(log_entry):
    """Format a log entry with color coding"""
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
        return f"🔍 {time_str} | {message}"
    elif "🎯" in message or "Target" in message or "target" in message:
        return f"🎯 {time_str} | {message}"
    elif "🤖" in message or "Bot sending" in message:
        return f"🤖 {time_str} | {message}"
    elif "ERROR" in message or "🚨" in message or "error" in message.lower():
        return f"❌ {time_str} | {message}"
    elif "INFO:" in message:
        return f"ℹ️  {time_str} | {message}"
    else:
        return f"📝 {time_str} | {message}"

def main():
    print("🔄 CaliBOT Real-Time Log Streaming")
    print(f"📡 Service: {SERVICE_ID}")
    print(f"👤 Owner: {OWNER_ID}")
    print("=" * 80)
    print("✅ Using WORKING API format: resource=serviceId")
    print("🎯 Watching for CaliBOT activity...")
    print("-" * 80)
    
    last_seen_logs = set()
    
    try:
        while True:
            logs = get_logs()
            
            if logs:
                # Filter out logs we've already seen
                new_logs = []
                for log in logs:
                    log_id = f"{log.get('timestamp', '')}-{log.get('message', '')[:50]}"
                    if log_id not in last_seen_logs:
                        new_logs.append(log)
                        last_seen_logs.add(log_id)
                
                # Keep only recent IDs to prevent memory buildup
                if len(last_seen_logs) > 1000:
                    last_seen_logs = set(list(last_seen_logs)[-500:])
                
                # Display new logs
                for log in new_logs:
                    print(format_log(log))
                    
                if new_logs:
                    print(f"📊 Displayed {len(new_logs)} new log entries")
            
            # Wait before next poll
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping log stream...")
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")

if __name__ == "__main__":
    # First, show recent logs
    print("📋 Recent logs:")
    logs = get_logs()
    if logs:
        for log in logs[-10:]:  # Show last 10
            print(format_log(log))
        print("\n" + "="*80)
    
    # Ask if user wants to start streaming
    choice = input("Start real-time streaming? (y/n): ").lower()
    if choice in ['y', 'yes']:
        main()
    else:
        print("💡 To view logs later: python scripts/final_logs.py")
