#!/usr/bin/env python3
"""
Stream logs from Render.com in real-time for debugging CaliBOT
Usage: python scripts/stream_logs.py
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime

# Render API configuration
RENDER_API_KEY = os.getenv('RENDER_API_KEY')
SERVICE_ID = os.getenv('RENDER_SERVICE_ID', 'srv-ctglj6qj1k6c73fpjbeg')  # CaliBOT service ID

async def stream_render_logs():
    """Stream logs from Render service in real-time"""
    
    if not RENDER_API_KEY:
        print("❌ RENDER_API_KEY environment variable not set")
        print("   Get your API key from: https://dashboard.render.com/user/settings")
        print("   Set it with: export RENDER_API_KEY='your_key_here'")
        return
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Render logs endpoint
    logs_url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"
    
    print(f"🔄 Streaming logs from CaliBOT service: {SERVICE_ID}")
    print(f"📡 API endpoint: {logs_url}")
    print("=" * 80)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(logs_url, headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Failed to connect to Render API: {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return
                
                print("✅ Connected to Render log stream")
                print("🎯 Watching for CaliBOT activity...")
                print("-" * 80)
                
                async for line in response.content:
                    if line:
                        try:
                            # Decode and parse the log line
                            log_data = json.loads(line.decode('utf-8'))
                            timestamp = log_data.get('timestamp', datetime.now().isoformat())
                            message = log_data.get('message', str(log_data))
                            
                            # Color code important log types
                            if '🔍 LLM' in message:
                                print(f"🔍 {timestamp} | {message}")
                            elif '🚨' in message:
                                print(f"🚨 {timestamp} | {message}")
                            elif 'ERROR' in message:
                                print(f"❌ {timestamp} | {message}")
                            elif 'Target' in message or 'target' in message:
                                print(f"🎯 {timestamp} | {message}")
                            elif 'Bot sending' in message:
                                print(f"🤖 {timestamp} | {message}")
                            else:
                                print(f"📝 {timestamp} | {message}")
                                
                        except json.JSONDecodeError:
                            # Handle plain text logs
                            line_str = line.decode('utf-8').strip()
                            if line_str:
                                print(f"📄 {datetime.now().strftime('%H:%M:%S')} | {line_str}")
                                
    except KeyboardInterrupt:
        print("\n🛑 Log streaming stopped by user")
    except Exception as e:
        print(f"❌ Error streaming logs: {e}")

def print_setup_instructions():
    """Print setup instructions for log streaming"""
    print("📋 Render Log Streaming Setup Instructions:")
    print()
    print("1. Get your Render API key:")
    print("   - Go to: https://dashboard.render.com/user/settings")
    print("   - Generate or copy your API key")
    print()
    print("2. Set environment variable:")
    print("   Windows: set RENDER_API_KEY=your_key_here")
    print("   Linux/Mac: export RENDER_API_KEY='your_key_here'")
    print()
    print("3. Run the log streamer:")
    print("   python scripts/stream_logs.py")
    print()
    print("4. Test CaliBOT while logs are streaming:")
    print("   - Send 'yesterdays schedule' to bot")
    print("   - Send 'move the last 3 events yesterday 1 hr later'")
    print("   - Watch real-time logs with target selection debugging")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_setup_instructions()
    else:
        asyncio.run(stream_render_logs())
