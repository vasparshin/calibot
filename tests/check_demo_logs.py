#!/usr/bin/env python3
"""
Quick log check without emojis to see the demo activity
"""
import requests
from datetime import datetime, timedelta

def check_demo_logs():
    url = 'https://api.render.com/v1/services/srv-cr5mq76ehbks739rh64g/logs'
    headers = {'Authorization': 'Bearer rnd_6KwXpcHKzNBv6dMaMIrIHwFQjTGI'}
    
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=10)
    
    params = {
        'startTime': start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'endTime': end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'limit': 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            logs = response.json()
            print(f"Found {len(logs)} log entries from last 10 minutes")
            
            # Look for your group activity
            your_group_logs = [log for log in logs if '-4627994150' in log.get('message', '')]
            print(f"\nActivity for your group (-4627994150): {len(your_group_logs)} entries")
            
            for log in your_group_logs[-10:]:  # Last 10 entries
                timestamp = log['timestamp'][:19]
                message = log['message'][:200]
                print(f"{timestamp} | {message}")
                
            # Look for multi-event activity
            multi_logs = [log for log in logs if 'multi_event' in log.get('message', '').lower() 
                         or 'update event' in log.get('message', '').lower()
                         or 'queue' in log.get('message', '').lower()]
            print(f"\nMulti-event activity: {len(multi_logs)} entries")
            
            for log in multi_logs[-5:]:  # Last 5 entries
                timestamp = log['timestamp'][:19]
                message = log['message'][:200]
                print(f"{timestamp} | {message}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_demo_logs()
