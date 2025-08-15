#!/usr/bin/env python3
"""
Get logs from this morning around 07:57 to find your group chat ID
"""
import requests
from datetime import datetime, timedelta

def get_morning_logs():
    """Get logs from around 07:57 this morning"""
    
    print("Searching logs from this morning around 07:57...")
    
    url = 'https://api.render.com/v1/services/srv-cr5mq76ehbks739rh64g/logs'
    headers = {'Authorization': 'Bearer rnd_6KwXpcHKzNBv6dMaMIrIHwFQjTGI'}
    
    # Search around 07:57 UTC this morning
    morning_time = datetime.fromisoformat('2025-08-15T07:57:00')
    start_time = (morning_time - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    end_time = (morning_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    params = {
        'startTime': start_time,
        'endTime': end_time,
        'limit': 500
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            logs = response.json()
            print(f"Found {len(logs)} log entries")
            
            chat_ids_found = set()
            
            for log in logs:
                message = log.get('message', '')
                timestamp = log.get('timestamp', '')
                
                # Look for chat IDs in bot messages
                if 'Bot sending to chat' in message or 'chat' in message.lower():
                    print(f"{timestamp[:19]} | {message[:200]}")
                    
                    # Extract chat ID
                    if 'chat' in message and '-' in message:
                        parts = message.split()
                        for part in parts:
                            if part.startswith('-') and part.replace('-', '').isdigit():
                                chat_ids_found.add(part)
                                
            print(f"\nChat IDs found around 07:57:")
            for chat_id in sorted(chat_ids_found):
                print(f"  {chat_id}")
                
            return sorted(chat_ids_found)
                
    except Exception as e:
        print(f"Error getting logs: {e}")
        return []

if __name__ == "__main__":
    chat_ids = get_morning_logs()
    print(f"\nFound {len(chat_ids)} chat IDs from morning logs")
