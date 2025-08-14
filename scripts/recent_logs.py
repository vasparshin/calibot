#!/usr/bin/env python3
"""
Recent CaliBOT Logs Fetcher - Gets logs from last 30 minutes
CRITICAL: Does NOT stream - fetches recent logs and exits to avoid getting stuck
"""
import requests
import time
import os
from datetime import datetime, timedelta

# Configuration
SERVICE_ID = "srv-d1vqbkp5pdvs73echbeg"
OWNER_ID = "tea-d1vp1ph5pdvs73ebf50g"
API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def get_recent_logs():
    """Get logs from last 30 minutes - NO STREAMING"""
    try:
        # Calculate time range for last 30 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=30)
        
        params = {
            "ownerId": OWNER_ID,
            "resource": SERVICE_ID,
            "limit": 100  # Reduced limit to avoid "too large" error
        }
        
        print(f"🔍 Fetching logs from {start_time.strftime('%H:%M:%S')} to {end_time.strftime('%H:%M:%S')} UTC")
        
        response = requests.get("https://api.render.com/v1/logs", headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("logs", [])
        elif response.status_code == 429:
            print("⏳ Rate limited - try again in 1 minute")
            return []
        else:
            print(f"❌ API Error {response.status_code}: {response.text[:200]}")
            return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def format_log(log_entry):
    """Format log with color coding and filtering"""
    timestamp = log_entry.get("timestamp", "")
    message = log_entry.get("message", "").strip()
    
    if not message:
        return None
    
    # Parse timestamp for display
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_str = dt.strftime("%H:%M:%S")
    except:
        time_str = timestamp[:8] if len(timestamp) >= 8 else "unknown"
    
    # Filter important log types
    if "multi_event" in message.lower() or "EventQueueHandler" in message:
        return f"🔄 {time_str} | {message}"
    elif "nlp_agent" in message.lower() or "intent" in message.lower():
        return f"🧠 {time_str} | {message}"
    elif "calendar" in message.lower() and any(x in message.lower() for x in ["get", "list", "found"]):
        return f"📅 {time_str} | {message}"
    elif "ERROR" in message or "🚨" in message or "error" in message.lower():
        return f"❌ {time_str} | {message}"
    elif "WARNING" in message:
        return f"⚠️  {time_str} | {message}"
    elif "INFO:" in message and any(important in message for important in [
        "multi_event", "nlp_agent", "calendar", "intent", "update", "create", "delete", "move"
    ]):
        return f"ℹ️  {time_str} | {message}"
    elif "POST /webhook" in message:
        return f"📨 {time_str} | New webhook request received"
    elif "move" in message.lower() or "last 2" in message.lower():
        return f"🎯 {time_str} | {message}"
    else:
        return f"📝 {time_str} | {message}"

def main():
    """Get recent logs from last 30 minutes - NO STREAMING"""
    print("🔍 CaliBOT Recent Logs (Last 30 Minutes)")
    print("=" * 80)
    
    logs = get_recent_logs()
    
    if not logs:
        print("❌ No logs found or error fetching logs")
        return
    
    print(f"📊 Found {len(logs)} log entries")
    print("-" * 80)
    
    # Filter and display important logs
    important_logs = []
    for log in logs:
        formatted = format_log(log)
        if formatted:
            important_logs.append(formatted)
    
    # Show most recent logs first
    for log in important_logs[-50:]:  # Last 50 important logs
        print(log)
    
    print("-" * 80)
    print(f"✅ Displayed {len(important_logs)} important log entries")
    print("🔍 Look for logs about 'move', 'last 2', 'multi_event', or 'nlp_agent'")

if __name__ == "__main__":
    main()
