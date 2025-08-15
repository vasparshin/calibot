#!/usr/bin/env python3
"""
Debug logs script - simplified version without Unicode issues
"""

import os
import requests
import json
from datetime import datetime, timedelta
import sys

# Service configuration
SERVICE_ID = "srv-ctglj6qj1k6c73fpjbeg"
RENDER_API_TOKEN = os.getenv('RENDER_API_TOKEN')

if not RENDER_API_TOKEN:
    print("ERROR: RENDER_API_TOKEN environment variable not set")
    sys.exit(1)

def get_recent_logs():
    """Get recent logs from Render API"""
    
    # Get logs from last 15 minutes
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    # Format for Render API (ISO format)
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"
    headers = {
        "Authorization": f"Bearer {RENDER_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    params = {
        "startTime": start_time_str,
        "endTime": end_time_str,
        "limit": 200
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            logs = response.json()
            
            # Filter for callback and queue related logs
            relevant_logs = []
            for log in logs:
                message = log.get('message', '')
                if any(keyword in message for keyword in [
                    'Callback query', 'Queue callback', 'process_queue_response',
                    'UPDATE Event', 'queue_confirm', '_process_single_event'
                ]):
                    relevant_logs.append(log)
            
            print("DEBUG LOGS - Queue Processing")
            print("=" * 50)
            
            if relevant_logs:
                for log in relevant_logs[-20:]:  # Last 20 relevant logs
                    timestamp = log.get('timestamp', 'Unknown')[:19]  # Remove microseconds
                    message = log.get('message', '').replace('\n', ' ')
                    print(f"{timestamp}: {message}")
            else:
                print("No recent queue/callback logs found")
                
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    get_recent_logs()
