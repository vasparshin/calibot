#!/usr/bin/env python3
"""
Live CaliBOT Log Streaming - Auto-refresh every 3 seconds
This allows me to monitor CaliBOT activity in real-time
"""
import requests
import time
import os
from datetime import datetime

# Configuration
SERVICE_ID = "srv-d1vqbkp5pdvs73echbeg"
OWNER_ID = "tea-d1vp1ph5pdvs73ebf50g"
API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

params = {
    "ownerId": OWNER_ID,
    "resource": SERVICE_ID,
    "limit": 100  # Get more logs for complete context
}

last_seen_timestamp = None
seen_messages = set()

def get_logs():
    """Get latest logs from CaliBOT"""
    try:
        response = requests.get("https://api.render.com/v1/logs", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("logs", [])
        elif response.status_code == 429:
            print("⏳ Rate limited, waiting...")
            time.sleep(30)
            return []
        else:
            print(f"❌ API Error {response.status_code}: {response.text[:100]}")
            return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def format_log(log_entry):
    """Format log with color coding and filtering"""
    timestamp = log_entry.get("timestamp", "")
    message = log_entry.get("message", "").strip()
    
    # Skip deployment/startup noise
    if any(skip in message for skip in [
        "==> Your service is live",
        "==> Available at",
        "==> ///////////",
        "==> Detected service running",
        "==> Docs on specifying"
    ]):
        return None
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_str = dt.strftime("%H:%M:%S")
    except:
        time_str = timestamp[:8] if timestamp else "unknown"
    
    # Color code by importance
    if "🔍" in message or "LLM" in message:
        return f"🔍 {time_str} | {message}"
    elif "🎯" in message or "Target" in message or "target" in message:
        return f"🎯 {time_str} | {message}"
    elif "🤖" in message or "Bot sending" in message:
        return f"🤖 {time_str} | {message}"
    elif "ERROR" in message or "🚨" in message or "error" in message.lower():
        return f"❌ {time_str} | {message}"
    elif "WARNING" in message:
        return f"⚠️  {time_str} | {message}"
    elif "INFO:" in message and any(important in message for important in [
        "multi_event", "nlp_agent", "calendar", "intent", "update", "create", "delete"
    ]):
        return f"ℹ️  {time_str} | {message}"
    elif "POST /webhook" in message:
        return f"📨 {time_str} | New webhook request received"
    else:
        return f"📝 {time_str} | {message}"

def stream_logs():
    """Stream logs with real-time updates"""
    global last_seen_timestamp, seen_messages
    
    print("🔄 CaliBOT Live Log Streaming")
    print(f"📡 Service: {SERVICE_ID}")
    print("=" * 80)
    print("🎯 Watching for CaliBOT activity (Press Ctrl+C to stop)...")
    print("-" * 80)
    
    try:
        while True:
            logs = get_logs()
            
            if logs:
                new_logs = []
                
                for log in logs:
                    timestamp = log.get("timestamp", "")
                    message = log.get("message", "")
                    
                    # Create unique identifier for this log entry
                    log_id = f"{timestamp}-{hash(message)}"
                    
                    # Only show new logs
                    if log_id not in seen_messages:
                        formatted = format_log(log)
                        if formatted:  # Skip filtered out logs
                            new_logs.append(formatted)
                        seen_messages.add(log_id)
                
                # Clean up old seen messages to prevent memory bloat
                if len(seen_messages) > 2000:
                    seen_messages = set(list(seen_messages)[-1000:])
                
                # Display new logs
                for log in new_logs[-20:]:  # Show last 20 new logs
                    print(log)
                
                if new_logs:
                    print(f"\n📊 {len(new_logs)} new entries | {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 80)
            
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping live log stream...")

if __name__ == "__main__":
    # Clear screen for clean output
    os.system('cls' if os.name == 'nt' else 'clear')
    stream_logs()
