#!/usr/bin/env python3
"""
Direct Render API Log Access - PowerShell Compatible
No emojis, proper Unicode handling, structured logging
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Service Configuration
OWNER_ID = "tea-kks41ij4d82bpujdqv0g"
SERVICE_ID = "srv-d1vqbkp5pdvs73echbeg"

def get_render_api_key() -> Optional[str]:
    """Get API key from environment or return None"""
    return os.getenv('RENDER_API_KEY')

def fetch_logs_via_api(minutes_back: int = 30, limit: int = 100) -> List[Dict]:
    """
    Fetch logs directly via Render API
    Reference: https://api-docs.render.com/openapi/6140fb3daeae351056086186
    """
    api_key = get_render_api_key()
    if not api_key:
        print("ERROR: RENDER_API_KEY not set")
        return []
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=minutes_back)
    
    params = {
        "ownerId": OWNER_ID,
        "resource": SERVICE_ID,
        "limit": limit,
        "startTime": start_time.isoformat() + "Z",
        "endTime": end_time.isoformat() + "Z"
    }
    
    try:
        print(f"[INFO] Fetching logs from {start_time.strftime('%H:%M:%S')} to {end_time.strftime('%H:%M:%S')} UTC")
        
        response = requests.get(
            "https://api.render.com/v1/logs", 
            headers=headers, 
            params=params, 
            timeout=15
        )
        
        print(f"[INFO] API Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            print(f"[INFO] Retrieved {len(logs)} log entries")
            return logs
        elif response.status_code == 429:
            print("[WARNING] Rate limited - try again in 1 minute")
            return []
        else:
            print(f"[ERROR] API Error {response.status_code}: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"[ERROR] Exception fetching logs: {e}")
        return []

def filter_important_logs(logs: List[Dict], filter_terms: List[str] = None) -> List[Dict]:
    """Filter logs for important CaliBOT events"""
    if filter_terms is None:
        # Default: show recent startup and any bot activity
        filter_terms = [
            "CaliBOT", "starting up", "Version:", "intent", "create", "update", 
            "error", "start_time", "nlp_agent", "EventQueueHandler", "multi_event",
            "webhook", "User message", "ERROR", "CRITICAL", "Extracted intent"
        ]
    
    important = []
    for log in logs:
        message = log.get("message", "").strip()
        
        # If filter terms provided, use them
        if filter_terms and any(term.lower() in message.lower() for term in filter_terms):
            important.append(log)
        # If no filter terms, show everything
        elif not filter_terms:
            important.append(log)
    
    return important

def format_log_for_analysis(log: Dict) -> str:
    """Format log entry for analysis - no emojis"""
    timestamp = log.get("timestamp", "")
    message = log.get("message", "").strip()
    
    if not message:
        return None
    
    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_str = dt.strftime("%H:%M:%S")
    except:
        time_str = timestamp[:8] if len(timestamp) >= 8 else "unknown"
    
    # Categorize log types
    if "ERROR" in message or "error" in message.lower():
        prefix = "[ERROR]"
    elif "intent" in message.lower() or "nlp_agent" in message.lower():
        prefix = "[INTENT]"
    elif "multi_event" in message.lower() or "EventQueueHandler" in message:
        prefix = "[QUEUE]"
    elif "webhook" in message.lower() or "User message" in message:
        prefix = "[USER]"
    else:
        prefix = "[INFO]"
    
    return f"{prefix} {time_str} | {message}"

def analyze_intent_extraction_errors(logs: List[Dict]) -> Dict:
    """Analyze logs for intent extraction issues"""
    analysis = {
        "total_logs": len(logs),
        "start_time_errors": 0,
        "intent_extractions": 0,
        "create_intents": 0,
        "update_intents": 0,
        "query_fallbacks": 0,
        "other_errors": 0
    }
    
    for log in logs:
        message = log.get("message", "")
        
        if "Error extracting intent:" in message and '"start_time"' in message:
            analysis["start_time_errors"] += 1
        elif "Extracted intent:" in message:
            analysis["intent_extractions"] += 1
            if '"intent": "create"' in message:
                analysis["create_intents"] += 1
            elif '"intent": "update"' in message:
                analysis["update_intents"] += 1
            elif '"intent": "query"' in message:
                analysis["query_fallbacks"] += 1
        elif "ERROR" in message:
            analysis["other_errors"] += 1
    
    return analysis

def main():
    """Main function - PowerShell compatible output"""
    if len(sys.argv) > 1:
        filter_terms = sys.argv[1:]
        print(f"[INFO] Filtering for: {', '.join(filter_terms)}")
    else:
        filter_terms = None
    
    print("=" * 80)
    print("CaliBOT Render API Log Analysis")
    print("=" * 80)
    
    # Fetch logs
    logs = fetch_logs_via_api()
    if not logs:
        print("[ERROR] No logs retrieved")
        return
    
    # Filter important logs
    important_logs = filter_important_logs(logs, filter_terms)
    print(f"[INFO] Found {len(important_logs)} important log entries")
    print("-" * 80)
    
    # Display filtered logs
    for log in important_logs:
        formatted = format_log_for_analysis(log)
        if formatted:
            print(formatted)
    
    print("-" * 80)
    
    # Analysis
    analysis = analyze_intent_extraction_errors(important_logs)
    print("ANALYSIS SUMMARY:")
    print(f"  - Total logs analyzed: {analysis['total_logs']}")
    print(f"  - 'start_time' errors: {analysis['start_time_errors']}")
    print(f"  - Intent extractions: {analysis['intent_extractions']}")
    print(f"  - Create intents: {analysis['create_intents']}")
    print(f"  - Update intents: {analysis['update_intents']}")
    print(f"  - Query fallbacks: {analysis['query_fallbacks']}")
    print(f"  - Other errors: {analysis['other_errors']}")
    
    if analysis['start_time_errors'] > 0:
        print("[WARNING] Still seeing 'start_time' errors - LLM fixes may not be working")
    elif analysis['create_intents'] > 0 or analysis['update_intents'] > 0:
        print("[SUCCESS] Intent extraction appears to be working")

if __name__ == "__main__":
    main()
