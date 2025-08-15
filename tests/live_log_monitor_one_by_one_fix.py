"""
Live Log Monitor for One-by-One Bug Fix Testing

This script monitors Render logs in real-time while you manually test the
one-by-one bug fix through Telegram. It focuses on detecting the specific
log patterns that indicate whether the bug is fixed.

Usage: Run this script, then test manually in Telegram
"""

import requests
import time
import json
from datetime import datetime, timedelta

class OneByOneLogMonitor:
    def __init__(self):
        self.render_api_url = "https://api.render.com/v1"
        self.render_api_key = "rnd_OxNGMpAcYq8b3wpjdOoNdjXOHGh1"
        self.service_id = "srv-cshqdfgl6cac738oi2k0"
        self.last_check_time = datetime.utcnow()
        
    def get_recent_logs(self, minutes: int = 2) -> list:
        """Fetch recent logs from Render API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.render_api_key}",
                "Content-Type": "application/json"
            }
            
            end_time = datetime.utcnow()
            start_time = self.last_check_time
            
            url = f"{self.render_api_url}/services/{self.service_id}/logs"
            params = {
                "startTime": start_time.isoformat() + "Z",
                "endTime": end_time.isoformat() + "Z", 
                "limit": 100
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                logs = response.json()
                self.last_check_time = end_time
                return logs
            else:
                print(f"❌ Failed to fetch logs: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching logs: {e}")
            return []
    
    def analyze_logs_for_bug_patterns(self, logs: list) -> dict:
        """Analyze logs for one-by-one bug patterns"""
        analysis = {
            "processing_single_events": [],
            "delete_confirmations": [],
            "bulk_deletions": [],
            "queue_operations": [],
            "one_by_one_mode": [],
            "button_clicks": []
        }
        
        for log_entry in logs:
            message = log_entry.get("message", "")
            timestamp = log_entry.get("timestamp", "")
            
            # Look for specific patterns
            if "Processing single event" in message:
                analysis["processing_single_events"].append(f"{timestamp}: {message}")
            elif "DELETE Event" in message and "of" in message:
                analysis["delete_confirmations"].append(f"{timestamp}: {message}")
            elif "Successfully deleted" in message and "event(s)" in message:
                analysis["bulk_deletions"].append(f"{timestamp}: {message}")
            elif "queue" in message.lower() and ("confirm" in message or "skip" in message):
                analysis["queue_operations"].append(f"{timestamp}: {message}")
            elif "one_by_one_mode" in message:
                analysis["one_by_one_mode"].append(f"{timestamp}: {message}")
            elif "callback" in message.lower() and ("queue_confirm" in message or "multi_one" in message):
                analysis["button_clicks"].append(f"{timestamp}: {message}")
        
        return analysis
    
    def monitor_continuously(self, duration_minutes: int = 10):
        """Monitor logs continuously for the specified duration"""
        print(f"🔍 Starting live log monitoring for {duration_minutes} minutes...")
        print("🚨 WATCHING FOR ONE-BY-ONE BUG PATTERNS:")
        print("   - Multiple 'Processing single event' logs = BUG STILL EXISTS")
        print("   - Single 'Processing single event' per 'yes' = BUG FIXED")
        print("   - 'DELETE Event 2 of X' after first 'yes' = BUG FIXED") 
        print("   - 'Successfully deleted X event(s)!' after first 'yes' = BUG EXISTS")
        print("=" * 80)
        print("📱 Now test manually in Telegram:")
        print("1. Create 3 test events: 'create Test001 tomorrow 14:00-15:00' etc.")
        print("2. Delete them: 'delete all Test events tomorrow'")
        print("3. Click 'One by One' button")
        print("4. Click 'Yes' for first event - WATCH THE LOGS!")
        print("=" * 80)
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            logs = self.get_recent_logs()
            
            if logs:
                analysis = self.analyze_logs_for_bug_patterns(logs)
                
                # Print relevant events
                for category, entries in analysis.items():
                    if entries:
                        print(f"\n🔍 {category.upper()}:")
                        for entry in entries[-3:]:  # Show last 3 entries
                            print(f"   {entry}")
                
                # Bug detection logic
                if analysis["processing_single_events"]:
                    count = len(analysis["processing_single_events"])
                    if count == 1:
                        print(f"✅ GOOD: Only {count} event processed")
                    elif count > 1:
                        print(f"❌ POTENTIAL BUG: {count} events processed simultaneously")
                
                if analysis["delete_confirmations"]:
                    latest = analysis["delete_confirmations"][-1]
                    if "Event 2 of" in latest or "Event 3 of" in latest:
                        print("✅ GOOD: Advanced to next event confirmation")
                
                if analysis["bulk_deletions"]:
                    print("⚠️ BULK DELETION DETECTED - Check if this was after individual processing")
            
            time.sleep(3)  # Check every 3 seconds
        
        print(f"\n🔍 Monitoring completed after {duration_minutes} minutes")

def main():
    monitor = OneByOneLogMonitor()
    
    print("🎯 ONE-BY-ONE BUG FIX LOG MONITOR")
    print("This script monitors logs while you manually test the fix")
    print("Version 0.1.136 should have the bug fixed")
    
    try:
        monitor.monitor_continuously(10)  # Monitor for 10 minutes
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")

if __name__ == "__main__":
    main()
