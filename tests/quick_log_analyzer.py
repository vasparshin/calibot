"""
Quick log analyzer for one-by-one bug fix verification
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from recent_logs import fetch_recent_logs
    
    print("🔍 ANALYZING LOGS FOR ONE-BY-ONE BUG FIX")
    print("=" * 60)
    
    logs = fetch_recent_logs()
    
    # Look for critical patterns
    patterns = [
        'Processing single event',
        'DELETE Event',
        'queue_confirm', 
        'one_by_one',
        'Successfully deleted',
        'multi_one',
        'Queue callback',
        'queue_continues'
    ]
    
    relevant_logs = []
    for log in logs:
        msg = log.get('message', '')
        timestamp = log.get('timestamp', '')
        
        if any(pattern in msg for pattern in patterns):
            relevant_logs.append((timestamp, msg))
    
    print(f"Found {len(relevant_logs)} relevant log entries:")
    print()
    
    for timestamp, msg in relevant_logs[-20:]:  # Show last 20 relevant entries
        print(f"{timestamp}: {msg}")
    
    # Analyze for bug patterns
    print("\n" + "=" * 60)
    print("🔬 BUG FIX ANALYSIS:")
    
    processing_events = [log for log in relevant_logs if 'Processing single event' in log[1]]
    delete_confirmations = [log for log in relevant_logs if 'DELETE Event' in log[1]]
    queue_callbacks = [log for log in relevant_logs if 'queue_confirm' in log[1]]
    
    print(f"📊 Processing single event logs: {len(processing_events)}")
    print(f"📊 DELETE Event confirmations: {len(delete_confirmations)}")
    print(f"📊 Queue callback logs: {len(queue_callbacks)}")
    
    if len(processing_events) <= len(queue_callbacks):
        print("✅ GOOD: Processing events matches or is less than queue callbacks")
    else:
        print("❌ ISSUE: More processing events than expected")
    
    # Check for sequential processing
    if len(delete_confirmations) > 1:
        print("✅ GOOD: Multiple DELETE Event confirmations (one-by-one working)")
    else:
        print("⚠️ Only one DELETE confirmation found")

except Exception as e:
    print(f"Error: {e}")
