#!/usr/bin/env python3
"""
Enhanced CaliBOT Log Viewer - focuses on LLM logging verification
Uses the working Render API configuration
"""
import requests
from datetime import datetime

# Working configuration
SERVICE_ID = "srv-d1vqbkp5pdvs73echbeg"
OWNER_ID = "tea-d1vp1ph5pdvs73ebf50g"
API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"

def get_calibot_logs(limit=100):
    """Get CaliBOT logs - WORKING VERSION"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {
        "ownerId": OWNER_ID,
        "resource": SERVICE_ID,
        "limit": limit
    }
    
    try:
        response = requests.get("https://api.render.com/v1/logs", headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            return logs
        else:
            print(f"❌ API Error {response.status_code}: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def analyze_llm_logging(logs):
    """Analyze logs for LLM logging patterns"""
    
    llm_logs = []
    datetime_error_count = 0
    logging_patterns = {
        'complete_system': 0,
        'complete_user': 0,
        'complete_response': 0,
        'system_chunks': 0,
        'length_indicators': 0,
        'truncation_indicators': 0
    }
    
    for log in logs:
        message = log.get('message', '')
        timestamp = log.get('timestamp', '')
        
        # Check for datetime error
        if 'cannot access local variable' in message and 'datetime' in message:
            datetime_error_count += 1
            
        # Check for LLM logging patterns
        if any(keyword in message for keyword in [
            '🔍 LLM', 'COMPLETE SYSTEM', 'COMPLETE USER', 'COMPLETE LLM RESPONSE',
            'System chunk', 'LLM CALL DEBUG', 'LLM RESPONSE DEBUG'
        ]):
            llm_logs.append({
                'timestamp': timestamp,
                'message': message,
                'type': 'llm_debug'
            })
            
            # Count specific patterns
            if 'COMPLETE SYSTEM MESSAGE' in message:
                logging_patterns['complete_system'] += 1
            if 'COMPLETE USER MESSAGE' in message:
                logging_patterns['complete_user'] += 1
            if 'COMPLETE LLM RESPONSE' in message:
                logging_patterns['complete_response'] += 1
            if 'System chunk' in message:
                logging_patterns['system_chunks'] += 1
            if 'Length ' in message and 'chars' in message:
                logging_patterns['length_indicators'] += 1
            if '...' in message and ('truncated' in message.lower() or 'preview' in message.lower()):
                logging_patterns['truncation_indicators'] += 1
                
    return llm_logs, datetime_error_count, logging_patterns

def main():
    """Main execution"""
    print("🔍 CaliBOT LLM Logging Analysis")
    print("=" * 50)
    print(f"⏰ {datetime.now()}")
    print()
    
    # Fetch logs
    print("📡 Fetching recent logs...")
    logs = get_calibot_logs(200)  # Get more logs for better analysis
    
    if not logs:
        print("❌ Could not fetch logs")
        return 1
        
    print(f"✅ Fetched {len(logs)} log entries")
    
    # Analyze LLM logging
    llm_logs, datetime_errors, patterns = analyze_llm_logging(logs)
    
    print(f"🔍 Found {len(llm_logs)} LLM-related log entries")
    print(f"❌ Found {datetime_errors} datetime errors")
    print()
    
    # Pattern analysis
    print("📊 LLM LOGGING PATTERNS:")
    print("-" * 30)
    for pattern, count in patterns.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {pattern.replace('_', ' ').title()}: {count}")
    print()
    
    # Show recent LLM logs
    if llm_logs:
        print("🔍 RECENT LLM LOGGING ACTIVITY:")
        print("-" * 40)
        for i, log in enumerate(llm_logs[-10:], 1):  # Last 10 LLM logs
            timestamp = log['timestamp'][:19] if log['timestamp'] else 'unknown'
            message = log['message'][:120] + '...' if len(log['message']) > 120 else log['message']
            print(f"{i:2d}. [{timestamp}] {message}")
    else:
        print("⚠️ No LLM logging activity found")
        
    print()
    
    # Show recent errors if any
    error_logs = [log for log in logs if any(keyword in log.get('message', '').lower() for keyword in ['error', 'exception', 'failed'])]
    if error_logs:
        print("❌ RECENT ERRORS:")
        print("-" * 20)
        for i, log in enumerate(error_logs[-5:], 1):  # Last 5 errors
            timestamp = log['timestamp'][:19] if log['timestamp'] else 'unknown'
            message = log['message'][:100] + '...' if len(log['message']) > 100 else log['message']
            print(f"{i:2d}. [{timestamp}] {message}")
    else:
        print("✅ No recent errors found")
        
    print()
    
    # Overall assessment
    print("🎯 LOGGING ASSESSMENT:")
    print("-" * 25)
    
    if datetime_errors > 0:
        print(f"❌ CRITICAL: {datetime_errors} datetime import errors - system not working!")
    elif patterns['complete_system'] > 0 and patterns['complete_user'] > 0:
        print("✅ GOOD: Complete LLM logging is active")
        if patterns['truncation_indicators'] > 0:
            print("⚠️ WARNING: Some truncation still detected")
        else:
            print("✅ EXCELLENT: No truncation indicators found")
    elif len(llm_logs) > 0:
        print("⚠️ PARTIAL: Some LLM logging detected but incomplete")
    else:
        print("❌ MISSING: No LLM logging activity detected")
        
    return 0

if __name__ == "__main__":
    exit(main())
