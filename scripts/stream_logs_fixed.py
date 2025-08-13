#!/usr/bin/env python3
"""
Stream logs from Render.com in real-time for debugging CaliBOT
Usage: python scripts/stream_logs_fixed.py
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime, timezone, timedelta

# Render API configuration
RENDER_API_KEY = 'rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP'  # Your API key
SERVICE_ID = 'srv-d1vqbkp5pdvs73echbeg'  # Correct CaliBOT service ID
OWNER_ID = 'tea-d1vp1ph5pdvs73ebf50g'  # Your owner ID

async def get_logs_batch(session, start_time=None, end_time=None):
    """Get a batch of logs from Render API"""
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Build query parameters
    params = {
        'ownerId': OWNER_ID,
        'resource': SERVICE_ID,  # Use 'resource' parameter for service filtering
        'limit': 100  # Max logs per request
    }
    
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time
    
    logs_url = "https://api.render.com/v1/logs"
    
    try:
        async with session.get(logs_url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                error_text = await response.text()
                print(f"❌ API Error {response.status}: {error_text}")
                return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

async def stream_render_logs():
    """Stream logs from Render service in real-time"""
    
    print(f"🔄 Streaming logs from CaliBOT service: {SERVICE_ID}")
    print(f"📡 API endpoint: https://api.render.com/v1/logs")
    print("=" * 80)
    print("✅ Connected to Render API")
    print("🎯 Watching for CaliBOT activity...")
    print("-" * 80)
    
    # Start from 5 minutes ago to catch recent activity
    start_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    
    try:
        async with aiohttp.ClientSession() as session:
            last_seen_time = start_time
            
            while True:
                # Get logs from the last seen time
                data = await get_logs_batch(session, start_time=last_seen_time)
                
                if data and 'logs' in data:
                    logs = data['logs']
                    
                    for log_entry in logs:
                        timestamp = log_entry.get('timestamp', '')
                        message = log_entry.get('message', '')
                        
                        # Format timestamp for display
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            display_time = dt.strftime("%H:%M:%S")
                        except:
                            display_time = timestamp[:8] if len(timestamp) > 8 else timestamp
                        
                        # Color code important log types
                        if "🔍 LLM" in message:
                            print(f"🔍 {display_time} | {message}")
                        elif "🚨" in message:
                            print(f"🚨 {display_time} | {message}")
                        elif "ERROR" in message:
                            print(f"❌ {display_time} | {message}")
                        elif "Target" in message or "target" in message:
                            print(f"🎯 {display_time} | {message}")
                        elif "Bot sending" in message:
                            print(f"🤖 {display_time} | {message}")
                        else:
                            print(f"📝 {display_time} | {message}")
                    
                    # Update last seen time for next batch
                    if logs:
                        last_seen_time = logs[-1].get('timestamp', last_seen_time)
                
                # Wait before next request to avoid rate limiting
                await asyncio.sleep(2)
                
    except KeyboardInterrupt:
        print("\n🛑 Log streaming stopped by user")
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        print("🔄 Retrying in 5 seconds...")
        await asyncio.sleep(5)
        # Retry with recursive call
        await stream_render_logs()

if __name__ == "__main__":
    print("🚀 Starting CaliBOT log streaming...")
    print("📋 Press Ctrl+C to stop")
    print()
    
    try:
        asyncio.run(stream_render_logs())
    except KeyboardInterrupt:
        print("\n👋 Log streaming stopped")
        sys.exit(0)
