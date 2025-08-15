#!/usr/bin/env python3
"""
Pull latest logs from Render API and store them in logs/ folder for every deployment.
This ensures logs are easily accessible without running scripts each time.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

# Render API configuration
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = "srv-cr8q02ogph6c73fkslcg"  # CaliBOT service ID

def ensure_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"✅ Created logs directory: {logs_dir}")
    return logs_dir

def pull_latest_logs(hours_back=2):
    """Pull logs from the last N hours"""
    if not RENDER_API_KEY:
        print("❌ RENDER_API_KEY environment variable not set")
        print("💡 Set it with: export RENDER_API_KEY=your_api_key")
        return None
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours_back)
    
    print(f"🔍 Fetching logs from {start_time.strftime('%H:%M:%S')} to {end_time.strftime('%H:%M:%S')} UTC")
    
    # Render API endpoint for logs
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {
        "startTime": start_time.isoformat() + "Z",
        "endTime": end_time.isoformat() + "Z", 
        "limit": 200
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            logs_data = response.json()
            print(f"📊 Retrieved {len(logs_data)} log entries")
            return logs_data
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching logs: {e}")
        return None

def save_logs_to_file(logs_data, logs_dir):
    """Save logs to timestamped file"""
    if not logs_data:
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"deployment_logs_{timestamp}.json"
    filepath = os.path.join(logs_dir, filename)
    
    # Save raw JSON
    with open(filepath, 'w') as f:
        json.dump(logs_data, f, indent=2)
    
    # Also save human-readable format
    readable_filename = f"deployment_logs_{timestamp}.txt"
    readable_filepath = os.path.join(logs_dir, readable_filename)
    
    with open(readable_filepath, 'w') as f:
        f.write(f"CaliBOT Deployment Logs - {timestamp}\n")
        f.write("=" * 60 + "\n\n")
        
        for entry in logs_data:
            timestamp_str = entry.get('timestamp', 'Unknown time')
            message = entry.get('message', 'No message')
            f.write(f"📝 {timestamp_str} | {message}\n")
    
    print(f"✅ Logs saved to:")
    print(f"   📄 Raw JSON: {filepath}")
    print(f"   📄 Readable: {readable_filepath}")
    
    return filepath

def cleanup_old_logs(logs_dir, keep_days=7):
    """Remove log files older than specified days"""
    cutoff_time = datetime.now() - timedelta(days=keep_days)
    
    for filename in os.listdir(logs_dir):
        if filename.startswith('deployment_logs_'):
            filepath = os.path.join(logs_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if file_time < cutoff_time:
                os.remove(filepath)
                print(f"🗑️  Removed old log file: {filename}")

def main():
    """Main function to pull and save deployment logs"""
    print("🚀 CaliBOT Deployment Logs Puller")
    print("=" * 40)
    
    # Ensure logs directory exists
    logs_dir = ensure_logs_directory()
    
    # Pull latest logs
    logs_data = pull_latest_logs(hours_back=2)
    
    if logs_data:
        # Save to files
        save_logs_to_file(logs_data, logs_dir)
        
        # Cleanup old logs
        cleanup_old_logs(logs_dir)
        
        print("\n✅ Deployment logs successfully pulled and saved!")
        print(f"📁 Check the logs/ directory for files")
    else:
        print("\n❌ Failed to pull logs")
        sys.exit(1)

if __name__ == "__main__":
    main()
