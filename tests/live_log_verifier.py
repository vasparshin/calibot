#!/usr/bin/env python3
"""
CaliBOT Live Log Verification Tool
==================================

This tool monitors CaliBOT's live logs to verify that:
1. Multi-event workflow is functioning properly
2. Queue processing bug fixes are working
3. No "operation not found" errors occur
4. Button callbacks work correctly

Run this tool while manually testing CaliBOT to see real-time proof.
"""

import requests
import time
import json
from datetime import datetime, timedelta
import sys

# Configuration
RENDER_API_KEY = "rnd_LBHy5V82CZc9Dc8cqJJLcCCfEiNi"
SERVICE_ID = "srv-cteqfmij1k6c73ea08i0"

class LogVerifier:
    def __init__(self):
        self.last_check_time = datetime.utcnow()
        self.error_count = 0
        self.success_count = 0
        
    def fetch_new_logs(self):
        """Fetch logs since last check"""
        url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"
        headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                logs_data = response.json()
                
                # Filter for new logs since last check
                new_logs = []
                for log in logs_data[-100:]:  # Check last 100 entries
                    timestamp_str = log.get('timestamp', '')
                    message = log.get('message', '')
                    
                    try:
                        # Parse timestamp
                        log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        
                        if log_time > self.last_check_time:
                            new_logs.append({
                                'timestamp': timestamp_str,
                                'message': message,
                                'parsed_time': log_time
                            })
                    except:
                        # Skip logs with bad timestamps
                        continue
                
                # Update last check time
                if new_logs:
                    self.last_check_time = max(log['parsed_time'] for log in new_logs)
                
                return new_logs
            else:
                print(f"❌ API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []
    
    def analyze_log_entry(self, log):
        """Analyze a single log entry for relevant information"""
        message = log['message'].lower()
        timestamp = log['timestamp']
        
        # Critical errors we fixed
        if "operation not found" in message:
            print(f"🚨 {timestamp} - CRITICAL ERROR: Operation not found detected!")
            self.error_count += 1
            return "error"
            
        if "invalid isoformat string" in message:
            print(f"🚨 {timestamp} - CRITICAL ERROR: Time formatting error!")
            self.error_count += 1
            return "error"
            
        if "traceback" in message and "error" in message:
            print(f"🚨 {timestamp} - ERROR: Python exception!")
            self.error_count += 1
            return "error"
            
        # Success indicators
        if "multi_event_one_by_one" in message:
            print(f"✅ {timestamp} - SUCCESS: One-by-one selection detected")
            self.success_count += 1
            return "success"
            
        if "switch_to_one_by_one" in message:
            print(f"✅ {timestamp} - SUCCESS: One-by-one workflow activated")
            self.success_count += 1
            return "success"
            
        if "queue_complete" in message:
            print(f"✅ {timestamp} - SUCCESS: Queue completion logic working")
            self.success_count += 1
            return "success"
            
        if "format_time_24hour" in message:
            print(f"✅ {timestamp} - SUCCESS: 24-hour formatting active")
            self.success_count += 1
            return "success"
            
        if "pending operations" in message and "cleared" not in message:
            print(f"✅ {timestamp} - SUCCESS: Pending operations managed")
            self.success_count += 1
            return "success"
            
        # Queue activities
        if any(word in message for word in ["queue", "pending", "callback", "button"]):
            print(f"🔄 {timestamp} - ACTIVITY: {log['message'][:100]}...")
            return "activity"
            
        # Multi-event related
        if any(word in message for word in ["multi_event", "event_yes", "event_skip", "event_cancel"]):
            print(f"🎯 {timestamp} - MULTI-EVENT: {log['message'][:100]}...")
            return "multi_event"
            
        return "normal"

def monitor_logs():
    """Monitor logs in real-time"""
    print("🔍 CaliBOT Live Log Verification Tool")
    print("=" * 60)
    print("Monitoring live logs for multi-event workflow verification...")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    verifier = LogVerifier()
    
    print(f"⏰ Starting monitoring at {datetime.now().strftime('%H:%M:%S')}")
    print(f"💬 Now test CaliBOT multi-event features in Telegram!")
    print(f"   Try: 'move my last 2 events tomorrow'")
    print(f"   Then select 'one by one' and press Yes/Skip buttons")
    print("=" * 60)
    
    try:
        while True:
            new_logs = verifier.fetch_new_logs()
            
            if new_logs:
                print(f"\n📥 Found {len(new_logs)} new log entries:")
                
                for log in new_logs:
                    verifier.analyze_log_entry(log)
                    
                # Show current stats
                total_relevant = verifier.success_count + verifier.error_count
                if total_relevant > 0:
                    success_rate = (verifier.success_count / total_relevant) * 100
                    print(f"\n📊 Current stats: {verifier.success_count} successes, {verifier.error_count} errors ({success_rate:.1f}% success rate)")
                    
            else:
                # Show heartbeat
                sys.stdout.write(f"\r⏳ Monitoring... {datetime.now().strftime('%H:%M:%S')} - {verifier.success_count} successes, {verifier.error_count} errors")
                sys.stdout.flush()
                
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n🏁 Monitoring stopped")
        print(f"📊 Final results:")
        print(f"   ✅ Successes: {verifier.success_count}")
        print(f"   ❌ Errors: {verifier.error_count}")
        
        if verifier.error_count == 0 and verifier.success_count > 0:
            print(f"🎉 EXCELLENT: No critical errors detected!")
            print(f"✅ Multi-event workflow fixes are working properly")
        elif verifier.error_count == 0:
            print(f"✅ No errors detected (test the multi-event features to see activity)")
        else:
            print(f"⚠️ Issues detected - review the errors above")

if __name__ == "__main__":
    monitor_logs()
